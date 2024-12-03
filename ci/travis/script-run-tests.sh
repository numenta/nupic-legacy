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
echo Running script-run-tests.sh...
echo

# Python unit tests and prep for coveralls reporting
python ${TRAVIS_BUILD_DIR}/scripts/run_nupic_tests.py -u --coverage --failfast || exit

mv ${TRAVIS_BUILD_DIR}/.coverage ${TRAVIS_BUILD_DIR}/.coverage_unit

# Python integration tests and prep for coveralls reporting
python ${TRAVIS_BUILD_DIR}/scripts/run_nupic_tests.py -i --coverage --failfast || exit

mv ${TRAVIS_BUILD_DIR}/.coverage ${TRAVIS_BUILD_DIR}/.coverage_integration
