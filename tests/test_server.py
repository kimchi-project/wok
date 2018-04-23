#
# Project Wok
#
# Copyright IBM Corp, 2013-2017
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

import base64
import cherrypy
import json
import tempfile
import threading
import unittest
from functools import partial

from wok.control.base import Collection, Resource

import utils


test_server = None
model = None
tmpfile = None


def setUpModule():
    global test_server, model, tmpfile

    utils.patch_auth()
    tmpfile = tempfile.mktemp()
    test_server = utils.run_server(test_mode=True)


def tearDownModule():
    test_server.stop()


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.request = partial(utils.request)

    def assertValidJSON(self, txt):
        try:
            json.loads(txt)
        except ValueError:
            self.fail("Invalid JSON: %s" % txt)

    def test_server_start(self):
        """
        Test that we can start a server and receive HTTP:200.
        """
        resp = self.request('/')
        self.assertEquals(200, resp.status)

    def test_multithreaded_connection(self):
        def worker():
            for i in xrange(100):
                ret = ['test']
                self.assertEquals('test', ret[0])

        threads = []
        for i in xrange(100):
            t = threading.Thread(target=worker)
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def test_collection(self):
        c = Collection(model)

        # The base Collection is always empty
        cherrypy.request.method = 'GET'
        cherrypy.request.headers['Accept'] = 'application/json'
        self.assertEquals('[]', c.index())

        # POST and DELETE raise HTTP:405 by default
        for method in ('POST', 'DELETE'):
            cherrypy.request.method = method
            try:
                c.index()
            except cherrypy.HTTPError, e:
                self.assertEquals(405, e.code)
            else:
                self.fail("Expected exception not raised")

    def test_resource(self):
        r = Resource(model)

        # Test the base Resource representation
        cherrypy.request.method = 'GET'
        cherrypy.request.headers['Accept'] = 'application/json'
        self.assertEquals('{}', r.index())

        # POST and DELETE raise HTTP:405 by default
        for method in ('POST', 'DELETE'):
            cherrypy.request.method = method
            try:
                r.index()
            except cherrypy.HTTPError, e:
                self.assertEquals(405, e.code)
            else:
                self.fail("Expected exception not raised")

    def test_404(self):
        """
        A non-existent path should return HTTP:404
        """
        url_list = ['/doesnotexist', '/tasks/blah']
        for url in url_list:
            resp = self.request(url)
            self.assertEquals(404, resp.status)

        # Verify it works for DELETE too
        resp = self.request('/tasks/blah', '', 'DELETE')
        self.assertEquals(404, resp.status)

    def test_accepts(self):
        """
        Verify the following expectations regarding the client Accept header:
          If omitted, default to html
          If 'application/json', serve the rest api
          If 'text/html', serve the UI
          If both of the above (in any order), serve the rest api
          If neither of the above, HTTP:406
        """
        resp = self.request("/", headers={})
        location = resp.getheader('location')
        self.assertTrue(location.endswith("login.html"))
        resp = self.request("/login.html", headers={})
        self.assertTrue('<!doctype html>' in resp.read().lower())

        resp = self.request("/", headers={'Accept': 'application/json'})
        self.assertValidJSON(resp.read())

        resp = self.request("/", headers={'Accept': 'text/html'})
        location = resp.getheader('location')
        self.assertTrue(location.endswith("login.html"))

        resp = self.request("/", headers={'Accept':
                                          'application/json, text/html'})
        self.assertValidJSON(resp.read())

        resp = self.request("/", headers={'Accept':
                                          'text/html, application/json'})
        self.assertValidJSON(resp.read())

        h = {'Accept': 'text/plain'}
        resp = self.request('/', None, 'GET', h)
        self.assertEquals(406, resp.status)

    def test_auth_unprotected(self):
        hdrs = {'AUTHORIZATION': ''}
        uris = ['/js/wok.min.js',
                '/images/favicon.png',
                '/login.html',
                '/logout']

        for uri in uris:
            resp = self.request(uri, None, 'HEAD', hdrs)
            self.assertEquals(200, resp.status)

    def test_auth_protected(self):
        hdrs = {'AUTHORIZATION': ''}
        uris = ['/tasks']

        for uri in uris:
            resp = self.request(uri, None, 'GET', hdrs)
            self.assertEquals(401, resp.status)

    def test_auth_bad_creds(self):
        # Test HTTPBA
        hdrs = {'AUTHORIZATION': "Basic " + base64.b64encode("nouser:badpass")}
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)

        # Test REST API
        hdrs = {'AUTHORIZATION': ''}
        req = json.dumps({'username': 'nouser', 'password': 'badpass'})
        resp = self.request('/login', req, 'POST', hdrs)
        self.assertEquals(401, resp.status)

    def test_auth_browser_no_httpba(self):
        # Wok detects REST requests from the browser by looking for a
        # specific header
        hdrs = {"X-Requested-With": "XMLHttpRequest"}

        # Try our request (Note that request() will add a valid HTTPBA header)
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)
        self.assertEquals(None, resp.getheader('WWW-Authenticate'))

    def test_auth_session(self):
        hdrs = {'AUTHORIZATION': '',
                'Content-Type': 'application/json',
                'Accept': 'application/json'}

        # Test we are logged out
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)

        # Execute a login call
        user, pw = utils.fake_user.items()[0]
        req = json.dumps({'username': user, 'password': pw})
        resp = self.request('/login', req, 'POST', hdrs)
        self.assertEquals(200, resp.status)

        user_info = json.loads(resp.read())
        self.assertEquals(sorted(user_info.keys()),
                          ['groups', 'role', 'username'])
        role = user_info['role']
        self.assertEquals(role, u'admin')

        cookie = resp.getheader('set-cookie')
        hdrs['Cookie'] = cookie

        # Test we are logged in with the cookie
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(200, resp.status)

        # Execute a logout call
        resp = self.request('/logout', '{}', 'POST', hdrs)
        self.assertEquals(200, resp.status)
        del hdrs['Cookie']

        # Test we are logged out
        resp = self.request('/tasks', None, 'GET', hdrs)
        self.assertEquals(401, resp.status)

    # TODO: uncomment and adapt when some wok API accepts parameters to test
#    def test_get_param(self):
#        # Create a mock ISO file
#        mockiso = '/tmp/mock.iso'
#        open('/tmp/mock.iso', 'w').close()
#
#        # Create 2 different templates
#        req = json.dumps({'name': 'test-tmpl1', 'cdrom': mockiso})
#        self.request('/plugins/kimchi/templates', req, 'POST')
#
#        req = json.dumps({'name': 'test-tmpl2', 'cdrom': mockiso})
#        self.request('/plugins/kimchi/templates', req, 'POST')
#
#        # Remove mock iso
#        os.unlink(mockiso)
#
#        # Get the templates
#        resp = self.request('/plugins/kimchi/templates')
#        self.assertEquals(200, resp.status)
#        res = json.loads(resp.read())
#        self.assertEquals(2, len(res))
#
#        # Get a specific template
#        resp = self.request('/plugins/kimchi/templates?name=test-tmpl1')
#        self.assertEquals(200, resp.status)
#        res = json.loads(resp.read())
#        self.assertEquals(1, len(res))
#        self.assertEquals('test-tmpl1', res[0]['name'])
