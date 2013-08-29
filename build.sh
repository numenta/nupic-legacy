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
[[ -z $NUPIC ]] && NUPIC=$PWD
[[ -z $BUILDDIR ]] && BUILDDIR=/tmp/ntabuild
[[ -z $MK_JOBS ]] && MK_JOBS=3
if [[ ! -z $1 ]] ; then
  NUPIC_INSTALL=$1
elif [[ ! -z $NTA ]] ; then
  NUPIC_INSTALL=$NTA
else
  NUPIC_INSTALL=$HOME/nta/eng
fi
# location of compiled runable binary
export NUPIC_INSTALL

# get PYTHON_VERSION early here
PY_VER=`python -c 'import platform; print platform.python_version()[:3]'`

STDOUT="$BUILDDIR/stdout.txt"

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

function prepDirectories {
  [[ -d $NUPIC_INSTALL ]] && echo "Warning: directory \"$NUPIC_INSTALL\" already exists and may contain (old) data. Consider removing it. "
  [[ -d $BUILDDIR ]] && echo "Warning: directory \"$BUILDDIR\" already exists and may contain (old) data. Consider removing it. "
  mkdir -p "$BUILDDIR/pip-build"
  mkdir -p "$NUPIC_INSTALL"
  pushd "$BUILDDIR"
}

function pythonSetup {
  python "$NUPIC/build_system/setup.py" --autogen

  # Workaround for matplotlib install bug: numpy must already be installed
  # see http://stackoverflow.com/questions/11797688/matplotlib-requirements-with-pip-install-in-virtualenv
  # https://github.com/matplotlib/matplotlib/wiki/MEP11
  PATH=$NUPIC_INSTALL:$PATH pip install --build="$BUILDDIR/pip-build" --find-links=file://$NUPIC/external/common/pip-cache --no-index --index-url=file:///dev/null --install-option="--install-scripts=$NUPIC_INSTALL/bin" --install-option="--install-lib=$NUPIC_INSTALL/lib/python${PY_VER}/site-packages" numpy==1.7.1
  exitOnError $?

  PATH=$NUPIC_INSTALL:$PATH pip install --build="$BUILDDIR/pip-build" --find-links=file://$NUPIC/external/common/pip-cache --no-index --index-url=file:///dev/null --install-option="--install-scripts=$NUPIC_INSTALL/bin" --install-option="--install-lib=$NUPIC_INSTALL/lib/python${PY_VER}/site-packages" -r $NUPIC/external/common/requirements.txt
  exitOnError $?
  # cov-core may fail to install properly, reporting something to the effect of:
  #
  #   Failed to write pth file for subprocess measurement to $NTA/lib/python2.6/site-packages/init_cov_core.pth
  #
  #   Subprocesses WILL NOT have coverage collected.
  #
  #   To measure subprocesses put the following in a pth file called init_cov_core.pth:
  #   import os; os.environ.get('COV_CORE_SOURCE') and __import__('cov_core_init').init()
  #
  # Therefore, explicitly write out the .pth file.
  echo "import os; os.environ.get('COV_CORE_SOURCE') and __import__('cov_core_init').init()" > $NUPIC_INSTALL/lib/python${PY_VER}/site-packages/init_cov_core.pth
  exitOnError $?
}

function doConfigure {
  "$NUPIC/configure" --enable-optimization --enable-assertions=yes --prefix="$NUPIC_INSTALL"
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

function cleanUpEnv {
  unset NUPIC_INSTALL
}

# Redirect stdout to a file but still print stderr.
mkdir -p `dirname $STDOUT`
{
  prepDirectories

  pythonSetup
  doConfigure
  doMake

  cleanUpDirectories
  cleanUpEnv
} 2>&1 > $STDOUT

echo
echo "Stdout redirected to: $STDOUT"
echo "Build successful."
