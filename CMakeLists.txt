cmake_minimum_required(VERSION 2.8)
project(Nupic)

###########################################
### 1st Part: Configure the environment ###
###########################################

# If we enable both static and shared libraries, each file is compiled twice. Once with -fPIC and once without.
# Gives the minimum version of Python necessary to get installation directories
# for use with ${PYTHON_VERSION}, etc.
find_package(PythonInterp 2.6 REQUIRED)
find_package(PythonLibs 2.6 REQUIRED)

#
# Find out version of Python
#
execute_process(COMMAND python -c "import sys;print str(sys.version_info[0]) + '.' + str(sys.version_info[1])"
                OUTPUT_VARIABLE PYTHON_VERSION)

#
# Find out path of Numpy headers
#
execute_process(COMMAND python -c "import numpy;print numpy.get_include()"
                OUTPUT_VARIABLE NUMPY_INCLUDE_DIRS)

# PIP is used for python modules
# TODO: find_program(PIP_EXECUTABLE pip PATHS ENV PATH)
# TODO: if(PIP_EXECUTABLE)
# TODO: else()
# TODO:   message(FATAL_ERROR "Error: pip is needed for Python dependencies.")
# TODO: endif()

#
# Minimum version of swig is 1.3.31 -- earlier versions *will* fail
#
# Put the external directory in our path so that the bundled version of swig is found.
# Set SWIG_DIR or swig will report its original installation location
# SWIG_DIR will show up as a Makefile variable. On Linux, this is exported into the
# environment, but not on darwin. So the PYSWIGCOMPILE macro (Includes.am) has to
# export it explicitly. Yuck.
#
# Make sure that we have an absolute path swig, or the build will fail
# Check if Swig exists. find_package and find_program are not able to do that.
find_package(Swig 1.3.31 REQUIRED)

#
# Default installation location. Extra quotes are to make sure ${HOME} i expanded
# at configure time, not autoconf time.
#
if(UNIX)
  set(CMAKE_INSTALL_PREFIX "$ENV{HOME}")
elseif(WIN32)
  set(CMAKE_INSTALL_PREFIX "$ENV{HOMEDRIVE}$ENV{HOMEPATH}")
  string(REGEX REPLACE "\\\\" "/" CMAKE_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
endif()
set(CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}/nta/eng")

#
# Determine NTA platform type
#
message(STATUS "checking platform... ")
if(${CMAKE_SIZEOF_VOID_P} MATCHES "8")
  set(nta_platform_arch "64")
else()
  set(nta_platform_arch "32")
endif()
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(CMAKE_OSX_DEPLOYMENT_TARGET ${_CURRENT_OSX_VERSION})
  set(nta_platform "darwin64")
  set(nta_platform_cxxflags "-fPIC -DPIC -Wnewline-eof -m64")
  set(nta_platform_asflags "")
  set(nta_platform_debug_flag "-gfull")
  set(nta_platform_ldflags "-Wl,-u,_munmap")
  set(nta_platform_libs "-liconv -lsqlite3 -framework CoreServices -framework Accelerate")
  set(nta_platform_mpi_extra_libs "")
  set(nta_platform_pypath "/Library/Frameworks/Python.framework/Versions/${PYTHON_VERSION}/lib/python${PYTHON_VERSION}/site-packages/")
  set(nta_platform_pyldflags "-bundle -undefined dynamic_lookup -fPIC")
  set(nta_platform_pyembed "")
  message("darwin on x86_64")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
  if(${nta_platform_arch} MATCHES "64")
    set(nta_platform "linux64")
    set(nta_platform_cxxflags "-m64 -fPIC -DPIC")
    set(nta_platform_asflags "-msse2")
    set(nta_platform_debug_flag "-g")
    # nta_platform_ldflags="-static-libgcc"
    # pthread needed by libapr-1
    set(nta_platform_libs "-lm -lpthread -ldl -lutil -lcrypt -lstdc++")
    set(nta_platform_mpi_extra_libs "-lrt")
    set(nta_platform_testldflags "-Wl,-R\${libdir}/test")
    set(nta_platform_pypath "/usr/lib/python${PYTHON_VERSION}/site-packages/")
    set(nta_platform_pyldflags "-pthread -shared")
    set(nta_platform_pyembed "-Wl,--export-dynamic")
    message("linux64 on x86_64")
  else()    
    set(nta_platform "linux32")
    set(nta_platform_cxxflags "-fPIC -DPIC -ffloat-store")
    set(nta_platform_asflags "")
    set(nta_platform_debug_flag "-g")
    set(nta_platform_ldflags "-static-libgcc")
    set(nta_platform_libs "-lm -lstdc++ -lpthread -ldl -lutil -lrt -lcrypt")
    set(nta_platform_mpi_extra_libs "-lrt")
    set(nta_platform_testldflags "-Wl,-R\${libdir}/test")
    set(nta_platform_pypath "/usr/lib/python${PYTHON_VERSION}/site-packages/")
    set(nta_platform_pyldflags "-pthread -shared")
    set(nta_platform_pyembed "-Wl,--export-dynamic")
    message("linux32 on x86")    
  endif()
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Windows")
  set(nta_platform "win32")
  set(nta_platform_cxxflags "-DWIN32 -fPIC -DPIC -ffloat-store")
  set(nta_platform_asflags "")
  set(nta_platform_debug_flag "-g")
  set(nta_platform_ldflags "-static-libgcc")
  set(nta_platform_libs "libcrypto libpcre")
  set(nta_platform_libs "lm lstdc++ lpthread ldl lutil lrt lcrypt")
  set(nta_platform_mpi_extra_libs "-lrt")
  set(nta_platform_testldflags "-Wl,-R\${libdir}/test")
  get_filename_component(nta_platform_pypath ${PYTHON_EXECUTABLE} PATH)
  set(nta_platform_pyldflags "-pthread -shared")
  set(nta_platform_pyembed "-Wl,--export-dynamic")
  message("windows32 on x86")
else()
  message(FATAL_ERROR "${CMAKE_CURRENT_LIST_FILE}:${CMAKE_CURRENT_LIST_LINE}: error: ${CMAKE_SYSTEM_NAME} not supported yet.")
endif()

#
# enable/disable debugging symbols (-g). Enabled by default (stripped for release)
# This is orthogonal to optimization
#
option(${debugsymbols} "--debugsymbols=[ON/OFF] turn on debug symbols [default=ON]" ON)
message(STATUS "Checking whether debug symbols are enabled... ")
if(${debugsymbols})
  message("on")
else()
  message("off")
endif()
set(NTA_DEBUGSYMBOLS_ENABLED ${debugsymbols})

#
# enable/disable optimization. Enabled by default
# This is orthogonal to debugging symbols
#
option(${optimization} "--optimization=[ON/OFF] turn on optimization [default=ON]" ON)
message(STATUS "Checking whether optimization is enabled... ")
if(${optimization})
  message("on")
else()
  message("off")
endif()
set(NTA_OPTIMIZATION_ENABLED ${optimization})

#
# enable/disable NTA_ASSERT.
#
option(${assertions} "--assertions=[ON/OFF] turn on assertions [default=ON]" ON)
message(STATUS "Checking whether assertions are enabled... ")
if(${assertions})
  message("on")
else()
  message("off")
endif()
set(NTA_ASSERTIONS_ENABLED ${assertions})

#
# enable/disable gprof profiling (this option is not frequently used/tested)
#
option(${profiling} "--profiling=[ON/OFF] turn on profiling [default=OFF]" OFF)
message(STATUS "Checking whether profiling is enabled... ")
if(${profiling})
  message("on")
else()
  message("off")
endif()
set(NTA_PROFILING_ENABLED ${profiling})


message(STATUS "============= Extra NTA Options ==============")

#
# Build using Python headers and library,
# and enable features that depend on Python.
option(${python-support} "--python-support=[ON/OFF] turn on python support [default=ON]" ON)
message(STATUS "Checking whether python support is enabled... ")
if(${python-support})
  message("on")
else()
  message("off")
endif()
set(NTA_PYTHON_SUPPORT ${python-support})

#
# Build using MPI headers and library,
# and enable features that depend on MPI.
option(${mpi} "--mpi=[ON/OFF] turn on MPI support [default=ON]" ON)
message(STATUS "Checking whether MPI support is enabled... ")
if(${mpi})
  message("on")
else()
  message("off")
endif()
set(NTA_MPI_SUPPORT ${mpi})

message(STATUS "Configured for platform ${nta_platform}")
message(STATUS "Platform-specific libraries: ${nta_platform_libs}")
message(STATUS "Platform-specific extra MPI libraries: ${nta_platform_mpi_extra_libs}")
message(STATUS "Platform-specific CXX flags: ${nta_platform_cxxflags}")
message(STATUS "Platform-specific AS flags: ${nta_platform_asflags}")
message(STATUS "Platform-specific Debug flag: ${nta_platform_debug_flag}")
message(STATUS "Platform-specific LD flags: ${nta_platform_ldflags}")
message(STATUS "Platform-specific test library link flags: ${nta_platform_testldflags}")
message(STATUS "Platform-specific Python path: ${nta_platform_pypath}")
message(STATUS "Platform-specific Python extension link flags: ${nta_platform_pyldflags}")
message(STATUS "Platform-specific Python embedding link flags: ${nta_platform_pyembed}")
message(STATUS "Debugging symbols enabled: ${enable_debugsymbols}")
message(STATUS "Assertions enabled: ${enable_assertions}")
message(STATUS "Optimization enabled: ${enable_optimization}")


### 2nd Part: Start the build ###

include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

add_library(libapr-1 STATIC IMPORTED)
set_property(TARGET libapr-1 PROPERTY IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/libapr-1${library_extension}")

add_library(libaprutil-1 STATIC IMPORTED)
set_property(TARGET libaprutil-1 PROPERTY IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/libaprutil-1${library_extension}")

add_library(libz STATIC IMPORTED)
set_property(TARGET libz PROPERTY IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/libz${library_extension}")

add_library(libyaml STATIC IMPORTED)
set_property(TARGET libyaml PROPERTY IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/libyaml${library_extension}")

if(WIN32)
  add_library(libcrypto STATIC IMPORTED)
  set_property(TARGET libcrypto PROPERTY IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/libeay32${library_extension}")

  add_library(libpcre STATIC IMPORTED)
  set_property(TARGET libpcre PROPERTY IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/libpcre${library_extension}")
endif()

# lang/py/support must be built before nta, but lang must be built after nta.
# This is due to the fact that both nta/pynode and lang/py/net_internal depend 
# on lang/py/support and lang/py/engine_internal depends on nta.
add_subdirectory(lang/py/support)
add_subdirectory(nta)
add_subdirectory(qa)
add_subdirectory(examples)
add_subdirectory(lang/py/bindings/engine_internal)
add_subdirectory(py)


### 3rd Part: Post build ###

# Copy all source directories after the build is done
macro (copy_directory SRC DST)
  message(STATUS "Copying from '${SRC}' to '${DST}'")
  execute_process(COMMAND ${CMAKE_COMMAND} -E copy_directory ${SRC} ${DST})
endmacro()
macro (copy_file SRC DST)
  message(STATUS "Copying from '${SRC}' to '${DST}'")
  execute_process(COMMAND ${CMAKE_COMMAND} -E copy ${SRC} ${DST})
endmacro()

# Python modules
copy_directory(${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/python${PYTHON_VERSION}/site-packages/matplotlib ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/matplotlib)
copy_directory(${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/python${PYTHON_VERSION}/site-packages/pytz ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/pytz)
copy_file(${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/python${PYTHON_VERSION}/site-packages/pylab.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/pylab.py)

# Platform independent python libraries
copy_file(${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib/python${PYTHON_VERSION}/site-packages/pkg_resources.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/pkg_resources.py)

# Platform independent executable scripts
copy_file(${CMAKE_SOURCE_DIR}/lang/py/bindings/__init__.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/bindings/__init__.py)

# Pull in the pieces of nupic that we want
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/algorithms ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/algorithms)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/frameworks ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/frameworks)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/analysis ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/analysis)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/image ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/image)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/research ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/research)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/data ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/data)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/database ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/database)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/swarming ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/swarming)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/encoders ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/encoders)
copy_directory(${CMAKE_SOURCE_DIR}/py/nupic/support ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/support)
copy_directory(${CMAKE_SOURCE_DIR}/py/regions	 ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/regions)

# Much of the stuff in nupic.math is old cruft. Get just what we want
copy_file(${CMAKE_SOURCE_DIR}/py/nupic/math/__init__.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/math/__init__.py)
copy_file(${CMAKE_SOURCE_DIR}/py/nupic/math/cross.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/math/cross.py)
copy_file(${CMAKE_SOURCE_DIR}/py/nupic/math/roc_utils.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/math/roc_utils.py)

# Examples
copy_directory(${CMAKE_SOURCE_DIR}/examples/prediction ${CMAKE_INSTALL_PREFIX}/share/prediction)
copy_directory(${CMAKE_SOURCE_DIR}/examples/opf ${CMAKE_INSTALL_PREFIX}/share/opf)

# Test data
copy_directory(${CMAKE_SOURCE_DIR}/qa/shared_data ${CMAKE_INSTALL_PREFIX}/share/test/data)
copy_directory(${CMAKE_SOURCE_DIR}/tests ${CMAKE_INSTALL_PREFIX}/tests)
copy_file(${CMAKE_SOURCE_DIR}/run_tests.sh ${CMAKE_INSTALL_PREFIX}/bin/run_tests.sh)
copy_file(${CMAKE_SOURCE_DIR}/bin/run_tests.py ${CMAKE_INSTALL_PREFIX}/bin/run_tests.py)
copy_file(${CMAKE_SOURCE_DIR}/bin/run_swarm.py ${CMAKE_INSTALL_PREFIX}/bin/run_swarm.py)

# miscellaneous files
copy_directory(${CMAKE_SOURCE_DIR}/external/licenses ${CMAKE_INSTALL_PREFIX}/share/doc/licenses)
copy_file(${CMAKE_SOURCE_DIR}/conf/default/nupic-default.xml ${CMAKE_INSTALL_PREFIX}/conf/default/nupic-default.xml)
copy_file(${CMAKE_SOURCE_DIR}/conf/default/nupic-logging.conf ${CMAKE_INSTALL_PREFIX}/conf/default/nupic-logging.conf)
copy_file(${CMAKE_SOURCE_DIR}/env.sh ${CMAKE_INSTALL_PREFIX}/env.sh)

# Python API and regions
copy_file(${CMAKE_SOURCE_DIR}/lang/py/__init__.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/__init__.py)
# This file is going to be replaced by a "documentored" version
copy_file(${CMAKE_SOURCE_DIR}/lang/py/engine/__init__.py ${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/engine/__init__.py)

# build_system
copy_directory(${CMAKE_SOURCE_DIR}/build_system ${CMAKE_INSTALL_PREFIX}/build_system)

message(STATUS "Removing .la, .pyc and .pyo files")
file(GLOB files 
  "${CMAKE_INSTALL_PREFIX}/lib/*.la"
  "${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/bindings/*.la"
  "${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/bindings/*.pyc"
  "${CMAKE_INSTALL_PREFIX}/lib/python2.6/site-packages/nupic/bindings/*.pyo"
)
foreach(file ${files})
  file(REMOVE ${file})
endforeach()

# TODO: if(not EXISTS "${CMAKE_INSTALL_PREFIX}/.buildinfo")
# TODO:   echo "DEVELOPER BUILD" > ${CMAKE_INSTALL_PREFIX}/.buildinfo
# TODO: endif()

# TODO: if(not EXISTS "${CMAKE_INSTALL_PREFIX}/.build.json")
# TODO:   echo "{""tag"": ""DEVELOPER BUILD""}" > ${CMAKE_INSTALL_PREFIX}/.build.json
# TODO: endif()
