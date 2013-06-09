#!/bin/sh
# Clean up all generated files left over from a build -- files generated
# by autogen.sh as well as files from a local (non-VPATH) build.
# Must be run from the root of the source directory

# for testing
# RM="/bin/echo RM"
RM="/bin/rm -v"

if test ! -d config
then
echo $0: please run me from the main source directory
fi


$RM -f configure.ac
$RM -rf autom4te.cache
$RM -f configure config.log config.status
$RM -f aclocal.m4
$RM -f config/config.guess config/config.sub config/ltmain.sh
$RM -f config/depcomp config/install-sh config/missing config/stamp-h1 config/config.h
$RM -f config/py-compile config/test.out
$RM -f Makefile.in Makefile libtool


# some files in testeverything are auto-generated
$RM -f qa/testeverything/{*headers.hpp,*addtests.hpp}

# unittest Makefile.am files are auto-generated. Delete them carefully
$RM -f nta/test/unittests/Makefile.am \
       nta/algorithms/unittests/Makefile.am \
       nta/math/unittests/Makefile.am \
       nta/runtime/unittests/Makefile.am \
       nta/node/unittests/Makefile.am \
       nta/os/unittests/Makefile.am \
       nta/foundation/unittests/Makefile.am \
       nta/common/unittests/Makefile.am \
       nta/client/object_model/unittests/Makefile.am \
       nta/client/session/unittests/Makefile.am \
       plugins/BasicPlugin/unittests/Makefile.am \
       plugins/LearningPlugin/unittests/Makefile.am \
       plugins/TestPlugin/unittests/Makefile.am \
       apps/numenta_runtime/unittests/Makefile.am

# files that are generated with an in-place build by swig
$RM -f \
       nta/nupic/internal_py.cpp \
       nta/nupic/internal.py \
       nta/nupic/util/dl_py.cpp \
       nta/nupic/util/dl.py \
       nta/algorithms/algorithms_py.cpp \
       nta/algorithms/algorithms.py \
       nta/foundation/foundation_py.cpp \
       nta/foundation/foundation.py

# remove the build applications carefully
$RM -f apps/numenta_runtime/numenta_runtime apps/launcher/launcher qa/testparallel/testparallel  apps/launcher/launcher

TODELETE='-name Makefile.in -or
          -name Makefile    -or
          -name \*.lo      -or
          -name \*.la      -or
          -name .deps       -or
          -name .libs       -or
          -name \.dirstamp   -or
          -name \*.pyc       -or
          -name \*.pyo       -or
          -name \*.o         -or
          -name \*~         -or
          -name \*.bak'

DIRS="nta plugins pynodes examples config apps qa release"
echo find $DIRS $TODELETE
find $DIRS $TODELETE | xargs $RM -rvf

# python will create the pyc files from .py files when a module is loaded
echo deleting compiled python code
find qa external nta/python examples pynodes config -name '*.py[oc]' | xargs $RM -vf

for ex in bitworm flu pictures sonar wallstreet waves
do
  (cd examples/$ex; echo cleaning up example $ex; python2 Cleanup.py)
done

echo done
