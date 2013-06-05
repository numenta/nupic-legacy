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

function exitOnError {
    echo "Checking exit status ${1}..."
    if [[ !( "$1" == 0 ) ]] ; then
        exit $1
    fi
}

function prepDirectories {
    rm -rf "$NTA"
    rm -rf "$BUILDDIR"
    mkdir "$BUILDDIR"
    pushd "$BUILDDIR"
}

function pythonSetup {
    python "$NUPIC/build_system/setup.py" --autogen
    echo "Python setup exit status: ${?}"
    exitOnError $?
}

function doConfigure {
    "$NUPIC/configure" --enable-optimization --enable-assertions=yes --prefix="$NTA"
    echo "Configure exit status: ${?}"
    exitOnError $?
}

function doMake {
    make -j 3
    make install
    echo "make install exit status: ${?}"
    exitOnError $?
}

function cleanUpDirectories {
    popd
    rm -r "$BUILDDIR"
}

prepDirectories

pythonSetup
doConfigure
doMake

cleanUpDirectories