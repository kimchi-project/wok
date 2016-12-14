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

import cherrypy
import glob
import json
import logging
import logging.handlers
import os.path
import time
import uuid

from cherrypy.process.plugins import BackgroundTask
from tempfile import NamedTemporaryFile

from wok.auth import USER_NAME
from wok.config import get_log_download_path, paths
from wok.exception import InvalidParameter, OperationFailed
from wok.message import WokMessage
from wok.stringutils import ascii_dict
from wok.utils import remove_old_files


# Log search setup
FILTER_FIELDS = ['app', 'date', 'ip', 'req', 'status', 'user', 'time']
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
REQUEST_LOG_FILE = "user-requests.data"
WOK_REQUEST_LOGGER = "wok_request_logger"

# AsyncTask handling
ASYNCTASK_REQUEST_METHOD = 'TASK'


def log_request(code, params, exception, method, status, app=None, user=None,
                ip=None):
    '''
    Add an entry to user request log

    @param settings
        base Measurement base, accepts 2 or 10. defaults to 2.
        unit The unit of the measurement, e.g., B, Bytes/s, bps, etc.
    @param code message code (ending with L) for the request made by user
    @param params templating parameters for the message referred by code
    @param exception None if no exception, or a dict containing
        code error message code (ending with E, I or W)
        params templating parameters for the message referred by code
    @param method the string corresponding to HTTP method (GET, PUT, POST,
        DELETE) or the string 'TASK', meaning a log entry to track completion
        of an asynchronous task. 'TASK' log entries are not visible to user.
    @param status HTTP request status code
    @param app the root URI of the mounted cherrypy application. Defaults to
        cherrypy request application
    @param user the logged in user that made the request. Defaults to cherrypy
        request user
    @param ip the IP address of the user that made the request. Defaults to
        cherrypy request remote IP address

    @returns ID of log entry
    '''
    if app is None:
        app = cherrypy.request.app.script_name

    if user is None:
        user = cherrypy.session.get(USER_NAME, 'N/A') or 'N/A'

    if ip is None:
        ip = cherrypy.request.remote.ip

    log_id = RequestRecord(
        {'code': code, 'params': params},
        exception,
        app=app,
        req=method,
        status=status,
        user=user,
        ip=ip
    ).log()

    return log_id


class RequestLogger(object):
    def __init__(self):
        log = os.path.join(paths.state_dir, REQUEST_LOG_FILE)
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

    def getTranslatedMessage(self, message, error, app_root):
        code = message.get('code', '')
        params = message.get('params', {})
        msg = WokMessage(code, params, app_root)
        text = msg.get_text(prepend_code=False, translate=True)

        if error:
            code = error.get('code', '')
            params = error.get('params', {})
            msg = WokMessage(code, params, app_root)
            text += ' (%s)' % msg.get_text(prepend_code=True, translate=True)

        return text

    def getRecords(self):
        records = self.getRecordsFromFile(self.baseFile)

        for filename in glob.glob(self.baseFile + "-*[!.gz]"):
            records.extend(self.getRecordsFromFile(filename))

        # normalize entries
        normalized = {}
        asynctask_updates = []
        for record in records:
            # because async tasks run in another thread, their record entry
            # may be recorded before original request record. Since we use
            # them to just update original request record, do it afterwards
            if record['info']['req'] == ASYNCTASK_REQUEST_METHOD:
                asynctask_updates.append(record)
                continue

            # initial request entry: generate translated message text
            message = record.pop('message')
            error = record.pop('error', None)
            uri = record['info']['app']
            text = self.getTranslatedMessage(message, error, uri)
            record['info']['message'] = text

            # get user-friendly app name
            app_name = 'wok'
            app = cherrypy.tree.apps.get(uri)
            if app:
                app_name = app.root.domain

            record['info']['app'] = app_name

            id = record.pop('id')
            normalized[id] = record['info']

        # time to update original records based on async task records
        for record in asynctask_updates:
            id = record.pop('id')

            # task id may not exist, since GET requests are not logged but
            # may generate tasks (i.e. AsyncResource)
            if id in normalized:
                normalized[id]['status'] = record['info']['status']

        # return results in chronological reverse order
        return sorted(normalized.values(), key=lambda k: k['date'] + k['time'],
                      reverse=True)

    def getRecordsFromFile(self, filename):
        """
        Returns a list of dict, where each dict corresponds to a request
        record.
        """
        records = []

        if not os.path.exists(filename):
            return []

        try:
            with open(filename) as f:
                line = f.readline()
                while line != "":
                    record = json.JSONDecoder().decode(line)
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
    def __init__(self, message, error, id=None, **kwargs):
        # data for message translation
        self.message = {
            'code': message['code'],
            'params': self.getSafeReqParams(message['params']),
        }

        # data for error translation (WokException)
        self.error = None
        if error:
            self.error = {
                'code': error.code,
                'params': error.params,
            }

        # log entry info
        self.id = id or str(uuid.uuid4())
        self.info = kwargs

        # generate timestamp
        timestamp = time.localtime()
        self.info.update({
            'date': time.strftime(TS_DATE_FORMAT, timestamp),
            'time': time.strftime(TS_TIME_FORMAT, timestamp),
            'zone': time.strftime(TS_ZONE_FORMAT, timestamp),
        })

    def getSafeReqParams(self, params):
        result = params.copy()
        for param in UNSAFE_REQUEST_PARAMETERS:
            result.pop(param, None)
        return result

    def __str__(self):
        entry = {
            "id": self.id,
            "message": self.message,
            "error": self.error,
            "info": self.info,
        }

        return json.JSONEncoder().encode(entry)

    def log(self):
        reqLogger = logging.getLogger(WOK_REQUEST_LOGGER)
        reqLogger.info(self)
        return self.id
