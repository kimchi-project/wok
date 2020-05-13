#
# Project Wok
#
# Copyright IBM Corp, 2015-2016
#
# Code derived from Project Kimchi
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
import threading
import time
import traceback
import uuid

import cherrypy
from wok.exception import InvalidOperation
from wok.exception import OperationFailed
from wok.exception import WokException
from wok.reqlogger import ASYNCTASK_REQUEST_METHOD
from wok.reqlogger import log_request

MSG_FAILED = 'WOKASYNC0002L'
MSG_SUCCESS = 'WOKASYNC0001L'
tasks_queue = {}


def clean_old_tasks():
    """
    Remove from tasks_queue any task that started before 12 hours ago and has
    current status equal do finished or failed.
    """
    for id, task in tasks_queue.copy().items():
        if task.timestamp < (time.time() - 43200):
            if (task.status == 'finished') or (task.status == 'failed'):
                task.remove()


def save_request_log_id(log_id, task_id):
    tasks_queue[task_id].log_id = log_id


class AsyncTask(object):
    def __init__(self, target_uri, fn, opaque=None, kill_cb=None):
        # task info
        self.id = str(uuid.uuid1())
        self.target_uri = target_uri
        self.fn = fn
        self.kill_cb = kill_cb
        self.log_id = None
        self.timestamp = time.time()

        # log info - save info to log on task finish
        self.app = ''
        if cherrypy.request.app:
            self.app = cherrypy.request.app.script_name

        # task context
        self.status = 'running'
        self.message = 'The request is being processing.'
        self._cp_request = cherrypy.serving.request
        self.thread = threading.Thread(
            target=self._run_helper, args=(opaque, self._status_cb)
        )
        self.thread.setDaemon(True)
        self.thread.start()

        # let's prevent memory leak in tasks_queue
        clean_old_tasks()
        tasks_queue[self.id] = self

    def _log(self, code, status, exception=None):
        log_request(
            code,
            {'target_uri': self.target_uri},
            exception,
            ASYNCTASK_REQUEST_METHOD,
            status,
            app=self.app,
            user='',
            ip='',
        )

    def _status_cb(self, message, success=None, exception=None):
        if success is not None:
            if success:
                self._log(MSG_SUCCESS, 200)
                self.status = 'finished'
            else:
                self._log(MSG_FAILED, 400, exception)
                self.status = 'failed'

        if message.strip():
            self.message = message

    def _run_helper(self, opaque, cb):
        cherrypy.serving.request = self._cp_request
        try:
            self.fn(cb, opaque)
        except WokException as e:
            cherrypy.log.error_log.error(f'Error in async_task {self.id}')
            cherrypy.log.error_log.error(traceback.format_exc())
            cb(str(e), success=False, exception=e)
        except Exception as e:
            cherrypy.log.error_log.error(f'Error in async_task {self.id}')
            cherrypy.log.error_log.error(traceback.format_exc())
            cb(str(e), success=False)

    def remove(self):
        try:
            del tasks_queue[self.id]
        except KeyError:
            msg = f"There's no task_id {self.id} in tasks_queue."
            cherrypy.log.error_log.error(msg)

    def kill(self):
        if self.kill_cb is None:
            raise InvalidOperation('WOKASYNC0002E')

        try:
            self.kill_cb()
            self.status = 'killed'
            self.message = 'Task killed by user.'
        except Exception as e:
            self.message = str(e)
            raise OperationFailed('WOKASYNC0004E', {'err': str(e)})
