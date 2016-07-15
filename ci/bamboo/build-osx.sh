#!/bin/bash
set -o errexit
set -o xtrace

# Fixup $PATH for --user installation
export PATH=${HOME}/Library/Python/2.7/bin:${PATH}
export PYTHONPATH=${HOME}/Library/Python/2.7/lib/python/site-packages:${PATH}

# Install pip
python ci/bamboo/get-pip.py --user --ignore-installed

# Build installable python packages
python setup.py bdist_wheel

# Install nupic wheel and dependencies, including nupic.bindings artifact in
# wheelwhouse/
pip install --user --ignore-installed -f wheelhouse/ dist/nupic-`cat VERSION`*.whl

# Invoke unit tests
python setup.py test --pytest-args="--junit-xml `pwd` --cov nupic unit"