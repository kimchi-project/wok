#
# Project Wok
#
# Copyright IBM Corp, 2013-2017
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
import json
import unittest

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server


test_server = None
model = None


def setup_server(environment='development'):
    global test_server, model

    patch_auth()
    test_server = run_server(test_mode=True, environment=environment)


class ExceptionTests(unittest.TestCase):
    def tearDown(self):
        test_server.stop()

    def test_production_env(self):
        """
        Test reasons sanitized in production env
        """
        setup_server('production')

        # test 404
        resp = json.loads(request('/tasks/blah').read())
        self.assertEqual('404 Not Found', resp.get('code'))

        # test 405 wrong method
        resp = json.loads(request('/', None, 'DELETE').read())
        msg = u'WOKAPI0002E: Delete is not allowed for wokroot'
        self.assertEqual('405 Method Not Allowed', resp.get('code'))
        self.assertEqual(msg, resp.get('reason'))

        # test 400 parse error
        resp = json.loads(request('/tasks', '{', 'POST').read())
        msg = u'WOKAPI0006E: Unable to parse JSON request'
        self.assertEqual('400 Bad Request', resp.get('code'))
        self.assertEqual(msg, resp.get('reason'))
        self.assertNotIn('call_stack', resp)

        # test 405 method not allowed
        req = json.dumps({})
        resp = json.loads(request('/tasks', req, 'POST').read())
        m = u'WOKAPI0005E: Create is not allowed for tasks'
        self.assertEqual('405 Method Not Allowed', resp.get('code'))
        self.assertEqual(m, resp.get('reason'))

    def test_development_env(self):
        """
        Test traceback thrown in development env
        """
        setup_server()
        # test 404
        resp = json.loads(request('/tasks/blah').read())
        self.assertEqual('404 Not Found', resp.get('code'))

        # test 405 wrong method
        resp = json.loads(request('/', None, 'DELETE').read())
        msg = u'WOKAPI0002E: Delete is not allowed for wokroot'
        self.assertEqual('405 Method Not Allowed', resp.get('code'))
        self.assertEqual(msg, resp.get('reason'))

        # test 400 parse error
        resp = json.loads(request('/tasks', '{', 'POST').read())
        msg = u'WOKAPI0006E: Unable to parse JSON request'
        self.assertEqual('400 Bad Request', resp.get('code'))
        self.assertEqual(msg, resp.get('reason'))
        self.assertIn('call_stack', resp)

        # test 405 method not allowed
        req = json.dumps({})
        resp = json.loads(request('/tasks', req, 'POST').read())
        m = u'WOKAPI0005E: Create is not allowed for tasks'
        self.assertEqual('405 Method Not Allowed', resp.get('code'))
        self.assertEqual(m, resp.get('reason'))
        self.assertIn('call_stack', resp)
