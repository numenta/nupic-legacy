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
echo Running after_success-report-coverage-linux.sh...
echo

if [ $CC = 'clang' ]; then
  pip install python-coveralls;
  # Only publishing unit test coverage at this point.
  coveralls -i --data_file=.coverage_unit;
fi

# TODO: figure out how to publish integration test coverage as well.
