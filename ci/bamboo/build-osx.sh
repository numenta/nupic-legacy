#!/bin/bash
set -o errexit
set -o xtrace

# Fixup $PATH for --user installation
export PATH=${HOME}/Library/Python/2.7/bin:${PATH}
export PYTHONPATH=${HOME}/Library/Python/2.7/lib/python/site-packages:${PYTHONPATH}

# Install specific versions of pip, setuptools, and wheel
./ci/bamboo/install-pip-setuptools-wheel.sh --user

# Build installable python packages
python setup.py bdist_wheel

# Install nupic wheel and dependencies, including nupic.bindings artifact in
# wheelhouse/
pip install --user --ignore-installed -f wheelhouse/ dist/nupic-`cat VERSION`*.whl

# Invoke unit tests
python setup.py test --pytest-args="--junit-xml=/shared/nupic-test-results.xml --cov nupic unit"
