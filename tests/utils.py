#
# Project Wok
#
# Copyright IBM Corp, 2013-2016
#
# Code delivered from Project Kimchi
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

import base64
import cherrypy
import grp
import httplib
import inspect
import os
import ssl
import sys
import threading
import time
import unittest

import wok.server

from wok.auth import User, USER_NAME, USER_GROUPS, USER_ROLES, tabs
from wok.config import config
from wok.exception import NotFoundError, OperationFailed
from wok.utils import wok_log

HOST = '0.0.0.0'
PROXY_PORT = 8001

fake_user = {'root': 'letmein!'}


def get_fake_user():
    return fake_user

# provide missing unittest decorators and API for python 2.6; these decorators
# do not actually work, just avoid the syntax failure
if sys.version_info[:2] == (2, 6):
    def skipUnless(condition, reason):
        if not condition:
            sys.stderr.write('[expected failure] ')
            raise Exception(reason)
        return lambda obj: obj

    unittest.skipUnless = skipUnless
    unittest.expectedFailure = lambda obj: obj

    def assertGreater(self, a, b, msg=None):
        if not a > b:
            self.fail('%s not greater than %s' % (repr(a), repr(b)))

    def assertGreaterEqual(self, a, b, msg=None):
        if not a >= b:
            self.fail('%s not greater than or equal to %s'
                      % (repr(a), repr(b)))

    def assertIsInstance(self, obj, cls, msg=None):
        if not isinstance(obj, cls):
            self.fail('%s is not an instance of %r' % (repr(obj), cls))

    def assertIn(self, a, b, msg=None):
        if a not in b:
            self.fail("%s is not in %b" % (repr(a), repr(b)))

    def assertNotIn(self, a, b, msg=None):
        if a in b:
            self.fail("%s is in %b" % (repr(a), repr(b)))

    unittest.TestCase.assertGreaterEqual = assertGreaterEqual
    unittest.TestCase.assertGreater = assertGreater
    unittest.TestCase.assertIsInstance = assertIsInstance
    unittest.TestCase.assertIn = assertIn
    unittest.TestCase.assertNotIn = assertNotIn


def run_server(test_mode, model=None, environment='dev', server_root=''):

    args = type('_', (object,),
                {'cherrypy_port': 8010, 'max_body_size': '4*1024',
                 'test': test_mode, 'access_log': '/dev/null',
                 'error_log': '/dev/null', 'environment': environment,
                 'log_level': 'debug', 'session_timeout': 10,
                 'server_root': server_root})()

    if model is not None:
        setattr(args, 'model', model)

    s = wok.server.Server(args)
    t = threading.Thread(target=s.start)
    t.setDaemon(True)
    t.start()
    cherrypy.engine.wait(cherrypy.engine.states.STARTED)
    return s


def running_as_root():
    return os.geteuid() == 0


def _request(conn, path, data, method, headers):
    if headers is None:
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
    if 'AUTHORIZATION' not in headers.keys():
        user, pw = fake_user.items()[0]
        hdr = "Basic " + base64.b64encode("%s:%s" % (user, pw))
        headers['AUTHORIZATION'] = hdr
    conn.request(method, path, data, headers)
    return conn.getresponse()


def request(path, data=None, method='GET', headers=None):
    # verify if HTTPSConnection has context parameter
    if "context" in inspect.getargspec(httplib.HTTPSConnection.__init__).args:
        context = ssl._create_unverified_context()
        conn = httplib.HTTPSConnection(HOST, PROXY_PORT, context=context)
    else:
        conn = httplib.HTTPSConnection(HOST, PROXY_PORT)

    return _request(conn, path, data, method, headers)


class FakeUser(User):
    auth_type = "fake"
    sudo = True

    def __init__(self, username):
        self.user = {}
        self.user[USER_NAME] = username
        self.user[USER_GROUPS] = None
        self.user[USER_ROLES] = dict.fromkeys(tabs, 'user')

    def get_groups(self):
        return sorted([group.gr_name for group in grp.getgrall()])[0:3]

    def get_roles(self):
        if self.sudo:
            self.user[USER_ROLES] = dict.fromkeys(tabs, 'admin')
        return self.user[USER_ROLES]

    def get_user(self):
        return self.user

    @staticmethod
    def authenticate(username, password, service="passwd"):
        try:
            return fake_user[username] == password
        except KeyError, e:
            raise OperationFailed("WOKAUTH0001E", {'username': 'username',
                                                   'code': e.message})


def patch_auth(sudo=True):
    """
    Override the authenticate function with a simple test against an
    internal dict of users and passwords.
    """
    config.set("authentication", "method", "fake")
    FakeUser.sudo = sudo


def wait_task(task_lookup, taskid, timeout=10):
    for i in range(0, timeout):
        task_info = task_lookup(taskid)
        if task_info['status'] == "running":
            wok_log.info("Waiting task %s, message: %s",
                         taskid, task_info['message'])
            time.sleep(1)
        else:
            return
    wok_log.error("Timeout while process long-run task, "
                  "try to increase timeout value.")


# The action functions in model backend raise NotFoundError exception if the
# element is not found. But in some tests, these functions are called after
# the element has been deleted if test finishes correctly, then NofFoundError
# exception is raised and rollback breaks. To avoid it, this wrapper ignores
# the NotFoundError.
def rollback_wrapper(func, resource, *args):
    try:
        func(resource, *args)
    except NotFoundError:
        # VM has been deleted already
        return


# This function is used to test storage volume upload.
# If we use self.request, we may encode multipart formdata by ourselves
# requests lib take care of encode part, so use this lib instead
def fake_auth_header():
    headers = {'Accept': 'application/json'}
    user, pw = fake_user.items()[0]
    hdr = "Basic " + base64.b64encode("%s:%s" % (user, pw))
    headers['AUTHORIZATION'] = hdr
    return headers
