#!/bin/bash
set -o errexit
set -o xtrace

# Fixup $PATH for --user installation
export PATH=${HOME}/Library/Python/2.7/bin:${PATH}
export PYTHONPATH=${HOME}/Library/Python/2.7/lib/python/site-packages:${PYTHONPATH}

# Install pip
python ci/bamboo/get-pip.py --user --ignore-installed

# Upgrade setuptools (for PEP-508 support used in extras_require); also wheel
pip install --user --upgrade --ignore-installed setuptools wheel
python -c 'import pip; print "pip version=", pip.__version__'
python -c 'import setuptools; print "setuptools version=", setuptools.__version__'
python -c 'import wheel; print "wheel version=", wheel.__version__'

# Build installable python packages
python setup.py bdist_wheel

# Install nupic wheel and dependencies, including nupic.bindings artifact in
# wheelhouse/
pip install --user --ignore-installed -f wheelhouse/ dist/nupic-`cat VERSION`*.whl

# Invoke unit tests
python setup.py test --pytest-args="--junit-xml=`pwd`/nupic-test-results.xml --cov nupic unit"