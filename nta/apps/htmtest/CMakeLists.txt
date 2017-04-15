include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_executable(htmtest
  htmtest.cpp
)

set(CMAKE_EXE_LINKER_FLAGS "${NTA_LINKFLAGS}")

target_link_libraries(htmtest
  ../../../nta/engine/libengine.a
  ../../../nta/regions/libregions.a
  ../../../nta/algorithms/libalgorithms.a
  ../../../lang/py/support/libsupport.a
  ../../../nta/os/libos.a
  ../../../nta/math/libmath.a
  ../../../nta/ntypes/libntypes.a
  ../../../nta/utils/libutils.a
  ../../../nta/types/libtypes.a
  -lcrypto
  ${NTA_STANDARD_LIBS}
)

install(TARGETS htmtest RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
