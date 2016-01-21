#
# Project Wok
#
# Copyright IBM, Corp. 2016
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
from functools import partial

import utils


test_server = None
model = None
host = None
port = None
ssl_port = None


def setUpModule():
    global test_server, model, host, port, ssl_port

    utils.patch_auth()
    host = '127.0.0.1'
    port = utils.get_free_port('http')
    ssl_port = utils.get_free_port('https')
    test_server = utils.run_server(host, port, ssl_port, test_mode=True)


def tearDownModule():
    test_server.stop()


class APITests(unittest.TestCase):

    def setUp(self):
        self.request = partial(utils.request, host, ssl_port)

    def test_config(self):
        resp = self.request('/config').read()
        conf = json.loads(resp)
        keys = ["auth", "ssl_port", "websockets_port", "version"]
        self.assertEquals(sorted(keys), sorted(conf.keys()))
