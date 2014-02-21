# --------------------------------------------------------------------------------------------------------------------------
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
#
# Contributor(s):
#   David Ragazzi (@DavidRagazzi): Full conversion and adaptation from Autotools scripts
# --------------------------------------------------------------------------------------------------------------------------
 

############################################################################################################################
###                                                                                                                      ###
###  Macros                                                                                                              ###
###                                                                                                                      ###
############################################################################################################################

# This macro set environment variables of the operating system
macro (show_environment_variable variable value)
  message(STATUS "  ${variable} = ${value}")
endmacro()

# This macro set environment variables of the operating system
macro (set_environment_variable variable value incremental)
  set(current_value "$ENV{${variable}}")
  set(new_value "${value}")

  # Check if variable already is set
  set(is_set OFF)
  string(REGEX MATCH "${new_value}" found_value "${current_value}")
  if("${found_value}" STREQUAL "${new_value}")
    set(is_set ON)
  endif()

  if(NOT is_set)
    # 'incremental' option means that new value wont replace current value, but increments it (ex: PATH variable)
    if("${incremental}" STREQUAL "ON")
      set(new_value "${new_value}:${current_value}")
    endif()

    if(LINUX)
      execute_process(COMMAND export ${variable}=${new_value})
    elseif(OSX)
      execute_process(COMMAND launchctl setenv ${variable} ${new_value})
    elseif(WINDOWS)
      execute_process(COMMAND setx ${variable} ${new_value})
    endif()
  endif()

  show_environment_variable(${variable} ${new_value})
endmacro()

# These macros copy all source directories after the configuration is done
# Note: If NTAX_DEVELOPER_BUILD is set, copy is optimized (directories are linked, and files are not copied if the modification time of the target is more recent).
macro (copy suffix src dst)  
  if("$ENV{NTAX_DEVELOPER_BUILD}" STREQUAL "1")
    message(STATUS "Linking from '${src}' to '${dst}'")
    get_filename_component(dst_dir ${dst} PATH)
    execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${dst_dir})
    execute_process(COMMAND ${CMAKE_COMMAND} -E create_symlink ${src} ${dst})
  else()
    message(STATUS "Copying from '${src}' to '${dst}'")
    execute_process(COMMAND ${CMAKE_COMMAND} -E copy${suffix} ${src} ${dst})
  endif()
endmacro()
macro (copy_file src dst)
  copy("" ${src} ${dst})
endmacro()
macro (copy_directory src dst)
  copy("_directory" ${src} ${dst})
endmacro()

# This macro get all files from a directory and its subdirectories.
macro (get_files_list current_dir dir_mask file_mask)
  file(GLOB children RELATIVE ${current_dir} ${current_dir}/*)
  foreach(child ${children})
    if(IS_DIRECTORY ${current_dir}/${child})
      get_files_list(${current_dir}/${child} ${dir_mask} ${file_mask})
    else()
      set(can_return_file ON)
      if(NOT "${dir_mask}" STREQUAL " ")
        if(NOT ${current_dir} MATCHES ${dir_mask})
          set(can_return_file OFF)
        endif()
      endif()
      if(NOT "${file_mask}" STREQUAL " ")
        if(NOT ${child} MATCHES ${file_mask})
          set(can_return_file OFF)
        endif()
      endif()
      if(can_return_file)
        set(FILES_RETURNED ${FILES_RETURNED} ${current_dir}/${child})
      endif()
    endif()
  endforeach()
endmacro()

# This macro generates a executable
macro(generate_executable name cxx_flags source_files link_flags libraries)
  add_executable(${name}
    ${source_files}
  )
  target_link_libraries(${name}
    ${libraries}
  )
  set_target_properties(${name} PROPERTIES COMPILE_FLAGS "${cxx_flags}")
  set_target_properties(${name} PROPERTIES LINK_FLAGS "${link_flags}")
endmacro()

# This macro generates a static library
macro(generate_static_library name cxx_flags source_files)
  add_library(${name}
    ${source_files}
  )
  set_target_properties(${name} PROPERTIES COMPILE_FLAGS "${cxx_flags}")
endmacro()

# This macro generates a dynamic library
macro(generate_dynamic_library name cxx_flags source_files link_flags libraries)
  add_library(${name} SHARED
    ${source_files}
  )
  target_link_libraries(${name}
    ${libraries}
  )
  set_target_properties(${name} PROPERTIES COMPILE_FLAGS "${cxx_flags}")
  set_target_properties(${name} PROPERTIES LINK_FLAGS "${link_flags}")
endmacro()

# This macro generates a swig module
macro(generate_swig_module name sub_dir swig_flags cxx_flags extra_source link_flags libraries)
  string(REPLACE " " ";" swig_flags ${swig_flags})
  file(MAKE_DIRECTORY "${TEMP_BUILD_DIR}/${sub_dir}")

  set(IMPLEMENTATION_FILE "${PROJECT_SOURCE_DIR}/${sub_dir}/${name}_py.i")
  set_source_files_properties(${IMPLEMENTATION_FILE} PROPERTIES CPLUSPLUS ON)
  set_source_files_properties(${IMPLEMENTATION_FILE} PROPERTIES SWIG_FLAGS "${swig_flags}")
  swig_add_module(${name} python
    ${IMPLEMENTATION_FILE}
    ${extra_source}
  )

  set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES COMPILE_FLAGS "${cxx_flags} -DSWIG_TYPE_TABLE=_nupic_${name}")
  set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES LINK_FLAGS "${link_flags}")
  set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SWIG_OUTDIR})
  foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG)
    set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${CMAKE_SWIG_OUTDIR})
  endforeach()
  swig_link_libraries(${name}
    ${libraries}
  )
endmacro()


############################################################################################################################
###                                                                                                                      ###
###  1st Part:                                                                                                           ###
###  Configuration of the environment                                                                                    ###
###                                                                                                                      ###
############################################################################################################################

#
# Set C++ compiler.
# According to CMake documentation, this must be done before any language is set (ie before any project() or enable_language() command).
#
set(USER_CXX_COMPILER "" CACHE STRING "Default C++ compiler to be used (GCC / CLANG) [default=system compiler]")
if(NOT "${USER_CXX_COMPILER}" STREQUAL "")
  set(CMAKE_CXX_COMPILER "${USER_CXX_COMPILER}")
endif()

cmake_minimum_required(VERSION 2.8)
project(Nupic CXX)

# Check if default C/C++ compiler is GNU or CLANG, otherwise exit with error.  
if(NOT(CMAKE_COMPILER_IS_GNUCXX OR ${CMAKE_CXX_COMPILER} MATCHES "clang"))
  message(FATAL_ERROR "${CMAKE_CXX_COMPILER} compiler not supported yet. If you have GNU or CLANG C++ compiler installed on your machine change $CXX environment variable or pass its location through USER_CXX_COMPILER option.")
endif()

#
# Sets default locations.
# 
# Default directories structure is:
#
# ~/../repository (root directory with repository downloaded from internet)
#         /docs (subdirectory with support documentation)
#         /source (subdirectory with all source code)
#         /release (subdirectory with executables and libraries generated by build proccess)
#         /build_system (subdirectory with build process [makefiles or IDE solution] generated by CMake)
#         Readme.md
#         Licence.txt
# /tmp/ntabuild (directory with temporary files generated by build proccess)
#
# Note that:
#   /repository/source is referenced by $NUPIC environment variable.
#   /repository/release is referenced by $NTA environment variable.
# This way, users have flexibility to change default locations.
#
# Repository root is the parent directory which this CMake file is located
# This CMake file must be always on /repository/source subdirectory.
get_filename_component(REPOSITORY_DIR ${PROJECT_SOURCE_DIR} PATH)
# 'release' is a subdirectory created on repository root,
# but if it already is specified on $NTA environment variable, simply re-use it!
if("$ENV{NTA}" STREQUAL "")
  set(CMAKE_INSTALL_PREFIX "$ENV{HOME}/nta/eng")
else()
  set(CMAKE_INSTALL_PREFIX "$ENV{NTA}")
endif()
# 'ntabuild' is a subdirectory created on system temporary directory.
set(TEMP_BUILD_DIR "/tmp/ntabuild")
# CMAKE_CURRENT_BINARY_DIR is used by swig module for put wrappers on, so don't erase this line!
set(CMAKE_CURRENT_BINARY_DIR ${TEMP_BUILD_DIR})

#
# Update repository submodules
#
execute_process(COMMAND git submodule update --init
                WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
                RESULT_VARIABLE EXIT_CODE)
if(NOT EXIT_CODE EQUAL 0)
  message(FATAL_ERROR "Updating submodules within ${PROJECT_SOURCE_DIR} failed.")
endif()

#
# Set OS flags
#
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  set(OSX ON)
  set(STATIC_LIB_EXTENSION "a")
  set(DYNAMIC_LIB_EXTENSION "dylib")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
  set(LINUX ON)
  set(STATIC_LIB_EXTENSION "a")
  set(DYNAMIC_LIB_EXTENSION "so")
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Windows")
  set(WINDOWS ON)
  set(STATIC_LIB_EXTENSION "lib")
  set(DYNAMIC_LIB_EXTENSION "dll")
endif()

#
# Determine NTA platform type
#
message(STATUS "Checking platform...")
if(${CMAKE_SIZEOF_VOID_P} MATCHES "8")
  set(NTA_PLATFORM_ARCH "64")
else()
  set(NTA_PLATFORM_ARCH "32")
endif()
if(OSX)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "10.7")
  set(NTA_PLATFORM_OS "darwin64")
  set(NTA_PLATFORM_CXXFLAGS "-fPIC -DPIC -m64")
  set(NTA_PLATFORM_ASFLAGS "")
  set(NTA_PLATFORM_DEBUGFLAGS "-gfull")
  set(NTA_PLATFORM_LINKFLAGS "-Wl,-u,_munmap")
  set(NTA_PLATFORM_LIBS "-stdlib=libstdc++ -std=c++11 -lc++abi -liconv -lsqlite3 -framework CoreServices -framework Accelerate")
  set(NTA_PLATFORM_MPI_EXTRA_LIBS "")
  set(NTA_PLATFORM_LINKFLAGS_PYMODULE "-bundle -undefined dynamic_lookup -fPIC")
  set(NTA_PLATFORM_LINKFLAGS_PYEMBED "")
elseif(LINUX)
  if(${NTA_PLATFORM_ARCH} MATCHES "64")
    set(NTA_PLATFORM_OS "linux64")
    set(NTA_PLATFORM_CXXFLAGS "-fPIC -DPIC -m64")
    set(NTA_PLATFORM_ASFLAGS "-msse2")
    set(NTA_PLATFORM_DEBUGFLAGS "-g")
    set(NTA_PLATFORM_LINKFLAGS "-Wl,--no-as-needed -static-libgcc")
    # pthread needed by libapr-1
    set(NTA_PLATFORM_LIBS "-stdlib=libstdc++ -lm -lpthread -ldl -lutil")
    set(NTA_PLATFORM_MPI_EXTRA_LIBS "-lrt")
    set(NTA_PLATFORM_LINKFLAGS_PYMODULE "-pthread -shared")
    set(NTA_PLATFORM_LINKFLAGS_PYEMBED "-Wl,--export-dynamic")
  else()    
    set(NTA_PLATFORM_OS "linux32")
    set(NTA_PLATFORM_CXXFLAGS "-fPIC -DPIC -ffloat-store")
    set(NTA_PLATFORM_ASFLAGS "")
    set(NTA_PLATFORM_DEBUGFLAGS "-g")
    set(NTA_PLATFORM_LINKFLAGS "-Wl,--no-as-needed -static-libgcc")
    set(NTA_PLATFORM_LIBS "-stdlib=libstdc++ -lm -lpthread -ldl -lutil -lrt")
    set(NTA_PLATFORM_MPI_EXTRA_LIBS "-lrt")
    set(NTA_PLATFORM_LINKFLAGS_PYMODULE "-pthread -shared")
    set(NTA_PLATFORM_LINKFLAGS_PYEMBED "-Wl,--export-dynamic")
  endif()
elseif(WINDOWS)
  set(NTA_PLATFORM_OS "win32")
  set(NTA_PLATFORM_CXXFLAGS "-DWIN32")
  set(NTA_PLATFORM_ASFLAGS "")
  set(NTA_PLATFORM_DEBUGFLAGS "")
  set(NTA_PLATFORM_LINKFLAGS "")
  set(NTA_PLATFORM_LIBS "")
  set(NTA_PLATFORM_MPI_EXTRA_LIBS "")
  set(NTA_PLATFORM_LINKFLAGS_PYMODULE "")
  set(NTA_PLATFORM_LINKFLAGS_PYEMBED "")
else()
  message(FATAL_ERROR "${CMAKE_CURRENT_LIST_FILE}:${CMAKE_CURRENT_LIST_LINE}: error: ${CMAKE_SYSTEM_NAME} not supported yet.")
endif()

message(STATUS "Platform: ${NTA_PLATFORM_OS}")
message(STATUS "Platform-specific flags:")
message(STATUS "  Libraries: ${NTA_PLATFORM_LIBS}")
message(STATUS "  Extra MPI libraries: ${NTA_PLATFORM_MPI_EXTRA_LIBS}")
message(STATUS "  CXX flags: ${NTA_PLATFORM_CXXFLAGS}")
message(STATUS "  AS flags: ${NTA_PLATFORM_ASFLAGS}")
message(STATUS "  Debug flags: ${NTA_PLATFORM_DEBUGFLAGS}")
message(STATUS "  LD flags: ${NTA_PLATFORM_LINKFLAGS}")
message(STATUS "  Python extension link flags: ${NTA_PLATFORM_LINKFLAGS_PYMODULE}")
message(STATUS "  Python embedding link flags: ${NTA_PLATFORM_LINKFLAGS_PYEMBED}")

#
# Checks if Python is installed and gets its variables.
# Minimum version of Python is 2.6 -- earlier versions *will* fail.
#
# Please don't use 'find_package' for finding Python (System version), it has presented several conflicting results.
# Instead we just use a shell command to execute a simple python command, if exit code is 0 ('success') then we have python installed.
#
message(STATUS "Checking software tools...")
execute_process(COMMAND python --version
                RESULT_VARIABLE EXIT_CODE)
if(NOT EXIT_CODE EQUAL 0)
  message(FATAL_ERROR "System Python not found. You do not have a system version of Python or it is not set on environment path.")
endif()

#
# Gives the version of Python necessary to get installation directories
# for use with ${PYTHON_VERSION}, etc.
#
execute_process(COMMAND python -c "import sys;sys.stdout.write(str(sys.version_info[0]) + '.' + str(sys.version_info[1]))"
                OUTPUT_VARIABLE PYTHON_VERSION)
if(NOT(${PYTHON_VERSION} EQUAL "2.6" OR ${PYTHON_VERSION} EQUAL "2.7"))
  message(FATAL_ERROR "Only these versions of Python are accepted: 2.6, 2.7")
endif()

#
# Find out where system installation of python is.
#
execute_process(COMMAND python -c "import sys;sys.stdout.write(sys.prefix)"
                OUTPUT_VARIABLE PYTHON_PREFIX)
string(REGEX REPLACE "\\\\" "/" PYTHON_PREFIX ${PYTHON_PREFIX})
set(PYTHON_INCLUDE_DIR "${PYTHON_PREFIX}/include/python${PYTHON_VERSION}")
set(PYTHON_LIBRARY_DIR "${PYTHON_PREFIX}/lib/python${PYTHON_VERSION}")
set(PYTHON_SITE_PACKAGES_DIR "${CMAKE_INSTALL_PREFIX}/lib/python${PYTHON_VERSION}/site-packages")

#
# Finds out version of Numpy and headers's path.
#
execute_process(COMMAND python -c "import sys;import numpy;sys.stdout.write(numpy.get_include())"
                OUTPUT_VARIABLE NUMPY_INCLUDE_DIR)
string(REGEX REPLACE "\\\\" "/" NUMPY_INCLUDE_DIR ${NUMPY_INCLUDE_DIR})
execute_process(COMMAND python -c "import sys;import numpy;sys.stdout.write(numpy.__version__)"
                OUTPUT_VARIABLE NUMPY_VERSION)

#
# Checks if Swig is installed and gets its variables.
# Minimum version of Swig is 1.3.36 -- earlier versions *will* fail
# Later versions greater than 2.0.3 also *will* fail (SWIGPY_SLICE_ARG bug)
#
set(SWIG_EXECUTABLE "${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/bin/swig")
set(SWIG_DIR "${PROJECT_SOURCE_DIR}/external/common/share/swig/1.3.36")
execute_process(COMMAND ${SWIG_EXECUTABLE} -version OUTPUT_VARIABLE SWIG_VERSION)
string(REGEX REPLACE ".*SWIG Version[^0-9.]*\([0-9.]+\).*" "\\1" SWIG_VERSION ${SWIG_VERSION})
include(${CMAKE_ROOT}/Modules/UseSWIG.cmake)

#
# Shows components details.
#
message(STATUS "Python details:")
message(STATUS "  Version: ${PYTHON_VERSION}")
message(STATUS "  Include dir: ${PYTHON_INCLUDE_DIR}")
message(STATUS "  Library dir: ${PYTHON_LIBRARY_DIR}")
message(STATUS "  Site packages dir: ${PYTHON_SITE_PACKAGES_DIR}")
message(STATUS "Numpy details:")
message(STATUS "  Version: ${NUMPY_VERSION}")
message(STATUS "  Include dir: ${NUMPY_INCLUDE_DIR}")
message(STATUS "Swig details:")
message(STATUS "  Version: ${SWIG_VERSION}")

#
# Config output paths.
# First config output paths for the generic no-config case.
# Second, for multi-config builds (DEBUG or RELEASE, for example).
#
set(CMAKE_SWIG_OUTDIR "${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${TEMP_BUILD_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_INSTALL_PREFIX}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_INSTALL_PREFIX}/lib)
foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
  string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG)
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${CMAKE_ARCHIVE_OUTPUT_DIRECTORY})
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})
  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
endforeach()

#
# Set environment variables of the operating system
#
message(STATUS "Checking environment...")
message(STATUS "Environment variables:")
set_environment_variable(PATH "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}" ON)
set_environment_variable(PYTHONPATH "${PYTHON_SITE_PACKAGES_DIR}" OFF)
set_environment_variable(NUPIC "${PROJECT_SOURCE_DIR}" OFF)
set_environment_variable(LD_LIBRARY_PATH "${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}" ON)
set_environment_variable(DYLD_LIBRARY_PATH "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}" ON)
# If $NTA (ie 'release' directory) already is set, don't change it!
if("$ENV{NTA}" STREQUAL "")
  set_environment_variable(NTA "${CMAKE_INSTALL_PREFIX}" OFF)
  set_environment_variable(NTA_ROOTDIR "${CMAKE_INSTALL_PREFIX}" OFF)
  set_environment_variable(NTA_DATA_PATH "${CMAKE_INSTALL_PREFIX}/share/prediction/data" OFF)
else()
  show_environment_variable(NTA "$ENV{NTA}")
  show_environment_variable(NTA_ROOTDIR "$ENV{NTA_ROOTDIR}")
  show_environment_variable(NTA_DATA_PATH "$ENV{NTA_DATA_PATH}")
endif()
if(OSX)
  set_environment_variable(MACOSX_DEPLOYMENT_TARGET "${CMAKE_OSX_DEPLOYMENT_TARGET}" OFF)
  message(STATUS "  (some variables will be updated only after login.)")
endif()
show_environment_variable(NTAX_DEVELOPER_BUILD "$ENV{NTAX_DEVELOPER_BUILD}")

#
# Project details
#
message(STATUS "Checking project...")
message(STATUS "Project: ${PROJECT_NAME}")
message(STATUS "Locations:")
message(STATUS "  Source: ${PROJECT_SOURCE_DIR}")
message(STATUS "  Build System: ${PROJECT_BINARY_DIR}")
message(STATUS "  Release: ${CMAKE_INSTALL_PREFIX}")


############################################################################################################################
###                                                                                                                      ###
###  2nd Part:                                                                                                           ###
###  Configuration of compiler flags                                                                                     ###
###                                                                                                                      ###
############################################################################################################################

#
# Include directories of headers
# Allows us to find includes for external libraries and enables
# #include <nta/common/...>
#
set(NTA_INCLUDEFLAGS "-I${PROJECT_SOURCE_DIR} -I${PROJECT_SOURCE_DIR}/external/common/include -I${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/include")

#
# NTA_INTERNAL tells us that the code is being built under the build system
# and not as a separate program. Used for cppvision example.
#
set(NTA_CXXFLAGS_BASE "${NTA_INCLUDEFLAGS} ${NTA_PLATFORM_CXXFLAGS} -DHAVE_CONFIG_H -DNTA_INTERNAL -DNTA_PLATFORM_${NTA_PLATFORM_OS} -DBOOST_NO_WREGEX -DNUPIC2 -fvisibility=hidden -Wall -Wreturn-type -Wunused-variable -Wno-deprecated")

#
# All executables and plugins are linked with these flags
#
set(NTA_LINKFLAGS "${NTA_PLATFORM_LINKFLAGS} ${NTA_PLATFORM_LIBS} -L${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib")


message(STATUS "Options:")

#
# Optimization can be set at configure time
#
option(NTA_OPTIMIZATION_ENABLED "--optimization=[ON/OFF] turn on optimization [default=ON]" ON)
if(NTA_OPTIMIZATION_ENABLED)
  # -ftree-vectorize conflicts with -no-tree-aliasing on leopard, so removed
  # flag NTA_ASM enables/disables our hand tuned assbembly code (SSE), but it's available only for some platform
  set(NTA_CXXFLAGS_OPTIMIZATION "-O3 -pipe -DNTA_ASM")
  set(NTA_CXXFLAGS_OPTIMIZATION_PYMODULE "-O1")
else()
  set(NTA_CXXFLAGS_OPTIMIZATION "-O0 -fno-inline")
  set(NTA_CXXFLAGS_OPTIMIZATION_PYMODULE "-O0 -fno-inline")
endif()
message(STATUS "  Optimization: ${NTA_OPTIMIZATION_ENABLED}")

#
# Enable/disable debugging symbols (-g). Enabled by default (stripped for release).
# This is orthogonal to optimization
#
option(NTA_DEBUGSYMBOLS_ENABLED "--debugsymbols=[ON/OFF] turn on debug symbols [default=ON]" ON)
if(NTA_DEBUGSYMBOLS_ENABLED)
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} ${NTA_PLATFORM_DEBUGFLAGS}")
endif()
message(STATUS "  Debug Symbols: ${NTA_DEBUGSYMBOLS_ENABLED}")

#
# Enable/disable NTA_ASSERT.
#
option(NTA_ASSERTIONS_ENABLED "--assertions=[ON/OFF] turn on assertions [default=ON]" ON)
if(NTA_ASSERTIONS_ENABLED)
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -DNTA_ASSERTIONS_ON")
else()
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -DNDEBUG")
endif()
message(STATUS "  Assertions: ${NTA_ASSERTIONS_ENABLED}")

#
# Enable/disable gprof profiling (this option is not frequently used/tested).
#
option(NTA_PROFILING_ENABLED "--profiling=[ON/OFF] turn on profiling [default=OFF]" OFF)
if(NTA_PROFILING_ENABLED)
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -pg")
  set(NTA_LINKFLAGS "${NTA_LINKFLAGS} -pg")
endif()
message(STATUS "  Profiling: ${NTA_PROFILING_ENABLED}")

#
# Build using Python headers and library,
# and enable features that depend on Python.
#
option(NTA_PYTHON_SUPPORT "--python-support=[ON/OFF] turn on python support [default=ON]" ON)
message(STATUS "  Python Support: ${NTA_PYTHON_SUPPORT}")

#
# Build using MPI headers and library,
# and enable features that depend on MPI.
#
option(NTA_MPI_SUPPORT "--mpi=[ON/OFF] turn on MPI support [default=ON]" ON)
message(STATUS "  MPI Support: ${NTA_MPI_SUPPORT}")

#
# Set GNU c/c++ flags in case of CLang is off.
#
if(CMAKE_COMPILER_IS_GNUCXX)
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -Wno-sign-compare")
  set(NTA_CXXFLAGS_OPTIMIZATION "${NTA_CXXFLAGS_OPTIMIZATION} -falign-loops=16")
endif()

#
# Python compile flags
# Flags necessary for Python support.
# NTA_CXXFLAGS_PYMODULE is the same as NTA_CXXFLAGS but without
# warnings=errors and without optimization.
# We compile without optimization because it greatly speeds up
# the build, and performance isn't too important for wrapper
# functions.
# NTA_LINKFLAGS_PYEMBED is for linking an executable with embedded interpreter
# NTA_LINKFLAGS_PYMODULE is for linking a python module
#
if(NTA_PYTHON_SUPPORT)

  set(NTA_SWIG_FLAGS "${NTA_SWIG_FLAGS} -features autodoc=0,directors=0 -noproxyimport -keyword -modern -modernargs -noproxydel -fvirtual -fastunpack -nofastproxy -fastquery -outputtuple -castmode -w402 -w503 -w511 -w302 -w362 -w312 -w389 -DNTA_PLATFORM_${NTA_PLATFORM_OS} -DNTA_PYTHON_SUPPORT=${PYTHON_VERSION} -I${PROJECT_SOURCE_DIR} -I${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/include -I${NUMPY_INCLUDE_DIR} -I${SWIG_DIR}/python -I${SWIG_DIR}")
  string(REPLACE " " ";" NTA_SWIG_FLAGS ${NTA_SWIG_FLAGS})

  # Minimal functional subset
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -DNTA_PYTHON_SUPPORT=${PYTHON_VERSION} -I${NUMPY_INCLUDE_DIR} -I${PYTHON_INCLUDE_DIR}")

  # -falign-functions is necessary to avoid a compiler problem on
  # darwin. If you build without -falign-functions, exceptions
  # thrown in a pynode result in an abort() instead of propagation
  # up the call stack.
  set(NTA_CXXFLAGS_PYMODULE "${NTA_CXXFLAGS_BASE} ${NTA_CXXFLAGS_OPTIMIZATION_PYMODULE} -falign-functions")

  set(NTA_LINKFLAGS_PY "-L${PYTHON_LIBRARY_DIR}/config -ldl -lpython${PYTHON_VERSION}")

  set(NTA_LINKFLAGS_PYEMBED "${NTA_PLATFORM_LINKFLAGS_PYEMBED} ${NTA_LINKFLAGS_PY}")

  set(NTA_LINKFLAGS_PYMODULE "${NTA_PLATFORM_LINKFLAGS_PYMODULE} ${NTA_LINKFLAGS_PY} ${NTA_PLATFORM_LIBS} -L${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib")

endif()

#
# NTA_CXXFLAGS are used everywhere.
#
set(NTA_CXXFLAGS "${NTA_CXXFLAGS_BASE} ${NTA_CXXFLAGS_OPTIMIZATION}")


############################################################################################################################
###                                                                                                                      ###
###  3rd Part:                                                                                                           ###
###  Generation of the project and its modules                                                                           ###
###                                                                                                                      ###
############################################################################################################################

#
# Set current source dir to source root
#
set(CURRENT_SOURCE_DIR ${PROJECT_SOURCE_DIR})

#
# Apache's external libraries.
#
set(LIB_STATIC_APR1 apr-1)
add_library(${LIB_STATIC_APR1} STATIC IMPORTED)
set_property(TARGET ${LIB_STATIC_APR1} PROPERTY IMPORTED_LOCATION "${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib/libapr-1.${STATIC_LIB_EXTENSION}")

set(LIB_STATIC_APRUTIL1 aprutil-1)
add_library(${LIB_STATIC_APRUTIL1} STATIC IMPORTED)
set_property(TARGET ${LIB_STATIC_APRUTIL1} PROPERTY IMPORTED_LOCATION "${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib/libaprutil-1.${STATIC_LIB_EXTENSION}")

set(LIB_STATIC_Z z)
add_library(${LIB_STATIC_Z} STATIC IMPORTED)
set_property(TARGET ${LIB_STATIC_Z} PROPERTY IMPORTED_LOCATION "${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib/libz.${STATIC_LIB_EXTENSION}")

set(LIB_STATIC_YAML yaml)
add_library(${LIB_STATIC_YAML} STATIC IMPORTED)
set_property(TARGET ${LIB_STATIC_YAML} PROPERTY IMPORTED_LOCATION "${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib/libyaml.${STATIC_LIB_EXTENSION}")

if(WINDOWS)
  set(LIB_STATIC_PCRE pcre)
  add_library(${LIB_STATIC_PCRE} STATIC IMPORTED)
  set_property(TARGET ${LIB_STATIC_PCRE} PROPERTY IMPORTED_LOCATION "${PROJECT_SOURCE_DIR}/external/${NTA_PLATFORM_OS}/lib/libpcre.${STATIC_LIB_EXTENSION}")
endif()

#
# Set list of external libraries to this project.
#
set(NTA_STANDARD_LIBS 
  ${LIB_STATIC_YAML}
  ${LIB_STATIC_APRUTIL1}
  ${LIB_STATIC_APR1}
  ${LIB_STATIC_Z}
)

#
# LibSupport
#
# lang/py/support must be built before nta, but lang must be built after nta.
# This is due to the fact that both nta/pynode and lang/py/net_internal depend 
# on lang/py/support and lang/py/engine_internal depends on nta.
#
set(LIB_STATIC_SUPPORT support)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/lang/py/support")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/NumpyVector.cpp
  ${CURRENT_SOURCE_DIR}/PyArray.cpp
  ${CURRENT_SOURCE_DIR}/PyHelpers.cpp
  ${CURRENT_SOURCE_DIR}/PythonStream.cpp
  ${CURRENT_SOURCE_DIR}/NumpyVector.hpp
  ${CURRENT_SOURCE_DIR}/PyArray.hpp
  ${CURRENT_SOURCE_DIR}/PyHelpers.hpp
  ${CURRENT_SOURCE_DIR}/PythonStream.hpp
  ${CURRENT_SOURCE_DIR}/WrappedVector.hpp
)
generate_static_library(${LIB_STATIC_SUPPORT} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibAlgorithms
#
set(LIB_STATIC_ALGORITHMS algorithms)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/algorithms")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/bit_history.cpp
  ${CURRENT_SOURCE_DIR}/Cell.cpp
  ${CURRENT_SOURCE_DIR}/Cells4.cpp
  ${CURRENT_SOURCE_DIR}/classifier_result.cpp
  ${CURRENT_SOURCE_DIR}/CondProbTable.cpp
  ${CURRENT_SOURCE_DIR}/fast_cla_classifier.cpp
  ${CURRENT_SOURCE_DIR}/flat_spatial_pooler.cpp
  ${CURRENT_SOURCE_DIR}/gaborNode.cpp
  ${CURRENT_SOURCE_DIR}/imageSensorLite.cpp
  ${CURRENT_SOURCE_DIR}/InSynapse.cpp
  ${CURRENT_SOURCE_DIR}/linear.cpp
  ${CURRENT_SOURCE_DIR}/OutSynapse.cpp
  ${CURRENT_SOURCE_DIR}/Segment.cpp
  ${CURRENT_SOURCE_DIR}/SegmentUpdate.cpp
  ${CURRENT_SOURCE_DIR}/spatial_pooler.cpp
  ${CURRENT_SOURCE_DIR}/svm.cpp
  ${CURRENT_SOURCE_DIR}/arrayBuffer.hpp
  ${CURRENT_SOURCE_DIR}/bit_history.hpp
  ${CURRENT_SOURCE_DIR}/Cell.hpp
  ${CURRENT_SOURCE_DIR}/Cells4.hpp
  ${CURRENT_SOURCE_DIR}/classifier_result.hpp
  ${CURRENT_SOURCE_DIR}/CondProbTable.hpp
  ${CURRENT_SOURCE_DIR}/fast_cla_classifier.hpp
  ${CURRENT_SOURCE_DIR}/FDRCSpatial.hpp
  ${CURRENT_SOURCE_DIR}/FDRSpatial.hpp
  ${CURRENT_SOURCE_DIR}/flat_spatial_pooler.hpp
  ${CURRENT_SOURCE_DIR}/gaborNode.hpp
  ${CURRENT_SOURCE_DIR}/imageSensorLite.hpp
  ${CURRENT_SOURCE_DIR}/InSynapse.hpp
  ${CURRENT_SOURCE_DIR}/linear.hpp
  ${CURRENT_SOURCE_DIR}/OutSynapse.hpp
  ${CURRENT_SOURCE_DIR}/scanning.hpp
  ${CURRENT_SOURCE_DIR}/Segment.hpp
  ${CURRENT_SOURCE_DIR}/SegmentUpdate.hpp
  ${CURRENT_SOURCE_DIR}/spatial_pooler.hpp
  ${CURRENT_SOURCE_DIR}/svm.hpp
  ${CURRENT_SOURCE_DIR}/svm_t.hpp
)
generate_static_library(${LIB_STATIC_ALGORITHMS} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibMath
#
set(LIB_STATIC_MATH math)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/math")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/SparseMatrixAlgorithms.cpp
  ${CURRENT_SOURCE_DIR}/stl_io.cpp
  ${CURRENT_SOURCE_DIR}/array2D.hpp
  ${CURRENT_SOURCE_DIR}/array_algo.hpp
  ${CURRENT_SOURCE_DIR}/convolution.hpp
  ${CURRENT_SOURCE_DIR}/DenseMatrix.hpp
  ${CURRENT_SOURCE_DIR}/Domain.hpp
  ${CURRENT_SOURCE_DIR}/erosion.hpp
  ${CURRENT_SOURCE_DIR}/functions.hpp
  ${CURRENT_SOURCE_DIR}/GraphAlgorithms.hpp
  ${CURRENT_SOURCE_DIR}/Index.hpp
  ${CURRENT_SOURCE_DIR}/math.hpp
  ${CURRENT_SOURCE_DIR}/NearestNeighbor.hpp
  ${CURRENT_SOURCE_DIR}/rotation.hpp
  ${CURRENT_SOURCE_DIR}/Set.hpp
  ${CURRENT_SOURCE_DIR}/SparseBinaryMatrix.hpp
  ${CURRENT_SOURCE_DIR}/SparseMatrix.hpp
  ${CURRENT_SOURCE_DIR}/SparseMatrix01.hpp
  ${CURRENT_SOURCE_DIR}/SparseMatrixAlgorithms.hpp
  ${CURRENT_SOURCE_DIR}/SparseRLEMatrix.hpp
  ${CURRENT_SOURCE_DIR}/SparseTensor.hpp
  ${CURRENT_SOURCE_DIR}/stl_io.hpp
  ${CURRENT_SOURCE_DIR}/types.hpp
  ${CURRENT_SOURCE_DIR}/utils.hpp
)
generate_static_library(${LIB_STATIC_MATH} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibTypes
#
set(LIB_STATIC_TYPES types)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/types")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/BasicType.cpp
  ${CURRENT_SOURCE_DIR}/Fraction.cpp
  ${CURRENT_SOURCE_DIR}/BasicType.hpp
  ${CURRENT_SOURCE_DIR}/Exception.hpp
  ${CURRENT_SOURCE_DIR}/Fraction.hpp
  ${CURRENT_SOURCE_DIR}/types.hpp
  ${CURRENT_SOURCE_DIR}/types.h
)
generate_static_library(${LIB_STATIC_TYPES} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibTest
#
set(LIB_STATIC_TEST test)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/test")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/Tester.cpp
  ${CURRENT_SOURCE_DIR}/Tester.hpp
)
generate_static_library(${LIB_STATIC_TEST} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibUtils
#
set(LIB_STATIC_UTILS utils)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/utils")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/LoggingException.cpp
  ${CURRENT_SOURCE_DIR}/LogItem.cpp
  ${CURRENT_SOURCE_DIR}/Random.cpp
  ${CURRENT_SOURCE_DIR}/StringUtils.cpp
  ${CURRENT_SOURCE_DIR}/TRandom.cpp
  ${CURRENT_SOURCE_DIR}/Watcher.cpp
  ${CURRENT_SOURCE_DIR}/Log.hpp
  ${CURRENT_SOURCE_DIR}/LoggingException.hpp
  ${CURRENT_SOURCE_DIR}/LogItem.hpp
  ${CURRENT_SOURCE_DIR}/Random.hpp
  ${CURRENT_SOURCE_DIR}/StringUtils.hpp
  ${CURRENT_SOURCE_DIR}/TRandom.hpp
  ${CURRENT_SOURCE_DIR}/utils.hpp
  ${CURRENT_SOURCE_DIR}/Watcher.hpp
)
generate_static_library(${LIB_STATIC_UTILS} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibNTypes
#
set(LIB_STATIC_NTYPES ntypes)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/ntypes")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/ArrayBase.cpp
  ${CURRENT_SOURCE_DIR}/Buffer.cpp
  ${CURRENT_SOURCE_DIR}/BundleIO.cpp
  ${CURRENT_SOURCE_DIR}/Collection.cpp
  ${CURRENT_SOURCE_DIR}/Dimensions.cpp
  ${CURRENT_SOURCE_DIR}/MemParser.cpp
  ${CURRENT_SOURCE_DIR}/Scalar.cpp
  ${CURRENT_SOURCE_DIR}/Value.cpp
  ${CURRENT_SOURCE_DIR}/Array.hpp
  ${CURRENT_SOURCE_DIR}/ArrayBase.hpp
  ${CURRENT_SOURCE_DIR}/ArrayRef.hpp
  ${CURRENT_SOURCE_DIR}/Buffer.hpp
  ${CURRENT_SOURCE_DIR}/BundleIO.hpp
  ${CURRENT_SOURCE_DIR}/Collection.hpp
  ${CURRENT_SOURCE_DIR}/Dimensions.hpp
  ${CURRENT_SOURCE_DIR}/MemParser.hpp
  ${CURRENT_SOURCE_DIR}/MemStream.hpp
  ${CURRENT_SOURCE_DIR}/NodeSet.hpp
  ${CURRENT_SOURCE_DIR}/object_model.hpp
  ${CURRENT_SOURCE_DIR}/Scalar.hpp
  ${CURRENT_SOURCE_DIR}/Value.hpp
  ${CURRENT_SOURCE_DIR}/object_model.h
)
generate_static_library(${LIB_STATIC_NTYPES} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibEngine
#
set(LIB_STATIC_ENGINE engine)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/engine")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/Collections.cpp
  ${CURRENT_SOURCE_DIR}/Input.cpp
  ${CURRENT_SOURCE_DIR}/Link.cpp
  ${CURRENT_SOURCE_DIR}/LinkPolicyFactory.cpp
  ${CURRENT_SOURCE_DIR}/Network.cpp
  ${CURRENT_SOURCE_DIR}/NuPIC.cpp
  ${CURRENT_SOURCE_DIR}/Output.cpp
  ${CURRENT_SOURCE_DIR}/Region.cpp
  ${CURRENT_SOURCE_DIR}/Region_io.cpp
  ${CURRENT_SOURCE_DIR}/Region_parameters.cpp
  ${CURRENT_SOURCE_DIR}/RegionImpl.cpp
  ${CURRENT_SOURCE_DIR}/RegionImplFactory.cpp
  ${CURRENT_SOURCE_DIR}/Spec.cpp
  ${CURRENT_SOURCE_DIR}/TestFanIn2LinkPolicy.cpp
  ${CURRENT_SOURCE_DIR}/TestNode.cpp
  ${CURRENT_SOURCE_DIR}/UniformLinkPolicy.cpp
  ${CURRENT_SOURCE_DIR}/YAMLUtils.cpp
  ${CURRENT_SOURCE_DIR}/Input.hpp
  ${CURRENT_SOURCE_DIR}/Link.hpp
  ${CURRENT_SOURCE_DIR}/LinkPolicy.hpp
  ${CURRENT_SOURCE_DIR}/LinkPolicyFactory.hpp
  ${CURRENT_SOURCE_DIR}/Network.hpp
  ${CURRENT_SOURCE_DIR}/NuPIC.hpp
  ${CURRENT_SOURCE_DIR}/Output.hpp
  ${CURRENT_SOURCE_DIR}/Region.hpp
  ${CURRENT_SOURCE_DIR}/RegionImpl.hpp
  ${CURRENT_SOURCE_DIR}/RegionImplFactory.hpp
  ${CURRENT_SOURCE_DIR}/Spec.hpp
  ${CURRENT_SOURCE_DIR}/TestFanIn2LinkPolicy.hpp
  ${CURRENT_SOURCE_DIR}/TestNode.hpp
  ${CURRENT_SOURCE_DIR}/UniformLinkPolicy.hpp
  ${CURRENT_SOURCE_DIR}/YAMLUtils.hpp
)
generate_static_library(${LIB_STATIC_ENGINE} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibOS
#
set(LIB_STATIC_OS os)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/os")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/Directory.cpp
  ${CURRENT_SOURCE_DIR}/DynamicLibrary.cpp
  ${CURRENT_SOURCE_DIR}/Env.cpp
  ${CURRENT_SOURCE_DIR}/FStream.cpp
  ${CURRENT_SOURCE_DIR}/OS.cpp
  ${CURRENT_SOURCE_DIR}/OSUnix.cpp
  ${CURRENT_SOURCE_DIR}/OSWin.cpp
  ${CURRENT_SOURCE_DIR}/Path.cpp
  ${CURRENT_SOURCE_DIR}/regex.cpp
  ${CURRENT_SOURCE_DIR}/Timer.cpp
  ${CURRENT_SOURCE_DIR}/Directory.hpp
  ${CURRENT_SOURCE_DIR}/DynamicLibrary.hpp
  ${CURRENT_SOURCE_DIR}/Env.hpp
  ${CURRENT_SOURCE_DIR}/FStream.hpp
  ${CURRENT_SOURCE_DIR}/OS.hpp
  ${CURRENT_SOURCE_DIR}/Path.hpp
  ${CURRENT_SOURCE_DIR}/regex.hpp
  ${CURRENT_SOURCE_DIR}/Timer.hpp
)
generate_static_library(${LIB_STATIC_OS} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# LibRegions
#
set(LIB_STATIC_REGIONS regions)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/regions")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/VectorFile.cpp
  ${CURRENT_SOURCE_DIR}/VectorFileEffector.cpp
  ${CURRENT_SOURCE_DIR}/VectorFileSensor.cpp
  ${CURRENT_SOURCE_DIR}/VectorFile.hpp
  ${CURRENT_SOURCE_DIR}/VectorFileEffector.hpp
  ${CURRENT_SOURCE_DIR}/VectorFileSensor.hpp
)
generate_static_library(${LIB_STATIC_REGIONS} "${NTA_CXXFLAGS}" "${SOURCE}")

#
# HtmTest
#
set(EXECUTABLE_HTMTEST htmtest)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/nta/apps/htmtest")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/htmtest.cpp
)
set(LIBRARIES
  ${LIB_STATIC_ENGINE}
  ${LIB_STATIC_REGIONS}
  ${LIB_STATIC_ALGORITHMS}
  ${LIB_STATIC_SUPPORT}
  ${LIB_STATIC_OS}
  ${LIB_STATIC_MATH}
  ${LIB_STATIC_NTYPES}
  ${LIB_STATIC_UTILS}
  ${LIB_STATIC_TYPES}
  ${NTA_STANDARD_LIBS}
)
generate_executable(${EXECUTABLE_HTMTEST} "${NTA_CXXFLAGS}" "${SOURCE}" "${NTA_LINKFLAGS}" "${LIBRARIES}")

#
# TestEverything
#
set(EXECUTABLE_TESTEVERYTHING testeverything)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/qa/testeverything")
set(FILES_RETURNED)
get_files_list(${PROJECT_SOURCE_DIR}/nta "unittests" "Test.cpp")
set(SOURCE ${FILES_RETURNED} ${CURRENT_SOURCE_DIR}/TestEverythingMain.cpp)
set(LIBRARIES
  ${LIB_STATIC_ENGINE}
  ${LIB_STATIC_REGIONS}
  ${LIB_STATIC_ALGORITHMS}
  ${LIB_STATIC_MATH}
  ${LIB_STATIC_NTYPES}
  ${LIB_STATIC_SUPPORT}
  ${LIB_STATIC_OS}
  ${LIB_STATIC_TEST}
  ${LIB_STATIC_UTILS}
  ${LIB_STATIC_TYPES}
  ${NTA_STANDARD_LIBS}
)
generate_executable(${EXECUTABLE_TESTEVERYTHING} "${NTA_CXXFLAGS}" "${SOURCE}" "${NTA_LINKFLAGS} ${NTA_LINKFLAGS_PYEMBED}" "${LIBRARIES}")

#
# LibCppRegion
#
# A regular shared library that is installed in <$NTA/lib> and
# loaded dynamically.
#
set(LIB_DYNAMIC_CPPREGION cpp_region)
set(CURRENT_SOURCE_DIR "${PROJECT_SOURCE_DIR}/py/cpp_region")
set(SOURCE
  ${CURRENT_SOURCE_DIR}/PyRegion.cpp
  ${CURRENT_SOURCE_DIR}/PyRegion.hpp
)
set(LIBRARIES
  ${LIB_STATIC_ENGINE}
  ${LIB_STATIC_REGIONS}
  ${LIB_STATIC_ALGORITHMS}
  ${LIB_STATIC_MATH}
  ${LIB_STATIC_NTYPES}
  ${LIB_STATIC_SUPPORT}
  ${LIB_STATIC_OS}
  ${LIB_STATIC_UTILS}
  ${LIB_STATIC_TYPES}
  ${NTA_STANDARD_LIBS}
)
generate_dynamic_library(${LIB_DYNAMIC_CPPREGION} "${NTA_CXXFLAGS}" "${SOURCE}" "${NTA_LINKFLAGS} ${NTA_LINKFLAGS_PYEMBED}" "${LIBRARIES}")

if(NTA_PYTHON_SUPPORT)
  # This script is generated by swig.
  # Its name is not specified explicitly to swig, but is implicit in
  # the name of the module that is being generated.
  # This module can be specified on swig's command line
  # (-module tools), or in the interface file (tools.i).
  # Here, we choose to specify it in the interface file, as it allows us
  # to add additional info that can't be specified on the command line:
  # the package that the module goes into (nupic),
  # and the module docstring.
  #
  # CMAKE_CXX_FLAGS are our C++ flags to use when compiling the sources that
  # generate the binding library.
  #
  # CMAKE_MODULE_LINKER_FLAGS are the set of linker flags to use when linking the _modulename.so
  # These are specific to Python, and architecture-specific as well.
  #
  # Bellow are the dynamic python modules that will be generated.
  # Python modules are always named _modulename.so. Unfortunately,
  # there is nothing Python-obvious about this name, so it may
  # conflict with libraries we generate for other target languages
  # in the future.
  # (The list of sources also includes the swig interface files, even 
  # though they're not used to compile, just to get the dependencies right.)
  # They will linked in the "real" C++ library that the bindings are wrapping.

  #
  # LibEngineInternal
  #
  set(LIB_SHARED_ENGINEINTERNAL engine_internal)
  set(LIBRARIES
    ${LIB_STATIC_ENGINE}
    ${LIB_STATIC_REGIONS}
    ${LIB_STATIC_ALGORITHMS}
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_OS}
    ${LIB_STATIC_MATH}
    ${LIB_STATIC_NTYPES}
    ${LIB_STATIC_UTILS}
    ${LIB_STATIC_TYPES}
    ${NTA_STANDARD_LIBS}
  )
  generate_swig_module(${LIB_SHARED_ENGINEINTERNAL} "/lang/py/bindings/engine_internal" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")

  #
  # LibBindingsMath
  #
  set(LIB_SHARED_MATH math)
  set(EXTRA_SOURCE
    ${PROJECT_SOURCE_DIR}/py/bindings/math/PySparseTensor.cpp
  )
  set(LIBRARIES
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_OS}
    ${LIB_STATIC_MATH}
    ${LIB_STATIC_NTYPES}
    ${LIB_STATIC_UTILS}
    ${LIB_STATIC_TYPES}
    ${NTA_STANDARD_LIBS}
  )
  generate_swig_module(${LIB_SHARED_MATH} "/py/bindings/math" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "${EXTRA_SOURCE}" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")

  #
  # LibBindingsAlgorithms
  #
  set(LIB_SHARED_ALGORITHMS algorithms)
  set(LIBRARIES
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_ALGORITHMS}
    ${LIB_STATIC_OS}
    ${LIB_STATIC_MATH}
    ${LIB_STATIC_NTYPES}
    ${LIB_STATIC_UTILS}
    ${LIB_STATIC_TYPES}
    ${NTA_STANDARD_LIBS}
  )
  generate_swig_module(${LIB_SHARED_ALGORITHMS} "/py/bindings/algorithms" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")

  #
  # LibBindingsIORange
  #
  set(LIB_SHARED_IORANGE iorange)
  set(LIBRARIES
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_OS}
    ${LIB_STATIC_NTYPES}
    ${LIB_STATIC_UTILS}
    ${LIB_STATIC_TYPES}
    ${NTA_STANDARD_LIBS}
  )
  generate_swig_module(${LIB_SHARED_IORANGE} "/py/bindings/iorange" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")
endif()


############################################################################################################################
###                                                                                                                      ###
###  4th Part:                                                                                                           ###
###  Post configuration operations                                                                                       ###
###                                                                                                                      ###
############################################################################################################################

#
# Create file with unit tests used by TestEverything
#
set(FILES_RETURNED)
get_files_list(${PROJECT_SOURCE_DIR}/nta "unittests" "Test.hpp")
set(files ${FILES_RETURNED})
set(tests_file_content "")
set(headers_file_content "")
foreach(file ${files})
  get_filename_component(test ${file} NAME_WE)
  if(NOT ${file} MATCHES "TesterTest")
    set(tests_file_content "${tests_file_content}ADD_TEST(${test});\n")
    set(headers_file_content "${headers_file_content}#include \"${file}\"\n")
  endif()
endforeach()
file(WRITE "${PROJECT_SOURCE_DIR}/qa/testeverything/everything_addtests.hpp" "${tests_file_content}")
file(WRITE "${PROJECT_SOURCE_DIR}/qa/testeverything/everything_headers.hpp" "${headers_file_content}")

# Copy platform independent executable scripts
copy_file(${PROJECT_SOURCE_DIR}/lang/py/bindings/__init__.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/__init__.py)

# Copy the pieces of nupic that we want
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/algorithms ${PYTHON_SITE_PACKAGES_DIR}/nupic/algorithms)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/frameworks ${PYTHON_SITE_PACKAGES_DIR}/nupic/frameworks)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/image ${PYTHON_SITE_PACKAGES_DIR}/nupic/image)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/research ${PYTHON_SITE_PACKAGES_DIR}/nupic/research)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/data ${PYTHON_SITE_PACKAGES_DIR}/nupic/data)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/database ${PYTHON_SITE_PACKAGES_DIR}/nupic/database)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/swarming ${PYTHON_SITE_PACKAGES_DIR}/nupic/swarming)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/encoders ${PYTHON_SITE_PACKAGES_DIR}/nupic/encoders)
copy_directory(${PROJECT_SOURCE_DIR}/py/nupic/support ${PYTHON_SITE_PACKAGES_DIR}/nupic/support)
copy_directory(${PROJECT_SOURCE_DIR}/py/regions         ${PYTHON_SITE_PACKAGES_DIR}/nupic/regions)

# Copy math libraries. Much of the stuff in nupic.math is old cruft. Get just what we want
copy_file(${PROJECT_SOURCE_DIR}/py/nupic/math/__init__.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/math/__init__.py)
copy_file(${PROJECT_SOURCE_DIR}/py/nupic/math/cross.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/math/cross.py)
copy_file(${PROJECT_SOURCE_DIR}/py/nupic/math/roc_utils.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/math/roc_utils.py)

# Copy examples
copy_directory(${PROJECT_SOURCE_DIR}/examples/prediction ${CMAKE_INSTALL_PREFIX}/share/prediction)
copy_directory(${PROJECT_SOURCE_DIR}/examples/opf ${CMAKE_INSTALL_PREFIX}/share/opf)

# Copy testing codes
copy_directory(${PROJECT_SOURCE_DIR}/qa/shared_data ${CMAKE_INSTALL_PREFIX}/share/test/data)
copy_directory(${PROJECT_SOURCE_DIR}/tests ${CMAKE_INSTALL_PREFIX}/tests)
copy_file(${PROJECT_SOURCE_DIR}/run_tests.sh ${CMAKE_INSTALL_PREFIX}/bin/run_tests.sh)
copy_file(${PROJECT_SOURCE_DIR}/bin/run_tests.py ${CMAKE_INSTALL_PREFIX}/bin/run_tests.py)
copy_file(${PROJECT_SOURCE_DIR}/bin/run_swarm.py ${CMAKE_INSTALL_PREFIX}/bin/run_swarm.py)

# Copy miscellaneous files
copy_directory(${PROJECT_SOURCE_DIR}/external/licenses ${CMAKE_INSTALL_PREFIX}/share/doc/licenses)
copy_file(${PROJECT_SOURCE_DIR}/conf/default/nupic-default.xml ${CMAKE_INSTALL_PREFIX}/conf/default/nupic-default.xml)
copy_file(${PROJECT_SOURCE_DIR}/conf/default/nupic-logging.conf ${CMAKE_INSTALL_PREFIX}/conf/default/nupic-logging.conf)
copy_file(${PROJECT_SOURCE_DIR}/env.sh ${CMAKE_INSTALL_PREFIX}/env.sh)

# Copy python API and regions
copy_file(${PROJECT_SOURCE_DIR}/lang/py/__init__.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/__init__.py)
# This file is going to be replaced by a "documentored" version
copy_file(${PROJECT_SOURCE_DIR}/lang/py/engine/__init__.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/engine/__init__.py)

# Just to separate from result message
message(STATUS "")
