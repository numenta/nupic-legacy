include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# A regular shared library that is installed in <lib> and
# loaded dynamically.
add_library(libcpp_region SHARED
  PyRegion.cpp
  PyRegion.hpp
)
set_target_properties(libcpp_region PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_INSTALL_PREFIX}/lib)
if (MSVC)
  set_target_properties(libcpp_region PROPERTIES PREFIX "../")
endif()

# Do not append version number to .so file name
set(CMAKE_SHARED_LINKER_FLAGS "-avoid-version ${NTA_LINKFLAGS} ${NTA_PYEMBEDFLAGS}")

link_directories(
  ${CMAKE_INSTALL_PREFIX}/nta/engine
  ${CMAKE_INSTALL_PREFIX}/nta/regions
  ${CMAKE_INSTALL_PREFIX}/nta/algorithm
  ${CMAKE_INSTALL_PREFIX}/nta/math
  ${CMAKE_INSTALL_PREFIX}/nta/ntypes
  ${CMAKE_INSTALL_PREFIX}/lang/py/support
  ${CMAKE_INSTALL_PREFIX}/nta/os
  ${CMAKE_INSTALL_PREFIX}/nta/utils
  ${CMAKE_INSTALL_PREFIX}/nta/types
  ${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib
)

target_link_libraries(libcpp_region
  libengine
  libregions
  libalgorithms
  libmath
  libntypes
  libsupport
  libos
  libutils
  libtypes
  ${NTA_STANDARD_LIBS}
  ${PYTHON_LIBRARIES}
)
