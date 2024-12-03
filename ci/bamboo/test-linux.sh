#!/bin/bash
# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

# Run NuPIC tests on Linux.

# ASSUMES:
#   1. Current working directory is root of nupic source tree
#   2. The nupic wheel is in the current working directory
#
# OUTPUTS:
#
# test results: nupic junit test results will be written to the file
#               nupic-test-results.xml in the root of the nupic source tree.
#
# code coverage report: in tests/htmlcov and tests/.coverage


set -o errexit
set -o xtrace


MY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NUPIC_ROOT_DIR="$( cd "${MY_DIR}/../.." && pwd )"


# Install nupic
pip install nupic-*.whl


#
# Test
#

# Some tests require NUPIC env var to locate config files.
# Some nupic config files reference USER env var, so it needs to be defined.


# Run unit and integration tests (integration tests require mysql server)
PYTEST_OPTS="--verbose --boxed --junit-xml=`pwd`/nupic-test-results.xml --cov nupic --cov-report html"

NUPIC="${NUPIC_ROOT_DIR}" \
USER=$(whoami) \
  python setup.py test --pytest-args="${PYTEST_OPTS} unit integration"
