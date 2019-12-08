#!/bin/bash

set -e o pipefail


function get_deps() {
    echo $(python3 -c "import yaml;print(' '.join(yaml.load(open('dependencies.yaml'), Loader=yaml.FullLoader)[\"$1\"][\"$2\"]))")
}


# install pyyaml and its dependencies
sudo apt install python3-setuptools python3-dev
pip3 install pyyaml

# install deps
sudo apt update
sudo apt install -y $(get_deps development-deps common)
sudo apt install -y $(get_deps development-deps ubuntu)

sudo apt install -y $(get_deps runtime-deps common)
sudo apt install -y $(get_deps runtime-deps ubuntu | sed 's/python3-cheetah//')

pip3 install -r requirements-UBUNTU.txt
pip3 install -r requirements-CI.txt

# autogen and make
./autogen.sh --system
make
