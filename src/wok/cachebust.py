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
import os

from wok.config import paths
from wok.config import PluginPaths


def href(url, plugin=None):
    if plugin is None:
        base_path = paths.ui_dir
    else:
        base_path = PluginPaths(plugin).ui_dir

    # for error.html, url is absolute path
    f = os.path.join(base_path, url.lstrip('/'))
    mtime = os.path.getmtime(f)
    return f'{url}?cacheBust={mtime}'
