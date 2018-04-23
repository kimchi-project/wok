#
# Project Wok
#
# Copyright IBM Corp, 2017
#
# Code derived from Kimchi Project
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
import re
import socket

from wok.config import config
from wok.utils import run_command, wok_log


class PeersModel(object):
    def __init__(self, **kargs):
        # check federation feature is enabled on Wok server
        if not config.get('server', 'federation') == 'on':
            return

        # register server on openslp
        hostname = socket.getfqdn()
        port = config.get("server", "proxy_port")
        self.url = hostname + ":" + port

        cmd = ["slptool", "register",
               "service:wokd://%s" % self.url]
        out, error, ret = run_command(cmd)
        if out and len(out) != 0:
            wok_log.error("Unable to register server on openSLP."
                          " Details: %s" % out)
        cherrypy.engine.subscribe('exit', self._peer_deregister)

    def _peer_deregister(self):
        cmd = ["slptool", "deregister",
               "service:wokd://%s" % self.url]
        out, error, ret = run_command(cmd)
        if out and len(out) != 0:
            wok_log.error("Unable to deregister server on openSLP."
                          " Details: %s" % out)

    def get_list(self):
        # check federation feature is enabled on Wok server
        if not config.get('server', 'federation') == 'on':
            return []

        cmd = ["slptool", "findsrvs", "service:wokd"]
        out, error, ret = run_command(cmd)
        if ret != 0:
            return []

        peers = []
        for server in out.strip().split("\n"):
            match = re.match("service:wokd://(.*?),.*", server)
            peer = match.group(1)
            if peer != self.url:
                peers.append("https://" + peer)

        return peers
