#!/bin/bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

echo
echo Running before_deploy-linux.sh...
echo

echo "sudo pip install wheel"
sudo pip install wheel

# pycapnp needs this for some reason.
echo "sudo pip install cython"
sudo pip install cython

cd ${TRAVIS_BUILD_DIR}

# Wheel fails unless we remove this.
sudo rm -rf external/linux32arm

# Build all NuPIC and all required python packages into dist/wheels as .whl
# files.
echo "pip wheel --wheel-dir=dist/wheels -r external/common/requirements.txt ."
pip wheel --wheel-dir=dist/wheels -r external/common/requirements.txt .

# The dist/wheels folder is expected to be published as the release.
