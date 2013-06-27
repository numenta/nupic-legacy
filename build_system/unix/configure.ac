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
#
# autoconf/automake configuration file for NuPIC
#

AC_INIT([NuPIC], 1.0.0)

# This directory is where libtoolize and automake put their scripts
# must come before AM_INIT_AUTOMAKE
AC_CONFIG_AUX_DIR([build_system/unix])

# Find out what system we're on.
# Must be called before AM_INIT_AUTOMAKE
AC_CANONICAL_SYSTEM

# Automake options
# foreign -- not a gnu package
# no-dist - don't emit code for "dist" target
# no-installinfo - don't generate/install info pages
# no-installman - don't generate/install man pages
# nostdinc -- don't include standard -I options
# subdir-objects -- put objects into subdirs. Without this we get very long .o names

AM_INIT_AUTOMAKE([foreign no-dist no-installinfo no-installman subdir-objects])

# Gets lots of stuff off of the command line
# None of our source code actually uses this header file.
AC_CONFIG_HEADER([build_system/unix/config.h])

AC_PROG_CC
# Fixes automake complaint in python bindings
AM_PROG_CC_C_O
AC_PROG_CXX

# Enable .S files
AM_PROG_AS

# If we enable both static and shared libraries, each file is compiled twice. Once with -fPIC and once without.
# Gives the minimum version of Python necessary to get installation directories
# for use with $(pythondir), $(pkgpythondir), $(PYTHON_VERSION), etc.
AM_PATH_PYTHON([2.6])
AC_MSG_NOTICE([Version of python is $PYTHON_VERSION])

# Some code is used in a static library (e.g. libfoundation.a) and the compiled code is reused in a shared library
# (e.g. the python bindings module _foundation.so). We compile all code for static libraries with -fPIC so that
# it can be linked into a shared library if needed
# These libtool macros speed up compilation by 2X.  (need to measure whether performance decrease from -fPIC
# is noticeable).
AC_DISABLE_STATIC
AC_ENABLE_SHARED

# Check for dlopen support
AC_LIBTOOL_DLOPEN
#
AC_PROG_LIBTOOL

AC_PROG_INSTALL

if [ "x$PYTHON_VERSION" != "x2.6" ] || [ "x$PYTHON_VERSION" != "x2.7" ]; then
    AC_MSG_ERROR([Python 2.6 or 2.7 is required. You have version $PYTHON_VERSION])
elif [ "x$PYTHON_VERSION" == "x2.7" ]; then
    AC_DEFINE(_PY27)
fi

#
# Find out where system installation of python is. This is different from our install prefixn
#
PYTHON_SYS_PREFIX=`$PYTHON -c "import sys; print sys.prefix"`
AC_MSG_NOTICE([Python sys prefix is $PYTHON_SYS_PREFIX])

PYTHON_SYS_LIB="$PYTHON_SYS_PREFIX/lib"
AC_MSG_NOTICE([Python lib dir is $PYTHON_SYS_LIB])
AC_SUBST(PYTHON_SYS_LIB)

PYTHON_SYS_INCLUDE="$PYTHON_SYS_PREFIX/include"
AC_SUBST(PYTHON_SYS_INCLUDE)

#
# Defaults for variables that may be overridded per-platform.
# Env1-1 are for extra environment variables that need to be set during builds.
nta_platform_ldflags=""
nta_platform_testldflags=""
nta_platform_linkall=""
nta_platform_linkmin=""
nta_platform_env1=""

#
# Determine NTA platform type
#
AC_MSG_CHECKING([platform])
case "${target}" in
     *darwin*)
        nta_platform="darwin64"
        nta_platform_cxxflags="-fPIC -DPIC -Wnewline-eof -m64"
        # link against the system version of python (64-bits)
        nta_platform_python_libs="-F/System/Library/Frameworks -framework Python"
        nta_platform_env1="MACOSX_DEPLOYMENT_TARGET=10.7"
        AC_MSG_RESULT([darwin on x86_64])
        nta_platform_asflags=""
        nta_platform_debug_flag="-gfull"
        nta_platform_ldflags="-Wl,-u,_munmap"
        nta_platform_libs="-liconv -lsqlite3 -framework CoreServices -framework Accelerate"
        nta_platform_mpi_extra_libs=""
        nta_platform_pyldflags="-bundle -undefined dynamic_lookup -fPIC"
        nta_platform_pyembed=""
	;;
     i*86-*-*linux*)
        nta_platform="linux32"
        nta_platform_cxxflags="-fPIC -DPIC -ffloat-store"
        nta_platform_asflags=""
        nta_platform_debug_flag="-g"
        nta_platform_ldflags="-static-libgcc"
	nta_platform_libs="-lm -lstdc++ -lpthread -ldl -lutil -lrt -lcrypt"
	nta_platform_mpi_extra_libs="-lrt"
	nta_platform_python_libs="-lpython\$(PYTHON_VERSION)"
	nta_platform_testldflags="-Wl,-R\$(libdir)/test"
	nta_platform_pyldflags="-pthread -shared"
	nta_platform_pyembed="-Wl,--export-dynamic"
	AC_MSG_RESULT([linux32 on x86])
	;;
     x86_64-*-linux*)
	nta_platform="linux64"
	nta_platform_cxxflags="-m64 -fPIC -DPIC"
        nta_platform_asflags="-msse2"
	nta_platform_debug_flag="-g"
	# nta_platform_ldflags="-static-libgcc"
	# pthread needed by libapr-1
	nta_platform_libs='-lm -lpthread -ldl -lutil -lcrypt -lstdc++'
	nta_platform_mpi_extra_libs="-lrt"
	nta_platform_python_libs="-lpython\$(PYTHON_VERSION)"
	nta_platform_testldflags="-Wl,-R\$(libdir)/test"
	nta_platform_pyldflags="-pthread -shared"
	nta_platform_pyembed="-Wl,--export-dynamic"
	AC_MSG_RESULT([linux64 on x86_64])
	;;
     *)
        AC_MSG_ERROR("${target} not supported yet.)
esac

# Old location of Python check.


#
# Minimum version of swig is 1.3.31 -- earlier versions *will* fail
#
# Put the external directory in our path so that the bundled version of swig is found.
# Set SWIG_LIB or swig will report its original installation location
# SWIG_LIB will show up as a Makefile variable. On Linux, this is exported into the
# environment, but not on darwin. So the PYSWIGCOMPILE macro (Includes.am) has to
# export it explicitly. Yuck.
#
# Make sure that we have an absolute path swig, or the build will fail
if test -d ${srcdir}/external/${nta_platform}; then
  cdir=$(pwd)
  cd ${srcdir}/external/${nta_platform}
  extdir=$(pwd)
  cd $cdir
else
  # directory doesnt exist, so we will eventually fail
  extdir=${srcdir}/external/${nta_platform}
fi

PATH=${extdir}/bin:${PATH}
AC_PATH_PROG([SWIG],[swig])
if test -z "$SWIG" ; then
   AC_MSG_WARN([Cannot find 'swig' program. It should be in the external directory of the NuPIC source distribution])
   SWIG='echo "Error: SWIG is not installed. Error in NuPIC source installation"'
fi

SWIG_LIB=${extdir}/share/swig/1.3.36
AC_SUBST([SWIG_LIB])

AC_MSG_NOTICE([SWIG executable is '$SWIG'])
AC_MSG_NOTICE([SWIG library directory is '$SWIG_LIB'])

SWIG_ENABLE_CXX
SWIG_PYTHON

#
# Default installation location. Extra quotes are to make sure $HOME i expanded
# at configure time, not autoconf time.
#
AC_PREFIX_DEFAULT([['${HOME}/nta/eng']])

#
# enable/disable debugging symbols (-g). Enabled by default (stripped for release)
# This is orthogonal to optimization
#
debugsymbols_default="yes"
AC_ARG_ENABLE(debugsymbols, [  --enable-debugsymbols=[no/yes] turn on debug symbols [default=$debugsymbols_default]],,enable_debugsymbols=$debugsymbols_default)
AC_MSG_CHECKING([whether debug symbols are enabled])
if test "x$enable_debugsymbols" = "xyes"; then
  AC_MSG_RESULT(yes)
else
  AC_MSG_RESULT(no)
fi
AM_CONDITIONAL(NTA_DEBUGSYMBOLS_ENABLED, test "x$enable_debugsymbols" = "xyes")

#
# enable/disable optimization. Enabled by default
# This is orthogonal to debugging symbols
#
optimization_default="yes"
AC_ARG_ENABLE(optimization, [  --enable-optimization=[no/yes] turn on optimization [default=$optimization_default]],,enable_optimization=$optimization_default)
AC_MSG_CHECKING([whether optimization is enabled])
if test "x$enable_optimization" = "xyes"; then
  AC_MSG_RESULT(yes)
else
  AC_MSG_RESULT(no)
fi

AM_CONDITIONAL(NTA_OPTIMIZATION_ENABLED, test "x$enable_optimization" = "xyes")

#
# enable/disable NTA_ASSERT.
#
assertions_default="yes"
AC_ARG_ENABLE(assertions, [  --enable-assertions=[no/yes] turn on assertions [default=$assertions_default]],,enable_assertions=$assertions_default)
AC_MSG_CHECKING([whether assertions are enabled])
if test "x$enable_assertions" = "xyes"; then
  AC_MSG_RESULT(yes)
else
  AC_MSG_RESULT(no)
fi

AM_CONDITIONAL(NTA_ASSERTIONS_ENABLED, test "x$enable_assertions" = "xyes")

#
# enable/disable gprof profiling (this option is not frequently used/tested)
#
profiling_default="no"
AC_ARG_ENABLE(profiling, [  --enable-profiling=[no/yes] turn on profiling [default=$profiling_default]],,enable_profiling=$profiling_default)
AC_MSG_CHECKING([whether profiling is enabled])
if test "x$enable_profiling" = "xyes"; then
  AC_MSG_RESULT(yes)
else
  AC_MSG_RESULT(no)
fi

AM_CONDITIONAL(NTA_PROFILING_ENABLED, test "x$enable_profiling" = "xyes")



AC_MSG_NOTICE([============= Extra NTA Options ==============])

#
# Build using Python headers and library,
# and enable features that depend on Python.
AC_ARG_WITH(python,
[  --with-python])
if test "$with_python" = ""
then
  with_python=yes
fi
AM_CONDITIONAL(NTA_PYTHON_SUPPORT, test "x$with_python" = "xyes")

#
# Build using MPI headers and library,
# and enable features that depend on MPI.
AC_ARG_WITH(mpi,
[  --with-mpi])
if test "$with_mpi" = ""
then
  with_mpi=yes
fi
AM_CONDITIONAL(NTA_MPI_SUPPORT, test "x$with_mpi" = "xyes")


AC_MSG_NOTICE([Configured for platform $nta_platform])
AC_SUBST(nta_platform)

AC_MSG_NOTICE([Platform-specific libraries: $nta_platform_libs])
AC_SUBST(nta_platform_libs)

AC_MSG_NOTICE([Platform-specific extra MPI libraries: $nta_platform_mpi_extra_libs])
AC_SUBST(nta_platform_mpi_extra_libs)

AC_MSG_NOTICE([Platform-specific CXX flags: $nta_platform_cxxflags])
AC_SUBST(nta_platform_cxxflags)

AC_MSG_NOTICE([Platform-specific AS flags: $nta_platform_asflags])
AC_SUBST(nta_platform_asflags)

AC_MSG_NOTICE([Platform-specific Debug flag: $nta_platform_debug_flag])
AC_SUBST(nta_platform_debug_flag)

AC_MSG_NOTICE([Platform-specific LD flags: $nta_platform_ldflags])
AC_SUBST(nta_platform_ldflags)

AC_MSG_NOTICE([Platform-specific test library link flags: $nta_platform_testldflags])
AC_SUBST(nta_platform_testldflags)

AC_MSG_NOTICE([Platform-specific Python extension link flags: $nta_platform_pyldflags])
AC_SUBST(nta_platform_pyldflags)
AC_MSG_NOTICE([Platform-specific Python embedding link flags: $nta_platform_pyembed])
AC_SUBST(nta_platform_pyembed)
AC_MSG_NOTICE([Platform-specific Python library: $nta_platform_python_libs])
AC_SUBST(nta_platform_python_libs)

AC_MSG_NOTICE([Platform-specific Environment Setting: $nta_platform_env1])
AC_SUBST(nta_platform_env1)

AC_SUBST(nta_platform_linkall)
AC_SUBST(nta_platform_linkmin)

AC_MSG_NOTICE([Debugging symbols enabled: $enable_debugsymbols])
AC_MSG_NOTICE([Assertions enabled: $enable_assertions])
AC_MSG_NOTICE([Optimization enabled: $enable_optimization])


AC_CONFIG_FILES([

           Makefile
           nta/Makefile
           examples/Makefile
           qa/Makefile
           qa/testeverything/Makefile
           build_system/post_build/Makefile
           nta/engine/Makefile
           nta/types/Makefile
           nta/ntypes/Makefile
           nta/test/Makefile
           nta/os/Makefile
           nta/utils/Makefile
           nta/math/Makefile
           nta/algorithms/Makefile
           nta/apps/Makefile
           nta/apps/htmtest/Makefile
           nta/regions/Makefile
           py/Makefile
           py/cpp_region/Makefile
           py/bindings/math/Makefile
           py/bindings/algorithms/Makefile
           py/bindings/iorange/Makefile
           lang/py/bindings/engine_internal/Makefile
           lang/py/support/Makefile
])

AC_OUTPUT
