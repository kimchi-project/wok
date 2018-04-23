#
# Project Wok
#
# Copyright IBM Corp, 2015-2017
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

import mock
import os
import tempfile
import unittest

from wok.exception import InvalidParameter
from wok.rollbackcontext import RollbackContext
from wok.utils import convert_data_size, set_plugin_state


class UtilsTests(unittest.TestCase):
    def test_convert_data_size(self):
        failure_data = [{'val': None, 'from': 'MiB'},
                        {'val': self, 'from': 'MiB'},
                        {'val': 1,    'from': None},
                        {'val': 1,    'from': ''},
                        {'val': 1,    'from': 'foo'},
                        {'val': 1,    'from': 'kib'},
                        {'val': 1,    'from': 'MiB', 'to': None},
                        {'val': 1,    'from': 'MiB', 'to': ''},
                        {'val': 1,    'from': 'MiB', 'to': 'foo'},
                        {'val': 1,    'from': 'MiB', 'to': 'kib'}]

        for d in failure_data:
            if 'to' in d:
                self.assertRaises(InvalidParameter, convert_data_size,
                                  d['val'], d['from'], d['to'])
            else:
                self.assertRaises(InvalidParameter, convert_data_size,
                                  d['val'], d['from'])

        success_data = [{'got': convert_data_size(5, 'MiB', 'MiB'),
                         'want': 5},
                        {'got': convert_data_size(5, 'MiB', 'KiB'),
                         'want': 5120},
                        {'got': convert_data_size(5, 'MiB', 'M'),
                         'want': 5.24288},
                        {'got': convert_data_size(5, 'MiB', 'GiB'),
                         'want': 0.0048828125},
                        {'got': convert_data_size(5, 'MiB', 'Tb'),
                         'want': 4.194304e-05},
                        {'got': convert_data_size(5, 'KiB', 'MiB'),
                         'want': 0.0048828125},
                        {'got': convert_data_size(5, 'M', 'MiB'),
                         'want': 4.76837158203125},
                        {'got': convert_data_size(5, 'GiB', 'MiB'),
                         'want': 5120},
                        {'got': convert_data_size(5, 'Tb', 'MiB'),
                         'want': 596046.4477539062},
                        {'got': convert_data_size(5, 'MiB'),
                         'want': convert_data_size(5, 'MiB', 'B')}]

        for d in success_data:
            self.assertEquals(d['got'], d['want'])

    def _get_fake_config_file_content(self, enable=True):
        return """\
[a_random_section]
# a random section for testing purposes
enable = 1

[wok]
# Enable plugin on Wok server (values: True|False)
enable   =         %s

[fakeplugin]
# Yet another comment on this config file
enable = 2
very_interesting_option = True
""" % str(enable)

    def _get_config_file_template(self, enable=True):
        return """\
[a_random_section]
# a random section for testing purposes
enable = 1

[wok]
# Enable plugin on Wok server (values: True|False)
enable = %s

[fakeplugin]
# Yet another comment on this config file
enable = 2
very_interesting_option = True
""" % str(enable)

    def _create_fake_config_file(self):
        _, tmp_file_name = tempfile.mkstemp(suffix='.conf')

        config_contents = self._get_fake_config_file_content()
        with open(tmp_file_name, 'w') as f:
            f.writelines(config_contents)

        return tmp_file_name

    @mock.patch('wok.utils.get_plugin_config_file')
    @mock.patch('wok.utils.update_cherrypy_mounted_tree')
    def test_set_plugin_state(self, mock_update_cherrypy, mock_config_file):
        mock_update_cherrypy.return_value = True

        with RollbackContext() as rollback:

            config_file_name = self._create_fake_config_file()
            rollback.prependDefer(os.remove, config_file_name)

            mock_config_file.return_value = config_file_name

            set_plugin_state('pluginA', False)
            with open(config_file_name, 'r') as f:
                updated_conf = f.read()
                self.assertEqual(
                    updated_conf,
                    self._get_config_file_template(enable=False)
                )

            set_plugin_state('pluginA', True)
            with open(config_file_name, 'r') as f:
                updated_conf = f.read()
                self.assertEqual(
                    updated_conf,
                    self._get_config_file_template(enable=True)
                )
