#
# Project Wok
#
# Copyright IBM Corp, 2014-2017
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
import unittest
from functools import partial

from tests.utils import patch_auth
from tests.utils import request
from tests.utils import run_server

test_server = None


def setUpModule():
    global test_server

    patch_auth()
    test_server = run_server(test_mode=True)


def tearDownModule():
    test_server.stop()


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(request, user='user')

    def test_nonroot_access(self):
        # Non-root users can not reload wok config
        resp = self.request('/config', '{}', 'GET')
        self.assertEqual(200, resp.status)
        resp = self.request('/config/reload', '{}', 'POST')
        self.assertEqual(403, resp.status)

        # Non-root users can not enable/disable a plugin
        resp = self.request('/config/plugins/sample', '{}', 'GET')
        self.assertEqual(200, resp.status)
        resp = self.request('/config/plugins/sample/enable', '{}', 'POST')
        self.assertEqual(403, resp.status)
        resp = self.request('/config/plugins/sample/disable', '{}', 'POST')
        self.assertEqual(403, resp.status)
