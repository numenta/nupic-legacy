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

# Upgrade setuptools (for PEP-508 support used in extras_require)
pip install --upgrade --ignore-installed setuptools

pip install --upgrade --ignore-installed pip

pip install wheel

python -c 'import pip; print "pip version=", pip.__version__'
python -c 'import setuptools; print "setuptools version=", setuptools.__version__'
python -c 'import wheel; print "wheel version=", wheel.__version__'

pip uninstall numpy --yes

# Fetch nupic.core build
export NUPIC_CORE_COMMITISH=`python -c "execfile('.nupic_modules'); print NUPIC_CORE_COMMITISH"`
echo "Downloading nupic.core build: https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/nupic_core-${NUPIC_CORE_COMMITISH}-linux64.tar.gz"
curl -O "https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/nupic_core-${NUPIC_CORE_COMMITISH}-linux64.tar.gz"
tar xzf "nupic_core-${NUPIC_CORE_COMMITISH}-linux64.tar.gz"

ls home/travis/build/numenta/nupic.core/bindings/py/dist/wheels

# Install nupic.bindings and dependencies from wheels
pip install --no-index --find-links=home/travis/build/numenta/nupic.core/bindings/py/dist/wheels nupic.bindings

# Workaround for multiprocessing.Queue SemLock error from run_opf_bechmarks_test.
# See: https://github.com/travis-ci/travis-cookbooks/issues/155
# Commented out to test to see if it works witout it in container mode.
# sudo rm -rf /dev/shm && sudo ln -s /run/shm /dev/shm
