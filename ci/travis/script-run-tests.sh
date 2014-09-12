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
echo Running `basename $0`...
echo

check_previous_exit_status () { if [ $? -ne 0 ]; then exit $?; fi; }

cd $TRAVIS_BUILD_DIR/build/scripts
# legacy binary tests
make tests_pyhtm
check_previous_exit_status

# Python unit tests and prep for coveralls reporting
make python_unit_tests
check_previous_exit_status

mv ${TRAVIS_BUILD_DIR}/.coverage ${TRAVIS_BUILD_DIR}/.coverage_unit
# Python integration tests and prep for coveralls reporting
make python_integration_tests
check_previous_exit_status

mv ${TRAVIS_BUILD_DIR}/.coverage ${TRAVIS_BUILD_DIR}/.coverage_integration
