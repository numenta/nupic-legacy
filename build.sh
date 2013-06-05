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

# Build NuPIC. This requires that the environment is set up as described in the
# README.

# Set sane defaults
[[ -z $NTA ]] && export NTA="${HOME}/nta/eng"
[[ -z $BUILDDIR ]] && export BUILDDIR="${HOME}/ntabuild"
[[ -z $MKE_JOBS ]] && export MKE_JOBS=3
if [[ -z $NUPIC_HOME ]]
then
    echo "NUPIC_HOME not set, using ${PWD}"
    export NUPIC_HOME="${PWD}"
fi

# Clean up first
echo "Cleaning up previous build."
[[ -d $NTA ]] && rm -rf "$NTA"
[[ -d $BUILDDIR ]] && rm -rf "$BUILDDIR"

# Build and install
echo "Building NuPIC."
echo "Using ${BUILDDIR} as build directory"
mkdir -p "$BUILDDIR"
pushd "$BUILDDIR"
python "$NUPIC_HOME/build_system/setup.py" --autogen
"$NUPIC_HOME/configure" --enable-optimization --enable-assertions=yes --prefix="$NTA"
make -j $MKE_JOBS
echo "Installing to ${NTA}" 
make install
popd

# Cleanup
[[ -d $BUILDDIR ]] && rm -rf "$BUILDDIR"
