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

import json
import time
import unittest
import utils

from functools import partial

from wok.asynctask import AsyncTask

test_server = None
model = None


def setUpModule():
    global test_server, model

    utils.patch_auth()
    test_server = utils.run_server(test_mode=True)


def tearDownModule():
    test_server.stop()


class APITests(unittest.TestCase):

    def setUp(self):
        self.request = partial(utils.request)

    def test_config(self):
        resp = self.request('/config').read()
        conf = json.loads(resp)
        keys = ["auth", "proxy_port", "websockets_port", "version",
                "server_root"]
        self.assertEquals(sorted(keys), sorted(conf.keys()))

    def test_user_log(self):
        # Login and logout to make sure there there are entries in user log
        hdrs = {'AUTHORIZATION': '',
                'Content-Type': 'application/json',
                'Accept': 'application/json'}

        user, pw = utils.fake_user.items()[0]
        req = json.dumps({'username': user, 'password': pw})
        resp = self.request('/login', req, 'POST', hdrs)

        resp = self.request('/logout', '{}', 'POST', hdrs)
        self.assertEquals(200, resp.status)

        # Test user logs JSON response
        resp = self.request('/logs?app=wok&download=True').read()
        conf = json.loads(resp)
        self.assertIn('records', conf)
        self.assertIn('uri', conf)

        # Test download URL
        uri = conf.get('uri')
        self.assertTrue(len(uri) > 0)

        # Test each record key
        records = conf.get('records', [])
        self.assertGreaterEqual(records, 1)
        for record in records:
            # Test search by app
            self.assertEquals(record['app'], 'wok')

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
        tasks = json.loads(self.request('/tasks').read())
        self.assertLessEqual(1, len(tasks))
        time.sleep(10)
        resp = self.request('/tasks/%s' % taskid, '{}', 'DELETE')
        self.assertEquals(204, resp.status)
        task = json.loads(self.request('/tasks/%s' % taskid).read())
        self.assertEquals('killed', task['status'])
