include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libalgorithms_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libalgorithms
  bit_history.cpp
  Cell.cpp
  Cells4.cpp
  classifier_result.cpp
  CondProbTable.cpp
  fast_cla_classifier.cpp
  gaborNode.cpp
  Grouper.cpp
  imageSensorLite.cpp
  InSynapse.cpp
  linear.cpp
  OutSynapse.cpp
  Segment.cpp
  SegmentUpdate.cpp
  SparsePooler.cpp
  SpatialPooler.cpp
  svm.cpp
  arrayBuffer.hpp
  bit_history.hpp
  Cell.hpp
  Cells2.hpp
  Cells4.hpp
  classifier_result.hpp
  CondProbTable.hpp
  fast_cla_classifier.hpp
  FDRCSpatial.hpp
  FDRSpatial.hpp
  gaborNode.hpp
  Grouper.hpp
  Grouper_t.hpp
  imageSensorLite.hpp
  InSynapse.hpp
  linear.hpp
  OutSynapse.hpp
  scanning.hpp
  Segment.hpp
  SegmentUpdate.hpp
  SparsePooler.hpp
  SparsePooler_t.hpp
  SpatialPooler.hpp
  SpatialPooler_t.hpp
  svm.hpp
  svm_t.hpp
  Zeta1Grouper_t.hpp
)
