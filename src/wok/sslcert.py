#
# Project Wok
#
# Copyright IBM Corp, 2015-2016
# Copyright (C) 2004-2005 OSAF. All Rights Reserved.
#
# Code derived from Project Kimchi
#
# Portions of this file were derived from the python-m2crypto unit tests:
#     http://svn.osafoundation.org/m2crypto/trunk/tests/test_x509.py
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
import time

from OpenSSL import crypto


class SSLCert(object):
    def __init__(self):
        self._gen()

    def _gen(self):
        self.ca_key = crypto.PKey()
        self.ca_key.generate_key(crypto.TYPE_RSA, 2048)

        self.ca_cert = crypto.X509()
        self.ca_cert.set_version(2)
        # Set a serial number that is unlikely to repeat
        self.ca_cert.set_serial_number(int(time.time()) % (2 ** 32 - 1))

        ca_subj = self.ca_cert.get_subject()
        ca_subj.C = 'US'
        ca_subj.CN = 'kimchi'
        ca_subj.O = 'kimchi-project.org'

        self.ca_cert.set_issuer(ca_subj)
        self.ca_cert.set_pubkey(self.ca_key)

        t = int(time.time() + time.timezone)
        self.ca_cert.gmtime_adj_notBefore(t)
        self.ca_cert.gmtime_adj_notAfter(t + 60 * 60 * 24 * 365)

        self.ca_cert.sign(self.ca_key, 'sha1')

    def cert_text(self):
        return crypto.dump_certificate(crypto.FILETYPE_TEXT, self.ca_cert)

    def cert_pem(self):
        return crypto.dump_certificate(crypto.FILETYPE_PEM, self.ca_cert)

    def key_pem(self):
        return crypto.dump_privatekey(crypto.FILETYPE_PEM, self.ca_key)


def main():
    c = SSLCert()
    print(c.cert_text())
    print(c.cert_pem())
    print(c.key_pem())


if __name__ == '__main__':
    main()
