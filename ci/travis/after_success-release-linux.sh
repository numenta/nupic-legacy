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

generic_filename=`ls dist/*.whl`
echo "Wheel created at ${generic_filename}."

# Change the name of the wheel based on our platform...
platform=`python -c "import distutils.util; print distutils.util.get_platform()"` || exit
new_filename=$(echo $generic_filename | sed -e "s/any/${platform}/")
# This is an attempt to get the right platform for linux pypi.
# See: https://mail.python.org/pipermail/distutils-sig/2014-October/025173.html
new_filename=$(echo $new_filename | sed -e "s/py2/cpy27/")
mv $generic_filename $new_filename
echo "Moved wheel to ${new_filename} before ${platform} deployment."

sudo twine upload "$new_filename" -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
