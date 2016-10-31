#
# Project Wok
#
# Copyright IBM Corp, 2015-2016
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
#

import cherrypy
import logging
import logging.handlers
import os

from string import Template

from wok import auth
from wok import config
from wok.config import config as configParser
from wok.config import PluginConfig, WokConfig
from wok.control import sub_nodes
from wok.model import model
from wok.proxy import start_proxy
from wok.reqlogger import RequestLogger
from wok.root import WokRoot
from wok.safewatchedfilehandler import SafeWatchedFileHandler
from wok.utils import get_enabled_plugins, import_class


LOGGING_LEVEL = {"debug": logging.DEBUG,
                 "info": logging.INFO,
                 "warning": logging.WARNING,
                 "error": logging.ERROR,
                 "critical": logging.CRITICAL}

def set_no_cache():
    from time import strftime, gmtime
    h = [('Expires', 'Mon, 26 Jul 1997 05:00:00 GMT'),
         ('Cache-Control',
          'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'),
         ('Pragma', 'no-cache'),
         ('Last-Modified', strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime()))]
    hList = cherrypy.response.header_list
    if isinstance(hList, list):
        hList.extend(h)
    else:
        hList = h


class Server(object):
    def __init__(self, options):
        # Launch reverse proxy
        start_proxy(options)

        make_dirs = [
            os.path.abspath(config.get_log_download_path()),
            os.path.abspath(configParser.get("logging", "log_dir")),
            os.path.dirname(os.path.abspath(options.access_log)),
            os.path.dirname(os.path.abspath(options.error_log)),
            os.path.dirname(os.path.abspath(config.get_object_store()))
        ]
        for directory in make_dirs:
            if not os.path.isdir(directory):
                os.makedirs(directory)

        self.configObj = WokConfig()
        # We'll use the session timeout (= 10 minutes) and the
        # nginx timeout (= 10 minutes). This monitor isn't involved
        # in anything other than monitor the timeout of the connection,
        # thus it is safe to unsubscribe.
        cherrypy.engine.timeout_monitor.unsubscribe()
        cherrypy.tools.nocache = cherrypy.Tool('on_end_resource', set_no_cache)
        cherrypy.tools.wokauth = cherrypy.Tool('before_handler', auth.wokauth)

        # Setting host to 127.0.0.1. This makes wok run
        # as a localhost app, inaccessible to the outside
        # directly. You must go through the proxy.
        cherrypy.server.socket_host = '127.0.0.1'
        cherrypy.server.socket_port = options.cherrypy_port

        max_body_size_in_bytes = eval(options.max_body_size) * 1024
        cherrypy.server.max_request_body_size = max_body_size_in_bytes

        cherrypy.log.access_file = options.access_log
        cherrypy.log.error_file = options.error_log

        logLevel = LOGGING_LEVEL.get(options.log_level, logging.DEBUG)
        dev_env = options.environment != 'production'

        # Enable cherrypy screen logging if running environment
        # is not 'production'
        if dev_env:
            cherrypy.log.screen = True

        # close standard file handlers because we are going to use a
        # watchedfiled handler, otherwise we will have two file handlers
        # pointing to the same file, duplicating log enries
        for handler in cherrypy.log.access_log.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                cherrypy.log.access_log.removeHandler(handler)

        for handler in cherrypy.log.error_log.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                cherrypy.log.error_log.removeHandler(handler)

        # Create handler to access log file
        h = logging.handlers.WatchedFileHandler(options.access_log, 'a',
                                                delay=1)
        h.setLevel(logLevel)
        h.setFormatter(cherrypy._cplogging.logfmt)

        # Add access log file to cherrypy configuration
        cherrypy.log.access_log.addHandler(h)

        # Create handler to error log file
        h = SafeWatchedFileHandler(options.error_log, 'a', delay=1)
        h.setLevel(logLevel)
        h.setFormatter(cherrypy._cplogging.logfmt)

        # Add error log file to cherrypy configuration
        cherrypy.log.error_log.addHandler(h)

        # start request logger
        self.reqLogger = RequestLogger()

        # Handling running mode
        if not dev_env:
            cherrypy.config.update({'environment': 'production'})

        if hasattr(options, 'model'):
            model_instance = options.model
        else:
            model_instance = model.Model()

        for ident, node in sub_nodes.items():
            if node.url_auth:
                cfg = self.configObj
                ident = "/%s" % ident
                cfg[ident] = {'tools.wokauth.on': True}

        self.app = cherrypy.tree.mount(WokRoot(model_instance, dev_env),
                                       config=self.configObj)

        self._load_plugins(options)
        cherrypy.lib.sessions.init()

    def _load_plugins(self, options):
        for plugin_name, plugin_config in get_enabled_plugins():
            try:
                plugin_class = ('plugins.%s.%s' %
                                (plugin_name,
                                 plugin_name[0].upper() + plugin_name[1:]))
                del plugin_config['wok']
                plugin_config.update(PluginConfig(plugin_name))
            except KeyError:
                continue

            try:
                plugin_app = import_class(plugin_class)(options)
            except (ImportError, Exception), e:
                cherrypy.log.error_log.error(
                    "Failed to import plugin %s, "
                    "error: %s" % (plugin_class, e.message)
                )
                continue

            # dynamically extend plugin config with custom data, if provided
            get_custom_conf = getattr(plugin_app, "get_custom_conf", None)
            if get_custom_conf is not None:
                plugin_config.update(get_custom_conf())

            # dynamically add tools.wokauth.on = True to extra plugin APIs
            try:
                sub_nodes = import_class('plugins.%s.control.sub_nodes' %
                                         plugin_name)

                urlSubNodes = {}
                for ident, node in sub_nodes.items():
                    if node.url_auth:
                        ident = "/%s" % ident
                        urlSubNodes[ident] = {'tools.wokauth.on': True}

                    plugin_config.update(urlSubNodes)

            except ImportError, e:
                cherrypy.log.error_log.error(
                    "Failed to import subnodes for plugin %s, "
                    "error: %s" % (plugin_class, e.message)
                )

            cherrypy.tree.mount(plugin_app,
                                config.get_base_plugin_uri(plugin_name),
                                plugin_config)

    def start(self):
        # Subscribe to SignalHandler plugin
        if hasattr(cherrypy.engine, 'signal_handler'):
            cherrypy.engine.signal_handler.subscribe()

        cherrypy.engine.start()
        cherrypy.engine.block()

    def stop(self):
        cherrypy.engine.exit()


def main(options):
    srv = Server(options)
    srv.start()
