#!/bin/bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

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
