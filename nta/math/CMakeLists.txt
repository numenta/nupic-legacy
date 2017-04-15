include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

# TODO: set(libmath_a_CCASFLAGS "${NTA_CXXFLAGS} ${nta_platform_asflags}")

add_library(libmath
  SparseMatrixAlgorithms.cpp
  stl_io.cpp
  AlignedAlloc.hpp
  array2D.hpp
  array_algo.hpp
  convolution.hpp
  DenseMatrix.hpp
  Domain.hpp
  erosion.hpp
  functions.hpp
  GraphAlgorithms.hpp
  Index.hpp
  math.hpp
  NearestNeighbor.hpp
  RandomNumberGenerator.hpp
  rotation.hpp
  Set.hpp
  SparseBinaryMatrix.hpp
  SparseMatrix.hpp
  SparseMatrix01.hpp
  SparseMatrixAlgorithms.hpp
  SparseR3FTensor.hpp
  SparseRLEMatrix.hpp
  SparseTensor.hpp
  StatisticsHistogram.hpp
  stl_io.hpp
  TAM.hpp
  types.hpp
  utils.hpp
)
