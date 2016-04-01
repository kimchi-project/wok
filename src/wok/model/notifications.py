#
# Project Wok
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

from wok.exception import NotFoundError, OperationFailed
from wok.message import WokMessage


class NotificationsModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']

    def get_list(self):
        with self.objstore as session:
            return session.get_list('notification')


class NotificationModel(object):
    def __init__(self, **kargs):
        self.objstore = kargs['objstore']

    def lookup(self, id):
        with self.objstore as session:
            notification = session.get('notification', str(id))

            # use WokMessage to translate the notification
            if notification:
                timestamp = notification['timestamp']
                plugin = notification.pop('_plugin_name', None)
                message = WokMessage(id, notification, plugin).get_text()
                return {"code": id, "message": message, "timestamp": timestamp}

        raise NotFoundError("WOKNOT0001E", {'id': str(id)})

    def delete(self, id):
        try:
            with self.objstore as session:
                session.delete('notification', str(id))
        except Exception as e:
            raise OperationFailed("WOKNOT0002E", {'id': str(id),
                                                  'msg': e.msg()})
