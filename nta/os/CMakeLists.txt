include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libos_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libos
  Directory.cpp
  DynamicLibrary.cpp
  Env.cpp
  FStream.cpp
  OS.cpp
  OSUnix.cpp
  OSWin.cpp
  Path.cpp
  regex.cpp
  Timer.cpp
  Directory.hpp
  DynamicLibrary.hpp
  Env.hpp
  FStream.hpp
  OS.hpp
  Path.hpp
  regex.hpp
  Timer.hpp
)
