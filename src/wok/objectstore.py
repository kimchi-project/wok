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

import json
import sqlite3
import threading
import traceback

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


from wok import config
from wok.exception import NotFoundError
from wok.utils import wok_log


class ObjectStoreSession(object):
    def __init__(self, conn):
        self.conn = conn
        self.conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")

    def _get_list(self, obj_type):
        c = self.conn.cursor()
        res = c.execute('SELECT id FROM objects WHERE type=?', (obj_type,))
        return [x[0] for x in res]

    def get_list(self, obj_type, sort_key=None):
        ids = self._get_list(obj_type)
        if sort_key is None:
            return ids
        objects = [(ident, self.get(obj_type, ident)) for ident in ids]
        objects.sort(key=lambda (_, obj): obj[sort_key])
        return [ident for ident, _ in objects]

    def get(self, obj_type, ident, ignore_missing=False):
        c = self.conn.cursor()
        res = c.execute('SELECT json FROM objects WHERE type=? AND id=?',
                        (obj_type, ident))
        try:
            jsonstr = res.fetchall()[0][0]
        except IndexError:
            self.conn.rollback()
            jsonstr = json.dumps({})
            if not ignore_missing:
                raise NotFoundError("WOKOBJST0001E", {'item': ident})
        return json.loads(jsonstr)

    def get_object_version(self, obj_type, ident):
        c = self.conn.cursor()
        res = c.execute('SELECT version FROM objects WHERE type=? AND id=?',
                        (obj_type, ident))
        return [x[0] for x in res]

    def delete(self, obj_type, ident, ignore_missing=False):
        c = self.conn.cursor()
        c.execute('DELETE FROM objects WHERE type=? AND id=?',
                  (obj_type, ident))
        if c.rowcount != 1 and not ignore_missing:
            self.conn.rollback()
            raise NotFoundError("WOKOBJST0001E", {'item': ident})
        self.conn.commit()

    def store(self, obj_type, ident, data, version=None):
        # Get Wok version if none was provided
        if version is None:
            version = config.get_version().split('-')[0]

        jsonstr = json.dumps(data)
        c = self.conn.cursor()
        c.execute('DELETE FROM objects WHERE type=? AND id=?',
                  (obj_type, ident))
        c.execute('''INSERT INTO objects (id, type, json, version)
                  VALUES (?,?,?,?)''',
                  (ident, obj_type, jsonstr, version))
        self.conn.commit()


class ObjectStore(object):
    def __init__(self, location=None):
        self._lock = threading.Semaphore()
        self._connections = OrderedDict()
        self.location = location or config.get_object_store()
        with self._lock:
            self._init_db()

    def _init_db(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''SELECT * FROM sqlite_master WHERE type='table' AND
                     tbl_name='objects'; ''')
        res = c.fetchall()
        if len(res) == 0:
            c.execute('''CREATE TABLE objects
                      (id TEXT, type TEXT, json TEXT, version TEXT,
                      PRIMARY KEY (id, type))''')
            conn.commit()
            return

    def _get_conn(self):
        ident = threading.currentThread().name
        try:
            return self._connections[ident]
        except KeyError:
            self._connections[ident] = sqlite3.connect(self.location,
                                                       timeout=10)
            if len(self._connections.keys()) > 10:
                id, conn = self._connections.popitem(last=False)
                conn.interrupt()
                del conn
            return self._connections[ident]

    def __enter__(self):
        self._lock.acquire()
        return ObjectStoreSession(self._get_conn())

    def __exit__(self, type, value, tb):
        self._lock.release()
        if type is not None and issubclass(type, sqlite3.DatabaseError):
                # Logs the error and return False, which makes __exit__ raise
                # exception again
                wok_log.error(traceback.format_exc())
                return False
