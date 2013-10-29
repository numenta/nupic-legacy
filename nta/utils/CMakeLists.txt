include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

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
