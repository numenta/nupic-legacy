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

# Install what's necessary on top of raw Ubuntu for testing a NuPIC wheel.
#
# NOTE much of this will eventually go into a docker image


set -o errexit
set -o xtrace


MY_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


apt-get update
apt-get install -y \
  apt-utils \
  python2.7 \
  python2.7-dev \
  libffi-dev \
  libssl-dev \
  curl \
  build-essential \
  openssl

update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --set python /usr/bin/python2.7


#
# Install and start mysql (needed for integration and swarming tests)
#

# Install, suppressing prompt for admin password, settling for blank password
DEBIAN_FRONTEND=noninteractive \
  debconf-set-selections <<< 'mysql-server mysql-server/root_password password'

DEBIAN_FRONTEND=noninteractive \
  debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password'

DEBIAN_FRONTEND=noninteractive \
  apt-get -y install mysql-server

# Start mysql server
/etc/init.d/mysql start


#
# Install pip/setuptools/wheel
#
${MY_DIR}/install-pip-setuptools-wheel.sh


# Hack to resolve SNIMissingWarning
pip install urllib3[secure]
