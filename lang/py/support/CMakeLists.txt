include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libsupport_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libsupport
  NumpyVector.cpp
  PyArray.cpp
  PyHelpers.cpp
  PythonStream.cpp
  NumpyVector.hpp
  PyArray.hpp
  PyHelpers.hpp
  PythonStream.hpp
  WrappedVector.hpp
)
