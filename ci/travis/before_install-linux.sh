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

# Upgrade the version of pip included with nupic-linux64
# TODO: remove after nupic-linux64 has been updated
pip install --upgrade --install-option="--prefix=`pwd`/nupic-linux64" pip
pip --version

pip uninstall numpy --yes

# Assuming pip 1.5.X is installed.
echo "pip install wheel --user"
pip install wheel --user -q

# Fetch nupic.core build
export NUPIC_CORE_COMMITISH=`python -c "execfile('.nupic_modules'); print NUPIC_CORE_COMMITISH"`
echo "Downloading nupic.core build: https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/nupic_core-${NUPIC_CORE_COMMITISH}-linux64.tar.gz"
curl -O "https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/nupic_core-${NUPIC_CORE_COMMITISH}-linux64.tar.gz"
tar xzf "nupic_core-${NUPIC_CORE_COMMITISH}-linux64.tar.gz"

ls home/travis/build/numenta/nupic.core/bindings/py/dist/wheels

# Install nupic.bindings and dependencies from wheels
pip install --user --no-index --find-links=home/travis/build/numenta/nupic.core/bindings/py/dist/wheels nupic.bindings

# Workaround for multiprocessing.Queue SemLock error from run_opf_bechmarks_test.
# See: https://github.com/travis-ci/travis-cookbooks/issues/155
# Commented out to test to see if it works witout it in container mode.
# sudo rm -rf /dev/shm && sudo ln -s /run/shm /dev/shm
