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
echo Running before_install-osx.sh...
echo

# Get Darwin64 libs for OSX
echo ">>> Cloning nupic-darwin64 at 40eee5d8b4f79fe52b282c393c8e1a1f5ba7a906..."
git clone https://github.com/numenta/nupic-darwin64.git
(cd nupic-darwin64 && git reset --hard 40eee5d8b4f79fe52b282c393c8e1a1f5ba7a906) || exit
echo ">>> Activating nupic-darwin64..."
source nupic-darwin64/bin/activate

# TODO: remove after nupic-darwin64 has been updated
pip install --upgrade pip
pip uninstall numpy --yes
pip install wheel --user
pip install --use-wheel numpy==1.9.2 --user
PY_VERSION=`python -c 'import sys; print(sys.version[:3])'`
export PYTHONPATH="/Users/travis/Library/Python/$PY_VERSION/lib/python/site-packages:$PYTHONPATH"

# Install and start MySQL on OSX
echo ">>> brew install mysql"
brew install mysql
echo ">>> mysql.server start"
mysql.server start
