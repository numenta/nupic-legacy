include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libregions_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libregions
  SpatialPoolerNode.cpp
  TemporalPoolerNode.cpp
  VectorFile.cpp
  VectorFileEffector.cpp
  VectorFileSensor.cpp
  SpatialPoolerNode.hpp
  TemporalPoolerNode.hpp
  VectorFile.hpp
  VectorFileEffector.hpp
  VectorFileSensor.hpp
)
