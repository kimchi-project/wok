#
# Project Wok
#
# Copyright IBM Corp, 2016
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#

import json
import logging
import logging.handlers
import os.path

from cherrypy.process.plugins import BackgroundTask
from datetime import datetime
from tempfile import NamedTemporaryFile

from wok.config import config, get_log_download_path
from wok.exception import InvalidParameter, OperationFailed
from wok.utils import ascii_dict, remove_old_files


# Log search setup
FILTER_FIELDS = ['app', 'date', 'download', 'req', 'user', 'time']
LOG_DOWNLOAD_URI = "/data/logs/%s"
LOG_DOWNLOAD_TIMEOUT = 6
LOG_FORMAT = "[%(date)s %(time)s] %(req)-6s %(app)-11s %(user)s: %(message)s\n"
SECONDS_PER_HOUR = 360

# Log handler setup
MAX_FILE_SIZE = 3072000
NUM_BACKUP_FILES = 1
REQUEST_LOG_FILE = "wok-req.log"
WOK_REQUEST_LOGGER = "wok_request_logger"


class RequestLogger(object):
    def __init__(self):
        log = os.path.join(config.get("logging", "log_dir"), REQUEST_LOG_FILE)
        h = logging.handlers.RotatingFileHandler(log, 'a',
                                                 maxBytes=MAX_FILE_SIZE,
                                                 backupCount=NUM_BACKUP_FILES)
        h.setFormatter(logging.Formatter('%(message)s'))
        self.handler = h
        self.logger = logging.getLogger(WOK_REQUEST_LOGGER)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        # start request log's downloadable temporary files removal task
        interval = LOG_DOWNLOAD_TIMEOUT * SECONDS_PER_HOUR
        self.clean_task = BackgroundTask(interval, self.cleanLogFiles)
        self.clean_task.start()

    def cleanLogFiles(self):
        globexpr = "%s/*.txt" % get_log_download_path()
        remove_old_files(globexpr, LOG_DOWNLOAD_TIMEOUT)


class RequestParser(object):
    def __init__(self):
        logger = logging.getLogger(WOK_REQUEST_LOGGER)
        self.baseFile = logger.handlers[0].baseFilename
        self.downloadDir = get_log_download_path()

    def generateLogFile(self, records):
        """
        Generates a log-format text file with lines for each record specified.
        Returns a download URI for the generated file.
        """
        try:
            # sort records chronologically
            sortedList = sorted(records, key=lambda k: k['date'] + k['time'])

            # generate log file
            fd = NamedTemporaryFile(mode='w', dir=self.downloadDir,
                                    suffix='.txt', delete=False)

            with fd:
                for record in sortedList:
                    asciiRecord = ascii_dict(record)
                    fd.write(LOG_FORMAT % asciiRecord)

                fd.close()
        except IOError as e:
            raise OperationFailed("WOKLOG0002E", {'err': str(e)})

        return LOG_DOWNLOAD_URI % os.path.basename(fd.name)

    def getRecords(self):
        records = self.getRecordsFromFile(self.baseFile)

        for count in range(NUM_BACKUP_FILES):
            filename = ".".join([self.baseFile, str(count + 1)])
            records.extend(self.getRecordsFromFile(filename))

        # Return ordered by latest events first
        return sorted(records, key=lambda k: k['date'] + k['time'],
                      reverse=True)

    def getRecordsFromFile(self, filename):
        """
        Returns a list of dict, where each dict corresponds to a request
        record.
        """
        records = []

        if not os.path.exists(filename):
            return []

        # read records from file
        try:
            with open(filename) as f:
                line = f.readline()
                while line != "":
                    data = line.split(">>>")
                    if len(data) > 1:
                        record = json.JSONDecoder().decode(data[0])
                        record['message'] = data[1].strip()
                        records.append(record)

                    line = f.readline()

            f. close()
        except IOError as e:
            raise OperationFailed("WOKLOG0002E", {'err': str(e)})

        return records

    def getFilteredRecords(self, filter_params):
        """
        Returns a dict containing the filtered list of request log entries
        (dicts), and an optional uri for downloading results in a text file.
        """
        uri = None
        results = []
        records = self.getRecords()

        # fail for unrecognized filter options
        for key in filter_params.keys():
            if key not in FILTER_FIELDS:
                filters = ", ".join(FILTER_FIELDS)
                raise InvalidParameter("WOKLOG0001E", {"filters": filters})

        download = filter_params.pop('download', False)

        # filter records according to parameters
        for record in records:
            if all(key in record and record[key] == val
                   for key, val in filter_params.iteritems()):
                results.append(record)

        # download option active: generate text file and provide donwload uri
        if download and len(results) > 0:
            uri = self.generateLogFile(results)

        return {'uri': uri, 'records': results}


class RequestRecord(object):
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

        # register timestamp
        timestamp = datetime.today()
        self.kwargs['date'] = timestamp.strftime('%Y-%m-%d')
        self.kwargs['time'] = timestamp.strftime('%H:%M:%S')

    def __str__(self):
        info = json.JSONEncoder().encode(self.kwargs)
        return '%s >>> %s' % (info, self.message)

    def log(self):
        reqLogger = logging.getLogger(WOK_REQUEST_LOGGER)
        reqLogger.info(self)
