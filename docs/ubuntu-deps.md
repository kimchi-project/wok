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

    $ sudo apt-get install python-cherrypy3 python-cheetah python-pam \
                            python-m2crypto python-jsonschema \
                            python-psutil python-ldap python-lxml nginx \
                            openssl websockify gettext

Packages required for UI development
------------------------------------

    $ sudo apt-get install g++ python-dev python-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo apt-get install pep8 pyflakes python-requests python-mock
