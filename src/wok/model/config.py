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
import time

import cherrypy
from wok.config import config
from wok.config import get_version
from wok.model.notifications import add_notification
from wok.utils import wok_log


class ConfigModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, name):
        return {'proxy_port': config.get('server', 'proxy_port'),
                'websockets_port': config.get('server', 'websockets_port'),
                'auth': config.get('authentication', 'method'),
                'server_root': config.get('server', 'server_root'),
                'federation': config.get('server', 'federation'),
                'version': get_version()}

    def reload(self, name):
        add_notification('WOKCONFIG0001I', plugin_name='/')
        # If we proceed with the cherrypy.engine.restart() right after
        # adding the notification, the server will reboot and the
        # opened UIs will most likely not see the notification at all. The
        # notification interval is set in wok.main.js as:
        #
        # wok.NOTIFICATION_INTERVAL = 2000
        #
        # Inserting a time.sleep(2) here will ensure that all opened
        # UI had the chance to see the reload notification.
        wok_log.info('Reloading WoK in two seconds ...')
        time.sleep(2)
        cherrypy.engine.restart()
