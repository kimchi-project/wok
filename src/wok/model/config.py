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

from wok.config import config as kconfig
from wok.config import get_version


class ConfigModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        ssl_port = kconfig.get('server', 'ssl_port')
        websockets_port = kconfig.get('server', 'websockets_port')

        return {'ssl_port': ssl_port,
                'websockets_port': websockets_port,
                'version': get_version()}
