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

import cherrypy

from wok.message import WokMessage


class WokException(Exception):
    def __init__(self, code='', args={}):
        self.code = code
        msg = WokMessage(code, args).get_text()
        cherrypy.log.error_log.error(msg)
        Exception.__init__(self, msg)


class NotFoundError(WokException):
    pass


class OperationFailed(WokException):
    pass


class MissingParameter(WokException):
    pass


class InvalidParameter(WokException):
    pass


class InvalidOperation(WokException):
    pass


class IsoFormatError(WokException):
    pass


class ImageFormatError(WokException):
    pass


class TimeoutExpired(WokException):
    pass


class UnauthorizedError(WokException):
    pass
