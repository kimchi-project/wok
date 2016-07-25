#!/usr/bin/python
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA

# This module contains functions that the manipulate
# and configure the Nginx proxy.

import os
import pwd
from string import Template

from wok import sslcert
from wok.config import paths
from wok.exception import OperationFailed
from wok.utils import run_command


HTTP_CONFIG = """
server {
    listen %(host_addr)s:%(proxy_port)s;
    rewrite ^/(.*)$ https://$host:%(proxy_ssl_port)s/$1 redirect;
}
"""


def _create_proxy_config(options):
    """Create nginx configuration file based on current ports config

    To allow flexibility in which port wok runs, we need the same
    flexibility with the nginx proxy. This method creates the config
    file dynamically by using 'nginx.conf.in' as a template, creating
    the file 'wok.conf' which will be used to launch the proxy.

    Arguments:
    options - OptionParser object with Wok config options
    """
    # User that will run the worker process of the proxy. Fedora,
    # RHEL and Suse creates an user called 'nginx' when installing
    # the proxy. Ubuntu creates an user 'www-data' for it.
    user_proxy = None
    user_list = ('nginx', 'www-data', 'http')
    sys_users = [p.pw_name for p in pwd.getpwall()]
    common_users = list(set(user_list) & set(sys_users))
    if len(common_users) == 0:
        raise Exception("No common user found")
    else:
        user_proxy = common_users[0]
    config_dir = paths.conf_dir
    nginx_config_dir = paths.nginx_conf_dir
    cert = options.ssl_cert
    key = options.ssl_key

    # No certificates specified by the user
    if not cert or not key:
        cert = '%s/wok-cert.pem' % config_dir
        key = '%s/wok-key.pem' % config_dir
        # create cert files if they don't exist
        if not os.path.exists(cert) or not os.path.exists(key):
            ssl_gen = sslcert.SSLCert()
            with open(cert, "w") as f:
                f.write(ssl_gen.cert_pem())
            with open(key, "w") as f:
                f.write(ssl_gen.key_pem())

    # Setting up Diffie-Hellman group with 2048-bit file
    dhparams_pem = os.path.join(config_dir, "dhparams.pem")

    http_config = ''
    if options.https_only == 'false':
        http_config = HTTP_CONFIG % {'host_addr': options.host,
                                     'proxy_port': options.port,
                                     'proxy_ssl_port': options.ssl_port}

    # Read template file and create a new config file
    # with the specified parameters.
    with open(os.path.join(nginx_config_dir, "wok.conf.in")) as template:
        data = template.read()
    data = Template(data)
    data = data.safe_substitute(user=user_proxy,
                                host_addr=options.host,
                                proxy_ssl_port=options.ssl_port,
                                http_config=http_config,
                                cherrypy_port=options.cherrypy_port,
                                websockets_port=options.websockets_port,
                                cert_pem=cert, cert_key=key,
                                max_body_size=eval(options.max_body_size),
                                session_timeout=options.session_timeout,
                                dhparams_pem=dhparams_pem)

    # Write file to be used for nginx.
    config_file = open(os.path.join(nginx_config_dir, "wok.conf"), "w")
    config_file.write(data)
    config_file.close()

    # If not running from the installed path (from a cloned and builded source
    # code), create a symbolic link in  system's dir to prevent errors on read
    # SSL certifications.
    if not paths.installed:
        dst = os.path.join(paths.sys_nginx_conf_dir, "wok.conf")
        if os.path.isfile(dst) or os.path.islink(dst):
            os.remove(dst)
        os.symlink(os.path.join(nginx_config_dir, "wok.conf"), dst)


def start_proxy(options):
    """Start nginx reverse proxy."""
    _create_proxy_config(options)
    # Restart system's nginx service to reload wok configuration
    cmd = ['systemctl', 'restart', 'nginx.service']
    output, error, retcode = run_command(cmd, silent=True)
    if retcode != 0:
        raise OperationFailed('WOKPROXY0001E', {'error': error})
