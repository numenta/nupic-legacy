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
[[ -z $SOURCE_DIR ]] && export SOURCE_DIR=$PWD
[[ -z $INSTALL_DIR ]] && export INSTALL_DIR=$HOME/nta/eng
[[ -z $BUILDDIR ]] && export BUILDDIR=$HOME/ntabuild
[[ -z $MK_JOBS ]] && export MK_JOBS=3

function exitOnError {
    if [[ !( "$1" == 0 ) ]] ; then
        exit $1
    fi
}

function prepDirectories {
    [[ -d $INSTALL_DIR ]] && rm -rf "$INSTALL_DIR"
    [[ -d $BUILDDIR ]] && rm -rf "$BUILDDIR"
    mkdir -p "$BUILDDIR"
    mkdir -p "$INSTALL_DIR"
    pushd "$BUILDDIR"
}

function pythonSetup {
    python "$SOURCE_DIR/build_system/setup.py" --autogen
    exitOnError $?
}

function doConfigure {
    "$SOURCE_DIR/configure" --enable-optimization --enable-assertions=yes --prefix="$INSTALL_DIR"
    exitOnError $?
}

function doMake {
    make -j $MK_JOBS
    make install
    exitOnError $?
}

function cleanUpDirectories {
    popd
    [[ -d $BUILDDIR ]] && rm -r "$BUILDDIR"
}

prepDirectories

pythonSetup
doConfigure
doMake

cleanUpDirectories

