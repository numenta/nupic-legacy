include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libengine_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libengine
  Collections.cpp
  Input.cpp
  Link.cpp
  LinkPolicyFactory.cpp
  Network.cpp
  NuPIC.cpp
  Output.cpp
  Region.cpp
  Region_io.cpp
  Region_parameters.cpp
  RegionImpl.cpp
  RegionImplFactory.cpp
  Spec.cpp
  TestFanIn2LinkPolicy.cpp
  TestNode.cpp
  UniformLinkPolicy.cpp
  YAMLUtils.cpp
  Input.hpp
  Link.hpp
  LinkPolicy.hpp
  LinkPolicyFactory.hpp
  Network.hpp
  NuPIC.hpp
  Output.hpp
  Region.hpp
  RegionImpl.hpp
  RegionImplFactory.hpp
  Spec.hpp
  TestFanIn2LinkPolicy.hpp
  TestNode.hpp
  UniformLinkPolicy.hpp
  YAMLUtils.hpp
)
