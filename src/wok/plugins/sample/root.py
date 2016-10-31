#
# Project Wok
#
# Copyright IBM Corp, 2016
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

import json
import os

from wok.config import CACHEEXPIRES, PluginConfig, PluginPaths
from wok.control.base import Collection, Resource
from wok.control.utils import UrlSubNode
from wok.plugins.sample.i18n import messages
from wok.plugins.sample.model import Model
from wok.root import WokRoot


samplePaths = PluginPaths('sample')


"""
The main class must be the plugin name starting with upper case. In this case,
Sample. The Sample class is a WokRoot instance with plugin specific details.

Each class attribute which is a Resource or a Collection will be translated as
a new REST API. So self.config to /config API, self.description to
/description API and so on.

self.paths represents the plugin paths. Usually it is PluginPath(<plugin-name>)

self.domain is the gettext domain name. Usually it is the plugin name.

self.messages is a list of all i18n messages used on backend side.
The messages used on UI are placed at ui/pages/i18n.json.tmpl

self.api_schema is the JSON Schema document necessary to validate each REST API
created by the plugin.
"""
class Sample(WokRoot):
    def __init__(self, wok_options):
        self.model = Model()
        super(Sample, self).__init__(self.model)
        self.config = Config(self.model)
        self.description = Description(self.model)
        self.rectangles = Rectangles(self.model)
        self.circles = Circles(self.model)

        self.paths = samplePaths
        self.domain = 'sample'
        self.messages = messages
        self.api_schema = json.load(open(os.path.join(os.path.dirname(
                                    os.path.abspath(__file__)), 'API.json')))


    """
    Re-write get_custom_conf() to expose static directories and files.
    It is for those APIs which do not rely on any backend logic to exist.
    """
    def get_custom_conf(self):
        return SampleConfig()


"""
Static directories and files configuration for Sample plugin.

The configuration is a dictionary supported by cherrypy.
"""
class SampleConfig(PluginConfig):
    def __init__(self):
        super(SampleConfig, self).__init__('sample')

        custom_config ={
            '/js': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': os.path.join(samplePaths.ui_dir, 'js'),
                'tools.wokauth.on': False,
                'tools.nocache.on': False,
                'tools.expires.on': True,
                'tools.expires.secs': CACHEEXPIRES
            },
            '/images': {
                'tools.wokauth.on': False,
                'tools.nocache.on': False,
                'tools.staticdir.dir': os.path.join(samplePaths.ui_dir,
                                                    'images'),
                'tools.staticdir.on': True
            },
            '/help': {'tools.nocache.on': True,
                      'tools.staticdir.dir': os.path.join(samplePaths.ui_dir,
                                                          'pages/help'),
                      'tools.staticdir.on': True},
        }

        self.update(custom_config)



"""
All the classes below correspond to a REST API.
"""
class Config(Resource):
    def __init__(self, model):
        super(Config, self).__init__(model)

    @property
    def data(self):
        return self.info



class Description(Resource):
    def __init__(self, model):
        super(Description, self).__init__(model)

    @property
    def data(self):
        return {'name': 'sample', 'version': '2.3.0'}


@UrlSubNode('circles', True)
class Circles(Collection):
    def __init__(self, model):
        super(Circles, self).__init__(model)
        self.resource = Circle
        self.admin_methods = ['POST', 'PUT']


@UrlSubNode('rectangles', True)
class Rectangles(Collection):
    def __init__(self, model):
        super(Rectangles, self).__init__(model)
        self.resource = Rectangle
        self.admin_methods = ['POST', 'PUT']


class Circle(Resource):
    def __init__(self, model, ident):
        super(Circle, self).__init__(model, ident)
        self.update_params = ['radius']

    @property
    def data(self):
        ret = {'name': self.ident}
        ret.update(self.info)
        return ret


class Rectangle(Resource):
    def __init__(self, model, ident):
        super(Rectangle, self).__init__(model, ident)
        self.update_params = ['length', 'width']

    @property
    def data(self):
        self.info.update({'name': self.ident})
        return self.info
