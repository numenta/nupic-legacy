cmake_minimum_required(VERSION 2.8)
project(Nupic)

### 1st Part: Configure the environment ###

# If we enable both static and shared libraries, each file is compiled twice. Once with -fPIC and once without.
# Gives the minimum version of Python necessary to get installation directories
# for use with ${PYTHON_VERSION}, etc.
find_package(PythonInterp 2.6 REQUIRED)
find_package(PythonLibs 2.6 REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

if(PYTHONLIBS_FOUND)
elseif(PYTHONINTERP_FOUND)
else()
  message(FATAL_ERROR "Error: python not found.")
endif()

set(PYTHON_VERSION "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}")
message(STATUS "Version of python is ${PYTHON_VERSION}")

#
# Find out where system installation of python is. This is different from our install prefixn
#
execute_process(COMMAND ${PYTHON_EXECUTABLE} -c "import sys;sys.stdout.write(sys.prefix)"
                    OUTPUT_VARIABLE PYTHON_PREFIX)
message(STATUS "Python sys prefix is ${PYTHON_PREFIX}")

set(PYTHON_LIB "${PYTHON_PREFIX}/lib")
message(STATUS "Python lib dir is ${PYTHON_LIB}")

set(PYTHON_INCLUDE "${PYTHON_PREFIX}/include")

# pip is used for python modules
find_program(PIP pip)
if(${PIP} STREQUAL "")
  message(FATAL_ERROR "Error: pip is needed for Python dependencies.")
endif()


#
# Defaults for variables that may be overridded per-platform.
# Env1-1 are for extra environment variables that need to be set during builds.
set(nta_platform_ldflags "")
set(nta_platform_testldflags "")
set(nta_platform_linkall "")
set(nta_platform_linkmin "")
set(nta_platform_env1 "")

#
# Determine NTA platform type
#
message(STATUS "checking platform... ")
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(nta_platform "darwin64")
  set(nta_platform_cxxflags "-fPIC -DPIC -Wnewline-eof -m64")
  # link against the system version of python (64-bits)
  set(nta_platform_python_libs "-F/System/Library/Frameworks -framework Python")
  set(nta_platform_env1 "MACOSX_DEPLOYMENT_TARGET=10.7")
  set(nta_platform_asflags "")
  set(nta_platform_debug_flag "-gfull")
  set(nta_platform_ldflags "-Wl,-u,_munmap")
  set(nta_platform_libs "-liconv -lsqlite3 -framework CoreServices -framework Accelerate")
  set(nta_platform_mpi_extra_libs "")
  set(nta_platform_pyldflags "-bundle -undefined dynamic_lookup -fPIC")
  set(nta_platform_pyembed "")
  message("darwin on x86_64")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
  if(${CMAKE_SIZEOF_VOID_P} MATCHES "8")
    set(nta_platform "linux64")
    set(nta_platform_cxxflags "-m64 -fPIC -DPIC")
    set(nta_platform_asflags "-msse2")
    set(nta_platform_debug_flag "-g")
    # nta_platform_ldflags="-static-libgcc"
    # pthread needed by libapr-1
    set(nta_platform_libs "-lm -lpthread -ldl -lutil -lcrypt -lstdc++")
    set(nta_platform_mpi_extra_libs "-lrt")
    set(nta_platform_python_libs "-lpython\${PYTHON_VERSION}")
    set(nta_platform_testldflags "-Wl,-R\${libdir}/test")
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
    set(nta_platform_python_libs "-lpython\${PYTHON_VERSION}")
    set(nta_platform_testldflags "-Wl,-R\${libdir}/test")
    set(nta_platform_pyldflags "-pthread -shared")
    set(nta_platform_pyembed "-Wl,--export-dynamic")
    message("linux32 on x86")    
  endif()
else()
  message(FATAL_ERROR "${CMAKE_CURRENT_LIST_FILE}:${CMAKE_CURRENT_LIST_LINE}: error: ${CMAKE_SYSTEM_NAME} not supported yet.")
endif()

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
find_package(SWIG 1.3.31 REQUIRED)
include(${SWIG_USE_FILE})
if(SWIG_FOUND)
else()
  message(WARNING "Cannot find 'swig' program. It should be in the external directory of the NuPIC source distribution")
endif()

message(STATUS "SWIG executable is '${SWIG_EXECUTABLE}'")
message(STATUS "SWIG library directory is '${SWIG_DIR}'")

#
# Default installation location. Extra quotes are to make sure ${HOME} i expanded
# at configure time, not autoconf time.
#
set(CMAKE_INSTALL_PREFIX "$ENV{HOME}/nta/eng")

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
message(STATUS "Platform-specific Python extension link flags: ${nta_platform_pyldflags}")
message(STATUS "Platform-specific Python embedding link flags: ${nta_platform_pyembed}")
message(STATUS "Platform-specific Python library: ${nta_platform_python_libs}")
message(STATUS "Platform-specific Environment Setting: $(nta_platform_env1)")
message(STATUS "Debugging symbols enabled: ${enable_debugsymbols}")
message(STATUS "Assertions enabled: ${enable_assertions}")
message(STATUS "Optimization enabled: ${enable_optimization}")


### 2nd Part: Start the build ###

include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

# lang/py/support must be built before nta, but lang must be built after nta.
# This is due to the fact that both nta/pynode and lang/py/net_internal depend 
# on lang/py/support and lang/py/engine_internal depends on nta.
add_subdirectory(lang/py/support)
add_subdirectory(nta)
add_subdirectory(qa)
add_subdirectory(examples)
add_subdirectory(lang/py/bindings/engine_internal)
add_subdirectory(py)

################################################
# Custom rules to speed up certain build targets
################################################

################################################
# End of custom rules
################################################


######################################################################
## Perform post-installation modifications to the install tree.
######################################################################

execute_process(COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/build_system/pybuild/install.py --overwrite ${CMAKE_SOURCE_DIR}/build_system/post_build/files_to_copy.txt ${CMAKE_SOURCE_DIR} ${CMAKE_INSTALL_PREFIX})

message(STATUS "Removing .la, .pyc and .pyo files")
file(GLOB files 
"${CMAKE_INSTALL_PREFIX}/lib/*.la"
"${CMAKE_INSTALL_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/nupic/bindings/*.la"
"${CMAKE_INSTALL_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/nupic/bindings/*.pyc"
"${CMAKE_INSTALL_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/nupic/bindings/*.pyo"
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
