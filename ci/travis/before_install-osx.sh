#!/bin/bash
# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

echo
echo Running before_install-osx.sh...
echo

# Upgrade setuptools (for PEP-508 support used in extras_require)
pip install --upgrade --ignore-installed setuptools

pip install --upgrade --ignore-installed pip

pip install wheel

python -c 'import pip; print "pip version=", pip.__version__'
python -c 'import setuptools; print "setuptools version=", setuptools.__version__'
python -c 'import wheel; print "wheel version=", wheel.__version__'

# Install and start MySQL on OSX
echo ">>> brew install mysql"
brew update
brew install mysql
echo ">>> mysql.server start"
mysql.server start
