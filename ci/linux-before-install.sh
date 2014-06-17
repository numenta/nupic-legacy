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

# Necessary Linux prep work
sudo add-apt-repository -y ppa:fkrull/deadsnakes
sudo apt-get update
# Install virtualenv
sudo apt-get install python$PY_VER python$PY_VER-dev python-virtualenv
sudo ls -laFh /usr/lib/libpython$PY_VER.so
# Prefix env with our own python installation
export PYTHONPATH=$PYTHONPATH:$NTA/lib/python$PY_VER/site-packages
# Execute virtualenv
virtualenv --python=`which python$PY_VER` .
source bin/activate
# Workaround for multiprocessing.Queue SemLock error from run_opf_bechmarks_test.
# See: https://github.com/travis-ci/travis-cookbooks/issues/155
sudo rm -rf /dev/shm && sudo ln -s /run/shm /dev/shm
# Install NuPIC python dependencies
travis_retry pip install -q -r $NUPIC/external/common/requirements.txt
