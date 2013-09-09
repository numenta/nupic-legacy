include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_library(libtest
  Tester.cpp
  Tester.hpp
)
