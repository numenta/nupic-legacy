include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# A regular shared library that is installed in <lib> and
# loaded dynamically.
add_library(libcpp_region SHARED
  PyRegion.cpp
  PyRegion.hpp
)

# Do not append version number to .so file name
set(CMAKE_SHARED_LINKER_FLAGS "-avoid-version ${NTA_LINKFLAGS} ${NTA_PYEMBEDFLAGS}")

target_link_libraries(libcpp_region
  ../../nta/engine/libengine.a
  ../../nta/regions/libregions.a
  ../../nta/algorithms/libalgorithms.a
  ../../nta/math/libmath.a
  ../../nta/ntypes/libntypes.a
  ../../lang/py/support/libsupport.a
  ../../nta/os/libos.a
  ../../nta/utils/libutils.a
  ../../nta/types/libtypes.a
  ${NTA_PYTHON_LIBS}
  ${externaldir}/lib/libaprutil-1.a
  ${externaldir}/lib/libapr-1.a
  ${externaldir}/lib/libz.a
)

install(TARGETS libcpp_region LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/lib)
