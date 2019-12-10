* [What is Wok?](#what-is-wok)
* [Browser Support](#browser-support)
    * [Desktop Browser Support](#desktop-browser-support)
    * [Mobile Browser Support](#mobile-browser-support)
* [Linux Support](#linux-support)
* [Getting started](#getting-started)
    * [Install Dependencies](#install-dependencies)
    * [Build and Install](#build-and-install)
    * [Starting up Wok](#starting-up-wok)
    * [Troubleshooting](/docs/troubleshooting.md)
* [Contributing to Wok Project](#contributing-to-wok-project)

# What is Wok?

Wok is a cherrypy-based web framework with HTML5 support originated from Kimchi.
It can be extended by plugins which expose functionality through REST APIs.

Examples of such plugins are [Kimchi](https://github.com/kimchi-project/kimchi/)
(Virtualization Management); [Ginger Base](https://github.com/kimchi-project/gingerbase/)
(Basic host management) and; [Ginger](https://github.com/kimchi-project/ginger/)
(System Administration).

Wok runs through wokd daemon.

# Browser Support

Wok and its plugins can run in any web browser that supports HTML5. The
Kimchi community (responsible for Wok project) makes an effort to
test it with the latest versions of Chrome and Firefox browsers, but the
following list can be used as reference to browser support.

## Desktop Browser Support:

* **Internet Explorer:** Current version
* **Chrome:** Current version
* **Firefox:** Current version
* **Safari:** Current version
* **Opera:** Current version

## Mobile Browser Support:

* **Safari iOS:** Current version
* **Android Browser** Current version

# Linux Support

Wok might run on any GNU/Linux distribution that meets the conditions
described on the 'Getting Started' section below.

The Kimchi community (responsible for Wok project) makes an effort to
test it with the latest versions of Fedora, openSUSE, and Ubuntu.

# Getting Started

## Install Dependencies

In order to have Wok running as expected in your system, please make sure to have
all the dependencies installed before building Wok or starting up the wokd service.

### Fedora

**Development Dependencies**

    sudo -H pip3 install -r requirements-dev.txt
    sudo dnf install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext-devel rpm-build libxslt gcc-c++ python3-devel python3-pep8 python3-pyflakes rpmlint python3-pyyaml

**Runtime Dependencies**

    sudo -H pip3 install -r requirements-FEDORA.txt
    sudo dnf install -y systemd logrotate python3-psutil python3-ldap python3-lxml python3-websockify python3-jsonschema openssl nginx python3-cherrypy python3-cheetah python3-pam python3-m2crypto gettext-devel

## Debian

**Development Dependencies**

    sudo -H pip3 install -r requirements-dev.txt
    sudo apt install -y gcc make autoconf automake git python3-pip python3-requests python3-mock

**Runtime Dependencies**

    sudo -H pip3 install -r requirements-DEBIAN.txt
    sudo apt install -y systemd logrotate python3-psutil python3-ldap python3-lxml python3-websockify python3-jsonschema openssl nginx python3-cherrypy3 python3-cheetah python3-pampy python-m2crypto gettext python3-openssl

## Ubuntu

**Development Dependencies**

    sudo -H pip3 install -r requirements-dev.txt
    sudo apt install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext pkgconf xsltproc python3-dev pep8 pyflakes python3-yaml

**Runtime Dependencies**

    sudo -H pip3 install -r requirements-UBUNTU.txt
    sudo apt install -y systemd logrotate python3-psutil python3-ldap python3-lxml python3-websockify python3-jsonschema openssl nginx python3-cherrypy3 python3-cheetah python3-pam python-m2crypto gettext python3-openssl

## openSUSE LEAP

**Development Dependencies**

    sudo -H pip3 install -r requirements-dev.txt
    sudo zypper install -y gcc make autoconf automake git python3-pip python3-requests python3-mock gettext-tools rpm-build libxslt-tools gcc-c++ python3-devel python3-pep8 python3-pyflakes rpmlint python3-PyYAML python3-distro

**Runtime Dependencies**

    sudo -H pip3 install -r requirements-OPENSUSE-LEAP.txt
    sudo zypper install -y systemd logrotate python3-psutil python3-ldap python3-lxml python3-websockify python3-jsonschema openssl nginx python3-CherryPy python3-Cheetah3 python3-python-pam python3-M2Crypto gettext-tools python3-distro

## Build and Install

    ./autogen.sh --system
    make

    # Optional if running from the source tree
    sudo make install

    # Or, to make installable .deb packages
    make deb

    # Or, for RPM packages
    make rpm

If you are looking for stable versions, there are some packages available at https://github.com/kimchi-project/wok/releases

## Starting up Wok

    sudo python3 src/wokd

To access Wok, please, connect your browser to https://localhost:8001.

# Contributing to Wok Project

There are a lof of ways to contribute to the Wok Project:

* Issues can be reported at [Github](https://github.com/kimchi-project/wok/issues)
* Patches are always welcome! Please, follow [these instructions](https://github.com/kimchi-project/wok/wiki/How-to-Contribute)
 on how to send patches to the mailing list (kimchi-devel@ovirt.org) or submit a pull request.

Find more information about Wok Project at https://github.com/kimchi-project/wok/wiki
