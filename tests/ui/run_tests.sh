#!/bin/bash

HOST=${HOST:-localhost}
PORT=${PORT:-8001}
USERNAME=${USERNAME:-root}
BROWSER=${BROWSER:-CHROME}

# ask for password if not passed
if [ -z $PASSWORD ]; then
    echo "Type password for host ${USERNAME}@${HOST}"
    read -s PASSWORD
fi

echo "Running on browser ${BROWSER}"
HOST=${HOST} PASSWORD=${PASSWORD} USERNAME=${USERNAME} PORT=${PORT} BROWSER=${BROWSER} python3 -m pytest 
