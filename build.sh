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

# A place to stash the exit status of build commands below
status=0

# Set sane defaults
[[ -z $NUPIC ]] && export NUPIC=$PWD
[[ -z $NTA ]] && export NTA=$HOME/nta/eng
[[ -z $BUILDDIR ]] && export BUILDDIR=/tmp/ntabuild
[[ -z $MK_JOBS ]] && export MK_JOBS=3

function exitOnError {
    if [[ !( "$1" == 0 ) ]] ; then
        exit $1
    fi
}

function prepDirectories {
    [[ -d $NTA ]] && echo "Warning: directory \"$NTA\" already exists and may contain (old) data. Consider removing it. "
    [[ -d $BUILDDIR ]] && echo "Warning: directory \"$BUILDDIR\" already exists and may contain (old) data. Consider removing it. "
    mkdir -p "$BUILDDIR"
    mkdir -p "$NTA"
    pushd "$BUILDDIR"
}

function pythonSetup {
    python "$NUPIC/build_system/setup.py" --autogen
    exitOnError $?
}

function doConfigure {
    "$NUPIC/configure" --enable-optimization --enable-assertions=yes --prefix="$NTA"
    exitOnError $?
}

function doMake {
    make -j $MK_JOBS
    make install
    exitOnError $?
}

function cleanUpDirectories {
    popd
    [[ -d $BUILDDIR ]] && echo "Warning: directory \"$BUILDDIR\" already exists and may contain (old) data. Consider removing it. "
}

prepDirectories

pythonSetup
doConfigure
doMake

cleanUpDirectories

