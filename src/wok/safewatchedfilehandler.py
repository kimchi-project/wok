#
# Project Kimchi
#
# Copyright IBM Corp, 2016
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
from logging.handlers import WatchedFileHandler
from multiprocessing import RLock


class SafeWatchedFileHandler(WatchedFileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=0):
        WatchedFileHandler.__init__(self, filename, mode, encoding, delay)
        self._lock = RLock()

    def close(self):
        self._lock.acquire(timeout=2)
        try:
            WatchedFileHandler.close(self)

        finally:
            self._lock.release()

    def emit(self, record):
        self._lock.acquire(timeout=2)
        try:
            WatchedFileHandler.emit(self, record)

        finally:
            self._lock.release()
