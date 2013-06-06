#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

# This script is intended to be sourced from your .bashrc to ensure the
# environment is set up correctly for NuPIC. It requires $NTA to be set prior
# to invocation as described in the README.

export PATH=$NTA/bin:$PATH
export PYTHONPATH=$NTA/lib/python2.6/site-packages:$PYTHONPATH
export NTA_ROOTDIR=$NTA

# Setup the OS dynamic library path to point to $NTA/lib. There are two
# different paths to set: DYLD_LIBRARY_PATH on Mac and LD_LIBRARY_PATH on
# Linux.
LDIR="$NTA/lib"
if [[ ! "$DYLD_LIBRARY_PATH" == "$LDIR" ]]; then
  export DYLD_LIBRARY_PATH=$LDIR:$DYLD_LIBRARY_PATH
fi
if [[ ! "$LD_LIBRARY_PATH" == "$LDIR" ]]; then
  export LD_LIBRARY_PATH=$LDIR:$LD_LIBRARY_PATH
fi
