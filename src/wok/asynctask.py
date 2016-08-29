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

import cherrypy
import threading
import time
import traceback
import uuid


tasks_queue = {}


def clean_old_tasks():
    """
    Remove from tasks_queue any task that started before 12 hours ago and has
    current status equal do finished or failed.
    """
    for id, task in tasks_queue.items():
        if (task.timestamp < (time.time()-43200)):
            if (task.status is 'finished') or (task.status is 'failed'):
                task.remove()


class AsyncTask(object):
    def __init__(self, target_uri, fn, opaque=None):
        self.id = str(uuid.uuid1())
        self.target_uri = target_uri
        self.fn = fn
        self.status = 'running'
        self.message = 'The request is being processing.'
        self.timestamp = time.time()
        self._cp_request = cherrypy.serving.request
        self.thread = threading.Thread(target=self._run_helper,
                                       args=(opaque, self._status_cb))
        self.thread.setDaemon(True)
        self.thread.start()
        # let's prevent memory leak in tasks_queue
        clean_old_tasks()
        tasks_queue[self.id] = self

    def _status_cb(self, message, success=None):
        if success is not None:
            self.status = 'finished' if success else 'failed'

        if message.strip():
            self.message = message

    def _run_helper(self, opaque, cb):
        cherrypy.serving.request = self._cp_request
        try:
            self.fn(cb, opaque)
        except Exception, e:
            cherrypy.log.error_log.error("Error in async_task %s " % self.id)
            cherrypy.log.error_log.error(traceback.format_exc())
            cb(e.message, False)

    def remove(self):
        try:
            del tasks_queue[self.id]
        except KeyError:
            msg = "There's no task_id %s in tasks_queue. Nothing changed."
            cherrypy.log.error_log.error(msg % self.id)
