#
# Project Wok
#
# Copyright IBM Corp, 2016-2017
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
import gettext

from wok.stringutils import decode_value
from wok.template import get_lang, validate_language


class WokMessage(object):
    def __init__(self, code='', args=None, plugin=None):
        if args is None:
            args = {}
        # make all args unicode
        for key, value in args.iteritems():
            if isinstance(value, unicode):
                continue

            try:
                # In case the value formats itself to an ascii string.
                args[key] = decode_value(value)
            except UnicodeEncodeError:
                # In case the value is a WokException or it formats
                # itself to a unicode string.
                args[key] = unicode(value)

        self.code = code
        self.args = args
        self.plugin = plugin

    def _get_text(self, translate):
        wok_app = cherrypy.tree.apps.get('', None)

        # get app from plugin path if specified
        if self.plugin:
            app = cherrypy.tree.apps.get(self.plugin, None)
        # if on request, try to get app from it
        elif cherrypy.request.app:
            app = cherrypy.request.app
        # fallback: get root app (WokRoot)
        else:
            app = wok_app

        if app is None:
            return self.code

        # fallback to Wok message in case plugins raise Wok exceptions
        text = app.root.messages.get(self.code, self.code)
        if text == self.code and wok_app is not None:
            app = wok_app
            text = app.root.messages.get(self.code, self.code)

        if translate:
            # do translation
            domain = app.root.domain
            paths = app.root.paths
            lang = validate_language(get_lang())

            try:
                translation = gettext.translation(domain, paths.mo_dir, [lang])
            except:
                translation = gettext

            return translation.gettext(text)

        return gettext.gettext(text)

    def get_text(self, prepend_code=True, translate=True):
        msg = self._get_text(translate)

        try:
            msg = decode_value(msg) % self.args
        except KeyError, e:
            # When new args are added to existing log messages, old entries in
            # log for the same message would fail due to lack of that new arg.
            # This avoids whole log functionality to break due to that, while
            # registers the problem.
            msg = decode_value(msg)
            cherrypy.log.error_log.error("KeyError: %s - %s" % (str(e), msg))

        if prepend_code:
            return "%s: %s" % (self.code, msg)

        return msg
