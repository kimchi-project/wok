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

import glob
import json
import logging
import logging.handlers
import os.path
import time

from cherrypy.process.plugins import BackgroundTask
from tempfile import NamedTemporaryFile

from wok.config import config, get_log_download_path
from wok.exception import InvalidParameter, OperationFailed
from wok.message import WokMessage
from wok.stringutils import ascii_dict
from wok.utils import remove_old_files


# Log search setup
FILTER_FIELDS = ['app', 'date', 'ip', 'req', 'status' 'user', 'time']
LOG_DOWNLOAD_URI = "/data/logs/%s"
LOG_DOWNLOAD_TIMEOUT = 6
LOG_FORMAT = "[%(date)s %(time)s %(zone)s] %(req)-6s %(status)s %(app)-11s " \
             "%(ip)-15s %(user)s: %(message)s\n"
RECORD_TEMPLATE_DICT = {
    'date': '',
    'time': '',
    'zone': '',
    'req': '',
    'status': '',
    'app': '',
    'ip': '',
    'user': '',
    'message': '',
}
SECONDS_PER_HOUR = 360
TS_DATE_FORMAT = "%Y-%m-%d"
TS_TIME_FORMAT = "%H:%M:%S"
TS_ZONE_FORMAT = "%Z"
UNSAFE_REQUEST_PARAMETERS = ['password', 'passwd']

# Log handler setup
REQUEST_LOG_FILE = "wok-req.log"
WOK_REQUEST_LOGGER = "wok_request_logger"


class RequestLogger(object):
    def __init__(self):
        log = os.path.join(config.get("logging", "log_dir"), REQUEST_LOG_FILE)
        h = logging.handlers.WatchedFileHandler(log, 'a')
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
                    asciiRecord = RECORD_TEMPLATE_DICT
                    asciiRecord.update(ascii_dict(record))
                    fd.write(LOG_FORMAT % asciiRecord)

                fd.close()
        except IOError as e:
            raise OperationFailed("WOKLOG0002E", {'err': str(e)})

        return LOG_DOWNLOAD_URI % os.path.basename(fd.name)

    def getTranslatedMessage(self, record, params):
        code = record.get('msgCode', '')
        app = record.get('app', 'wok')
        plugin = None
        if app != 'wok':
            plugin = "/plugins/%s" % app

        msg = WokMessage(code, params, plugin)
        return msg.get_text(prepend_code=False, translate=True)

    def getRecords(self):
        records = self.getRecordsFromFile(self.baseFile)

        for filename in glob.glob(self.baseFile + "-*[!.gz]"):
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

                        if len(data) > 2:
                            # new log format: translate message on the fly
                            params = json.JSONDecoder().decode(data[1])
                            msg = self.getTranslatedMessage(record, params)
                        else:
                            # make it compatible with v2.2 log files, which
                            # messages are already translated
                            msg = data[1].strip()

                        record['message'] = msg
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
        download = filter_params.pop('download', False)

        # fail for unrecognized filter options
        for key in filter_params.keys():
            if key not in FILTER_FIELDS:
                filters = ", ".join(FILTER_FIELDS)
                raise InvalidParameter("WOKLOG0001E", {"filters": filters})

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
    def __init__(self, msgParams, **kwargs):
        # log record data
        self.logData = kwargs

        # data for message translation
        self.code = self.logData['msgCode']
        self.params = self.getSafeReqParams(msgParams)

        # register timestamp in local time
        timestamp = time.localtime()
        self.logData['date'] = time.strftime(TS_DATE_FORMAT, timestamp)
        self.logData['time'] = time.strftime(TS_TIME_FORMAT, timestamp)
        self.logData['zone'] = time.strftime(TS_ZONE_FORMAT, timestamp)

    def getSafeReqParams(self, params):
        result = params.copy()
        for param in UNSAFE_REQUEST_PARAMETERS:
            result.pop(param, None)
        return result

    def __str__(self):
        msg = WokMessage(self.code, self.params)
        msgText = msg.get_text(prepend_code=False, translate=False)
        logData = json.JSONEncoder().encode(self.logData)
        msgParams = json.JSONEncoder().encode(self.params)
        return '%s >>> %s >>> %s' % (logData, msgParams, msgText)

    def log(self):
        reqLogger = logging.getLogger(WOK_REQUEST_LOGGER)
        reqLogger.info(self)
