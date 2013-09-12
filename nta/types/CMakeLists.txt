include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_library(libtypes
  BasicType.cpp
  Fraction.cpp
  BasicType.hpp
  Exception.hpp
  Fraction.hpp
  types.hpp
  types.h
)
