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

import time
import unittest

from utils import wait_task

from wok.asynctask import AsyncTask, tasks_queue
from wok.model import model


class AsyncTaskTests(unittest.TestCase):
    def _quick_op(self, cb, message):
        cb(message, True)

    def _long_op(self, cb, params):
        time.sleep(params.get('delay', 3))
        cb(params.get('message', ''), params.get('result', False))

    def _continuous_ops(self, cb, params):
        cb("step 1 OK")
        time.sleep(2)
        cb("step 2 OK")
        time.sleep(2)
        cb("step 3 OK", params.get('result', True))

    def _task_lookup(self, id):
        task = tasks_queue[id]
        return {'id': id,
                'status': task.status,
                'message': task.message,
                'target_uri': task.target_uri}

    def test_async_tasks(self):
        class task_except(Exception):
            pass

        def abnormal_op(cb, params):
            try:
                raise task_except
            except:
                cb("Exception raised", False)

        taskid = AsyncTask('', self._quick_op, 'Hello').id
        wait_task(self._task_lookup, taskid)
        self.assertEquals('finished', self._task_lookup(taskid)['status'])
        self.assertEquals('Hello', self._task_lookup(taskid)['message'])

        params = {'delay': 3, 'result': False,
                  'message': 'It was not meant to be'}
        taskid = AsyncTask('', self._long_op, params).id
        self.assertEquals('running', self._task_lookup(taskid)['status'])
        self.assertEquals('The request is being processing.',
                          self._task_lookup(taskid)['message'])
        wait_task(self._task_lookup, taskid)
        self.assertEquals('failed', self._task_lookup(taskid)['status'])
        self.assertEquals('It was not meant to be',
                          self._task_lookup(taskid)['message'])

        taskid = AsyncTask('', abnormal_op, {}).id
        wait_task(self._task_lookup, taskid)
        self.assertEquals('Exception raised',
                          self._task_lookup(taskid)['message'])
        self.assertEquals('failed', self._task_lookup(taskid)['status'])

        taskid = AsyncTask('', self._continuous_ops, {'result': True}).id
        self.assertEquals('running', self._task_lookup(taskid)['status'])
        wait_task(self._task_lookup, taskid, timeout=10)
        self.assertEquals('finished', self._task_lookup(taskid)['status'])

    def test_async_tasks_model(self):
        class task_except(Exception):
            pass

        def abnormal_op(cb, params):
            try:
                raise task_except
            except:
                cb("Exception raised", False)

        inst = model.Model()
        taskid = AsyncTask('', self._quick_op, 'Hello').id
        inst.task_wait(taskid)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])
        self.assertEquals('Hello', inst.task_lookup(taskid)['message'])

        params = {'delay': 3, 'result': False,
                  'message': 'It was not meant to be'}
        taskid = AsyncTask('', self._long_op, params).id
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        self.assertEquals('The request is being processing.',
                          inst.task_lookup(taskid)['message'])
        inst.task_wait(taskid)
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])
        self.assertEquals('It was not meant to be',
                          inst.task_lookup(taskid)['message'])

        taskid = AsyncTask('', abnormal_op, {}).id
        inst.task_wait(taskid)
        self.assertEquals('Exception raised',
                          inst.task_lookup(taskid)['message'])
        self.assertEquals('failed', inst.task_lookup(taskid)['status'])

        taskid = AsyncTask('', self._continuous_ops, {'result': True}).id
        self.assertEquals('running', inst.task_lookup(taskid)['status'])
        inst.task_wait(taskid, timeout=10)
        self.assertEquals('finished', inst.task_lookup(taskid)['status'])

    def test_kill_async_task(self):
        def continuous_ops(cb, params):
            for i in range(30):
                cb("...step %s OK" % i)
                time.sleep(2)
            cb("FINAL step OK", params.get('result', True))

        def kill_function():
            print "... killing task...... BUUUUUUM"

        taskid = AsyncTask('', continuous_ops, {'result': True},
                           kill_function).id
        self.assertEquals('running', self._task_lookup(taskid)['status'])
        time.sleep(10)
        tasks_queue[taskid].kill()
        self.assertEquals('killed', self._task_lookup(taskid)['status'])
