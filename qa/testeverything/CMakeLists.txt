include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_executable(testeverything
  ${CMAKE_SOURCE_DIR}/nta/algorithms/unittests/CondProbTableTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/algorithms/unittests/FastCLAClassifierTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/algorithms/unittests/NearestNeighborUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/algorithms/unittests/SpatialPoolerUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/algorithms/unittests/TAMUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/engine/unittests/InputTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/engine/unittests/NetworkTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/engine/unittests/RegionTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/engine/unittests/UniformLinkPolicyTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/engine/unittests/YAMLUtilsTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/DenseTensorUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/DomainUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/IndexUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/MathsTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/SparseMatrix01UnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/SparseMatrixUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/math/unittests/SparseTensorUnitTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/ArrayTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/BufferTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/CollectionTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/DimensionsTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/MemParserTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/MemStreamTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/NodeSetTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/ScalarTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/ntypes/unittests/ValueTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/DirectoryTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/DynamicLibraryTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/EnvTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/OSTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/PathTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/regexTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/os/unittests/TimerTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/test/unittests/TesterTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/types/unittests/BasicTypeTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/types/unittests/ExceptionTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/types/unittests/FractionTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/utils/unittests/RandomTest.cpp
  ${CMAKE_SOURCE_DIR}/nta/utils/unittests/WatcherTest.cpp
  TestEverythingMain.cpp
)
set_target_properties(testeverything PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_INSTALL_PREFIX}/bin)
if (MSVC)
  set_target_properties(testeverything PROPERTIES PREFIX "../")
endif()

set(CMAKE_EXE_LINKER_FLAGS "${NTA_LINKFLAGS} ${NTA_PYEMBEDFLAGS}")

link_directories(
  ${CMAKE_INSTALL_PREFIX}/nta/engine
  ${CMAKE_INSTALL_PREFIX}/nta/regions
  ${CMAKE_INSTALL_PREFIX}/nta/algorithms
  ${CMAKE_INSTALL_PREFIX}/nta/math
  ${CMAKE_INSTALL_PREFIX}/nta/ntypes
  ${CMAKE_INSTALL_PREFIX}/lang/py/support
  ${CMAKE_INSTALL_PREFIX}/nta/os
  ${CMAKE_INSTALL_PREFIX}/nta/test
  ${CMAKE_INSTALL_PREFIX}/nta/utils
  ${CMAKE_INSTALL_PREFIX}/nta/types
  ${CMAKE_SOURCE_DIR}/external/${nta_platform}/lib
)

target_link_libraries(testeverything
  libengine
  libregions
  libalgorithms
  libmath
  libntypes
  libsupport
  libos
  libtest
  libutils
  libtypes
  ${NTA_STANDARD_LIBS}
)
