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

# This function reads variables from a file in the following format:
# FOO = 'bar'
function (read_variable_from_file file_content variable value)
  set(${value} PARENT_SCOPE)

  # Get the value between quotes
  string(REGEX REPLACE ".*${variable} = '([^']+)'.*" "\\1" tag_value "${file_content}")

  # If multiple lines are found, it's because regex return the entire text
  if(NOT "${tag_value}" MATCHES "\n")
    set(${value} "${tag_value}" PARENT_SCOPE)
  endif()
endfunction()

# This macro shows variables from the config file
macro (show_config_variable variable value)
  message(STATUS "  ${variable} = ${value}")
endmacro()

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

    set(NEED_LOGOFF ON)
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

# This macro get all subdirectories from a directory.
macro (get_directories_list current_dir dir_mask)
  file(GLOB children RELATIVE ${current_dir} ${current_dir}/*)
  foreach(child ${children})
    if(IS_DIRECTORY ${current_dir}/${child})
      get_directories_list(${current_dir}/${child} ${dir_mask})
      set(can_return_item ON)
      if(NOT "${dir_mask}" STREQUAL " ")
        if(NOT ${current_dir} MATCHES ${dir_mask})
          set(can_return_item OFF)
        endif()
      endif()
      if(can_return_item)
        set(ITEMS_RETURNED ${ITEMS_RETURNED} ${current_dir}/${child})
      endif()
    endif()
  endforeach()
endmacro()

# This macro get all files from a directory and its subdirectories.
macro (get_files_list current_dir dir_mask file_mask)
  file(GLOB children RELATIVE ${current_dir} ${current_dir}/*)
  foreach(child ${children})
    if(IS_DIRECTORY ${current_dir}/${child})
      get_files_list(${current_dir}/${child} ${dir_mask} ${file_mask})
    else()
      set(can_return_item ON)
      if(NOT "${dir_mask}" STREQUAL " ")
        if(NOT ${current_dir} MATCHES ${dir_mask})
          set(can_return_item OFF)
        endif()
      endif()
      if(NOT "${file_mask}" STREQUAL " ")
        if(NOT ${child} MATCHES ${file_mask})
          set(can_return_item OFF)
        endif()
      endif()
      if(can_return_item)
        set(ITEMS_RETURNED ${ITEMS_RETURNED} ${current_dir}/${child})
      endif()
    endif()
  endforeach()
endmacro()

# This macro get all source files from a directory and its subdirectories.
macro(get_source_groups src_dir)
  set(SOURCE_RETURNED)
  set(ITEMS_RETURNED)

  # Add root files as a blank source group
  file(GLOB src_files
    ${src_dir}/*.cpp
    ${src_dir}/*.hpp
    ${src_dir}/*.h
  )
  if(src_files)
    set(SOURCE_RETURNED ${SOURCE_RETURNED} ${src_files})
    source_group("" FILES ${src_files})
  endif()

  # Add every subdir as a source group
  get_directories_list(${src_dir} " ")
  set(src_sub_dirs ${ITEMS_RETURNED})
  if(src_sub_dirs)
    foreach(dir ${src_sub_dirs})
      file(GLOB src_files
        ${dir}/*.cpp
        ${dir}/*.hpp
        ${dir}/*.h
      )
      get_filename_component(src_group ${dir} NAME)
      set(SOURCE_RETURNED ${SOURCE_RETURNED} ${src_files})
      source_group(${src_group} FILES ${src_files})
    endforeach()
  endif()
endmacro()

# This macro generates a executable
macro(generate_executable name src_dir output_dir cxx_flags link_flags libraries)
  get_source_groups(${src_dir})
  add_executable(${name}
    ${SOURCE_RETURNED}
  )
  target_link_libraries(${name}
    ${libraries}
  )
  set_target_properties(${name} PROPERTIES COMPILE_FLAGS "${cxx_flags}")
  set_target_properties(${name} PROPERTIES LINK_FLAGS "${link_flags}")
  set_target_properties(${name} PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${output_dir})
  foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG)
    set_target_properties(${name} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${output_dir})
  endforeach()
endmacro()

# This macro generates a static library
macro(generate_static_library name src_dir output_dir cxx_flags)
  get_source_groups(${src_dir})
  add_library(${name}
    ${SOURCE_RETURNED}
  )
  set_target_properties(${name} PROPERTIES COMPILE_FLAGS "${cxx_flags}")
  set_target_properties(${name} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY ${output_dir})
  foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG)
    set_target_properties(${name} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${output_dir})
  endforeach()
endmacro()

# This macro generates a dynamic library
macro(generate_dynamic_library name src_dir output_dir cxx_flags link_flags project_libraries external_libraries)
  get_source_groups(${src_dir})
  add_library(${name} SHARED
    ${SOURCE_RETURNED}
  )

  # All project libraries should included as whole into dynamic library
  foreach(library ${project_libraries})
    target_link_libraries(${name}
      ${NTA_LINKFLAGS_ARCHIVES} ${library}
    )
  endforeach()
  target_link_libraries(${name}
    ${external_libraries}
  )

  set_target_properties(${name} PROPERTIES COMPILE_FLAGS "${cxx_flags}")
  set_target_properties(${name} PROPERTIES LINKER_LANGUAGE "CXX")
  set_target_properties(${name} PROPERTIES LINK_FLAGS "${link_flags}")
  set_target_properties(${name} PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${output_dir})
  foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG)
    set_target_properties(${name} PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${output_dir})
  endforeach()
endmacro()

# This macro generates a swig module
macro(generate_swig_module name output_dir sub_dir swig_flags cxx_flags extra_source link_flags libraries)
  string(REPLACE " " ";" swig_flags ${swig_flags})
  file(MAKE_DIRECTORY "${PROJECT_BUILD_TEMP_DIR}/${sub_dir}")

  set(CMAKE_SWIG_OUTDIR "${output_dir}")

  snake_case_to_upper_camel_case(${name} camelized_name)
  set(IMPLEMENTATION_FILE "${REPOSITORY_DIR}/${sub_dir}/${camelized_name}Py.i")
  set_source_files_properties(${IMPLEMENTATION_FILE} PROPERTIES CPLUSPLUS ON)
  set_source_files_properties(${IMPLEMENTATION_FILE} PROPERTIES SWIG_FLAGS "${swig_flags}")
  swig_add_module(${name} python
    ${IMPLEMENTATION_FILE}
    ${extra_source}
  )

  set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES COMPILE_FLAGS "${cxx_flags} -DSWIG_TYPE_TABLE=_nupic_${name}")
  set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES LINK_FLAGS "${link_flags}")
  set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${output_dir})
  foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG)
    set_target_properties(${SWIG_MODULE_${name}_REAL_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} ${output_dir})
  endforeach()
  swig_link_libraries(${name}
    ${libraries}
  )
endmacro()

# This macro generates imported library from submodules
macro(generate_submodule_library name submodule_dir extra_cxxflags extra_linkflags remote commitish)

  # checkout git dependency
  if (NOT EXISTS ${submodule_dir})
    execute_process(COMMAND git clone ${remote} ${submodule_dir}
                    RESULT_VARIABLE EXIT_CODE)
    if(NOT EXIT_CODE EQUAL 0)
      message(FATAL_ERROR "Unable to clone ${remote} into ${submodule_dir}")
    endif()
  else()
    execute_process(COMMAND git fetch ${remote}
                    WORKING_DIRECTORY ${submodule_dir}
                    RESULT_VARIABLE EXIT_CODE)
    if(NOT EXIT_CODE EQUAL 0)
      message(FATAL_ERROR "Unable to fetch ${remote}")
    endif()
  endif()
  execute_process(COMMAND git checkout ${commitish}
                  WORKING_DIRECTORY ${submodule_dir}
                  RESULT_VARIABLE EXIT_CODE)
  if(NOT EXIT_CODE EQUAL 0)
    message(FATAL_ERROR "Unable to checkout ${commitish} in ${submodule_dir}")
  endif()

  # Build and set external libraries
  message(STATUS "Building '${name}' library...")

  # Clean 'build/scripts' subfolder at submodule folder
  execute_process(COMMAND ${CMAKE_COMMAND} -E remove_directory ${submodule_dir}/build/scripts)
  execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${submodule_dir}/build/scripts)
  # Generate the Make scripts
  execute_process(COMMAND ${CMAKE_COMMAND} ${submodule_dir}/src -DUSER_CXXFLAGS:STRING=${extra_cxxflags} -DUSER_LINKFLAGS:STRING=${extra_linkflags}
                  WORKING_DIRECTORY ${submodule_dir}/build/scripts)
  # Execute the Make scripts
  execute_process(COMMAND make -j3
                  WORKING_DIRECTORY ${submodule_dir}/build/scripts
                  RESULT_VARIABLE EXIT_CODE)
  if(NOT EXIT_CODE EQUAL 0)
    message(FATAL_ERROR "Compiling '${name}' library within ${REPOSITORY_DIR} failed.")
  endif()
  # Copy binaries outputted by submodule build process to 'release' folder
  copy_directory(${submodule_dir}/build/release/bin ${PROJECT_BUILD_RELEASE_DIR}/bin)
  copy_directory(${submodule_dir}/build/release/lib ${PROJECT_BUILD_RELEASE_DIR}/lib)
  copy_directory(${submodule_dir}/build/release/include ${PROJECT_BUILD_RELEASE_DIR}/include)

  # Configure submodule libraries
  add_library(${name} STATIC IMPORTED GLOBAL)
  set_property(TARGET ${name} PROPERTY IMPORTED_LOCATION "${PROJECT_BUILD_RELEASE_DIR}/lib/lib${name}.${STATIC_LIB_EXTENSION}")
endmacro()

# This macro converts a "snake_case" style string to an "UpperCamelCase" style string
# for example: "engine_internal" will be converted to "EngineInternal"
macro (snake_case_to_upper_camel_case before after)

  # I wanted to use `string(REGEX REPLACE "^[a-z]" ${first_letter_to_upper} temp ${before})`,
  # but it's buggy and turn "engine_internal_py" into "EEEEEE_internal_py"
  string(REGEX REPLACE "^([a-z])(.*)$" "\\1" first_letter "${before}")
  string(REGEX REPLACE "^([a-z])(.*)$" "\\2" rest "${before}")

  string(TOUPPER ${first_letter} first_letter_to_upper)

  string(REGEX MATCHALL "_([a-z])" all_underscore_and_next_letters ${rest})

  foreach(underscore_and_next_letter ${all_underscore_and_next_letters})

    string(TOUPPER ${underscore_and_next_letter} underscore_and_next_letter_to_upper)

    string(SUBSTRING ${underscore_and_next_letter_to_upper} 1 -1 next_letter_to_upper)

    string(REPLACE ${underscore_and_next_letter} ${next_letter_to_upper} rest "${rest}")

  endforeach(underscore_and_next_letter)

  set(${after} "${first_letter_to_upper}${rest}")

endmacro()


############################################################################################################################
###                                                                                                                      ###
###  1st Part:                                                                                                           ###
###  Configuration of the environment                                                                                    ###
###                                                                                                                      ###
############################################################################################################################

cmake_minimum_required(VERSION 2.8)
project(nupic CXX)
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
set(NEED_LOGOFF OFF)

#
# Set C++ compiler.
# According to CMake documentation, this must be done before any language is set (ie before any project() or enable_language() command).
#
set(USER_CXX_COMPILER "" CACHE STRING "Default C++ compiler to be used (GCC / CLANG) [default=system compiler]")
if(NOT "${USER_CXX_COMPILER}" STREQUAL "")
  set(CMAKE_CXX_COMPILER "${USER_CXX_COMPILER}")
endif()

#
# Get default directories passed by command line.
#
set(PROJECT_BUILD_RELEASE_DIR "" CACHE STRING "Release dir")
set(PROJECT_BUILD_TEMP_DIR "" CACHE STRING "Temporary dir")

#
# Sets default locations.
#
# Default directories structure is:
#
# ~/../repository (root directory with repository downloaded from internet)
#         /docs (subdirectory with support documentation)
#         /src (subdirectory with all source code)
#         /build/scripts ([suggested] subdirectory with build process [makefiles or IDE solution] generated by CMake)
#         /build/release (subdirectory with executables and libraries generated by build proccess)
#         /build/temp (directory with temporary files generated by build proccess)
#         Readme.md
#         Licence.txt
#
# Repository root is the parent directory which this CMake file is located
# This CMake file must be always on /repository/src subdirectory.
#get_filename_component(REPOSITORY_DIR ${PROJECT_SOURCE_DIR} PATH)
set(REPOSITORY_DIR ${PROJECT_SOURCE_DIR})
# 'release' is a subdirectory created on /build root.
set(PROJECT_BUILD_RELEASE_DIR "$ENV{NTA}")
if("${PROJECT_BUILD_RELEASE_DIR}" STREQUAL "")
  set(PROJECT_BUILD_RELEASE_DIR "${REPOSITORY_DIR}/build/release")
endif()
# 'temp' is a subdirectory created on /build root.
if("${PROJECT_BUILD_TEMP_DIR}" STREQUAL "")
  set(PROJECT_BUILD_TEMP_DIR "${REPOSITORY_DIR}/build/temp")
endif()
# CMAKE_CURRENT_BINARY_DIR is used by swig module for put wrappers on, so don't erase this line!
set(CMAKE_CURRENT_BINARY_DIR ${PROJECT_BUILD_TEMP_DIR})


#
# Prepare directory structure
#
execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_RELEASE_DIR}/include)
execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_RELEASE_DIR}/lib)
execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_RELEASE_DIR}/bin)
execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_TEMP_DIR}/lib)
execute_process(COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_TEMP_DIR}/obj)

#
# Set OS flags
#
if(UNIX)
  set(LIB_PREFIX "lib")
  set(STATIC_LIB_EXTENSION "a")
  if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    set(OSX ON)
    set(DYNAMIC_LIB_EXTENSION "dylib")
  elseif(${CMAKE_SYSTEM_NAME} MATCHES "Linux")
    set(LINUX ON)
    set(DYNAMIC_LIB_EXTENSION "so")
  endif()
elseif(${CMAKE_SYSTEM_NAME} MATCHES "Windows")
  set(WINDOWS ON)
  set(LIB_PREFIX "")
  set(STATIC_LIB_EXTENSION "lib")
  set(DYNAMIC_LIB_EXTENSION "dll")
endif()

#
# Determine project platform type
#
message(STATUS "Checking platform...")
if(${CMAKE_SIZEOF_VOID_P} MATCHES "8")
  set(NTA_PLATFORM_ARCH "64")
else()
  set(NTA_PLATFORM_ARCH "32")
endif()
set(NTA_PLATFORM_CXXFLAGS "-fPIC -DPIC")
set(NTA_PLATFORM_LINKFLAGS "")
set(NTA_PLATFORM_LIBS "-std=c++98")
if(OSX)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "10.7")
  set(NTA_PLATFORM_OS "darwin64")
  set(NTA_PLATFORM_CXXFLAGS "${NTA_PLATFORM_CXXFLAGS} -m64")
  set(NTA_PLATFORM_DEBUGFLAGS "-gfull")
  set(NTA_PLATFORM_LINKFLAGS "${NTA_PLATFORM_LINKFLAGS} -Wl,-u,_munmap")
  set(NTA_PLATFORM_LIBS "${NTA_PLATFORM_LIBS} -stdlib=libstdc++ -lc++abi -liconv -lsqlite3 -framework CoreServices -framework Accelerate")
  set(NTA_PLATFORM_LINKFLAGS_PYMODULE "-bundle -undefined dynamic_lookup -fPIC")
  set(NTA_PLATFORM_LINKFLAGS_PYEMBED "")
elseif(LINUX)
  set(NTA_PLATFORM_DEBUGFLAGS "-g")
  set(NTA_PLATFORM_LINKFLAGS "${NTA_PLATFORM_LINKFLAGS} -Wl,--no-as-needed -static-libgcc")
  set(NTA_PLATFORM_LIBS "${NTA_PLATFORM_LIBS} -lm -lpthread -ldl -lutil")
  set(NTA_PLATFORM_LINKFLAGS_PYMODULE "-pthread -shared")
  set(NTA_PLATFORM_LINKFLAGS_PYEMBED "-Wl,--export-dynamic")
  if(${NTA_PLATFORM_ARCH} MATCHES "64")
    set(NTA_PLATFORM_OS "linux64")
    set(NTA_PLATFORM_CXXFLAGS "${NTA_PLATFORM_CXXFLAGS} -m64")
  else()
    set(NTA_PLATFORM_OS "linux32")
    set(NTA_PLATFORM_CXXFLAGS "${NTA_PLATFORM_CXXFLAGS} -ffloat-store")
  endif()
elseif(WINDOWS)
  set(NTA_PLATFORM_OS "win32")
  set(NTA_PLATFORM_CXXFLAGS "${NTA_PLATFORM_CXXFLAGS} -DWIN32")
else()
  message(FATAL_ERROR "${CMAKE_CURRENT_LIST_FILE}:${CMAKE_CURRENT_LIST_LINE}: error: ${CMAKE_SYSTEM_NAME} not supported yet.")
endif()

message(STATUS "Platform: ${NTA_PLATFORM_OS}")
message(STATUS "Platform-specific flags:")
message(STATUS "  Libraries: ${NTA_PLATFORM_LIBS}")
message(STATUS "  CXX flags: ${NTA_PLATFORM_CXXFLAGS}")
message(STATUS "  Debug flags: ${NTA_PLATFORM_DEBUGFLAGS}")
message(STATUS "  LD flags: ${NTA_PLATFORM_LINKFLAGS}")
message(STATUS "  Python extension link flags: ${NTA_PLATFORM_LINKFLAGS_PYMODULE}")
message(STATUS "  Python embedding link flags: ${NTA_PLATFORM_LINKFLAGS_PYEMBED}")

message(STATUS "Checking software tools...")

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

#
# Find out where system installation of python is.
#
execute_process(COMMAND ${PYTHON} -c "import sys;sys.stdout.write(sys.prefix)"
                OUTPUT_VARIABLE PYTHON_PREFIX)
string(REGEX REPLACE "\\\\" "/" PYTHON_PREFIX ${PYTHON_PREFIX})
set(PYTHON_INCLUDE_DIR "${PYTHON_PREFIX}/include/python${PYTHON_VERSION}")
set(PYTHON_LIBRARY_DIR "${PYTHON_PREFIX}/lib/python${PYTHON_VERSION}")
set(PYTHON_SITE_PACKAGES_DIR "${PROJECT_BUILD_RELEASE_DIR}/lib/python${PYTHON_VERSION}/site-packages")
find_package(PythonLibs ${PYTHON_VERSION} REQUIRED)

#
# Finds out version of Numpy and headers's path.
#
execute_process(COMMAND ${PYTHON} -c "import sys;import numpy;sys.stdout.write(numpy.get_include())"
                OUTPUT_VARIABLE NUMPY_INCLUDE_DIR)
string(REGEX REPLACE "\\\\" "/" NUMPY_INCLUDE_DIR ${NUMPY_INCLUDE_DIR})
execute_process(COMMAND ${PYTHON} -c "import sys;import numpy;sys.stdout.write(numpy.__version__)"
                OUTPUT_VARIABLE NUMPY_VERSION)

#
# Checks if Swig is installed and gets its variables.
# Minimum version of Swig is 1.3.36 -- earlier versions *will* fail
# Later versions greater than 2.0.3 also *will* fail (SWIGPY_SLICE_ARG bug)
#
set(SWIG_EXECUTABLE "${REPOSITORY_DIR}/external/${NTA_PLATFORM_OS}/bin/swig")
set(SWIG_DIR "${REPOSITORY_DIR}/external/common/share/swig/1.3.36")
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
message(STATUS "  Python lib: ${PYTHON_LIBRARY}")
message(STATUS "  Python command: ${PYTHON}")
message(STATUS "Numpy details:")
message(STATUS "  Version: ${NUMPY_VERSION}")
message(STATUS "  Include dir: ${NUMPY_INCLUDE_DIR}")
message(STATUS "Swig details:")
message(STATUS "  Version: ${SWIG_VERSION}")

#
# Set environment variables of the operating system
#
message(STATUS "Checking environment...")
message(STATUS "Environment variables:")
set_environment_variable(PYTHONPATH "${PYTHON_SITE_PACKAGES_DIR}" OFF)
set_environment_variable(NUPIC "${REPOSITORY_DIR}" OFF)
set_environment_variable(NTA "${PROJECT_BUILD_RELEASE_DIR}" OFF)
set_environment_variable(NTA_DATA_PATH "${PROJECT_BUILD_RELEASE_DIR}/share/prediction/data" OFF)
if(OSX)
  set_environment_variable(MACOSX_DEPLOYMENT_TARGET "${CMAKE_OSX_DEPLOYMENT_TARGET}" OFF)
endif()
show_environment_variable(NTAX_DEVELOPER_BUILD "$ENV{NTAX_DEVELOPER_BUILD}")
if(NEED_LOGOFF)
  message("You should logoff your system in order to some environment variables are changed permanently. If the problem persists, consider set manually the variables above in your 'bashrc' file")
endif()


#
# Project details
#
message(STATUS "Checking project...")
message(STATUS "Project: ${PROJECT_NAME}")
message(STATUS "Locations:")
message(STATUS "  Source: ${PROJECT_SOURCE_DIR}")
message(STATUS "  Build System: ${PROJECT_BINARY_DIR}")
message(STATUS "  Build Directory: ${PROJECT_BUILD_TEMP_DIR}")
message(STATUS "  Release: ${PROJECT_BUILD_RELEASE_DIR}")


############################################################################################################################
###                                                                                                                      ###
###  2nd Part:                                                                                                           ###
###  Configuration of compiler flags                                                                                     ###
###                                                                                                                      ###
############################################################################################################################

#
# Define custom preprocessor variables (#define XX in C++ code)
#
# The reason to use add_definitions() instead of appending flag -std=c++0x directly to CXXBASE_FLAGS is that
# cmake deploys "internal smarts" for compatibility with different compilers (clang, gcc 4.6 vs 4.8)
#add_definitions(-DNPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION) # silence numpy1.7 deprecated warning
add_definitions(-std=c++98) # smart flag setting for gcc/clang

#
# Include directories of headers
# Allows us to find includes for external libraries and enables
# #include <nta/common/...>
#
set(NTA_INCLUDEFLAGS "-I${REPOSITORY_DIR} -I${REPOSITORY_DIR}/extensions -I${PROJECT_BUILD_RELEASE_DIR}/include -isystem${REPOSITORY_DIR}/extensions/core/external/common/include -isystem${REPOSITORY_DIR}/extensions/core/external/${NTA_PLATFORM_OS}/include -isystem${REPOSITORY_DIR}/external/common/include -isystem${REPOSITORY_DIR}/external/${NTA_PLATFORM_OS}/include")

#
# NTA_INTERNAL tells us that the code is being built under the build system
# and not as a separate program. Used for cppvision example.
#
set(NTA_CXXFLAGS_BASE "${NTA_INCLUDEFLAGS} ${NTA_PLATFORM_CXXFLAGS} -DHAVE_CONFIG_H -DNTA_INTERNAL -DNTA_PLATFORM_${NTA_PLATFORM_OS} -DBOOST_NO_WREGEX -DNUPIC2 -fvisibility=hidden -Wall -Wreturn-type -Wunused -Wno-unused-parameter")

#
# All executables and plugins are linked with these flags
#
set(NTA_LINKFLAGS "${NTA_PLATFORM_LINKFLAGS} ${NTA_PLATFORM_LIBS} -L${PROJECT_BUILD_RELEASE_DIR}/lib -L${REPOSITORY_DIR}/extensions/core/external/${NTA_PLATFORM_OS}/lib -L${REPOSITORY_DIR}/external/${NTA_PLATFORM_OS}/lib")

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
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -DNTA_ASM")
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
# Build using MPI headers and library,
# and enable features that depend on MPI.
#
option(NTA_MPI_SUPPORT "--mpi=[ON/OFF] turn on MPI support [default=ON]" ON)
message(STATUS "  MPI Support: ${NTA_MPI_SUPPORT}")

#
# Build using Python headers and library,
# and enable features that depend on Python.
#
option(NTA_PYTHON_SUPPORT "--python-support=[ON/OFF] turn on python support [default=ON]" ON)
message(STATUS "  Python Support: ${NTA_PYTHON_SUPPORT}")

#
# Compiler specific (clang, gcc, ..) flags can be set here
#
if(CMAKE_COMPILER_IS_GNUCXX)
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -Wno-sign-compare -Wno-error=format=")
  set(NTA_CXXFLAGS_OPTIMIZATION "${NTA_CXXFLAGS_OPTIMIZATION} -falign-loops=16")
  # workaround for gcc 4.4 in Grok
  execute_process(COMMAND ${CMAKE_C_COMPILER} -dumpversion OUTPUT_VARIABLE GCC_VERSION)
  if (GCC_VERSION VERSION_GREATER 4.6 OR GCC_VERSION VERSION_EQUAL 4.6)
    set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -Wno-error=cpp -Werror")
  endif()
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

  set(NTA_SWIG_FLAGS "${NTA_SWIG_FLAGS} -features autodoc=0,directors=0 -noproxyimport -keyword -modern -modernargs -noproxydel -fvirtual -fastunpack -nofastproxy -fastquery -outputtuple -castmode -w402 -w503 -w511 -w302 -w362 -w312 -w389 -DNTA_PLATFORM_${NTA_PLATFORM_OS} -DNTA_PYTHON_SUPPORT=${PYTHON_VERSION} -I${NUMPY_INCLUDE_DIR} -I${SWIG_DIR}/python -I${SWIG_DIR} ${NTA_INCLUDEFLAGS}")
  string(REGEX REPLACE "-isystem" "-I" NTA_SWIG_FLAGS ${NTA_SWIG_FLAGS}) # C++ includes need -isystem, but swig can't handle that
  string(REPLACE " " ";" NTA_SWIG_FLAGS ${NTA_SWIG_FLAGS})

  # Minimal functional subset
  set(NTA_CXXFLAGS_BASE "${NTA_CXXFLAGS_BASE} -DNTA_PYTHON_SUPPORT=${PYTHON_VERSION} -isystem${NUMPY_INCLUDE_DIR} -isystem${PYTHON_INCLUDE_DIR}")

  # -falign-functions is necessary to avoid a compiler problem on
  # darwin. If you build without -falign-functions, exceptions
  # thrown in a pynode result in an abort() instead of propagation
  # up the call stack.
  set(NTA_CXXFLAGS_PYMODULE "${NTA_CXXFLAGS_BASE} ${NTA_CXXFLAGS_OPTIMIZATION_PYMODULE} -falign-functions")

  set(NTA_LINKFLAGS_PY "-L${PYTHON_LIBRARY_DIR}/config -ldl -lpython${PYTHON_VERSION}")

  set(NTA_LINKFLAGS_PYEMBED "${NTA_PLATFORM_LINKFLAGS_PYEMBED} ${NTA_LINKFLAGS_PY}")

  set(NTA_LINKFLAGS_PYMODULE "${NTA_PLATFORM_LINKFLAGS_PYMODULE} ${NTA_LINKFLAGS_PY} ${NTA_PLATFORM_LIBS} -L${PROJECT_BUILD_RELEASE_DIR}/lib -L${REPOSITORY_DIR}/external/${NTA_PLATFORM_OS}/lib")

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
# LibSupport
#
# lang/py/support must be built before nta, but lang must be built after nta.
# This is due to the fact that both nta/pynode and lang/py/net_internal depend
# on lang/py/support and lang/py/engine_internal depends on nta.
#
set(LIB_STATIC_SUPPORT py_support)
generate_static_library(${LIB_STATIC_SUPPORT} "${REPOSITORY_DIR}/extensions/py_support" "${PROJECT_BUILD_TEMP_DIR}/lib" "${NTA_CXXFLAGS}")

#
# LibNupicCore
#
# Put content from module config (.nupic_modules) file into variables
if(EXISTS "${REPOSITORY_DIR}/.nupic_config")
  file(READ "${REPOSITORY_DIR}/.nupic_config" MODULES_FILE_CONTENT)
elseif(EXISTS "$ENV{HOME}/.nupic_config")
  file(READ "$ENV{HOME}/.nupic_config" MODULES_FILE_CONTENT)
else()
  file(READ "${REPOSITORY_DIR}/.nupic_modules" MODULES_FILE_CONTENT)
endif()
read_variable_from_file("${MODULES_FILE_CONTENT}" "NUPIC_CORE_REMOTE" NUPIC_CORE_REMOTE)
read_variable_from_file("${MODULES_FILE_CONTENT}" "NUPIC_CORE_COMMITISH" NUPIC_CORE_COMMITISH)
set(LIB_STATIC_NUPICCORE nupic_core)
generate_submodule_library(${LIB_STATIC_NUPICCORE} "${REPOSITORY_DIR}/extensions/core" "-DNTA_PYTHON_SUPPORT=${PYTHON_VERSION}" "" "${NUPIC_CORE_REMOTE}" "${NUPIC_CORE_COMMITISH}")

#
# HtmTest
#
set(EXECUTABLE_HTMTEST testpyhtm)
set(LIBRARIES
  ${LIB_STATIC_SUPPORT}
  ${LIB_STATIC_NUPICCORE}
)
generate_executable(${EXECUTABLE_HTMTEST} "${REPOSITORY_DIR}/extensions/htmtest" "${PROJECT_BUILD_RELEASE_DIR}/bin" "${NTA_CXXFLAGS}" "${NTA_LINKFLAGS}" "${LIBRARIES}")

#
# LibCppRegion
#
# A regular shared library that is installed in <$NTA/lib> and
# loaded dynamically.
#
set(LIB_DYNAMIC_CPPREGION cpp_region)
set(PROJECT_LIBRARIES
  ${LIB_STATIC_SUPPORT}
  ${LIB_STATIC_NUPICCORE}
)
set(EXTERNAL_LIBRARIES
  ${PYTHON_LIBRARY}
)
generate_dynamic_library(${LIB_DYNAMIC_CPPREGION} "${REPOSITORY_DIR}/extensions/cpp_region" "${PROJECT_BUILD_RELEASE_DIR}/lib" "${NTA_CXXFLAGS}" "${NTA_LINKFLAGS} ${NTA_LINKFLAGS_PYEMBED}" "${PROJECT_LIBRARIES}" "${EXTERNAL_LIBRARIES}")

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
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_NUPICCORE}
  )
  generate_swig_module(${LIB_SHARED_ENGINEINTERNAL} "${REPOSITORY_DIR}/nupic/bindings" "/extensions/bindings/py/engine_internal" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")

  #
  # LibBindingsMath
  #
  set(LIB_SHARED_MATH math)
  set(EXTRA_SOURCE
    ${REPOSITORY_DIR}/extensions/bindings/py/math/PySparseTensor.cpp
  )
  set(LIBRARIES
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_NUPICCORE}
  )
  generate_swig_module(${LIB_SHARED_MATH} "${REPOSITORY_DIR}/nupic/bindings" "/extensions/bindings/py/math" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "${EXTRA_SOURCE}" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")

  #
  # LibBindingsAlgorithms
  #
  set(LIB_SHARED_ALGORITHMS algorithms)
  set(LIBRARIES
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_NUPICCORE}
  )
  generate_swig_module(${LIB_SHARED_ALGORITHMS} "${REPOSITORY_DIR}/nupic/bindings" "/extensions/bindings/py/algorithms" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")

  #
  # LibBindingsIORange
  #
  set(LIB_SHARED_IORANGE iorange)
  set(LIBRARIES
    ${LIB_STATIC_SUPPORT}
    ${LIB_STATIC_NUPICCORE}
  )
  generate_swig_module(${LIB_SHARED_IORANGE} "${REPOSITORY_DIR}/nupic/bindings" "/extensions/bindings/py/iorange" "${NTA_SWIG_FLAGS}" "${NTA_CXXFLAGS_PYMODULE}" "" "${NTA_LINKFLAGS_PYMODULE}" "${LIBRARIES}")
endif()


############################################################################################################################
###                                                                                                                      ###
###  4th Part:                                                                                                           ###
###  Post configuration operations                                                                                       ###
###                                                                                                                      ###
############################################################################################################################

# Copy bindings to $NTA after build
# This is palliative and should be removed after "Pip Installable" PR being merged!
add_custom_command(TARGET _engine_internal POST_BUILD
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/engine_internal.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/engine_internal.py
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/_engine_internal.so ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/_engine_internal.so)
add_custom_command(TARGET _math POST_BUILD
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/math.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/math.py
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/_math.so ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/_math.so)
add_custom_command(TARGET _algorithms POST_BUILD
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/algorithms.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/algorithms.py
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/_algorithms.so ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/_algorithms.so)
add_custom_command(TARGET _iorange POST_BUILD
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/iorange.py ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/iorange.py
                   COMMAND ${CMAKE_COMMAND} -E copy ${REPOSITORY_DIR}/nupic/bindings/_iorange.so ${PYTHON_SITE_PACKAGES_DIR}/nupic/bindings/_iorange.so)

# Copy the pieces of nupic that we want
copy_directory(${REPOSITORY_DIR}/nupic ${PYTHON_SITE_PACKAGES_DIR}/nupic)

# Copy examples
copy_directory(${REPOSITORY_DIR}/examples/prediction ${PROJECT_BUILD_RELEASE_DIR}/share/prediction)
copy_directory(${REPOSITORY_DIR}/examples/opf ${PROJECT_BUILD_RELEASE_DIR}/share/opf)

# Copy testing codes
copy_directory(${REPOSITORY_DIR}/resources ${PROJECT_BUILD_RELEASE_DIR}/share/test/data)
copy_directory(${REPOSITORY_DIR}/tests ${PROJECT_BUILD_RELEASE_DIR}/tests)
copy_directory(${REPOSITORY_DIR}/scripts ${PROJECT_BUILD_RELEASE_DIR}/scripts)

# Copy miscellaneous files
copy_directory(${REPOSITORY_DIR}/extensions/core/external/licenses ${PROJECT_BUILD_RELEASE_DIR}/share/doc/licenses)
copy_directory(${REPOSITORY_DIR}/external/licenses ${PROJECT_BUILD_RELEASE_DIR}/share/doc/licenses)
copy_file(${REPOSITORY_DIR}/conf/default/nupic-default.xml ${PROJECT_BUILD_RELEASE_DIR}/conf/default/nupic-default.xml)
copy_file(${REPOSITORY_DIR}/conf/default/nupic-logging.conf ${PROJECT_BUILD_RELEASE_DIR}/conf/default/nupic-logging.conf)


############################################################################################################################
###                                                                                                                      ###
###  5th Part:                                                                                                           ###
###  Custom targets                                                                                                      ###
###                                                                                                                      ###
############################################################################################################################

#
# Tests
#
add_custom_target(tests_run
                  COMMAND python ${PROJECT_BUILD_RELEASE_DIR}/scripts/run_tests.py -n2
                  COMMENT "Python tests")

add_custom_target(tests_run_all
                  COMMAND python ${PROJECT_BUILD_RELEASE_DIR}/scripts/run_tests.py --all  # swarming tests fail with the -n parallel run
                  COMMENT "Python tests + swarming (requires DB)")

add_custom_target(tests_pyhtm
                  COMMAND ${PROJECT_BUILD_RELEASE_DIR}/bin/testpyhtm
                  COMMENT "Basic tests in Python")

add_custom_target(tests_cpphtm
                  COMMAND ${PROJECT_BUILD_RELEASE_DIR}/bin/testcpphtm
                  COMMENT "Basic tests in C++")

add_custom_target(tests_everything
                  COMMAND ${PROJECT_BUILD_RELEASE_DIR}/bin/testeverything
                  COMMENT "C++ unit tests")

# Tests_all just calls other targets
add_custom_target(tests_all
                  DEPENDS tests_run
                  DEPENDS tests_pyhtm
                  DEPENDS tests_cpphtm
                  DEPENDS tests_everything
                  COMMENT "Running all tests")

#
# Clean
#
add_custom_target(distclean
		# Clean '/build/release' and build/temp
		COMMAND ${CMAKE_COMMAND} -E remove_directory ${PROJECT_BUILD_RELEASE_DIR}
		COMMAND ${CMAKE_COMMAND} -E remove_directory ${PROJECT_BUILD_TEMP_DIR}
		# recreate folders
		COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_RELEASE_DIR}/include
		COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_RELEASE_DIR}/lib
		COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_RELEASE_DIR}/bin
		COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_TEMP_DIR}/lib
		COMMAND ${CMAKE_COMMAND} -E make_directory ${PROJECT_BUILD_TEMP_DIR}/obj
		COMMENT "Cleaning temporary & release build files")

# Just to separate from result message
message(STATUS "")

