#!/bin/bash
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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
# -----------------------------------------------------------------------------

# Run NuPIC tests on OS X.

# ASSUMES:
#   1. Current working directory is root of nupic source tree
#   2. The nupic wheel is in the current working directory



set -o errexit
set -o xtrace


MY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

NUPIC_ROOT_DIR="$( cd "${MY_DIR}/../.." && pwd )"


# Install nupic
pip install --user nupic-*.whl


# Execute unit tests
py.test --verbose "${NUPIC_ROOT_DIR}/tests/unit"

# Execute Integration tests, too (requires mysql server and NUPIC env var)
NUPIC="${NUPIC_ROOT_DIR}" \
  py.test --verbose "${NUPIC_ROOT_DIR}/tests/integration"
