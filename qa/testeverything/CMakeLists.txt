include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_executable(testeverything
  ../../nta/algorithms/unittests/CondProbTableTest.cpp
  ../../nta/algorithms/unittests/FastCLAClassifierTest.cpp
  ../../nta/algorithms/unittests/GrouperUnitTest.cpp
  ../../nta/algorithms/unittests/NearestNeighborUnitTest.cpp
  ../../nta/algorithms/unittests/SpatialPoolerUnitTest.cpp
  ../../nta/algorithms/unittests/TAMUnitTest.cpp
  ../../nta/engine/unittests/InputTest.cpp
  ../../nta/engine/unittests/NetworkTest.cpp
  ../../nta/engine/unittests/RegionTest.cpp
  ../../nta/engine/unittests/UniformLinkPolicyTest.cpp
  ../../nta/engine/unittests/YAMLUtilsTest.cpp
  ../../nta/math/unittests/DenseTensorUnitTest.cpp
  ../../nta/math/unittests/DomainUnitTest.cpp
  ../../nta/math/unittests/IndexUnitTest.cpp
  ../../nta/math/unittests/MathsTest.cpp
  ../../nta/math/unittests/SparseMatrix01UnitTest.cpp
  ../../nta/math/unittests/SparseMatrixUnitTest.cpp
  ../../nta/math/unittests/SparseTensorUnitTest.cpp
  ../../nta/ntypes/unittests/ArrayTest.cpp
  ../../nta/ntypes/unittests/BufferTest.cpp
  ../../nta/ntypes/unittests/CollectionTest.cpp
  ../../nta/ntypes/unittests/DimensionsTest.cpp
  ../../nta/ntypes/unittests/MemParserTest.cpp
  ../../nta/ntypes/unittests/MemStreamTest.cpp
  ../../nta/ntypes/unittests/NodeSetTest.cpp
  ../../nta/ntypes/unittests/ScalarTest.cpp
  ../../nta/ntypes/unittests/ValueTest.cpp
  ../../nta/os/unittests/DirectoryTest.cpp
  ../../nta/os/unittests/DynamicLibraryTest.cpp
  ../../nta/os/unittests/EnvTest.cpp
  ../../nta/os/unittests/OSTest.cpp
  ../../nta/os/unittests/PathTest.cpp
  ../../nta/os/unittests/regexTest.cpp
  ../../nta/os/unittests/TimerTest.cpp
  ../../nta/test/unittests/TesterTest.cpp
  ../../nta/types/unittests/BasicTypeTest.cpp
  ../../nta/types/unittests/ExceptionTest.cpp
  ../../nta/types/unittests/FractionTest.cpp
  ../../nta/utils/unittests/RandomTest.cpp
  ../../nta/utils/unittests/WatcherTest.cpp
  TestEverythingMain.cpp
)

set(CMAKE_EXE_LINKER_FLAGS "${NTA_LINKFLAGS} ${NTA_PYEMBEDFLAGS}")

target_link_libraries(testeverything
  ../../nta/engine/libengine.a
  ../../nta/regions/libregions.a
  ../../nta/algorithms/libalgorithms.a
  ../../nta/math/libmath.a
  ../../nta/ntypes/libntypes.a
  ../../lang/py/support/libsupport.a
  ../../nta/os/libos.a
  ../../nta/test/libtest.a
  ../../nta/utils/libutils.a
  ../../nta/types/libtypes.a
  -lcrypto
  ${NTA_STANDARD_LIBS}
  ${NTA_PYTHON_LIBS}
)

install(TARGETS testeverything RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
