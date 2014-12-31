# --------------------------------------------------------------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
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
#
# Contributor(s):
#   David Ragazzi (@DavidRagazzi): Full conversion and adaptation from Autotools scripts
#   Austin Marshall (amarshall@numenta.com): On-going maintenance
#   Matthew Taylor (matt@numenta.org): Updates for nupic.core integration
# --------------------------------------------------------------------------------------------------------------------------

# Command Line Options
# ====================
# -DNUPIC_CORE        : (optional) Absolute path to nupic.core binary release directory

cmake_minimum_required(VERSION 2.8)
project(nupic CXX)
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# This function reads variables from a file in the following format:
# FOO = 'bar'
function (read_variable_from_file file_content variable value)
  set(${value} PARENT_SCOPE)
  foreach(line ${file_content})
    string(REGEX MATCH "^${variable}" match "${line}")
    if(NOT "${match}" STREQUAL "")
      string(REGEX REPLACE "${variable} = '([^']+)'.*" "\\1" tag_value "${line}")
      set(${value} "${tag_value}" PARENT_SCOPE)
    endif()
  endforeach()
endfunction()

function (unpack_nupic_core source_path package_file)
  string(REGEX REPLACE "\\.tar\\.gz" "" UNPACK_DIR "${package_file}")
  message(STATUS "Unpacking ${package_file} into ${UNPACK_DIR}...")
  set(RELEASE_DIR "${source_path}/build/release")
  file(REMOVE_RECURSE "${source_path}/build/release/bin")
  file(REMOVE_RECURSE "${source_path}/build/release/include")
  file(REMOVE_RECURSE "${source_path}/build/release/lib")
  execute_process(
    COMMAND ${CMAKE_COMMAND} -E tar xzf "${package_file}"
    WORKING_DIRECTORY "${source_path}/build/release"
  )
  file(RENAME "${UNPACK_DIR}/bin" "${RELEASE_DIR}/bin")
  file(RENAME "${UNPACK_DIR}/include" "${RELEASE_DIR}/include")
  file(RENAME "${UNPACK_DIR}/lib" "${RELEASE_DIR}/lib")
  file(REMOVE_RECURSE "${UNPACK_DIR}")
endfunction()

#
# Identify platform
#
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(PLATFORM "darwin")
  set(STDLIB "-stdlib=libc++")
  set(CMAKE_OSX_DEPLOYMENT_TARGET "10.7")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
  set(PLATFORM "linux")
  set(STDLIB "")
endif()

set(BITNESS 32)
if(CMAKE_SIZEOF_VOID_P EQUAL 8)
  set(BITNESS 64)
endif()

#
# Checks if Python is installed and gets its variables.
# Minimum version of Python is 2.6 -- earlier versions *will* fail.
#
# Please don't use 'find_package' for finding Python (System version), it has presented several conflicting results.
# Instead we just use a shell command to execute a simple python command, if exit code is 0 ('success') then we have python installed.
#

#
# Check for user-defined PYTHON env variable
#
if(NOT "$ENV{PYTHON}" STREQUAL "")
  set(PYTHON "$ENV{PYTHON}")
else()
  set(PYTHON "python")
endif()

execute_process(COMMAND ${PYTHON} --version
                RESULT_VARIABLE EXIT_CODE)
if(NOT EXIT_CODE EQUAL 0)
  message(FATAL_ERROR "System Python not found. You do not have a system version of Python or it is not set on environment path.")
endif()

#
# Gives the version of Python necessary to get installation directories
# for use with ${PYTHON_VERSION}, etc.
#
execute_process(COMMAND ${PYTHON} -c "import sys;sys.stdout.write(str(sys.version_info[0]) + '.' + str(sys.version_info[1]))"
                OUTPUT_VARIABLE PYTHON_VERSION)
if(NOT(${PYTHON_VERSION} EQUAL "2.6" OR ${PYTHON_VERSION} EQUAL "2.7"))
  message(FATAL_ERROR "Only these versions of Python are accepted: 2.6, 2.7")
endif()

set(NUPIC_CORE_EXTRA_CXXFLAGS, "-DNTA_PYTHON_SUPPORT=${PYTHON_VERSION} ${NUPIC_CORE_EXTRA_CXXFLAGS}")

#
# Find out where system installation of python is.
#
execute_process(COMMAND ${PYTHON} -c "import sys;sys.stdout.write(sys.prefix)"
                OUTPUT_VARIABLE PYTHON_PREFIX)
string(REGEX REPLACE "\\\\" "/" PYTHON_PREFIX ${PYTHON_PREFIX})
set(PYTHON_INCLUDE_DIR "${PYTHON_PREFIX}/include/python${PYTHON_VERSION}")
set(PYTHON_LIBRARY_DIR "${PYTHON_PREFIX}/lib/python${PYTHON_VERSION}")

#
# Finds out version of Numpy and headers's path.
#
execute_process(COMMAND ${PYTHON} -c "import sys;import numpy;sys.stdout.write(numpy.get_include())"
                OUTPUT_VARIABLE NUMPY_INCLUDE_DIR)
string(REGEX REPLACE "\\\\" "/" NUMPY_INCLUDE_DIR ${NUMPY_INCLUDE_DIR})
execute_process(COMMAND ${PYTHON} -c "import sys;import numpy;sys.stdout.write(numpy.__version__)"
                OUTPUT_VARIABLE NUMPY_VERSION)

set(CMAKE_INSTALL_PREFIX ${PROJECT_SOURCE_DIR})

if("${NUPIC_CORE}" STREQUAL "")
  # User did not specify NUPIC_CORE binary location, assume relative to nupic
  set(NUPIC_CORE "${PROJECT_SOURCE_DIR}/extensions/core/build/release")
  set(NUPIC_CORE_SOURCE "${PROJECT_SOURCE_DIR}/extensions/core")
  set(FETCH_NUPIC_CORE TRUE)
else()
  # User specified that they have their own nupic.core
  set(FETCH_NUPIC_CORE FALSE)
endif()

set(CMAKE_PREFIX_PATH ${NUPIC_CORE})
set(CMAKE_INCLUDE_PATH "${NUPIC_CORE}/include")

add_definitions(-DNTA_PLATFORM_${PLATFORM}${BITNESS}
                -DHAVE_CONFIG_H
                -DNTA_INTERNAL
                -DBOOST_NO_WREGEX
                -DNUPIC2
                -DNTA_ASSERTIONS_ON
                -DNTA_ASM
                -DNTA_PYTHON_SUPPORT=${PYTHON_VERSION})

include_directories(SYSTEM
                    "${PROJECT_SOURCE_DIR}/external/${PLATFORM}${BITNESS}/include"
                    "${PROJECT_SOURCE_DIR}/external/common/include"
                    "${PROJECT_SOURCE_DIR}/extensions"
                    "${PROJECT_SOURCE_DIR}"
                    "${PROJECT_BINARY_DIR}"
                    "${PYTHON_PREFIX}/lib"
                    "${PYTHON_INCLUDE_DIR}"
                    ${CMAKE_INCLUDE_PATH}
                    ${NUMPY_INCLUDE_DIR})

set(COMMON_COMPILE_FLAGS "-fPIC") # `position independent code`, required for shared libraries
set(COMMON_COMPILE_FLAGS "${COMMON_COMPILE_FLAGS} -std=c++11") # Adhere to c++11 spec
set(COMMON_COMPILE_FLAGS "${COMMON_COMPILE_FLAGS} ${STDLIB}") # Adhere to c++11 spec
set(COMMON_COMPILE_FLAGS "${COMMON_COMPILE_FLAGS} -m${BITNESS}") # Generate 32 or 64 bit code
set(COMMON_COMPILE_FLAGS "${COMMON_COMPILE_FLAGS} -fvisibility=hidden -Wall -Wreturn-type -Wunused -Wno-unused-parameter")

set(LIB_STATIC_SUPPORT py_support)
add_library(${LIB_STATIC_SUPPORT}
            extensions/py_support/NumpyVector.cpp
            extensions/py_support/PyArray.cpp
            extensions/py_support/PyHelpers.cpp
            extensions/py_support/PythonStream.cpp)
set_target_properties(${LIB_STATIC_SUPPORT} PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS})
set_target_properties(${LIB_STATIC_SUPPORT} PROPERTIES LINK_FLAGS "-m${BITNESS} {STDLIB}")

set(NUPIC_CORE_BUCKET "https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core")

if(FETCH_NUPIC_CORE)
  # User has not specified NUPIC_CORE location, so we'll download the binaries

  # First, get the nupic.core SHA and remote location from local config.
  if(EXISTS "${PROJECT_SOURCE_DIR}/.nupic_config")
    file(STRINGS "${PROJECT_SOURCE_DIR}/.nupic_config" MODULES_FILE_CONTENT REGEX "^[^#]")
  elseif(EXISTS "$ENV{HOME}/.nupic_config")
    file(STRINGS "$ENV{HOME}/.nupic_config" MODULES_FILE_CONTENT REGEX "^[^#]")
  else()
    file(STRINGS "${PROJECT_SOURCE_DIR}/.nupic_modules" MODULES_FILE_CONTENT REGEX "^[^#]")
  endif()
  read_variable_from_file("${MODULES_FILE_CONTENT}" "NUPIC_CORE_REMOTE" NUPIC_CORE_REMOTE)
  read_variable_from_file("${MODULES_FILE_CONTENT}" "NUPIC_CORE_COMMITISH" NUPIC_CORE_COMMITISH)

  set(NUPIC_CORE_REMOTE_URL "${NUPIC_CORE_BUCKET}/nupic_core-${NUPIC_CORE_COMMITISH}-${PLATFORM}${BITNESS}.tar.gz")
  set(NUPIC_CORE_LOCAL_PACKAGE "${NUPIC_CORE}/nupic_core-${NUPIC_CORE_COMMITISH}-${PLATFORM}${BITNESS}.tar.gz")

  if(EXISTS "${NUPIC_CORE_LOCAL_PACKAGE}")
    message(STATUS "Target nupic.core package already exists at ${NUPIC_CORE_LOCAL_PACKAGE}.")
    unpack_nupic_core("${NUPIC_CORE_SOURCE}" "${NUPIC_CORE_LOCAL_PACKAGE}")
  else()
    message(STATUS "Attempting to fetch nupic.core binaries from ${NUPIC_CORE_REMOTE_URL} and save to ${NUPIC_CORE_LOCAL_PACKAGE}...")
    file(DOWNLOAD "${NUPIC_CORE_REMOTE_URL}" "${NUPIC_CORE_LOCAL_PACKAGE}"
      INACTIVITY_TIMEOUT 30
      TIMEOUT 300
      STATUS "NUPIC_CORE_DOWNLOAD_STATUS"
      SHOW_PROGRESS)

    # TODO: Give user a way to clean up all the downloaded binaries. It can be
    # manually done with `rm -rf ${NUPIC_CORE}/extensions/core` but would be
    # cleaner with something like `python setup.py clean`.

    if(NOT NUPIC_CORE_DOWNLOAD_STATUS EQUAL 0)
      message(WARNING "Error downloading nupic.core package: ${NUPIC_CORE_DOWNLOAD_STATUS}")
      message(STATUS "Building nupic.core from local checkout ${NUPIC_CORE_SOURCE}...")
      # Remove the local package file, which didn't get populated due to the
      # download failure.
      file(REMOVE "${NUPIC_CORE_LOCAL_PACKAGE}")

      # Get nupic.core dependency through git.
      if (NOT(EXISTS "${NUPIC_CORE_SOURCE}/.git"))
        # There's not a git repo in NUPIC_CORE_SOURCE, so we can blow the whole
        # directory away and clone nupic.core there.
        file(REMOVE_RECURSE "${NUPIC_CORE_SOURCE}")
        file(MAKE_DIRECTORY "${NUPIC_CORE_SOURCE}")
        execute_process(COMMAND git clone ${NUPIC_CORE_REMOTE} ${NUPIC_CORE_SOURCE}
                        RESULT_VARIABLE EXIT_CODE)
        if(NOT EXIT_CODE EQUAL 0)
          message(FATAL_ERROR "Unable to clone ${NUPIC_CORE_REMOTE} into ${NUPIC_CORE_SOURCE}")
        endif()
      else()
        # Fetch if already cloned.
        execute_process(COMMAND git fetch ${NUPIC_CORE_REMOTE}
                        WORKING_DIRECTORY ${NUPIC_CORE_SOURCE}
                        RESULT_VARIABLE EXIT_CODE)
        if(NOT EXIT_CODE EQUAL 0)
          message(FATAL_ERROR "Unable to fetch ${NUPIC_CORE_REMOTE}")
        endif()
      endif()

      # Get the exact SHA we need for nupic.core.
      execute_process(COMMAND git reset --hard ${NUPIC_CORE_COMMITISH}
                      WORKING_DIRECTORY ${NUPIC_CORE_SOURCE}
                      RESULT_VARIABLE EXIT_CODE)
      if(NOT EXIT_CODE EQUAL 0)
        message(FATAL_ERROR "Unable to checkout ${NUPIC_CORE_COMMITISH} in ${NUPIC_CORE_SOURCE}")
      endif()

      # Execute the Make scripts
      execute_process(COMMAND git clean -fdx
                      WORKING_DIRECTORY ${NUPIC_CORE_SOURCE}
                      RESULT_VARIABLE EXIT_CODE)
      if(NOT EXIT_CODE EQUAL 0)
        message(FATAL_ERROR "Compiling 'nupic.core' library within ${PROJECT_SOURCE_DIR} failed: ${BUILD_NUPIC_CORE_OUTP}")
      endif()

      # Build and set external libraries
      message(STATUS "Building 'nupic.core' library...")

      # Clean 'build/scripts' subfolder at submodule folder
      execute_process(COMMAND ${CMAKE_COMMAND} -E remove_directory ${NUPIC_CORE_SOURCE}/build/scripts)
      execute_process(COMMAND ${CMAKE_COMMAND} -E remove_directory ${NUPIC_CORE_SOURCE}/build/scripts)
      execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${NUPIC_CORE_SOURCE}/build/scripts)
      execute_process(COMMAND ${CMAKE_COMMAND} -E remove_directory ${NUPIC_CORE})
      # Generate the Make scripts
      execute_process(COMMAND ${CMAKE_COMMAND} ${NUPIC_CORE_SOURCE}/src -DCMAKE_INSTALL_PREFIX=${NUPIC_CORE}
                      WORKING_DIRECTORY ${NUPIC_CORE_SOURCE}/build/scripts)

      set(USER_MAKE_COMMAND "make" CACHE STRING "Default `make` command used to build nupic.core")

      # Execute the Make scripts
      execute_process(COMMAND ${USER_MAKE_COMMAND} install -j3
                      WORKING_DIRECTORY ${NUPIC_CORE_SOURCE}/build/scripts
                      RESULT_VARIABLE EXIT_CODE
                      OUTPUT_VARIABLE OUTP)
      if(NOT EXIT_CODE EQUAL 0)
        message(FATAL_ERROR "Compiling 'nupic.core' library within ${NUPIC_SOURCE_DIR} failed")
      endif()

      message(STATUS "Done.")
    else()
      message(STATUS "Download successful.")
      unpack_nupic_core("${NUPIC_CORE_SOURCE}" "${NUPIC_CORE_LOCAL_PACKAGE}")
    endif()
  endif()
else()
  message(STATUS "Using nupic.core binaries at ${NUPIC_CORE}")
endif()

find_library(LIB_STATIC_GTEST gtest)

set(LIB_STATIC_NUPICCORE nupic_core)
find_library(LIB_STATIC_NUPICCORE_LOC ${LIB_STATIC_NUPICCORE} "${NUPIC_CORE}/lib")

add_library(${LIB_STATIC_NUPICCORE_LOC} STATIC IMPORTED GLOBAL)

set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} -fPIC")
set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} -m${BITNESS}")
set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} -std=c++11")
set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} ${STDLIB}")
set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} -L${NUPIC_CORE}/lib")
set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} -lyaml-cpp")
set(COMMON_LINK_FLAGS "${COMMON_LINK_FLAGS} -L${PYTHON_PREFIX}/lib")

set(COMMON_LIBS ${LIB_STATIC_NUPICCORE})
if("${PLATFORM}" STREQUAL "linux")
  list(APPEND COMMON_LIBS pthread dl)
elseif("${PLATFORM}" STREQUAL "darwin")
  set(COMPILE_FLAGS "${COMPILE_FLAGS} -O3")
endif()

set(EXECUTABLE_HTMTEST testpyhtm)
set(LIBRARIES ${LIB_STATIC_SUPPORT})
add_executable(${EXECUTABLE_HTMTEST} extensions/htmtest/htmtest.cpp)
target_link_libraries(${EXECUTABLE_HTMTEST} ${COMMON_LIBS})
set_target_properties(${EXECUTABLE_HTMTEST}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS "${COMMON_LINK_FLAGS}")
add_custom_target(tests_htm
                  COMMAND ${EXECUTABLE_HTMTEST}
                  DEPENDS ${EXECUTABLE_HTMTEST})

set(LIB_MODULE_CPPREGION cpp_region)
add_library(${LIB_MODULE_CPPREGION}
            MODULE
            extensions/cpp_region/PyRegion.cpp
            extensions/cpp_region/unittests/PyHelpersTest.cpp)
target_link_libraries(${LIB_MODULE_CPPREGION}
                      dl
                      python${PYTHON_VERSION}
                      ${LIB_STATIC_SUPPORT}
                      ${LIB_STATIC_GTEST}
                      ${COMMON_LIBS})
set_target_properties(${LIB_MODULE_CPPREGION}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS})

#
# SWIG
#
set(SWIG_EXECUTABLE "${PROJECT_SOURCE_DIR}/external/${PLATFORM}${BITNESS}/bin/swig" CACHE STRING "Swig executable")
set(SWIG_DIR "${PROJECT_SOURCE_DIR}/external/common/share/swig/3.0.2" CACHE STRING "Swig dir")
set(PROJECT_BUILD_TEMP_DIR ${PROJECT_SOURCE_DIR}/temp)
# CMAKE_CURRENT_BINARY_DIR is used by swig module for put wrappers on, so don't erase this line!
set(CMAKE_CURRENT_BINARY_DIR ${PROJECT_BUILD_TEMP_DIR})
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -I${PROJECT_SOURCE_DIR}")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -I${PROJECT_SOURCE_DIR}/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -I${PROJECT_BUILD_INCLUDE_DIR}")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -I${PROJECT_SOURCE_DIR}/extensions")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -I${PROJECT_BUILD_RELEASE_DIR}/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -isystem${PROJECT_SOURCE_DIR}/extensions/core/external/${NTA_PLATFORM_OS}/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -isystem${PROJECT_SOURCE_DIR}/extensions/core/external/common/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -isystem${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -isystem${PROJECT_SOURCE_DIR}/external/common/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -isystem${NUPIC_CORE}/include")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -isystem${NUPIC_CORE}/include/yaml-cpp")
set(NTA_INCLUDEFLAGS "${NTA_INCLUDEFLAGS} -I${PYTHON_PREFIX}/lib")

include(${CMAKE_ROOT}/Modules/UseSWIG.cmake)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# swig options from: https://github.com/swig/swig/blob/master/Source/Modules/python.cxx#L111
set(CMAKE_SWIG_FLAGS
    -features
    autodoc=0,directors=0
    -noproxyimport
    -keyword
    -modern
    -modernargs
    -noproxydel
    -fvirtual
    -fastunpack
    -nofastproxy #TODO remove this for optimization -O
    -fastquery
    -outputtuple
    -castmode
    -fastdispatch
    -nosafecstrings
    -fastinit
    -nobuildnone
    -dirvtable
    -w402 #TODO what are these?
    -w503
    -w511
    -w302
    -w362
    -w312
    -w389
    -DSWIG_PYTHON_LEGACY_BOOL
    -DNTA_PLATFORM_${PLATFORM}${BITNESS}
    -DNTA_PYTHON_SUPPORT=${PYTHON_VERSION}
    -I${NUMPY_INCLUDE_DIR}
    -I${SWIG_DIR}/python
    -I${SWIG_DIR}
    -I${PYTHON_PREFIX}/lib)

set(SWIG_COMMON_LIBRARIES
    ${PYTHON_LIBRARIES}
    dl
    python${PYTHON_VERSION}
    ${LIB_STATIC_NUPICCORE}
    ${LIB_STATIC_SUPPORT})

file(MAKE_DIRECTORY "${PROJECT_BUILD_TEMP_DIR}/nupic/bindings")

set(LIB_MODULE_ENGINEINTERNAL engine_internal)
set_source_files_properties(nupic/bindings/engine_internal.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE nupic/bindings/engine_internal.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_MODULE_ENGINEINTERNAL}
                python
                nupic/bindings/engine_internal.i)
set_target_properties(${SWIG_MODULE_${LIB_MODULE_ENGINEINTERNAL}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_MODULE_ENGINEINTERNAL} ${SWIG_COMMON_LIBRARIES})

set(LIB_MODULE_MATH math)
set_source_files_properties(nupic/bindings/math.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE nupic/bindings/math.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_MODULE_MATH}
                python
                nupic/bindings/math.i
                nupic/bindings/PySparseTensor.cpp)
set_target_properties(${SWIG_MODULE_${LIB_MODULE_MATH}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_MODULE_MATH} ${SWIG_COMMON_LIBRARIES})

set(LIB_MODULE_ALGORITHMS algorithms)
set_source_files_properties(nupic/bindings/algorithms.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE nupic/bindings/algorithms.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_MODULE_ALGORITHMS} python nupic/bindings/algorithms.i)
set_target_properties(${SWIG_MODULE_${LIB_MODULE_ALGORITHMS}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_MODULE_ALGORITHMS} ${SWIG_COMMON_LIBRARIES})

set(SKIP_COMPARE_VERSIONS (NOT ${FETCH_NUPIC_CORE}) CACHE BOOL "Skip nupic.core version comparison")

if (NOT ${SKIP_COMPARE_VERSIONS})
  # Compare expected version of nupic.core against installed version
  set(EXECUTABLE_COMPAREVERSION compare_nupic_core_version)
  add_executable(${EXECUTABLE_COMPAREVERSION} extensions/compare_nupic_core_version.cpp)
  target_link_libraries(${EXECUTABLE_COMPAREVERSION} ${COMMON_LIBS})
  set_target_properties(${EXECUTABLE_COMPAREVERSION}
                        PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                   LINK_FLAGS "${COMMON_LINK_FLAGS}")

  add_dependencies(${EXECUTABLE_COMPAREVERSION} ${COMMON_LIBS})

  add_custom_target(assert_nupic_core_version
                    COMMAND ${EXECUTABLE_COMPAREVERSION} ${NUPIC_CORE_COMMITISH}
                    DEPENDS ${EXECUTABLE_COMPAREVERSION})

  add_dependencies(${LIB_MODULE_CPPREGION} assert_nupic_core_version)
endif()



#
# Installation targets
#

install(TARGETS
        ${EXECUTABLE_HTMTEST}
        DESTINATION ${PROJECT_SOURCE_DIR}/bin)
install(TARGETS
        ${LIB_MODULE_CPPREGION}
        DESTINATION ${PROJECT_SOURCE_DIR}/nupic)
install(FILES
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_MODULE_ENGINEINTERNAL}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_MODULE_ENGINEINTERNAL}.py"
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_MODULE_MATH}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_MODULE_MATH}.py"
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_MODULE_ALGORITHMS}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_MODULE_ALGORITHMS}.py"
        DESTINATION ${PROJECT_SOURCE_DIR}/nupic/bindings)
