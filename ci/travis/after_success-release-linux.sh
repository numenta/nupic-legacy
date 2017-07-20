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

echo "Installing boto..."
pip install boto || exit
echo "Installing wheel..."
pip install wheel || exit
echo "Installing twine..."
pip install twine || exit

echo "Creating distribution files..."
# This release build creates the source distribution. All other release builds
# should not.
python setup.py sdist bdist bdist_wheel || exit

echo "Created the following distribution files:"
ls -l dist
# These should get created on linux:
# nupic-0.0.33-cp27-none-linux-x86_64.whl
# nupic-0.0.33.linux-x86_64.tar.gz
# nupic-0.0.33-py2.7-linux-x86_64.egg
# nupic-0.0.33.tar.gz

NUPIC_VERSION=`cat ${NUPIC}/VERSION`
echo "Uploading Linux egg to PyPi..."
twine upload dist/nupic-${NUPIC_VERSION}*.egg -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"
echo "Uploading source package to PyPi..."
twine upload dist/nupic-${NUPIC_VERSION}.tar.gz -u "${PYPI_USERNAME}" -p "${PYPI_PASSWD}"

# We can't upload the wheel to PyPi because PyPi rejects linux platform wheel
# files. So we'll push it up into S3.
# See: https://bitbucket.org/pypa/pypi-metadata-formats/issue/15/enhance-the-platform-tag-definition-for

wheel_file=`ls dist/*.whl`
echo "Deploying ${wheel_file} to S3..."
python ci/travis/deploy-wheel-to-s3.py "${wheel_file}"
