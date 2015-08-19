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
echo Running before_install-linux.sh...
echo

alias gcc='gcc-4.8'
alias g++='g++-4.8'

if [ $CC == 'gcc' ]; then
    export CC='gcc-4.8'
    export CXX='g++-4.8'
fi

echo ">>> Installing nupic-linux64..."
git clone https://github.com/numenta/nupic-linux64.git
(cd nupic-linux64 && git reset --hard 99863c7da8b923c57bb4e59530ab087c91fd3992)
source nupic-linux64/bin/activate

# TODO: remove after nupic-linux64 has been updated
pip uninstall numpy --yes
pip install numpy==1.9.2 --user

# Workaround for multiprocessing.Queue SemLock error from run_opf_bechmarks_test.
# See: https://github.com/travis-ci/travis-cookbooks/issues/155
# Commented out to test to see if it works witout it in container mode.
# sudo rm -rf /dev/shm && sudo ln -s /run/shm /dev/shm
