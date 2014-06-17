#!/bin/sh
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

# We need to move the pip requirements into the archived directory so they can
# be installed for regression tests
cp ${TRAVIS_BUILD_DIR}/external/common/requirements.txt ${NTA}/.
# This is the directory we'll be archiving.
mkdir ${TRAVIS_BUILD_DIR}/build/archive
# Tar up the release directory
tar -zcf ${TRAVIS_BUILD_DIR}/build/archive/nupic-linux64-${TRAVIS_COMMIT}.tar.gz -C $NTA/.. --transform=s/eng/nupic-linux64-${TRAVIS_COMMIT}/ --exclude="*.pyc" eng
