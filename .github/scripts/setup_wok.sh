#!/bin/bash

set -euxo pipefail


function get_deps() {
    echo $(python3 -c "import yaml;print(' '.join(yaml.load(open('dependencies.yaml'), Loader=yaml.FullLoader)[\"$1\"][\"$2\"]))")
}

function install_PyYAML() {
    pip3 install PyYAML==5.2
}

function install_python_deps() {
    pip3 install -r requirements-dev.txt
    pip3 install -r requirements-CI.txt
}

function build(){
    # autogen and make
    ./autogen.sh --system
    make
}

function setup_ubuntu(){
    # install pyyaml and its dependencies
    sudo apt update
    sudo apt install -y python3-setuptools python3-dev python3-pip
    install_PyYAML

    # install deps
    sudo apt install -y $(get_deps development-deps common)
    sudo apt install -y $(get_deps development-deps ubuntu)
    sudo apt install -y $(get_deps runtime-deps common)
    sudo apt install -y $(get_deps runtime-deps ubuntu | sed 's/python3-cheetah//')

    # install python deps and build
    install_python_deps
    build
}

function setup_debian(){
    # install pyyaml and its dependencies
    sudo apt update
    sudo apt install -y python3-setuptools python3-dev python3-pip
    install_PyYAML

    # install deps
    sudo apt install -y $(get_deps development-deps common)
    sudo apt install -y $(get_deps development-deps debian)
    sudo apt install -y $(get_deps runtime-deps common)
    sudo apt install -y $(get_deps runtime-deps debian)

    # install python deps and build
    install_python_deps
    build
}

function setup_fedora(){
    # install pyyaml and its dependencies
    sudo dnf update
    sudo dnf install -y python3-setuptools python3-devel python3-pip
    install_PyYAML

    # install deps
    sudo dnf install -y $(get_deps development-deps common)
    sudo dnf install -y $(get_deps development-deps fedora)
    sudo dnf install -y $(get_deps runtime-deps common)
    sudo dnf install -y $(get_deps runtime-deps fedora)

    # install python deps and build
    install_python_deps
    build
}

function setup_opensuse(){
    # install pyyaml and its dependencies
    sudo zypper update
    sudo zypper install -y python3-setuptools python3-dev python3-pip
    install_PyYAML

    # install deps
    sudo zypper install -y $(get_deps development-deps common)
    sudo zypper install -y $(get_deps development-deps opensuse-leap)
    sudo zypper install -y $(get_deps runtime-deps common)
    sudo zypper install -y $(get_deps runtime-deps opensuse-leap)

    # install python deps and build
    install_python_deps
    build
}

if [ $# -eq 0 ]; then
    echo "No distro specified. Pick one: ubuntu, debian, fedora or opensuse-leap"
fi

setup_$1
