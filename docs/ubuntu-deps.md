Ubuntu dependencies for Wok
================================

* [Build Dependencies](#build-dependencies)
* [Runtime Dependencies](#runtime-dependencies)
* [Packages required for UI development](#packages-required-for-ui-development)
* [Packages required for tests](#packages-required-for-tests)

Build Dependencies
--------------------

    $ sudo apt-get install gcc make autoconf automake gettext git pkgconf \
                           xsltproc logrotate

Runtime Dependencies
--------------------

    $ sudo apt-get install python3-cherrypy3 python-cheetah python3-pam \
                            python3-openssl python3-jsonschema \
                            python3-psutil python3-ldap python3-lxml nginx \
                            openssl python3-websockify gettext

Packages required for UI development
------------------------------------

    $ sudo apt-get install g++ python3-dev python3-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo apt-get install pep8 pyflakes python-requests python-mock
