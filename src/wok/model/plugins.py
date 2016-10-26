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

import cherrypy

from wok.config import get_base_plugin_uri
from wok.utils import get_enabled_plugins


class PluginsModel(object):
    def __init__(self, **kargs):
        pass

    def get_list(self):
        # Will only return plugins that were loaded correctly by WOK and are
        # properly configured in cherrypy
        return [plugin for (plugin, config) in get_enabled_plugins()
                if get_base_plugin_uri(plugin) in cherrypy.tree.apps.keys()]
