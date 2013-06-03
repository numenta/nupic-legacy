#!/bin/bash
#
# autogen.sh sets up the Numenta build system
# It automatically runs makelinks, aclocal, autoconf, automake and should be run from the root
# of the source tree. The second step is to run "configure", which is created in the root of the
# source tree, which which is run from the root of the build tree. 
#

# must be run from main directory
# as a sanity check, make sure "build_system" directory exists
if [ ! -d build_system ]; then
  echo $0: must be run from root of source directory
  exit 1
fi

# Intentionally ignore clean requests that appear to come from Xcode.
do_clean=false
if [ "x$1" == "xclean" ]; then
  do_clean=true
  if [ -n "${XCODE_APP_SUPPORT_DIR}" ]; then
    echo "Ignoring 'autogen.sh clean' which is most likely run from Xcode."
    exit 0
  fi
fi



WHICH="type -p"

ACLOCAL=aclocal
AUTOCONF=autoconf
AUTOMAKE=automake
AUTORECONF=autoreconf
LIBTOOLIZE=libtoolize

if [ -z "$(${WHICH} ${LIBTOOLIZE})" ]; then
  LIBTOOLIZE=glibtoolize
fi

#echo "Using tools:"
${WHICH} ${ACLOCAL}
${WHICH} ${AUTOCONF}
${WHICH} ${AUTOMAKE}
${WHICH} ${AUTORECONF}
${WHICH} ${LIBTOOLIZE}

echo running libtoolize...
${LIBTOOLIZE} -f -c 
if [ $? != 0 ]; then
  echo ${LIBTOOLIZE} failed. Exiting
  exit 1
fi

echo running aclocal...
${ACLOCAL} --force -I build_system/unix
if [ $? != 0 ]; then
  echo ${ACLOCAL} failed. Exiting
  exit 1
fi

echo running autoconf...
${AUTOCONF} --force -I build_system/unix
if [ $? != 0 ]; then
  echo ${AUTOCONF} failed. Exiting
  exit 1
fi

echo running automake...
${AUTOMAKE} --add-missing --copy
if [ $? != 0 ]; then
  echo ${AUTOMAKE} failed. Exiting
  exit 1
fi

echo "Setup finished"

