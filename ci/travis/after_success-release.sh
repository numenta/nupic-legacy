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
echo Running after_success-release.sh...
echo

echo Installing python modules: wheel, twine
sudo pip install twine wheel

# Creates wheel in dist/nupic-0.0.X-py2-none-any.whl
python setup.py bdist_wheel
# Change the name of the wheel based on our platform...
platform=`python -c "import distutils.util; print distutils.util.get_platform()"`
generic_filename=`ls dist/*.whl`
new_filename=$(echo $generic_filename | sed -e "s/none/${platform}/")

mv $generic_filename $new_filename

twine upload "$new_filename" -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
