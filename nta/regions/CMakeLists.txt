include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_library(libregions
  SpatialPoolerNode.cpp
  VectorFile.cpp
  VectorFileEffector.cpp
  VectorFileSensor.cpp
  SpatialPoolerNode.hpp
  VectorFile.hpp
  VectorFileEffector.hpp
  VectorFileSensor.hpp
)
