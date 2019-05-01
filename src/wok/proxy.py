#!/usr/bin/python
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA
# This module contains functions that the manipulate
# and configure the Nginx proxy.
import os

from wok import sslcert
from wok.config import paths
from wok.utils import run_command


DH_COMMAND = 'openssl dhparam -dsaparam -out %s 2048'


def check_proxy_config():
    # When running from a installed system, there is nothing to do
    if paths.installed:
        return

    # Otherwise, ensure essential directories and files are placed on right
    # place to avoid problems
    #
    # If not running from a installed system, nginx and wok conf
    # directories may not exist, so create them if needed
    dirs = [paths.sys_nginx_conf_dir, paths.sys_conf_dir]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)

    # Create a symbolic link in system's dir to prevent errors while
    # running from source code
    symlinks = [{'target': os.path.join(paths.nginx_conf_dir, 'wok.conf'),
                 'link': os.path.join(paths.sys_nginx_conf_dir, 'wok.conf')}]
    for item in symlinks:
        link = item['link']
        if os.path.isfile(link) or os.path.islink(link):
            os.remove(link)
        os.symlink(item['target'], link)

    # Generate unique Diffie-Hellman group with 2048-bit
    dh_file = os.path.join(paths.sys_conf_dir, 'dhparams.pem')
    if not os.path.exists(dh_file):
        os.system(DH_COMMAND % dh_file)

    # Create cert files if they don't exist
    cert = os.path.join(paths.sys_conf_dir, 'wok-cert.pem')
    key = os.path.join(paths.sys_conf_dir, 'wok-key.pem')

    if not os.path.exists(cert) or not os.path.exists(key):
        ssl_gen = sslcert.SSLCert()
        with open(cert, 'w') as f:
            f.write(ssl_gen.cert_pem())
        with open(key, 'w') as f:
            f.write(ssl_gen.key_pem())

    # Reload nginx configuration.
    cmd = ['service', 'nginx', 'status']
    output, error, rc = run_command(cmd)
    if rc != 0:
        os.system('service nginx start')
    else:
        os.system('nginx -s reload')
