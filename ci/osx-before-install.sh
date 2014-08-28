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

# Get Darwin64 libs for OSX
echo ">>> git clone https://github.com/numenta/nupic-darwin64.git"
git clone https://github.com/numenta/nupic-darwin64.git
echo ">>> (cd nupic-darwin64 && git reset --hard 6496136d3748f5f15eaf8e85e48c113d7447149b)"
(cd nupic-darwin64 && git reset --hard 6496136d3748f5f15eaf8e85e48c113d7447149b)
echo ">>> source nupic-darwin64/bin/activate"
source nupic-darwin64/bin/activate

# Install cmake on OSX
echo ">>> brew install cmake"
brew install cmake

# Install and start MySQL on OSX
echo ">>> brew install mysql"
brew install mysql
echo ">>> mysql.server start"
mysql.server start

# Prefix env with our user installation
echo ">>> export PYTHONPATH=$PYTHONPATH:/Users/travis/Library/Python/$PY_VER/lib/python/site-packages"
export PYTHONPATH=$PYTHONPATH:/Users/travis/Library/Python/$PY_VER/lib/python/site-packages
