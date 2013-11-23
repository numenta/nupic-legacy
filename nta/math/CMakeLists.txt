include("${CMAKE_SOURCE_DIR}/CMakeInclude.txt")

set(CMAKE_CXX_FLAGS "${NTA_CXXFLAGS} -DNUPIC2")

add_library(libmath
  SparseMatrixAlgorithms.cpp
  stl_io.cpp
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
  rotation.hpp
  Set.hpp
  SparseBinaryMatrix.hpp
  SparseMatrix.hpp
  SparseMatrix01.hpp
  SparseMatrixAlgorithms.hpp
  SparseRLEMatrix.hpp
  SparseTensor.hpp
  stl_io.hpp
  TAM.hpp
  types.hpp
  utils.hpp
)
