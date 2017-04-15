include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libntypes_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libntypes
  ArrayBase.cpp
  Buffer.cpp
  BundleIO.cpp
  Collection.cpp
  Dimensions.cpp
  MemParser.cpp
  Scalar.cpp
  Value.cpp
  Array.hpp
  ArrayBase.hpp
  ArrayRef.hpp
  Buffer.hpp
  BundleIO.hpp
  Collection.hpp
  Dimensions.hpp
  MemParser.hpp
  MemStream.hpp
  NodeSet.hpp
  object_model.hpp
  Scalar.hpp
  Value.hpp
  object_model.h
)
