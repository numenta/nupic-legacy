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
echo Running `basename $0`...
echo

# Necessary Linux prep work
echo ">>> Doing prep work..."
sudo add-apt-repository -y ppa:fkrull/deadsnakes
sudo apt-get -qq update

# Install gcc 4.8
echo ">>> Installing gcc 4.8"
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo apt-get -qq update
sudo apt-get -qq install g++-4.8
alias gcc='gcc-4.8'
alias g++='g++-4.8'
if [ $CC = 'gcc' ]; then export CC='gcc-4.8'; export CXX='g++-4.8'; fi

# Install virtualenv
echo ">>> Installing virtualenv..."
sudo apt-get -qq install python$PY_VER python$PY_VER-dev python-virtualenv
sudo ls -laFh /usr/lib/libpython$PY_VER.so

# Execute virtualenv
echo ">>> Executing virtualenv..."
virtualenv --python=`which python$PY_VER` .
source bin/activate

# Workaround for multiprocessing.Queue SemLock error from run_opf_bechmarks_test.
# See: https://github.com/travis-ci/travis-cookbooks/issues/155
sudo rm -rf /dev/shm && sudo ln -s /run/shm /dev/shm

# Install NuPIC python dependencies
echo ">>> Installing python requirements..."
pip install -q -r $NUPIC/external/common/requirements.txt
