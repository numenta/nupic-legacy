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

pip install --upgrade pip
pip --version

pip uninstall numpy --yes

pip install wheel --user

# Add --user location to PYTHONPATH
export PYTHONPATH="/Users/travis/Library/Python/$PY_VERSION/lib/python/site-packages:$PYTHONPATH"

# Fetch nupic.core build
export NUPIC_CORE_COMMITISH=`python -c "execfile('.nupic_modules'); print NUPIC_CORE_COMMITISH"`
echo "Downloading nupic.core build: https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/nupic_core-${NUPIC_CORE_COMMITISH}-darwin64.tar.gz"
curl -O "https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/nupic_core-${NUPIC_CORE_COMMITISH}-darwin64.tar.gz"
tar xzf "nupic_core-${NUPIC_CORE_COMMITISH}-darwin64.tar.gz"

# Install nupic.bindings and dependencies from wheels
pip install --user --no-index --find-links=Users/travis/build/numenta/nupic.core/bindings/py/dist/wheels nupic.bindings

# Install and start MySQL on OSX
echo ">>> brew install mysql"
brew install mysql
echo ">>> mysql.server start"
mysql.server start
