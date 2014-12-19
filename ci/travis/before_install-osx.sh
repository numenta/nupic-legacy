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
echo Running before_install-osx.sh...
echo

# Get Darwin64 libs for OSX
echo ">>> Cloning nupic-darwin64 at 40eee5d8b4f79fe52b282c393c8e1a1f5ba7a906..."
git clone https://github.com/numenta/nupic-darwin64.git
(cd nupic-darwin64 && git reset --hard 40eee5d8b4f79fe52b282c393c8e1a1f5ba7a906) || exit
echo ">>> Activating nupic-darwin64..."
source nupic-darwin64/bin/activate

# Install and start MySQL on OSX
echo ">>> brew install mysql"
brew install mysql
echo ">>> mysql.server start"
mysql.server start