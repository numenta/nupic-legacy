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

# Do a clean build of NuPIC.

# Set up sane defaults.
[[ -z $BUILDDIR ]] && BUILDDIR=/tmp/ntabuild
if [[ ! -z $1 ]] ; then
    NUPIC_INSTALL=$1
elif [[ ! -z $NTA ]] ; then
    NUPIC_INSTALL=$NTA
else
    NUPIC_INSTALL=$HOME/nta/eng
fi

# Remove old build and install dirs and remake the directories.
rm -r "$BUILDDIR"
mkdir -p "$BUILDDIR"
rm -r "$NUPIC_INSTALL"
mkdir -p "$NUPIC_INSTALL"

pushd `dirname $0`

# Clean up source location.
python build_system/setup.py --clean

# Do the build.
./build.sh "$NUPIC_INSTALL"

popd
