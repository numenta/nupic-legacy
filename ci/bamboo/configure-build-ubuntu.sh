#!/bin/bash
# ----------------------------------------------------------------------
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

# Install what's necessary on top of raw Ubuntu for building a NuPIC wheel.
#
# NOTE much of this will eventually go into a custom docker image


set -o errexit
set -o xtrace


MY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


apt-get update
apt-get install -y python2.7 curl

update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --set python /usr/bin/python2.7


${MY_DIR}/install-pip-setuptools-wheel.sh
