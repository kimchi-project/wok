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
import unittest

from utils import get_free_port, patch_auth, request, run_server


test_server = None
model = None
host = None
port = None
ssl_port = None


def setup_server(environment='development', server_root=''):
    global test_server, model, host, port, ssl_port

    patch_auth()
    host = '127.0.0.1'
    port = get_free_port('http')
    ssl_port = get_free_port('https')
    test_server = run_server(host, port, ssl_port, test_mode=True,
                             environment=environment,
                             server_root=server_root)


class ServerRootTests(unittest.TestCase):
    def tearDown(self):
        test_server.stop()

    def test_production_env(self):
        """
        Test reasons sanitized in production env
        """
        server_root = '/test'
        setup_server('production', server_root)

        # check if server_root in config is the same used to start server
        resp = request(host, ssl_port, server_root + '/config').read()
        conf = json.loads(resp)
        self.assertEquals(len(conf), 5)

    def test_development_env(self):
        """
        Test traceback thrown in development env
        """
        server_root = '/test'
        setup_server(server_root=server_root)

        # check if server_root in config is the same used to start server
        resp = request(host, ssl_port, server_root + '/config').read()
        conf = json.loads(resp)
        self.assertEquals(len(conf), 5)
