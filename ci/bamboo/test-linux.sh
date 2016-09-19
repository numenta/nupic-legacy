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

# Run NuPIC tests on Linux.

# ASSUMES:
#   1. Current working directory is root of nupic source tree
#   2. The nupic wheel is in the current working directory



set -o errexit
set -o xtrace


# ZZZ Work around for linux until we have proper PyPI-compatible Linux wheels
pip install https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/releases/nupic.bindings/nupic.bindings-0.4.8-cp27-none-linux_x86_64.whl


# Install nupic
pip install nupic-*.whl

# TODO Investigate why setting USER is necessary here (borrowed from Scott's
# nupic-source build plan)
echo "ZZZ I am: $( whoami )"
USER=ubuntu python setup.py test \
  --pytest-args="--junit-xml=`pwd`/nupic-test-results.xml --cov nupic unit"

# ZZZ TODO Execute Integration tests, too. Requires mysql server and NUPIC env var.