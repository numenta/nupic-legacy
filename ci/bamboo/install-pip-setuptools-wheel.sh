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

# Wrapper around get-pip.py that sets specific versions of pip, setuptools, and
# wheel for use on *nix platforms.
#
# ARGS: the caller may pass additional args for get-pip.py. This is primarily
#       intended to facilitate passing of --user when needed, which is
#       omitted by default.

set -o errexit
set -o xtrace

# Tool requirements:
#   Fleshed out PEP-508 support (Dependency Specification)
_PIP_VER="8.1.2"
_SETUPTOOLS_VER="25.2.0"
_WHEEL_VER="0.29.0"

# Download get-pip.py
curl --silent --show-error --retry 5 -O http://releases.numenta.org/pip/1ebd3cb7a5a3073058d0c9552ab074bd/get-pip.py

python get-pip.py "$@" --ignore-installed \
  pip==${_PIP_VER} \
  setuptools==${_SETUPTOOLS_VER} \
  wheel==${_WHEEL_VER}

python -c 'import pip; print "pip version=", pip.__version__'
python -c 'import setuptools; print "setuptools version=", setuptools.__version__'
python -c 'import wheel; print "wheel version=", wheel.__version__'
