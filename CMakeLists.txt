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
# --------------------------------------------------------------------------------------------------------------------------

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
  # User did not specify NUPIC_CORE location, assume relative to nupic

  set(NUPIC_CORE_SOURCE "${PROJECT_SOURCE_DIR}/extensions/core")
  set(NUPIC_CORE "${PROJECT_SOURCE_DIR}/extensions/core/build/release")
  set(CMAKE_PREFIX_PATH ${NUPIC_CORE})
  set(BUILD_NUPIC_CORE "TRUE")
else()
  set(CMAKE_PREFIX_PATH ${NUPIC_CORE})
  set(BUILD_NUPIC_CORE "")
endif()

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


if(BUILD_NUPIC_CORE)
  # User has not specified NUPIC_CORE location, build it from scratch
  if(EXISTS "${PROJECT_SOURCE_DIR}/.nupic_config")
    file(STRINGS "${PROJECT_SOURCE_DIR}/.nupic_config" MODULES_FILE_CONTENT REGEX "^[^#]")
  elseif(EXISTS "$ENV{HOME}/.nupic_config")
    file(STRINGS "$ENV{HOME}/.nupic_config" MODULES_FILE_CONTENT REGEX "^[^#]")
  else()
    file(STRINGS "${PROJECT_SOURCE_DIR}/.nupic_modules" MODULES_FILE_CONTENT REGEX "^[^#]")
  endif()
  read_variable_from_file("${MODULES_FILE_CONTENT}" "NUPIC_CORE_REMOTE" NUPIC_CORE_REMOTE)
  read_variable_from_file("${MODULES_FILE_CONTENT}" "NUPIC_CORE_COMMITISH" NUPIC_CORE_COMMITISH)

  # checkout git dependency
  if (NOT EXISTS ${NUPIC_CORE_SOURCE})
    execute_process(COMMAND git clone ${NUPIC_CORE_REMOTE} ${NUPIC_CORE_SOURCE}
                    RESULT_VARIABLE EXIT_CODE)
    if(NOT EXIT_CODE EQUAL 0)
      message(FATAL_ERROR "Unable to clone ${NUPIC_CORE_REMOTE} into ${NUPIC_CORE_SOURCE}")
    endif()
  else()
    execute_process(COMMAND git fetch ${NUPIC_CORE_REMOTE}
                    WORKING_DIRECTORY ${NUPIC_CORE_SOURCE}
                    RESULT_VARIABLE EXIT_CODE)
    if(NOT EXIT_CODE EQUAL 0)
      message(FATAL_ERROR "Unable to fetch ${NUPIC_CORE_REMOTE}")
    endif()
  endif()
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
    message(FATAL_ERROR "Compiling 'nupic_core' library within ${PROJECT_SOURCE_DIR} failed: ${BUILD_NUPIC_CORE_OUTP}")
  endif()


  # Build and set external libraries
  message(STATUS "Building 'nupic_core' library...")

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
    message(FATAL_ERROR "Compiling 'nupic_core' library within ${NUPIC_SOURCE_DIR} failed")
  endif()

  message(STATUS "Done.")
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

set(LIB_DYNAMIC_CPPREGION cpp_region)
add_library(${LIB_DYNAMIC_CPPREGION}
            SHARED
            extensions/cpp_region/PyRegion.cpp
            extensions/cpp_region/unittests/PyHelpersTest.cpp)
target_link_libraries(${LIB_DYNAMIC_CPPREGION}
                      dl
                      python${PYTHON_VERSION}
                      ${LIB_STATIC_SUPPORT}
                      ${LIB_STATIC_GTEST}
                      ${COMMON_LIBS})
set_target_properties(${LIB_DYNAMIC_CPPREGION}
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
    -nofastproxy
    -fastquery
    -outputtuple
    -castmode
    -w402
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

set(LIB_SHARED_ENGINEINTERNAL engine_internal)
file(MAKE_DIRECTORY "${PROJECT_BUILD_TEMP_DIR}/extensions/bindings/py/engine_internal")
set_source_files_properties(extensions/bindings/py/engine_internal/EngineInternalPy.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE extensions/bindings/py/engine_internal/EngineInternalPy.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_SHARED_ENGINEINTERNAL}
                python
                extensions/bindings/py/engine_internal/EngineInternalPy.i)
set_target_properties(${SWIG_MODULE_${LIB_SHARED_ENGINEINTERNAL}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_SHARED_ENGINEINTERNAL} ${SWIG_COMMON_LIBRARIES})

set(LIB_SHARED_MATH math)
file(MAKE_DIRECTORY "${PROJECT_BUILD_TEMP_DIR}/extensions/bindings/py/math")
set_source_files_properties(extensions/bindings/py/math/MathPy.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE extensions/bindings/py/math/MathPy.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_SHARED_MATH}
                python
                extensions/bindings/py/math/MathPy.i
                extensions/bindings/py/math/PySparseTensor.cpp)
set_target_properties(${SWIG_MODULE_${LIB_SHARED_MATH}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_SHARED_MATH} ${SWIG_COMMON_LIBRARIES})

set(LIB_SHARED_ALGORITHMS algorithms)
file(MAKE_DIRECTORY "${PROJECT_BUILD_TEMP_DIR}/extensions/bindings/py/algorithms")
set_source_files_properties(extensions/bindings/py/algorithms/AlgorithmsPy.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE extensions/bindings/py/algorithms/AlgorithmsPy.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_SHARED_ALGORITHMS} python extensions/bindings/py/algorithms/AlgorithmsPy.i)
set_target_properties(${SWIG_MODULE_${LIB_SHARED_ALGORITHMS}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_SHARED_ALGORITHMS} ${SWIG_COMMON_LIBRARIES})

set(LIB_SHARED_IORANGE iorange)
file(MAKE_DIRECTORY "${PROJECT_BUILD_TEMP_DIR}/extensions/bindings/py/iorange")
set_source_files_properties(extensions/bindings/py/iorange/IorangePy.i PROPERTIES CPLUSPLUS ON)
set_property(SOURCE extensions/bindings/py/iorange/IorangePy.i PROPERTY SWIG_FLAGS ${CMAKE_SWIG_FLAGS})
swig_add_module(${LIB_SHARED_IORANGE} python extensions/bindings/py/iorange/IorangePy.i)
set_target_properties(${SWIG_MODULE_${LIB_SHARED_IORANGE}_REAL_NAME}
                      PROPERTIES COMPILE_FLAGS ${COMMON_COMPILE_FLAGS}
                                 LINK_FLAGS ${COMMON_LINK_FLAGS}
                                 LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR})
swig_link_libraries(${LIB_SHARED_IORANGE} ${SWIG_COMMON_LIBRARIES})

#
# Custom targets
#

add_custom_target(python_unit_tests
                  COMMAND ${PYTHON} ${PROJECT_SOURCE_DIR}/scripts/run_tests.py -u --coverage
                  COMMENT "Python unit tests")

add_custom_target(python_integration_tests
                  COMMAND ${PYTHON} ${PROJECT_SOURCE_DIR}/scripts/run_tests.py -i --coverage
                  COMMENT "Python integration tests")

add_custom_target(python_swarming_tests
                  COMMAND ${PYTHON} ${PROJECT_SOURCE_DIR}/scripts/run_tests.py -w --coverage
                  COMMENT "Python swarming tests")

add_custom_target(python_all_tests
                  COMMAND ${PYTHON} ${PROJECT_SOURCE_DIR}/scripts/run_tests.py --all --coverage # swarming tests fail with the -n parallel run
                  COMMENT "Python tests + integration + swarming (requires DB)")

add_custom_target(tests_pyhtm
                  COMMAND ${PROJECT_BINARY_DIR}/testpyhtm
                  COMMENT "Basic tests in Python")

add_custom_target(tests_cpphtm
                  COMMAND ${PROJECT_BINARY_DIR}/testcpphtm
                  COMMENT "Basic tests in C++")

add_custom_target(cpp_unit_tests
                  COMMAND ${PROJECT_BINARY_DIR}/unit_tests
                  COMMENT "C++ unit tests")

add_custom_target(tests_all
                  DEPENDS python_all_tests
                  DEPENDS tests_pyhtm
                  DEPENDS tests_cpphtm
                  DEPENDS cpp_unit_tests
                  COMMENT "Running all tests")

#
# Installation targets
#

install(TARGETS
        ${EXECUTABLE_HTMTEST}
        DESTINATION ${PROJECT_SOURCE_DIR}/bin)
install(TARGETS
        ${LIB_DYNAMIC_CPPREGION}
        DESTINATION ${PROJECT_SOURCE_DIR}/nupic)
install(FILES
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_SHARED_ENGINEINTERNAL}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_SHARED_ENGINEINTERNAL}.py"
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_SHARED_MATH}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_SHARED_MATH}.py"
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_SHARED_ALGORITHMS}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_SHARED_ALGORITHMS}.py"
        "${PROJECT_BINARY_DIR}/${SWIG_MODULE_${LIB_SHARED_IORANGE}_REAL_NAME}.so"
        "${PROJECT_BUILD_TEMP_DIR}/${LIB_SHARED_IORANGE}.py"
        DESTINATION ${PROJECT_SOURCE_DIR}/nupic/bindings)
