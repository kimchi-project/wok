#
# Project Wok
#
# Copyright IBM Corp, 2015-2017
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
import errno
import json
import os
import time

import cherrypy
from Cheetah.Template import Template
from wok import config as config
from wok.config import paths

EXPIRES_ON = 'Session-Expires-On'
REFRESH = 'robot-refresh'


def get_lang():
    cookie = cherrypy.request.cookie
    if 'wokLang' in cookie.keys():
        return [cookie['wokLang'].value]

    langs = get_accept_language()

    return langs


def get_accept_language():
    lang = cherrypy.request.headers.get('Accept-Language', 'en_US')

    if lang and lang.find(';') != -1:
        lang, _ = lang.split(';', 1)
    # the language from Accept-Language is the format as en-us
    # convert it into en_US
    langs = lang.split(',')
    for idx, val in enumerate(langs):
        if '-' in val:
            langCountry = val.split('-')
            langCountry[1] = langCountry[1].upper()
            langs[idx] = '_'.join(langCountry)
    return langs


def validate_language(langs, domain):
    for lang in langs:
        filepath = os.path.join(
            paths.mo_dir, lang, 'LC_MESSAGES', domain + '.mo')
        if os.path.exists(filepath):
            return lang
    return 'en_US'


def can_accept(mime):
    if 'Accept' not in cherrypy.request.headers:
        accepts = 'text/html'
    else:
        accepts = cherrypy.request.headers['Accept']

    if accepts.find(';') != -1:
        accepts, _ = accepts.split(';', 1)

    if mime in map(lambda x: x.strip(), accepts.split(',')):
        return True

    return False


def can_accept_html():
    return (
        can_accept('text/html')
        or can_accept('application/xaml+xml')
        or can_accept('*/*')
    )


def render_cheetah_file(resource, data):
    paths = cherrypy.request.app.root.paths
    domain = cherrypy.request.app.root.domain
    filename = paths.get_template_path(resource)
    try:
        params = {}
        lang = validate_language(get_lang(), domain)
        gettext_conf = {'domain': domain,
                        'localedir': paths.mo_dir, 'lang': [lang]}
        params['lang'] = gettext_conf
        params['data'] = data
        return Template(file=filename, searchList=params).respond()
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise cherrypy.HTTPError(404)
        else:
            raise


def render(resource, data):
    # get timeout and last refresh
    s_timeout = float(config.config.get('server', 'session_timeout'))
    cherrypy.session.acquire_lock()
    last_req = cherrypy.session.get(REFRESH)
    cherrypy.session.release_lock()

    # last_request is present: calculate remaining time
    if last_req is not None:
        session_expires = (float(last_req) + (s_timeout * 60)) - time.time()
        cherrypy.response.headers[EXPIRES_ON] = session_expires

    if can_accept('application/json'):
        content_type = 'application/json;charset=utf-8'
        cherrypy.response.headers['Content-Type'] = content_type
        response = json.dumps(data, indent=2, separators=(',', ':'))
        return response.encode('utf-8')
    elif can_accept_html():
        content = render_cheetah_file(resource, data)
        return content.encode('utf-8')
    else:
        raise cherrypy.HTTPError(406)
