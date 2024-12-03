#!/bin/bash
# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
