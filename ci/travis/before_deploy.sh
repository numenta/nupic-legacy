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
echo Running before_deploy.sh...
echo

cd ${TRAVIS_BUILD_DIR}

# If this branch is master, this is an iterative deployment, so we'll package
# wheels ourselves for deployment to S3. No need to build docs.
if [ "${TRAVIS_BRANCH}" = "master" ]; then
    # There are now a bunch of symlinks in ${TRAVIS_BUILD_DIR}/extensions that
    # need to be converted to real files. We will do this with a tar hack.
    echo "Removing symlinks from extensions..."
    mkdir tmp_extensions
    tar -hcf - -C extensions . | tar -xf - -C tmp_extensions
    rm -rf extensions
    mv tmp_extensions extensions

    # Build all NuPIC and all required python packages into dist/wheels as .whl
    # files.
    echo "pip wheel --wheel-dir=dist/wheels . --find-links=extensions/core/build/release"
    pip wheel --wheel-dir=dist/wheels -r extensions/core/build/release/requirements.txt -q
    wheel convert extensions/core/build/release/*.egg --dest-dir=dist/wheels
    pip wheel --wheel-dir=dist/wheels -r requirements.txt --find-links=dist/wheels -q
    python setup.py bdist_wheel -d dist/wheels
    python setup.py bdist_egg -d dist
    ls dist/wheels

    # Create a tarball named according to commit sha
    mkdir -p artifacts/travis-ci
    tar -zcvf artifacts/travis-ci/nupic-${TRAVIS_COMMIT}.tar.gz dist/wheels/nupic-*.whl

    # The dist/wheels folder is expected to be deployed to S3.

# If this is a tag, we're doing a release deployment, so we want to build docs
# for pypi...
else

    # For docs, direct people to numenta.org/docs/nupic.
    mkdir ./build/docs
    echo "<html><body>See NuPIC docs at <a href='http://numenta.org/docs/nupic/'>http://numenta.org/docs/nupic/</a>.</body></html>" > build/docs/index.html

fi
