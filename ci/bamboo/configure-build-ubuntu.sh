#!/bin/bash
# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
