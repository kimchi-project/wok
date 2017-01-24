#
# Project Wok
#
# Copyright IBM Corp, 2016-2017
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

from wok.config import config, get_version


class ConfigModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        return {'proxy_port': config.get('server', 'proxy_port'),
                'websockets_port': config.get('server', 'websockets_port'),
                'auth': config.get('authentication', 'method'),
                'server_root': config.get('server', 'server_root'),
                'version': get_version()}

    def reload(self, name):
        cherrypy.engine.restart()
