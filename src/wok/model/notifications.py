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

from datetime import datetime

from wok.exception import NotFoundError, OperationFailed
from wok.message import WokMessage
from wok.utils import wok_log


notificationsStore = {}


def add_notification(code, args={}, plugin_name=None):
    if not code:
        wok_log.error("Unable to add notification: invalid code '%(code)s'" %
                      {'code': str(code)})
        return

    global notificationsStore
    notification = notificationsStore.get(code)

    # do not update timestamp if notification already exists
    timestamp = datetime.now().isoformat() if notification is None else \
        notification['timestamp']

    args.update({"_plugin_name": plugin_name, "timestamp": timestamp})
    notificationsStore[code] = args


def del_notification(code):
    global notificationsStore

    try:
        del notificationsStore[str(code)]
    except Exception as e:
        raise OperationFailed("WOKNOT0002E", {'id': str(code), 'msg': e.msg()})


class NotificationsModel(object):
    def __init__(self, **kargs):
        pass

    def get_list(self):
        global notificationsStore
        return notificationsStore.keys()


class NotificationModel(object):
    def __init__(self, **kargs):
        pass

    def lookup(self, id):
        global notificationsStore
        notification = notificationsStore.get(str(id))

        # use WokMessage to translate the notification
        if notification:
            timestamp = notification.get('timestamp', None)
            plugin = notification.get('_plugin_name', None)
            message = WokMessage(str(id), notification, plugin).get_text()
            return {"code": id, "message": message, "timestamp": timestamp}

        raise NotFoundError("WOKNOT0001E", {'id': str(id)})

    def delete(self, id):
        del_notification(id)
