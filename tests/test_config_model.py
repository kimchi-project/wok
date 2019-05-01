#
# Project Wok
#
# Copyright IBM Corp, 2017
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

import mock
from wok.model import model


class ConfigModelTests(unittest.TestCase):
    def test_config_lookup(self):
        inst = model.Model()
        config = inst.config_lookup('')
        self.assertListEqual(
            sorted(
                [
                    'proxy_port',
                    'websockets_port',
                    'auth',
                    'server_root',
                    'version',
                    'federation',
                ]
            ),
            sorted(list(config.keys())),
        )

    @mock.patch('cherrypy.engine.restart')
    def test_config_reload(self, mock_restart):
        inst = model.Model()
        inst.config_reload('')
        mock_restart.assert_called_once_with()
