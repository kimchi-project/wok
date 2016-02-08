#!/bin/bash

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

IGNORE_FILES=" "
if [ -f ./IBM-license-blacklist ]; then
    IGNORE_FILES=$(cat ./IBM-license-blacklist)
fi

for FILE in $(git grep --cached -Il '' | grep -v "$IGNORE_FILES" | grep -v check-IBM-license-header.sh | grep -v IBM-license-blacklist)
do

    grep -q "Copyright IBM.*Corp.*" $FILE
    if [ $? -ne 0 ]; then
        echo "License header missing for" $FILE
    fi

    FIRST=$(git log --pretty=format:%cd --date=short $FILE | cut -d - -f 1 | sort | uniq | head -1)
    LAST=$(git log --pretty=format:%cd --date=short $FILE | cut -d - -f 1 | sort | uniq | tail -1)
    if [ $FIRST -eq $LAST ]; then
        sed -i s/" Copyright.*IBM.*"/" Copyright IBM Corp, "$FIRST/g $FILE
    else
        sed -i s/" Copyright.*IBM.*"/" Copyright IBM Corp, "$FIRST"-"$LAST/g $FILE
    fi
done
