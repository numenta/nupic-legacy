include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libutils_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libutils
  LoggingException.cpp
  LogItem.cpp
  Random.cpp
  StringUtils.cpp
  TRandom.cpp
  Watcher.cpp
  Log.hpp
  LoggingException.hpp
  LogItem.hpp
  Random.hpp
  StringUtils.hpp
  TRandom.hpp
  utils.hpp
  Watcher.hpp
)
