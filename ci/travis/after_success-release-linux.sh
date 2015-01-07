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
echo "Running after_success-release.sh..."
echo

echo "Installing wheel..."
pip install wheel --user || exit
echo "Installing twine..."
sudo pip install twine || exit

echo "Creating distribution files..."
# This release build creates the source distribution. All other release builds
# should not.
python setup.py sdist bdist || exit

echo "Created the following distribution files:"
ls -l dist

echo "Attempting to upload all distribution files to PyPi..."
twine upload dist/* -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"

# I want to create the linux wheel here just to see what gets produced with the
# intent to later upload it to a place other than PyPi, because PyPi rejects
# linux platform wheel files.
# See: https://bitbucket.org/pypa/pypi-metadata-formats/issue/15/enhance-the-platform-tag-definition-for
python setup.py bdist_wheel || exit
echo "Created the following linux platform wheel:"
ls dist/*.whl
echo "Not doing anything with this wheel at this time."