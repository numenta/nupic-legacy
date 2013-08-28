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

# get PYTHON_VERSION early here
PY_VER=`python -c 'import sys; print sys.version[:3]'`

#orig values for paths, before env.sh has been run
if [[ -z $_PATH ]]; then
  export _PATH=$PATH
fi
if [[ -z $_PYTHONPATH ]]; then
  export _PYTHONPATH=$PYTHONPATH
fi

export PATH="$NTA/bin:$PATH"
export PYTHONPATH="$NTA/lib/python${PY_VER}/site-packages:$PYTHONPATH"
export NTA_ROOTDIR="$NTA"

# Setup the path to data for OPF experiments
export NTA_DATA_PATH="$NTA/share/prediction/data:$NTA_DATA_PATH"

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
