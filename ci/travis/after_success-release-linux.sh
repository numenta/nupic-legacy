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

# Creates wheel in dist/nupic-0.0.X-py2-none-any.whl
echo "Creating wheel..."
python setup.py bdist_wheel || exit

wheel_filename=`ls dist/*.whl`
echo "Wheel created at ${wheel_filename}."

sudo twine upload "$wheel_filename" -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
