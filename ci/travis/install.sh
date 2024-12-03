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
echo Running install-linux.sh...
echo

# Verify cmake version
cmake --version

# Verify python version
python --version
python -c 'import setuptools; print "setuptools version=", setuptools.__version__'
python -c 'import wheel; print "wheel version=", wheel.__version__'
python -c 'import pip; print "pip version=", pip.__version__'

# Build NuPIC
cd ${TRAVIS_BUILD_DIR}
pip install .

# Show nupic installation folder by trying to import nupic, if works, it prints
# the absolute path of nupic.__file__, which the installation folder itself.
python -c 'import sys;import os;import nupic.data;sys.stdout.write(os.path.abspath(os.path.join(nupic.data.__file__, "../..")))' || exit
