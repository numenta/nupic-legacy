include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libtest_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libtest
  Tester.cpp
  Tester.hpp
)
