openSUSE dependencies for Wok
================================

* [Build Dependencies](#build-dependencies)
* [Runtime Dependencies](#runtime-dependencies)
* [Packages required for UI development](#packages-required-for-ui-development)
* [Packages required for tests](#packages-required-for-tests)

Build Dependencies
--------------------

    $ sudo zypper install gcc make autoconf automake gettext-tools git \
                          rpm-build libxslt-tools firewalld

Runtime Dependencies
--------------------

    $ sudo zypper install python-CherryPy python-Cheetah python-pam \
                          python-M2Crypto python-jsonschema python-psutil \
                          python-ldap python-lxml python-xml nginx openssl \
                          google-opensans-fonts fontawesome-fonts logrotate

Packages required for UI development
------------------------------------

    $ sudo zypper install gcc-c++ python-devel python-pip
    $ sudo pip install cython libsass

Packages required for tests
---------------------------

    $ sudo zypper install python-pyflakes python-pep8 python-requests rpmlint
