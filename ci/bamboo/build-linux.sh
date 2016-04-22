#!/bin/bash
set -o errexit
set -o xtrace

# Prepare environment
if [ -z "${USER}" ]; then
    USER="docker"
fi
export USER

# Setup compiler
if [ -z "${CC}" ]; then
    CC="gcc"
fi
export CC

if [ "${CC}" = "clang" ]; then
    if [ -z "${CXX}" ]; then
        CXX="clang++"
    fi
    COMPILER_PACKAGES="clang-3.4" # Ubuntu-specific apt package name
else
    if [ -z "${CXX}" ]; then
        CXX="g++"
    fi
    COMPILER_PACKAGES="${CC} ${CXX}" # Ubuntu-specific apt package names
fi
export CXX

# Install OS dependencies, assuming stock ubuntu:latest
apt-get update
apt-get install -y \
    wget \
    git \
    ${COMPILER_PACKAGES} \
    build-essential \
    python \
    python2.7 \
    python2.7-dev
wget https://bootstrap.pypa.io/get-pip.py -O - | python
pip install --upgrade --ignore-installed setuptools
pip install wheel

# Move into root of nupic repository
pushd `git rev-parse --show-toplevel`

# Build installable python packages
python setup.py bdist_wheel

# Install nupic wheel and dependencies, including nupic.bindings artifact in
# wheelwhouse/
pip install -f wheelhouse/ dist/nupic-`cat VERSION`*.whl

# Invoke tests
python setup.py test

# Return to original path
popd
