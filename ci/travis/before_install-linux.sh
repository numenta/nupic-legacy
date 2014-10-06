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

echo ">>> Doing prep work..."
sudo add-apt-repository -y ppa:fkrull/deadsnakes
sudo apt-get update

echo ">>> Installing virtualenv..."
sudo apt-get install python$PY_VER python$PY_VER-dev python-virtualenv
sudo ls -laFh /usr/lib/libpython$PY_VER.so

echo ">>> Installing nupic-linux64..."
git clone https://github.com/oxtopus/nupic-linux64.git
(cd nupic-linux64 && git reset --hard 3aba138e2db0ca4b1caad65379208c4ac10ac2dd)
source nupic-linux64/bin/activate
ls -laFh nupic-linux64/lib
ldd -d lib/python2.7/site-packages/PIL/_imaging.so

# Let's see what pip packages have been installed now...
pip list

# Workaround for multiprocessing.Queue SemLock error from run_opf_bechmarks_test.
# See: https://github.com/travis-ci/travis-cookbooks/issues/155
sudo rm -rf /dev/shm && sudo ln -s /run/shm /dev/shm
