#
# Project Wok
#
# Copyright IBM Corp, 2017
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
import os
import select
import socket
import threading

import cherrypy
import wok.websocket as websocket
from wok.config import get_pushserver_socket_dir
from wok.utils import wok_log


BASE_DIRECTORY = get_pushserver_socket_dir()
TOKEN_NAME = 'woknotifications'
END_OF_MESSAGE_MARKER = '//EOM//'
push_server = None


def start_push_server():
    global push_server

    if not push_server:
        push_server = PushServer()


def send_websocket_notification(message):
    global push_server

    if push_server:
        push_server.send_notification(message)


def send_wok_notification(uri, entity, method, action_name=None):
    app_name = 'wok'
    app = cherrypy.tree.apps.get(uri)
    if app:
        app_name = app.root.domain

    source = f'/{app_name}/{entity}'
    if action_name:
        source = f'{source}/{action_name}'

    message = f'{method}:{source}'
    send_websocket_notification(message)


class PushServer(object):
    def set_socket_file(self):
        if not os.path.isdir(BASE_DIRECTORY):
            try:
                os.mkdir(BASE_DIRECTORY)
            except OSError:
                raise RuntimeError(
                    f'PushServer base UNIX socket dir {BASE_DIRECTORY} \
                    not found.'
                )

        if os.path.exists(self.server_addr):
            try:
                os.remove(self.server_addr)
            except Exception:
                raise RuntimeError(
                    f'There is an existing connection in {self.server_addr}'
                )

    def __init__(self):
        self.server_addr = os.path.join(BASE_DIRECTORY, TOKEN_NAME)
        self.set_socket_file()

        websocket.add_proxy_token(TOKEN_NAME, self.server_addr, True)

        self.connections = []

        self.server_running = True
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(self.server_addr)
        self.server_socket.listen(10)
        wok_log.info(f'Push server created on address {self.server_addr}')

        self.connections.append(self.server_socket)
        cherrypy.engine.subscribe('stop', self.close_server, 1)

        server_loop = threading.Thread(target=self.listen)
        server_loop.setDaemon(True)
        server_loop.start()

    def listen(self):
        try:
            while self.server_running:
                read_ready, _, _ = select.select(self.connections, [], [], 1)

                for sock in read_ready:
                    if not self.server_running:
                        break

                    if sock == self.server_socket:
                        new_socket, addr = self.server_socket.accept()
                        self.connections.append(new_socket)
                    else:
                        try:
                            data = sock.recv(4096)
                            if not data:
                                self.connections.remove(sock)
                                sock.close()
                        except Exception:
                            try:
                                self.connections.remove(sock)
                            except ValueError:
                                pass
                            finally:
                                sock.close()

        except Exception as e:
            raise RuntimeError(
                f'Exception ocurred in listen() of pushserver module: {str(e)}'
            )

    def send_notification(self, message):
        message += END_OF_MESSAGE_MARKER
        for sock in self.connections:
            if sock != self.server_socket:
                try:
                    sock.send(message.encode('utf-8'))
                except IOError as e:
                    if 'Broken pipe' in str(e):
                        sock.close()
                        try:
                            self.connections.remove(sock)
                        except ValueError:
                            pass

    def close_server(self):
        try:
            self.server_running = False
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
            os.remove(self.server_addr)
        except Exception:
            pass
        finally:
            cherrypy.engine.unsubscribe('stop', self.close_server)
