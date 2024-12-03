#!/bin/bash
# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
