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

from wok.control.base import Collection, Resource
from wok.control.utils import UrlSubNode


CONFIG_REQUESTS = {
    'POST': {
        'reload': "WOKCONFIG0001L",
    },
}


PLUGIN_REQUESTS = {
    'POST': {
        'enable': "WOKPLUGIN0001L",
        'disable': "WOKPLUGIN0002L",
    },
}


@UrlSubNode("config")
class Config(Resource):
    def __init__(self, model, id=None):
        super(Config, self).__init__(model, id)
        self.uri_fmt = '/config/%s'
        self.admin_methods = ['POST']
        self.plugins = Plugins(self.model)
        self.log_map = CONFIG_REQUESTS
        self.reload = self.generate_action_handler('reload', protected=True)

    @property
    def data(self):
        return self.info


class Plugins(Collection):
    def __init__(self, model):
        super(Plugins, self).__init__(model)
        self.resource = Plugin


class Plugin(Resource):
    def __init__(self, model, ident=None):
        super(Plugin, self).__init__(model, ident)
        self.ident = ident
        self.admin_methods = ['POST']
        self.uri_fmt = "/config/plugins/%s"
        self.log_map = PLUGIN_REQUESTS
        self.enable = self.generate_action_handler('enable', protected=True)
        self.disable = self.generate_action_handler('disable', protected=True)

    @property
    def data(self):
        return self.info
