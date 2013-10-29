include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_executable(htmtest
  htmtest.cpp
)
set_target_properties(htmtest PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_INSTALL_PREFIX}/bin)
set_target_properties(htmtest PROPERTIES PREFIX "../")

set(CMAKE_EXE_LINKER_FLAGS "${NTA_LINKFLAGS}")

link_directories(
  ${CMAKE_INSTALL_PREFIX}/nta/engine
  ${CMAKE_INSTALL_PREFIX}/nta/regions
  ${CMAKE_INSTALL_PREFIX}/nta/algorithms
  ${CMAKE_INSTALL_PREFIX}/lang/py/support
  ${CMAKE_INSTALL_PREFIX}/nta/os
  ${CMAKE_INSTALL_PREFIX}/nta/math
  ${CMAKE_INSTALL_PREFIX}/nta/ntypes
  ${CMAKE_INSTALL_PREFIX}/nta/utils
  ${CMAKE_INSTALL_PREFIX}/nta/types
  ${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib
)

target_link_libraries(htmtest
  libengine
  libregions
  libalgorithms
  libsupport
  libos
  libmath
  libntypes
  libutils
  libtypes
  ${NTA_STANDARD_LIBS}
)
