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
echo "Running after_success-release.sh..."
echo

echo "Installing wheel..."
pip install wheel || exit
echo "Installing twine..."
pip install twine || exit

# Twine gets installed into /Users/travis/Library/Python/2.7/bin, which needs to
# be added to the PATH
export PATH=/Users/travis/Library/Python/2.7/bin:${PATH}

echo "Creating distribution files..."
# We are not creating sdist here, because it's being created and uploaded in the
# linux Travis-CI release build.
python setup.py bdist bdist_wheel || exit

echo "Created the following distribution files:"
ls -l dist
# These should get created on osx:
# nupic-0.0.33-cp27-none-macosx_10_9_intel.whl
# nupic-0.0.33-py2.7-macosx-10.9-intel.egg
# nupic-0.0.33.macosx-10.9-intel.tar.gz

echo "Uploading OS X egg to PyPi..."
twine upload dist/nupic-*.egg -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
echo "Uploading OS x wheel to PyPi..."
twine upload dist/nupic-*.whl -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"

echo "Attempting to upload all distribution files to PyPi..."
twine upload dist/* -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
