#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

echo "---------- DEPRECATION WARNING ----------------------"
echo "  THIS BUILD.SH SCRIPT IS DEPRECATED. PLEASE USE"
echo "  CMAKE DIRECTLY AS SPECIFIED IN README"
echo ""
echo "  THIS IS YOUR LAST WARNING (WELL MAYBE NOT)"
echo "---------------------------------------------------"

# Set sane defaults
[[ -z $NUPIC ]] && NUPIC=$PWD
[[ -z $BUILDDIR ]] && BUILDDIR=/tmp/ntabuild
[[ -z $MK_JOBS ]] && MK_JOBS=3
if [[ ! -z $1 ]] ; then
  NUPIC_INSTALL=$1
elif [[ ! -z $NTA ]] ; then
  NUPIC_INSTALL=$NTA
else
  NUPIC_INSTALL=$HOME/nta/eng
  $NTA=$HOME/nta/eng
fi
# location of compiled runable binary
export NUPIC_INSTALL

STDOUT="$NUPIC/build_system/stdout.txt"

function exitOnError {
  if [[ !( "$1" == 0 ) ]] ; then
    {
      echo
      echo "STDOUT redirected to: $STDOUT"
      echo "Build failed!!!"
      echo
    } 1>&2
    exit $1
  fi
}

function runCMake {
  [[ -d $NUPIC_INSTALL ]] && echo "Warning: directory \"$NUPIC_INSTALL\" already exists and may contain (old) data. Consider removing it. "
  [[ -d $BUILDDIR ]] && echo "Warning: directory \"$BUILDDIR\" already exists and may contain (old) data. Consider removing it. "
  mkdir -p $NUPIC/build_system
  pushd $NUPIC/build_system
  cmake -DCMAKE_VERBOSE_MAKEFILE=ON -DTEMP_BUILD_DIR=$BUILDDIR $NUPIC
  mkdir -p "$BUILDDIR/pip-build"
}


function doMake {
  make -j $MK_JOBS
  exitOnError $?
}

function cleanUp {
  unset NUPIC_INSTALL
  popd
}

# Redirect stdout to a file but still print stderr.
mkdir -p `dirname $STDOUT`
{
  runCMake
  doMake
  cleanUp
} 2>&1 > $STDOUT

echo
echo "Stdout redirected to: $STDOUT"
echo "Build successful."
