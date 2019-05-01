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
#
import base64
import grp
import http
import inspect
import os
import ssl
import sys
import threading
import time
import unittest

import cherrypy
import wok.server
from wok.auth import User
from wok.config import config
from wok.exception import NotFoundError
from wok.exception import OperationFailed
from wok.utils import wok_log

HOST = '0.0.0.0'
PORT = 8010
PROXY_PORT = 8001

fake_user = {'admin': 'letmein!', 'user': 'letmein!'}


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
            self.fail(f'{repr(a)} not greater than {repr(b)}')

    def assertGreaterEqual(self, a, b, msg=None):
        if not a >= b:
            self.fail(f'{repr(a)} not greater than or equal to {repr(b)}')

    def assertIsInstance(self, obj, cls, msg=None):
        if not isinstance(obj, cls):
            self.fail(f'{repr(obj)} is not an instance of {cls}')

    def assertIn(self, a, b, msg=None):
        if a not in b:
            self.fail(f'{repr(a)} is not in {repr(b)}')

    def assertNotIn(self, a, b, msg=None):
        if a in b:
            self.fail(f'{repr(a)} is in {repr(b)}')

    unittest.TestCase.assertGreaterEqual = assertGreaterEqual
    unittest.TestCase.assertGreater = assertGreater
    unittest.TestCase.assertIsInstance = assertIsInstance
    unittest.TestCase.assertIn = assertIn
    unittest.TestCase.assertNotIn = assertNotIn


def run_server(test_mode, environment='dev', server_root='', no_proxy=True):

    port = PORT if no_proxy else PROXY_PORT
    args = type(
        '_',
        (object,),
        {
            'cherrypy_port': port,
            'max_body_size': '4*1024',
            'test': test_mode,
            'access_log': '/dev/null',
            'error_log': '/dev/null',
            'environment': environment,
            'log_level': 'debug',
            'session_timeout': 10,
            'server_root': server_root,
            'no_proxy': no_proxy,
        },
    )()

    s = wok.server.Server(args)
    t = threading.Thread(target=s.start)
    t.setDaemon(True)
    t.start()
    cherrypy.engine.wait(cherrypy.engine.states.STARTED)
    return s


def running_as_root():
    return os.geteuid() == 0


def _request(conn, path, data, method, headers, user):
    if headers is None:
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
    if 'AUTHORIZATION' not in headers.keys():
        user, pw = user, fake_user[user]
        encoded_auth = base64.b64encode(f'{user}:{pw}'.encode('utf-8'))
        hdr = 'Basic ' + encoded_auth.decode('utf-8')
        headers['AUTHORIZATION'] = hdr
    conn.request(method, path, data, headers)
    return conn.getresponse()


def requestHttps(path, data=None, method='GET', headers=None, user='admin'):
    # To work, this requires run_server() to be called with no_proxy=False.
    https_conn = http.client.HTTPSConnection.__init__
    if 'context' in inspect.getfullargspec(https_conn).args:
        context = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(HOST, PROXY_PORT, context=context)
    else:
        conn = http.client.HTTPSConnection(HOST, PROXY_PORT)

    return _request(conn, path, data, method, headers, user)


def request(path, data=None, method='GET', headers=None, user='admin'):
    conn = http.client.HTTPConnection(HOST, PORT)
    return _request(conn, path, data, method, headers, user)


class FakeUser(User):
    auth_type = 'fake'

    def __init__(self, username):
        super(FakeUser, self).__init__(username)

    def _get_groups(self):
        return sorted([group.gr_name for group in grp.getgrall()])[0:3]

    def _get_role(self):
        return self.name

    @staticmethod
    def authenticate(username, password, service='passwd'):
        try:
            return fake_user[username] == password
        except KeyError as e:
            raise OperationFailed(
                'WOKAUTH0001E', {'username': 'username', 'code': str(e)}
            )


def patch_auth():
    """
    Override the authenticate function with a simple test against an
    internal dict of users and passwords.
    """
    config.set('authentication', 'method', 'fake')


def wait_task(task_lookup, taskid, timeout=10):
    for i in range(0, timeout):
        task_info = task_lookup(taskid)
        if task_info['status'] == 'running':
            wok_log.info(
                f"Waiting task {taskid}, message: {task_info['message']}")
            time.sleep(1)
        else:
            return

    msg = 'Timeout while process long-run task, try to increase timeout value.'
    wok_log.error(msg)


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
    user = next(iter(fake_user))
    pw = fake_user[user]
    hdr = 'Basic ' + \
        base64.b64encode(f'{user}:{pw}'.encode('utf-8')).decode('utf-8')
    headers['AUTHORIZATION'] = hdr
    return headers
