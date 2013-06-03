dnl @synopsis AC_PROG_SWIG([major.minor.micro])
dnl
dnl This macro searches for a SWIG installation on your system. If
dnl found you should call SWIG via $(SWIG). You can use the optional
dnl first argument to check if the version of the available SWIG is
dnl greater than or equal to the value of the argument. It should have
dnl the format: N[.N[.N]] (N is a number between 0 and 999. Only the
dnl first N is mandatory.)
dnl
dnl If the version argument is given (e.g. 1.3.17), AC_PROG_SWIG checks
dnl that the swig package is this version number or higher.
dnl
dnl In configure.in, use as:
dnl
dnl             AC_PROG_SWIG(1.3.17)
dnl             SWIG_ENABLE_CXX
dnl             SWIG_MULTI_MODULE_SUPPORT
dnl             SWIG_PYTHON
dnl
dnl @category InstalledPackages
dnl @author Sebastian Huber <sebastian-huber@web.de>
dnl @author Alan W. Irwin <irwin@beluga.phys.uvic.ca>
dnl @author Rafael Laboissiere <rafael@laboissiere.net>
dnl @author Andrew Collier <abcollier@yahoo.com>
dnl @version 2004-09-20
dnl @license GPLWithACException

AC_DEFUN([AC_PROG_SWIG],[
        AC_PATH_PROG([SWIG],[swig])
        if test -z "$SWIG" ; then
                AC_MSG_WARN([cannot find 'swig' program. You should look at http://www.swig.org])
                SWIG='echo "Error: SWIG is not installed. You should look at http://www.swig.org" ; false'
        elif test -n "$1" ; then
                AC_MSG_CHECKING([for SWIG version])
                [swig_version=`$SWIG -version 2>&1 | grep 'SWIG Version' | sed 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/g'`]
                AC_MSG_RESULT([$swig_version])
                if test -n "$swig_version" ; then
                        # Calculate the required version number components
                        [required=$1]
                        [required_major=`echo $required | sed 's/[^0-9].*//'`]
                        if test -z "$required_major" ; then
                                [required_major=0]
                        fi
                        [required=`echo $required | sed 's/[0-9]*[^0-9]//'`]
                        [required_minor=`echo $required | sed 's/[^0-9].*//'`]
                        if test -z "$required_minor" ; then
                                [required_minor=0]
                        fi
                        [required=`echo $required | sed 's/[0-9]*[^0-9]//'`]
                        [required_patch=`echo $required | sed 's/[^0-9].*//'`]
                        if test -z "$required_patch" ; then
                                [required_patch=0]
                        fi
                        # Calculate the available version number components
                        [available=$swig_version]
                        [available_major=`echo $available | sed 's/[^0-9].*//'`]
                        if test -z "$available_major" ; then
                                [available_major=0]
                        fi
                        [available=`echo $available | sed 's/[0-9]*[^0-9]//'`]
                        [available_minor=`echo $available | sed 's/[^0-9].*//'`]
                        if test -z "$available_minor" ; then
                                [available_minor=0]
                        fi
                        [available=`echo $available | sed 's/[0-9]*[^0-9]//'`]
                        [available_patch=`echo $available | sed 's/[^0-9].*//'`]
                        if test -z "$available_patch" ; then
                                [available_patch=0]
                        fi
                        if test $available_major -ne $required_major \
                                -o $available_minor -ne $required_minor \
                                -o $available_patch -lt $required_patch ; then
                                AC_MSG_WARN([SWIG version >= $1 is required.  You have $swig_version.  You should look at http://www.swig.org])
                                SWIG='echo "Error: SWIG version >= $1 is required.  You have '"$swig_version"'.  You should look at http://www.swig.org" ; false'
                        else
                                AC_MSG_NOTICE([SWIG executable is '$SWIG'])
                                SWIG_LIB=`$SWIG -swiglib`
                                AC_MSG_NOTICE([SWIG library directory is '$SWIG_LIB'])
                        fi
                else
                        AC_MSG_WARN([cannot determine SWIG version])
                        SWIG='echo "Error: Cannot determine SWIG version.  You should look at http://www.swig.org" ; false'
                fi
        fi
        AC_SUBST([SWIG_LIB])
])

# SWIG_ENABLE_CXX()
#
# Enable SWIG C++ support.  This affects all invocations of $(SWIG).
AC_DEFUN([SWIG_ENABLE_CXX],[
        AC_REQUIRE([AC_PROG_SWIG])
        AC_REQUIRE([AC_PROG_CXX])
        SWIG="$SWIG -c++"
])

# SWIG_MULTI_MODULE_SUPPORT()
#
# Enable support for multiple modules.  This effects all invocations
# of $(SWIG).  You have to link all generated modules against the
# appropriate SWIG runtime library.  If you want to build Python
# modules for example, use the SWIG_PYTHON() macro and link the
# modules against $(SWIG_PYTHON_LIBS).
#
#AC_DEFUN([SWIG_MULTI_MODULE_SUPPORT],[
#        AC_REQUIRE([AC_PROG_SWIG])
#        SWIG="$SWIG -noruntime"
#])

# SWIG_PYTHON([use-shadow-classes = {no, yes}])
#
# Checks for Python and provides the $(SWIG_PYTHON_CPPFLAGS),
# and $(SWIG_PYTHON_OPT) output variables.
#
# $(SWIG_PYTHON_OPT) contains all necessary SWIG options to generate
# code for Python.  Shadow classes are enabled unless the value of the
# optional first argument is exactly 'no'.  If you need multi module
# support (provided by the SWIG_MULTI_MODULE_SUPPORT() macro) use
# $(SWIG_PYTHON_LIBS) to link against the appropriate library.  It
# contains the SWIG Python runtime library that is needed by the type
# check system for example.
AC_DEFUN([SWIG_PYTHON],[
        AC_REQUIRE([AC_PROG_SWIG])
        AC_REQUIRE([AC_PYTHON_DEVEL])
        test "x$1" != "xno" || swig_shadow=" -noproxy"
        AC_SUBST([SWIG_PYTHON_OPT],[-python$swig_shadow])
        AC_SUBST([SWIG_PYTHON_CPPFLAGS],[$PYTHON_CPPFLAGS])
])


dnl @synopsis AC_LIB_WAD
dnl
dnl This macro searches for installed WAD library.
dnl
AC_DEFUN([AC_LIB_WAD],
[
        AC_REQUIRE([AC_PYTHON_DEVEL])
        AC_ARG_ENABLE(wad,
        AC_HELP_STRING([--enable-wad], [enable wad module]),
        [
                case "${enableval}" in
                        no)     ;;
                        *)      if test "x${enableval}" = xyes;
                                then
                                        check_wad="yes"
                                fi ;;
                esac
        ], [])

        if test -n "$check_wad";
        then
                AC_CHECK_LIB(wadpy, _init, [WADPY=-lwadpy], [], $PYTHON_LDFLAGS $PYTHON_EXTRA_LIBS)
                AC_SUBST(WADPY)
        fi
])
