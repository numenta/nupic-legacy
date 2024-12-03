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
