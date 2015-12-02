#!/bin/bash

#
# Project Wok
#
# Copyright IBM, Corp. 2015
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

function build {
    sudo make clean
    sudo ./autogen.sh --system && sudo make
    rc=$?
    if [[ $rc != 0 ]]; then
        echo "Exiting..."
        exit 1
    fi
}

echo "Building wok..."
sleep 2
build

for plugin in $(ls -d src/wok/plugins/*/ | grep -v sample); do
    echo
    echo "Entering $plugin ..."
    sleep 2
    cd $plugin
    if [ ! -f autogen.sh ]; then
        echo "Nothing to do"
        echo
    else
        build
    fi
    cd ../../../../
done
