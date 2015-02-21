/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

%{
#include <nupic/math/SparseMatrix.hpp>
#include <nupic/math/SparseMatrixAlgorithms.hpp>
#include <nupic/math/SparseBinaryMatrix.hpp>
#include <nupic/math/NearestNeighbor.hpp>
#include <nupic/proto/SparseMatrixProto.capnp.h>
#include <nupic/proto/SparseBinaryMatrixProto.capnp.h>
#include <py_support/PyCapnp.hpp>
#include <py_support/NumpyVector.hpp>
#include <py_support/PythonStream.hpp>

%}  

//--------------------------------------------------------------------------------
// Global epsilon
//--------------------------------------------------------------------------------
%inline { 

  nupic::Real getGlobalEpsilon() { return nupic::Epsilon; }

}

%ignore nupic::Domain::operator[];
%ignore print;

//--------------------------------------------------------------------------------
%include <nupic/math/Math.hpp>
%include <nupic/math/Domain.hpp>
%include <nupic/math/SparseMatrix.hpp>
%include <nupic/math/SparseMatrixAlgorithms.hpp>
%include <nupic/math/SparseBinaryMatrix.hpp>
 //%include <nupic/math/SparseRLEMatrix.hpp>

%template(_Domain32) nupic::Domain<nupic::UInt32>;
%template(_Domain2D32) nupic::Domain2D<nupic::UInt32>;
%template(_DistanceToZero32) nupic::DistanceToZero<nupic::Real32>;

//%template(_DistanceToZero64) nupic::DistanceToZero<nupic::Real64>;
//%template(_DistanceToZero128) nupic::DistanceToZero<nupic::Real128>;

%template(_SparseMatrix32) nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >;
//%template(_SparseMatrix64) nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >;
//%template(_SparseMatrix128) nupic::SparseMatrix<nupic::UInt32,nupic::Real128,nupic::Int32,nupic::Real128,nupic::DistanceToZero<nupic::Real128 > >;

//%template(_SM_01_32_16) nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt16>;
%template(_SM_01_32_32) nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt32>;

//%template(_SM_RLE_16_8) nupic::SparseRLEMatrix<nupic::UInt16, unsigned char>;
//%template(_SM_RLE_16_16) nupic::SparseRLEMatrix<nupic::UInt16, nupic::UInt16>;
//%template(_SM_RLE_32_32) nupic::SparseRLEMatrix<nupic::UInt32, nupic::Real32>;

//--------------------------------------------------------------------------------
%define SparseMatrix_(N1, N2, N3, N4)

#define SparseMatrix ## N2 nupic::SparseMatrix<nupic::UInt ## N1,nupic::Real ## N2,nupic::Int ## N3,nupic::Real ## N4,nupic::DistanceToZero<nupic::Real ## N2 > >

%extend nupic::SparseMatrix<nupic::UInt ## N1,nupic::Real ## N2,nupic::Int ## N3,nupic::Real ## N4,nupic::DistanceToZero<nupic::Real ## N2 > >
{
%pythoncode %{

allowed_scalar_types = ['int', 'float', 'float32', 'float64', 'float128']

def __init__(self, *args): 
  """
  Constructs a new SparseMatrix from the following available arguments:
                SparseMatrix(): An empty sparse matrix with 0 rows and columns.
    SparseMatrix(nrows, ncols): A zero sparse matrix with the 
                                specified rows and columns.
    SparseMatrix(SparseMatrix): Copies an existing sparse matrix.
          SparseMatrix(string): Loads a SparseMatrix from its serialized form.
     SparseMatrix(numpy.array): Loads a SparseMatrix from a numpy array.
     SparseMatrix([[...],[...]]): Creates an array from a list of lists.
  """
  serialized,dense,from01,fromstr3f = None,None,False,False
  fromSpecRowCols = False
    
  if (len(args) == 3) and isinstance(args[0], _SparseMatrix32):
    fromSpecRowCols = True

  if (len(args) == 1):
    if isinstance(args[0], basestring):
      serialized = args[0]
      args = tuple() 
    elif isinstance(args[0], numpy.ndarray):
      dense = args[0] 
      args = tuple() 
    elif hasattr(args[0], '__iter__'):
      dense = args[0] 
      args = tuple() 
    elif isinstance(args[0], _SM_01_32_32): #or isinstance(args[0], _SM_01_32_16):
      from01 = True

  if from01 or fromSpecRowCols:	
    this = _MATH.new__SparseMatrix ## N2(1,1)
  else:
    this = _MATH.new__SparseMatrix ## N2(*args)
    
  try: 
    self.this.append(this)
  except: 
    self.this = this

  if serialized is not None: 
    s = serialized.split(None, 1)
    self.fromPyString(serialized) 
    
  elif dense is not None:
    self.fromDense(numpy.asarray(dense,dtype=GetNumpyDataType('NTA_Real' + #N2))) 
    
  elif from01:
    nz_i,nz_j = args[0].getAllNonZeros(True)
    nz_ones = numpy.ones((len(nz_i)))
    self.setAllNonZeros(args[0].nRows(), args[0].nCols(), nz_i, nz_j, nz_ones)    
    
  elif fromstr3f:
    nz_i,nz_j,nz_v = args[1].getAllNonZeros(args[0], True)
    self.setAllNonZeros(args[1].nRows(), args[1].nCols(), nz_i,nz_j,nz_v)  
    
  elif fromSpecRowCols:
    if args[2] == 0:
      self.__initializeWithRows(args[0], args[1])
    elif args[2] == 1:
      self.__initializeWithCols(args[0], args[1])

# def _fixSlice(self, dim, ub):
#   """Used internally to fill out blank fields in slicing records."""
#   start = dim.start
#   if start is None: start = 0
#   elif start < 0: start += ub
#   stop = dim.stop
#   if stop is None: stop = ub
#   elif stop < 0: stop += ub
#   return slice(start, stop, 1)

# def _getDomain(self, key, bounds):
#   """Used internally to convert a list of slices to a valid Domain."""
#   slices = [None] * len(bounds)
#   cur = 0
#   hasEllipsis = False
#   for dim in key:
#     if dim is Ellipsis:
#       hasEllipsis = True
#       toFill = len(bounds) - len(key) + 1
#       if toFill > 0:
#         for j in xrange(toFill-1):
#           slices[cur] = slice(0, bounds[cur], 1)
#           cur += 1
#         slices[cur] = slice(0, bounds[cur], 1)
#     elif isinstance(dim, slice): 
#       slices[cur] = self._fixSlice(dim, bounds[cur])
#     else: slices[cur] = slice(dim, dim, 0)
#     cur += 1
#   return Domain([x.start for x in slices], [x.stop for x in slices])

# def getSliceWrap(self, key):
#   bounds = [ self.nRows(), self.nCols() ]                                                    d = self._getDomain(key, bounds)
#   return self.getSlice(d[0].getLB(), d[0].getUB(), d[1].getLB(), d[1].getUB())
          
# def setSliceWrap(self, key, value):
#   bounds = [ self.nRows(), self.nCols() ]                                                    d = self._getDomain(key, bounds)
#   return self.setSlice(d[0].getLB(), d[1].getLB(), value)

# def __getitem__(self, key):
#   if isinstance(key, tuple):
#     hasSlices = False
#     for dim in key:
#       if (dim is Ellipsis) or isinstance(dim, slice):
#         hasSlices = True
#         break
#     if hasSlices: return self.getSliceWrap(key)
#     else: return _MATH.SparseMatrix ## N2_get(self, key)
#   elif (key is Ellipsis) or isinstance(key, slice):
#     return self.getSliceWrap((key,))
#   else:
#     return _MATH.SparseMatrix ## N2_get(self, (key,))

# def __setitem__(self, key, value):
#   if isinstance(key, tuple):
#     hasSlices = False
#     for dim in key:
#       if isinstance(dim, slice): hasSlices = True
#     if hasSlices: return self.setSliceWrap(key, value)
#     else: return _MATH.SparseMatrix ## N2_set(self, key, value)
#   elif (key is Ellipsis) or isinstance(key, slice):
#     return self.setSliceWrap((key,), value)
#   else:
#     return _MATH.SparseMatrix ## N2_set(self, (key,), value)

def setRowFromDense(self, row, x):
  self._setRowFromDense(row, x)

def __getitem__(self, index):
  return numpy.float ## N2(self.get(index[0], index[1]))

def __setitem__(self, index, value):
  self.set(index[0], index[1], value)

def __getstate__(self):
  """
  Used by the pickling mechanism to get state that will be saved.
  """
  return (self.toPyString(),)

def __setstate__(self,tup):
  """
  Used by the pickling mechanism to restore state that was saved.
  """
  self.this = _MATH.new__SparseMatrix ## N2(1, 1)
  self.thisown = 1
  self.fromPyString(tup[0])

def __str__(self):
  return self.toDense().__str__()

def _setShape(self, *args):
  if len(args) == 1:
    self.resize(*(args[0]))
  elif len(args) == 2:
    self.resize(*args)
  else:
    raise RuntimeError("Error: setShape(rows, cols) or setShape((rows, cols))")
shape = property(fget=lambda self: (self.nRows(), self.nCols()), fset=_setShape,
    doc="rows, cols")

def getTransposed(self):
  result = self.__class__()
  self.transpose(result)
  return result

def __neg__(self):
  result = _SparseMatrix ## N2(self)
  result.negate()
  return result

def __abs__(self):
  result = _SparseMatrix ## N2(self)
  result.abs()
  return result

def __iadd__(self, other):
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    self.__add(other)
  elif t == 'ndarray':
    self.add(_SparseMatrix ## N2(other))
  elif t == '_SparseMatrix' + #N2:
    self.add(other)
  else:
    raise Exception("Can't use type: " + t)
  return self

def __add__(self, other):
  arg = None
  result = _SparseMatrix ## N2(self)
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    result.__add(other)
  elif t == 'ndarray':
    result.add(_SparseMatrix ## N2(other))
  elif t == '_SparseMatrix' + #N2:
    result.add(other)
  else:
    raise Exception("Can't use type: " + t)
  return result

def __radd__(self, other):
  return self.__add__(other)

def __isub__(self, other):
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    self.__subtract(other)
  elif t == 'ndarray':
    self.subtract(_SparseMatrix ## N2(other))
  elif t == '_SparseMatrix' + #N2:
    self.subtract(other)                      
  else:
    raise Exception("Can't use type: " + t)
  return self

def __sub__(self, other):
  result = _SparseMatrix ## N2(self)
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    result.__subtract(other)
  elif t == 'ndarray':
    result.subtract(_SparseMatrix ## N2(other))
  elif t == '_SparseMatrix' + #N2:
    result.subtract(other)     
  else:
    raise Exception("Can't use type: " + t)
  return result

def __rsub__(self, other):
  return self.__sub__(other)

def __imul__(self, other):
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    self.__multiply(other)
  elif t == '_SparseMatrix' + #N2:
    self.multiply(other)     
  else:
    raise Exception("Can't use type: " + t)
  return self

def __mul__(self, other):
  t = type(other).__name__
  arg = other
  result = None
  if t in self.allowed_scalar_types:
    result = _SparseMatrix ## N2(self)
    result.__multiply(arg)
  elif t == 'ndarray':
    if arg.ndim == 1:
      result = numpy.array(self.rightVecProd(arg))
    elif arg.ndim == 2:
      arg = _SparseMatrix ## N2(other)
      result = _SparseMatrix ## N2()
      self.multiply(arg, result)
    else:
      raise Exception("Wrong ndim: " + str(arg.ndim))
  elif t == '_SparseMatrix' + #N2:
    if other.nCols() == 1:
      if self.nRows() == 1:
        result = self.rightVecProd(other.getCol(0))[0]
      else:
        result_list = self.rightVecProd(other.getCol(0))
        result = _SparseMatrix ## N2(self.nRows(), 0)
        result.addCol(result_list)
    else:
      result = _SparseMatrix ## N2()
      self.multiply(arg, result)
  else:
    raise Exception("Can't use type: " + t + " for multiplication")
  return result

def __rmul__(self, other):
  t = type(other).__name__
  arg = other
  result = None
  if t in self.allowed_scalar_types:
    result = _SparseMatrix ## N2(self)
    result.__multiply(arg)
  elif t == 'ndarray':
    if arg.ndim == 1:
      result = numpy.array(self.leftVecProd(arg))
    elif arg.ndim == 2:
      arg = _SparseMatrix ## N2(other)
      result = _SparseMatrix ## N2()
      arg.multiply(self, result)
    else:
      raise Exception("Wrong ndim: " + str(arg.ndim))
  elif t == '_SparseMatrix' + #N2:
    if other.nRows() == 1:
      if self.nCols() == 1:
        result = self.leftVecProd(other.getRow(0))[0]
      else:
        result_list = self.leftVecProd(other.getRow(0))
        result = _SparseMatrix ## N2(self.nCols(), 0)
        result.addRow(result_list)
    else:
      result = _SparseMatrix ## N2()
      arg.multiply(self, result)
  else:
    raise Exception("Can't use type: " + t + " for multiplication")
  return result

def __idiv__(self, other):
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    self.__divide(other)
  else:
    raise Exception("Can't use type: " + t)
  return self

def __div__(self, other):
  t = type(other).__name__
  if t in self.allowed_scalar_types:
    result = _SparseMatrix ## N2(self)
    result.__divide(other)       
    return result
  else:
    raise Exception("Can't use type: " + t)
%}
                         
  void __initializeWithRows(const SparseMatrix ##N2& other, PyObject* py_take)
  {
    nupic::NumpyVectorT<nupic::UInt32> take(py_take);
    self->initializeWithRows(other, take.begin(), take.end());
  }
  
  void __initializeWithCols(const SparseMatrix ##N2& other, PyObject* py_take)
  {
    nupic::NumpyVectorT<nupic::UInt32> take(py_take);
    self->initializeWithCols(other, take.begin(), take.end());
  }

  void __add(PyObject* val)     
  {
    self->add(nupic::convertToValueType<nupic::Real ## N2>(val));
  }
  
  void __multiply(PyObject* val)
  {
    self->multiply(nupic::convertToValueType<nupic::Real ## N2>(val));
  }

  void __subtract(PyObject* val)
  {
    self->subtract(nupic::convertToValueType<nupic::Real ## N2>(val));
  }
           
  void __divide(PyObject* val)
  {
    self->divide(nupic::convertToValueType<nupic::Real ## N2>(val));
  }

  void copy(const SparseMatrix ## N2& other)
  {
    self->copy(other);
  }

  void fromDense(PyObject *matrix)
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(matrix);
    self->fromDense(m.rows(), m.columns(), m.addressOf(0, 0));
  }

  PyObject *toDense() const 
  {
    int dims[] = { static_cast<int>(self->nRows()), static_cast<int>(self->nCols()) };
    nupic::NumpyMatrixT<nupic::Real ## N2> out(dims);
    self->toDense(out.addressOf(0, 0));
    return out.forPython();
  }

  void _setRowFromDense(nupic::UInt ## N1 row, PyObject* py_row)
  { 
    nupic::NumpyVectorT<nupic::Real ## N2> row_data(py_row);
    self->setRowFromDense(row, row_data.begin());
  }

  void setRowFromSparse(nupic::UInt ## N1 row, PyObject* py_ind, PyObject* py_nz)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> ind(py_ind);
    nupic::NumpyVectorT<nupic::Real ## N2> nz(py_nz);
    self->setRowFromSparse(row, ind.begin(), ind.end(), nz.begin());
  }

  inline void binarySaveToFile(const std::string& filename)
  {
    std::ofstream save_file(filename.c_str());
    self->toBinary(save_file);
    save_file.close();
  }

  inline void binaryLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromBinary(load_file);
    load_file.close();
  }

  inline void write(PyObject* pyBuilder) const
  {
    SparseMatrixProto::Builder proto =
        nupic::getBuilder<SparseMatrixProto>(pyBuilder);
    self->write(proto);
  }

  inline void read(PyObject* pyReader)
  {
    SparseMatrixProto::Reader proto =
        nupic::getReader<SparseMatrixProto>(pyReader);
    self->read(proto);
  }

  void addRow(PyObject *row)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> v(row);
    self->addRow(v.begin());
  }

  void addRowNZ(PyObject *ind, PyObject *nz, bool zero_permissive =false)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> cpp_ind(ind);
    nupic::NumpyVectorT<nupic::Real ## N2> cpp_nz(nz);
    self->addRow(cpp_ind.begin(), cpp_ind.end(), cpp_nz.begin(),
		 zero_permissive);
  }

  void addCol(PyObject *col)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> cpp_col(col);
    self->addCol(cpp_col.begin());
  }

  void addColNZ(PyObject *ind, PyObject *nz)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> cpp_ind(ind);
    nupic::NumpyVectorT<nupic::Real ## N2> cpp_nz(nz);
    self->addCol(cpp_ind.begin(), cpp_ind.end(), cpp_nz.begin());
  }
  
  void deleteRows(PyObject *rowIndices)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> cpp_rowIndices(rowIndices);
    self->deleteRows(cpp_rowIndices.begin(), cpp_rowIndices.end());
  }
  
  void deleteCols(PyObject *colIndices)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> cpp_colIndices(colIndices);
    self->deleteCols(cpp_colIndices.begin(), cpp_colIndices.end());
  }

  PyObject* getRow(nupic::UInt ## N1 row) const
  {
    const nupic::UInt ## N1 ncols = self->nCols();
    nupic::NumpyVectorT<nupic::Real ## N2> dense_row(ncols);
    self->getRowToDense(row, dense_row.begin());
    return dense_row.forPython();
  }

  PyObject* getCol(nupic::UInt ## N1 col) const
  {
    const nupic::UInt ## N1 nrows = self->nRows();
    nupic::NumpyVectorT<nupic::Real ## N2> dense_col(nrows);
    self->getColToDense(col, dense_col.begin());
    return dense_col.forPython();
  }

  PyObject* getDiagonal() const
  {
    const nupic::UInt ## N1 nrows = self->nRows();
    nupic::NumpyVectorT<nupic::Real ## N2> diag(nrows);
    self->getDiagonalToDense(diag.begin());
    return diag.forPython();
  }

  PyObject* rowNonZeros(nupic::UInt ## N1 row) const
  {
    const nupic::UInt ## N1 n = self->nNonZerosOnRow(row);
    std::vector<nupic::UInt ## N1> ind(n);
    nupic::NumpyVectorT<nupic::Real ## N2> val(n);
    self->getRowToSparse(row, ind.begin(), val.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt ## N1 ## Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  PyObject* rowNonZeroIndices(nupic::UInt ## N1 row) const
  {
    const nupic::UInt ## N1 n = self->nNonZerosOnRow(row);
    nupic::NumpyVectorT<nupic::UInt ## N1> ind(n);
    self->getRowIndicesToSparse(row, ind.begin());
    return ind.forPython();
  }

  PyObject* colNonZeros(nupic::UInt ## N1 col) const
  {
    const nupic::UInt ## N1 n = self->nNonZerosOnCol(col);
    std::vector<nupic::UInt ## N1> ind(n);
    nupic::NumpyVectorT<nupic::Real ## N2> val(n);
    self->getColToSparse(col, ind.begin(), val.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt ## N1 ## Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  PyObject* nonZeroRows() const
  {
    const nupic::UInt ## N1 nNonZeroRows = self->nNonZeroRows();
    nupic::NumpyVectorT<nupic::UInt ## N1> nzRows(nNonZeroRows);
    self->nonZeroRows(nzRows.begin());
    return nzRows.forPython();
  }

  PyObject* zeroRows() const
  {
    const nupic::UInt ## N1 nZeroRows = self->nZeroRows();
    nupic::NumpyVectorT<nupic::UInt ## N1> zRows(nZeroRows);
    self->zeroRows(zRows.begin());
    return zRows.forPython();
  }

  PyObject* nonZeroCols() const
  {
    const nupic::UInt ## N1 nNonZeroCols = self->nNonZeroCols();
    nupic::NumpyVectorT<nupic::UInt ## N1> nzCols(nNonZeroCols);
    self->nonZeroCols(nzCols.begin());
    return nzCols.forPython();
  }

  PyObject* zeroCols() const
  {
    const nupic::UInt ## N1 nZeroCols = self->nZeroCols();
    nupic::NumpyVectorT<nupic::UInt ## N1> zCols(nZeroCols);
    self->zeroCols(zCols.begin());
    return zCols.forPython();
  }

  PyObject* zeroRowAndCol() const
  {
    std::vector<nupic::UInt ## N1> zrc;
    nupic::UInt ## N1 c = self->zeroRowAndCol(std::back_inserter(zrc));
    nupic::NumpyVectorT<nupic::UInt ## N1> toReturn(c);
    std::copy(zrc.begin(), zrc.end(), toReturn.begin());
    return toReturn.forPython();
  }

  void setElements(PyObject* py_i, PyObject* py_j, PyObject* py_v)
  {
    const nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    const nupic::NumpyVectorT<nupic::Real ## N2> v(py_v);
    self->setElements(i.begin(), i.end(), j.begin(), v.begin());
  }

  PyObject* getElements(PyObject* py_i, PyObject* py_j) const
  {
    const nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    nupic::NumpyVectorT<nupic::Real ## N2> v(i.size());
    self->getElements(i.begin(), i.end(), j.begin(), v.begin());
    return v.forPython();
  }

  // Sets on the outer product of the passed ranges.
  void setOuter(PyObject* py_i, PyObject* py_j, PyObject* py_v)
  {
    const nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    const nupic::NumpyMatrixT<nupic::Real ## N2> v(py_v);
    self->setOuter(i.begin(), i.end(), j.begin(), j.end(), v);
  }

  // Get on the outer products of the passed ranges.
  SparseMatrix ## N2 getOuter(PyObject* py_i, PyObject* py_j) const
  {
    const nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    SparseMatrix ## N2 v(i.size(), j.size());
    self->getOuter(i.begin(), i.end(), j.begin(), j.end(), v);
    return v;
  }

  // Returns the positions and values of all the non-zeros stored
  // in this matrix. The result can be either three lists ((i), (j), (v))
  // or one list of triples (i,j,v).
  PyObject* getAllNonZeros(bool three_lists =false) const
  {
    const nupic::UInt ## N1 nnz = self->nNonZeros();
    nupic::NumpyVectorT<nupic::UInt ## N1> rows(nnz), cols(nnz);
    nupic::NumpyVectorT<nupic::Real ## N2> vals(nnz);

    self->getAllNonZeros(rows.begin(), cols.begin(), vals.begin());

    PyObject* toReturn = NULL;

    if (!three_lists) {
      // Return one list of triples
      toReturn = PyTuple_New(nnz);
      for (nupic::UInt ## N1 i = 0; i != nnz; ++i) {
	PyObject* tuple = nupic::createTriplet ## N1(rows.get(i), cols.get(i), vals.get(i));
	PyTuple_SET_ITEM(toReturn, i, tuple);
      }
    } else {
      // Return three lists
      toReturn = PyTuple_New(3);
      PyTuple_SET_ITEM(toReturn, 0, rows.forPython());
      PyTuple_SET_ITEM(toReturn, 1, cols.forPython());
      PyTuple_SET_ITEM(toReturn, 2, vals.forPython());
    }

    return toReturn;
  }

  void setAllNonZeros(nupic::UInt ## N1 nrows, nupic::UInt ## N1 ncols,
		      PyObject* py_i, PyObject* py_j, PyObject* py_v, bool sorted =true)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    nupic::NumpyVectorT<nupic::Real ## N2> v(py_v);
    self->setAllNonZeros(nrows, ncols,
			 i.begin(), i.end(),
			 j.begin(), j.end(),
			 v.begin(), v.end(),
			 sorted);
  }

  PyObject* getNonZerosInBox(nupic::UInt ## N1 row_begin, nupic::UInt ## N1 row_end,
			     nupic::UInt ## N1 col_begin, nupic::UInt ## N1 col_end) const
  {
    std::vector<nupic::UInt ## N1> rows, cols;
    std::vector<nupic::Real ## N2> vals;
    self->getNonZerosInBox(row_begin, row_end, col_begin, col_end,
			   std::back_inserter(rows),
			   std::back_inserter(cols),
			   std::back_inserter(vals));
    PyObject* toReturn = PyList_New(rows.size());
    for (nupic::UInt ## N1 i = 0; i != rows.size(); ++i) {
      PyObject* tuple = nupic::createTriplet ## N1(rows[i], cols[i], vals[i]);
      PyList_SET_ITEM(toReturn, i, tuple);
    }
    return toReturn;
  }

  PyObject* tolist() const
  {
    const nupic::UInt ## N1 nnz = self->nNonZeros();
    std::vector<nupic::UInt ## N1> rows(nnz), cols(nnz);
    nupic::NumpyVectorT<nupic::Real ## N2> vals(nnz);
    self->getAllNonZeros(rows.begin(), cols.begin(), vals.begin());

    PyObject* ind_list = PyTuple_New(nnz);
    for (nupic::UInt32 i = 0; i != nnz; ++i) {
      PyObject* idx = PyTuple_New(2);
      PyTuple_SET_ITEM(idx, 0, PyInt_FromLong(rows[i]));
      PyTuple_SET_ITEM(idx, 1, PyInt_FromLong(cols[i]));
      PyTuple_SET_ITEM(ind_list, i, idx);
    }
    PyObject* toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, ind_list);
    PyTuple_SET_ITEM(toReturn, 1, vals.forPython());
    return toReturn;
  }

  void setSlice(nupic::UInt ## N1 i_begin, nupic::UInt ## N1 j_begin,
		const SparseMatrix ## N2& other)
  {
    self->setSlice(i_begin, j_begin, other);
  }

  void setSlice(nupic::UInt ## N1 i_begin, nupic::UInt ## N1 j_begin,
		PyObject* py_other)
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> other(py_other);
    self->setSlice(i_begin, j_begin, other);
  }

  SparseMatrix ## N2
    getSlice(nupic::UInt ## N1 i_begin, nupic::UInt ## N1 i_end,
	     nupic::UInt ## N1 j_begin, nupic::UInt ## N1 j_end) const
  {
    SparseMatrix ## N2 other(i_end - i_begin, j_end - j_begin);
    self->getSlice(i_begin, i_end, j_begin, j_end, other);
    return other;
  }

  SparseMatrix ## N2
    getSlice2(nupic::UInt ## N1 i_begin, nupic::UInt ## N1 i_end,
	     nupic::UInt ## N1 j_begin, nupic::UInt ## N1 j_end) const
  {
    SparseMatrix ## N2 other(i_end - i_begin, j_end - j_begin);
    self->getSlice2(i_begin, i_end, j_begin, j_end, other);
    return other;
  }

  inline void setRowsToZero(PyObject* py_rows)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> rows(py_rows);
    self->setRowsToZero(rows.begin(), rows.end());
  }

  inline void setColsToZero(PyObject* py_cols)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> cols(py_cols);
    self->setColsToZero(cols.begin(), cols.end());
  }

  inline void setDiagonal(PyObject* py_v)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> v(py_v);
    self->setDiagonal(v.begin());
  }

  void incrementOnOuterWNZ(PyObject* py_i, PyObject* py_j, nupic::Real ## N2 delta=1)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    self->incrementOnOuterWNZ(i.begin(), i.end(), j.begin(), j.end(), delta);
  }

  void incrementOnOuterWNZWThreshold(PyObject* py_i, PyObject* py_j, 
                                     nupic::Real ## N2 threshold, nupic::Real ## N2 delta=1)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> i(py_i), j(py_j);
    self->incrementOnOuterWNZWThreshold(i.begin(), i.end(), j.begin(), j.end(), 
                                        threshold, delta);
  }

  // Returns the number of non-zeros per row, for all rows
  PyObject* nNonZerosPerRow() const
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> nnzpr(self->nRows());
    self->nNonZerosPerRow(nnzpr.begin());
    return nnzpr.forPython();
  }

  // Returns the number of non-zeros per col, for all cols
  PyObject* nNonZerosPerCol() const
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> nnzpc(self->nCols());
    self->nNonZerosPerCol(nnzpc.begin());
    return nnzpc.forPython();
  }

  PyObject* rowBandwidths() const
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> nnzpc(self->nRows());
    self->rowBandwidths(nnzpc.begin());
    return nnzpc.forPython();
  }

  PyObject* colBandwidths() const
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> nnzpc(self->nCols());
    self->colBandwidths(nnzpc.begin());
    return nnzpc.forPython();
  }

  SparseMatrix ## N1
    nNonZerosPerBox(PyObject* box_i, PyObject* box_j) const
    {
      nupic::NumpyVectorT<nupic::UInt ## N1> bounds_i(box_i);
      nupic::NumpyVectorT<nupic::UInt ## N1> bounds_j(box_j);
      SparseMatrix ## N1 result(bounds_i.size(), bounds_j.size());
      self->nNonZerosPerBox(bounds_i.begin(), bounds_i.end(),
			    bounds_j.begin(), bounds_j.end(), 
			    result);
      return result;
    }

  PyObject* max() const
  {
    nupic::UInt ## N1 max_row, max_col;
    nupic::Real ## N2 max_val;
    self->max(max_row, max_col, max_val);
    return nupic::createTriplet ## N1(max_row, max_col, max_val);
  }

  PyObject* min() const
  {
    nupic::UInt ## N1 min_row, min_col;
    nupic::Real ## N2 min_val;
    self->min(min_row, min_col, min_val);
    return nupic::createTriplet ## N1(min_row, min_col, min_val);
  }

  PyObject* rowMin(nupic::UInt ## N1 row_index) const
  {
    nupic::UInt ## N1 idx;
    nupic::Real ## N2 min_val;
    self->rowMin(row_index, idx, min_val);
    return nupic::createPair ## N1(idx, min_val);
  }
	
  PyObject* rowMax(nupic::UInt ## N1 row_index) const
  {
    nupic::UInt ## N1 idx;
    nupic::Real ## N2 max_val;
    self->rowMax(row_index, idx, max_val);
    return nupic::createPair ## N1(idx, max_val);
  }
	
  PyObject* colMin(nupic::UInt ## N1 col_index) const
  {
    nupic::UInt ## N1 idx;
    nupic::Real ## N2 min_val;
    self->colMin(col_index, idx, min_val);
    return nupic::createPair ## N1(idx, min_val);
  }
	
  PyObject* colMax(nupic::UInt ## N1 row_index) const
  {
    nupic::UInt ## N1 idx;
    nupic::Real ## N2 max_val;
    self->colMax(row_index, idx, max_val);
    return nupic::createPair ## N1(idx, max_val);
  }

  PyObject* rowMax() const
  {
    nupic::UInt ## N1 n = self->nRows();
    std::vector<nupic::UInt ## N1> ind(n);
    nupic::NumpyVectorT<nupic::Real ## N2> val(n);
    self->rowMax(ind.begin(), val.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt ## N1 ## Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  PyObject* rowMin() const
  {
    nupic::UInt ## N1 n = self->nRows();
    std::vector<nupic::UInt ## N1> ind(n);
    nupic::NumpyVectorT<nupic::Real ## N2> val(n);
    self->rowMin(ind.begin(), val.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt ## N1 ## Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  PyObject* colMax() const
  {
    nupic::UInt ## N1 n = self->nCols();
    std::vector<nupic::UInt ## N1> ind(n);
    nupic::NumpyVectorT<nupic::Real ## N2> val(n);
    self->colMax(ind.begin(), val.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt ## N1 ## Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  PyObject* colMin() const
  {
    nupic::UInt ## N1 n = self->nCols();
    std::vector<nupic::UInt ## N1> ind(n);
    nupic::NumpyVectorT<nupic::Real ## N2> val(n);
    self->colMin(ind.begin(), val.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt ## N1 ## Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  PyObject* boxMin(nupic::UInt ## N1 begin_row, nupic::UInt ## N1 end_row,
		   nupic::UInt ## N1 begin_col, nupic::UInt ## N1 end_col) const
  {
    nupic::UInt ## N1 min_row, min_col;
    nupic::Real ## N2 min_val;
    self->boxMin(begin_row, end_row, begin_col, end_col, min_row, min_col, min_val);
    return nupic::createTriplet ## N1(min_row, min_col, min_val);
  }

  PyObject* boxMax(nupic::UInt ## N1 begin_row, nupic::UInt ## N1 end_row,
		   nupic::UInt ## N1 begin_col, nupic::UInt ## N1 end_col) const
  {
    nupic::UInt ## N1 max_row, max_col;
    nupic::Real ## N2 max_val;
    self->boxMax(begin_row, end_row, begin_col, end_col, max_row, max_col, max_val);
    return nupic::createTriplet ## N1(max_row, max_col, max_val);
  }

  PyObject* whereEqual(nupic::UInt ## N1 begin_row, nupic::UInt ## N1 end_row,
		       nupic::UInt ## N1 begin_col, nupic::UInt ## N1 end_col,
		       const nupic::Real ## N2& value) const
  {
    std::vector<nupic::UInt ## N1> rows, cols;
    self->whereEqual(begin_row, end_row, begin_col, end_col, value, 
		     std::back_inserter(rows), std::back_inserter(cols));

    PyObject* toReturn = PyTuple_New(rows.size());    

    for (size_t i = 0; i != rows.size(); ++i) {
      PyObject* p = PyTuple_New(2);
      PyTuple_SET_ITEM(p, 0, PyInt_FromLong(rows[i]));
      PyTuple_SET_ITEM(p, 1, PyInt_FromLong(cols[i]));
      PyTuple_SET_ITEM(toReturn, i, p);
    }

    return toReturn;
  }

  PyObject* whereGreater(nupic::UInt ## N1 begin_row, nupic::UInt ## N1 end_row,
			 nupic::UInt ## N1 begin_col, nupic::UInt ## N1 end_col,
			 const nupic::Real ## N2& value) const
  {
    std::vector<nupic::UInt ## N1> rows, cols;
    self->whereGreater(begin_row, end_row, begin_col, end_col, value, 
		       std::back_inserter(rows), std::back_inserter(cols));

    int dims[] = {static_cast<int>(rows.size()), 2};
    nupic::NumpyMatrixT<nupic::UInt ## N1> toReturn(dims);
    for (size_t i = 0; i != rows.size(); ++i) {  
      toReturn.set(i, 0, rows[i]);
      toReturn.set(i, 1, cols[i]);
    }
    return toReturn.forPython();

    /*
    PyObject* toReturn = PyTuple_New(rows.size());    
    for (size_t i = 0; i != rows.size(); ++i) {
      PyObject* p = PyTuple_New(2);
      PyTuple_SET_ITEM(p, 0, PyInt_FromLong(rows[i]));
      PyTuple_SET_ITEM(p, 1, PyInt_FromLong(cols[i]));
      PyTuple_SET_ITEM(toReturn, i, p);
    }

    return toReturn;
    */
  }

  PyObject* whereGreaterEqual(nupic::UInt ## N1 begin_row, nupic::UInt ## N1 end_row,
                              nupic::UInt ## N1 begin_col, nupic::UInt ## N1 end_col,
                              const nupic::Real ## N2& value) const
  {
    std::vector<nupic::UInt ## N1> rows, cols;
    self->whereGreaterEqual(begin_row, end_row, begin_col, end_col, value, 
                            std::back_inserter(rows), std::back_inserter(cols));
    
    
    int dims[] = {static_cast<int>(rows.size()), 2};
    nupic::NumpyMatrixT<nupic::UInt ## N1> toReturn(dims);
    for (size_t i = 0; i != rows.size(); ++i) {  
      toReturn.set(i, 0, rows[i]);
      toReturn.set(i, 1, cols[i]);
    }
    return toReturn.forPython();

    /*
    PyObject* toReturn = PyTuple_New(rows.size());    

    for (size_t i = 0; i != rows.size(); ++i) {
      PyObject* p = PyTuple_New(2);
      PyTuple_SET_ITEM(p, 0, PyInt_FromLong(rows[i]));
      PyTuple_SET_ITEM(p, 1, PyInt_FromLong(cols[i]));
      PyTuple_SET_ITEM(toReturn, i, p);
    }
    return toReturn;
    */

  }

  nupic::UInt32 countWhereGreaterOrEqual(nupic::UInt ## N1 begin_row, nupic::UInt ## N1 end_row,
                                       nupic::UInt ## N1 begin_col, nupic::UInt ## N1 end_col,
                                       const nupic::Real ## N2& value) const
  {
    std::vector<nupic::UInt ## N1> rows, cols;
    return self->countWhereGreaterEqual(begin_row, end_row, begin_col, end_col, value);
  }

  void permuteRows(PyObject* py_permutation)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> p(py_permutation);
    self->permuteRows(p.begin());
  }

  void permuteCols(PyObject* py_permutation)
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> p(py_permutation);
    self->permuteCols(p.begin());
  }

  PyObject* rowSums() const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> m(self->nRows());
    self->rowSums(m.begin());
    return m.forPython();
  }

  PyObject* colSums() const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> m(self->nCols());
    self->colSums(m.begin());
    return m.forPython();
  }

  PyObject* addRows(PyObject* whichRows) const 
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> indicator(whichRows);
    nupic::NumpyVectorT<nupic::Real ## N2> res(self->nCols());
    self->addRows(indicator.begin(), indicator.end(), res.begin(), res.end());
    return res.forPython();
  }

  PyObject* addListOfRows(PyObject* py_whichRows) const 
  {
    nupic::NumpyVectorT<nupic::UInt ## N1> whichRows(py_whichRows);
    nupic::NumpyVectorT<nupic::Real ## N2> res(self->nCols());
    self->addListOfRows(whichRows.begin(), whichRows.end(), res.begin(), res.end());
    return res.forPython();
  }

  PyObject* rowProds() const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> m(self->nRows());
    self->rowProds(m.begin());
    return m.forPython();
  }

  PyObject* colProds() const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> m(self->nCols());
    self->colProds(m.begin());
    return m.forPython();
  }

  PyObject* logRowSums() const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> m(self->nRows());
    self->logRowSums(m.begin(), m.end());
    return m.forPython();
  }

  PyObject* logColSums() const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> m(self->nCols());
    self->logColSums(m.begin(), m.end());
    return m.forPython();
  }

  void scaleRows(PyObject* py_s)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> s(py_s);
    self->scaleRows(s.begin());
  }

  void scaleCols(PyObject* py_s)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> s(py_s);
    self->scaleCols(s.begin());
  }

  void normalizeBlockByRows(PyObject* py_inds, 
			    nupic::Real ## N2 val=-1.0, nupic::Real ## N2 eps_n=1e-6)
  {
    nupic::NumpyVectorT<nupic::UInt ## N2> inds(py_inds);
    self->normalizeBlockByRows(inds.begin(), inds.end(), val, eps_n);
  }

  void normalizeBlockByRows_binary(PyObject* py_inds, 
				   nupic::Real ## N2 val=-1.0, nupic::Real ## N2 eps_n=1e-6)
  {
    nupic::NumpyVectorT<nupic::UInt ## N2> inds(py_inds);
    self->normalizeBlockByRows_binary(inds.begin(), inds.end(), val, eps_n);
  }

  void axby(nupic::UInt ## N1 row, nupic::Real ## N2 a, nupic::Real ## N2 b, PyObject *xIn)
  {
    PyArrayObject* x = (PyArrayObject*) xIn;
    nupic::Real ## N2* x_begin = (nupic::Real ## N2*)(x->data);
    self->axby(row, a, b, x_begin);
  }

  void axby(nupic::Real ## N2 a, nupic::Real ## N2 b, PyObject *xIn)
  {
    PyArrayObject* x = (PyArrayObject*) xIn;
    nupic::Real ## N2* x_begin = (nupic::Real ## N2*)(x->data);
    self->axby(a, b, x_begin);
  }

  // Computes the dot product of the given row with the given vector.
  nupic::Real ## N2 rightVecProd(nupic::UInt ## N1 row, PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    return self->rightVecProd(row, x.begin());
  }

  // Regular matrix vector multiplication, with allocation of the result.
  inline PyObject* rightVecProd(PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::Real ## N2> y(self->nRows());
    self->rightVecProd(x.begin(), y.begin());
    return y.forPython();
  }

  // Regular matrix vector multiplication, with allocation of the result.
  // Fast because doesn't go through NumpyVectorT and doesn't allocate
  // memory.
  inline void rightVecProd_fast(PyObject *xIn, PyObject *yOut) const
  {
    PyArrayObject* x = (PyArrayObject*) xIn;
    nupic::Real ## N2* x_begin = (nupic::Real ## N2*)(x->data);
    PyArrayObject* y = (PyArrayObject*) yOut;
    nupic::Real ## N2* y_begin = (nupic::Real ## N2*)(y->data);
    self->rightVecProd(x_begin, y_begin);
  }

  // Matrix vector product on the right side, only for some rows.
  PyObject* rightVecProd(PyObject* pyRows, PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::UInt ## N1> rows(pyRows);
    nupic::NumpyVectorT<nupic::Real ## N2> y(rows.size());
    self->rightVecProd(rows.begin(), rows.end(), x.begin(), y.begin());
    return y.forPython();
  }

  SparseMatrix ## N2 
    blockRightVecProd(nupic::UInt ## N1 block_size, PyObject* xIn) const
  {
    SparseMatrix ## N2 result;
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->blockRightVecProd(block_size, x.begin(), result);
    return result;
  }

  // Dot product of column col and vector xIn. 
  nupic::Real ## N2 leftVecProd(nupic::UInt ## N1 col, PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    return self->leftVecProd(col, x.begin());
  }

  // Vector matrix product on the left, i.e. dot product of xIn and 
  // each column of the matrix.
  PyObject* leftVecProd(PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::Real ## N2> y(self->nCols());
    self->leftVecProd(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* leftVecProd(PyObject* pyCols, PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::UInt ## N2> cols(pyCols);
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(cols.size());
    self->leftVecProd(cols.begin(), cols.end(), x.begin(), y.begin());
    return y.forPython();
  }

  // Binary search for the columns.
  PyObject* leftVecProd_binary(PyObject* pyCols, PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::UInt ## N2> cols(pyCols);
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(cols.size());
    self->leftVecProd_binary(cols.begin(), cols.end(), x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* rightDenseMatProd(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = self->nRows();
    nRowsCols[1] = m.nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    self->rightDenseMatProd(m,r);
    return r.forPython();
  }

  PyObject* rightDenseMatProdAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = self->nRows();
    nRowsCols[1] = m.nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    self->rightDenseMatProdAtNZ(m,r);
    return r.forPython();
  }

  PyObject* denseMatExtract(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = self->nRows();
    nRowsCols[1] = m.nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    self->denseMatExtract(m,r);
    return r.forPython();
  }

  PyObject* leftDenseMatProd(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecProd(m.begin(i), r.begin(i));
    return r.forPython();
  }

  void elementRowAdd(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementRowAdd(i, x.begin());
  }

  void elementRowSubtract(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementRowSubtract(i, x.begin());
  }

  void elementRowMultiply(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementRowMultiply(i, x.begin());
  }

  void elementRowDivide(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementRowDivide(i, x.begin());
  }

  void elementColAdd(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementColAdd(i, x.begin());
  }

  void elementColSubtract(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementColSubtract(i, x.begin());
  }

  void elementColMultiply(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementColMultiply(i, x.begin());
  }

  void elementColDivide(nupic::UInt ## N1 i, PyObject* xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    self->elementColDivide(i, x.begin());
  }

  void elementMultiply(PyObject* mIn)
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    self->elementMultiply(m.begin(0));
  }

  //--------------------------------------------------------------------------------
  // AtNZ operations, i.e. considering the sparse matrix as a 0/1 sparse matrix.
  //--------------------------------------------------------------------------------
  PyObject* rightVecProdAtNZ(PyObject* xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(self->nRows());
    self->rightVecProdAtNZ(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* leftVecProdAtNZ(PyObject* xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(self->nCols());
    self->leftVecProdAtNZ(x.begin(), y.begin());
    return y.forPython();
  }

  // Regular matrix vector multiplication, but assumes that all the non-zeros
  // in the SparseMatrix are 1, so that we can save computing the multiplications:
  // this routine just adds the values of xIn at the positions of the non-zeros
  // on each row. 
  inline PyObject* rightVecSumAtNZ(PyObject* xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::Real ## N2> y(self->nRows());
    self->rightVecSumAtNZ(x.begin(), y.begin());
    return y.forPython();
  }
  
  inline PyObject* 
    rightVecSumAtNZGtThreshold(PyObject* xIn, nupic::Real ## 32 threshold) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::Real ## N2> y(self->nRows());
    self->rightVecSumAtNZGtThreshold(x.begin(), y.begin(), threshold);
    return y.forPython();
  }

  // Regular matrix vector multiplication, without allocation of the result,
  // and assuming that the values of the non-zeros are always 1 in the 
  // sparse matrix, so that we can save computing multiplications explicitly.
  // Also fast because doesn't go through NumpyVectorT and doesn't allocate
  // memory.
  inline void rightVecSumAtNZ_fast(PyObject *xIn, PyObject *yOut) const
  {
    PyArrayObject* x = (PyArrayObject*) xIn;
    nupic::Real ## N2* x_begin = (nupic::Real ## N2*)(x->data);
    PyArrayObject* y = (PyArrayObject*) yOut;
    nupic::Real ## N2* y_begin = (nupic::Real ## N2*)(y->data);
    self->rightVecSumAtNZ(x_begin, y_begin);
  }

  // Regular matrix vector multiplication on the left side, assuming that the 
  // values of the non-zeros are all 1, so that we can save actually computing
  // the multiplications. Allocates the result.
  inline PyObject* leftVecSumAtNZ(PyObject* xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::Real ## N2> y(self->nCols());
    self->leftVecSumAtNZ(x.begin(), y.begin());
    return y.forPython();
  }

  // Regular matrix vector multiplication on the left, without allocation 
  // of the result, assuming that the values of the non-zeros are always 1 in the 
  // sparse matrix, so that we can save computing multiplications explicitly.
  // Also fast because doesn't go through NumpyVectorT and doesn't allocate
  // memory.
  inline void leftVecSumAtNZ_fast(PyObject *xIn, PyObject *yOut) const
  {
    PyArrayObject* x = (PyArrayObject*) xIn;
    nupic::Real ## N2* x_begin = (nupic::Real ## N2*)(x->data);
    PyArrayObject* y = (PyArrayObject*) yOut;
    nupic::Real ## N2* y_begin = (nupic::Real ## N2*)(y->data);
    self->leftVecSumAtNZ(x_begin, y_begin);
  }

   inline void
    rightVecSumAtNZGtThreshold_fast(PyObject* xIn, PyObject *yOut, nupic::Real ## 32 threshold) const
  {
    PyArrayObject* x = (PyArrayObject*) xIn;
    nupic::Real ## N2* x_begin = (nupic::Real ## N2*)(x->data);
    PyArrayObject* y = (PyArrayObject*) yOut;
    nupic::Real ## N2* y_begin = (nupic::Real ## N2*)(y->data);
    self->rightVecSumAtNZGtThreshold(x_begin, y_begin, threshold);
  }

  PyObject* rightDenseMatProdAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nRows();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->rightVecProdAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* leftDenseMatProdAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecProdAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* rightDenseMatSumAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nRows();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->rightVecSumAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* leftDenseMatSumAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecSumAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* rightDenseMatMaxAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nRows();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->rightVecMaxAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* leftDenseMatMaxAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real ## N2> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real ## N2> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecMaxAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* vecArgMaxAtNZ(PyObject *xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::UInt ## N1> y(self->nRows());
    self->vecArgMaxAtNZ(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* vecMaxAtNZ(PyObject *xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(self->nRows());
    self->vecMaxAtNZ(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* rowVecProd(PyObject* xIn, nupic::Real ## N2 lb =nupic::Epsilon) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(self->nRows());
    self->rowVecProd(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* vecMaxProd(PyObject *xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn), y(self->nRows());
    self->vecMaxProd(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* vecArgMaxProd(PyObject *xIn)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::UInt ## N1> y(self->nRows());
    self->vecArgMaxProd(x.begin(), y.begin());
    return y.forPython();
  }

  PyObject* getNonZerosSorted(nupic::Int n =-1, bool ascending_values =true) const
  {
    typedef nupic::ijv<nupic::UInt ## N1, nupic::Real ## N2> IJV;

    nupic::UInt ## N1 nnz = self->nNonZeros();
    nupic::UInt ## N1 N = n == -1 ? nnz : n;
    std::vector<IJV> ijvs(N);
    if (ascending_values)
      self->getNonZerosSorted(ijvs.begin(), N, IJV::greater_value());
    else
      self->getNonZerosSorted(ijvs.begin(), N, IJV::less_value());
    PyObject* toReturn = PyTuple_New(N);
    for (nupic::UInt ## N1 i = 0; i != N; ++i) {
      PyObject* tuple = 
	nupic::createTriplet ## N1(ijvs[i].i(), ijvs[i].j(), ijvs[i].v());
      PyTuple_SET_ITEM(toReturn, i, tuple);
    }
    return toReturn;
  }

  //--------------------------------------------------------------------------------
  PyObject* threshold(nupic::Real ## N2 threshold, bool getCuts=false)
  {
    if (!getCuts) {
      self->threshold(threshold);
      return NULL;
    } 

    std::vector<nupic::UInt ## N1> cut_i, cut_j;
    std::vector<nupic::Real ## N2> cut_nz;
    nupic::UInt ## N1 c = 0;
    c = self->threshold(threshold, 
			std::back_inserter(cut_i),
			std::back_inserter(cut_j),
			std::back_inserter(cut_nz));
    PyObject* toReturn = PyTuple_New(c);
    for (nupic::UInt ## N1 i = 0; i != c; ++i) {
      PyObject* tuple = nupic::createTriplet ## N1(cut_i[i], cut_j[i], cut_nz[i]);
      PyTuple_SET_ITEM(toReturn, i, tuple);
    }
    return toReturn;
  }

  //--------------------------------------------------------------------------------
  PyObject* toPyString() const
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  bool fromPyString(PyObject *s) 
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(s, &buf, &n); // Reference-neutral.
    if((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
      return true;
    }
    else {
      throw std::runtime_error("Failed to read SparseMatrix state from string.");
      return false;
    }
  }

  bool __eq__(const SparseMatrix ## N2& other) const
  { return (*self) == other; }
  bool __ne__(const SparseMatrix ## N2& other) const
  { return (*self) != other; }

} // End extend SparseMatrix 
%enddef // End def macro SparseMatrix_

//--------------------------------------------------------------------------------
SparseMatrix_(32, 32, 32, 64)
 //SparseMatrix_(32, 64, 32, 64)
//SparseMatrix_(64, 128, 64, 128)

%inline {

  /*
void _copyFrom__SparseMatrix64(
    const nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > &input,
    nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > &output
  )
{
  output.copy(input);
}

void _copyFrom__SparseMatrix32(
    const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > &input,
    nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > &output
  )
{
  output.copy(input);
}

void aX_plus_bX_elementMultiply_Y(
    double a,
    nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > &X,
    double b,
    const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > &Y
  )
{
  nupic::SparseMatrixAlgorithms::aX_plus_bX_elementMultiply_Y(a, X, b, Y);
}

void aX_plus_bX_elementMultiply_Y(
    double a,
    nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > &X,
    double b,
    const nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > &Y
  )
{
  nupic::SparseMatrixAlgorithms::aX_plus_bX_elementMultiply_Y(a, X, b, Y);
}
  */

PyObject* 
kthroot_product(const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > & sm, nupic::UInt32 segment_size, PyObject* xIn, nupic::Real32 threshold)
{
  nupic::NumpyVectorT<nupic::Real32> x(xIn), y(sm.nRows());
  nupic::SparseMatrixAlgorithms::kthroot_product(sm, segment_size, x.begin(), y.begin(), threshold);
  return y.forPython();
}

/*
PyObject* 
kthroot_product(const nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > & sm, nupic::UInt32 segment_size, PyObject* xIn, nupic::Real64 threshold)
{
  nupic::NumpyVectorT<nupic::Real64> x(xIn), y(sm.nRows());
  nupic::SparseMatrixAlgorithms::kthroot_product(sm, segment_size, x.begin(), y.begin(), threshold);
  return y.forPython();
}

PyObject* sparseRightVecProd(const nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& a,
                             nupic::UInt32 m, nupic::UInt32 n,
                             PyObject* x)
{
  nupic::NumpyVectorT<nupic::Real64> xx(x), yy(a.nRows());
  nupic::SparseMatrixAlgorithms::sparseRightVecProd(a, m, n, xx.begin(), yy.begin());
  return yy.forPython();
}
*/

PyObject* sparseRightVecProd(const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& a,
                             nupic::UInt32 m, nupic::UInt32 n,
                             PyObject* x)
{
  nupic::NumpyVectorT<nupic::Real32> xx(x), yy(a.nRows());
  nupic::SparseMatrixAlgorithms::sparseRightVecProd(a, m, n, xx.begin(), yy.begin());
  return yy.forPython();
}

//--------------------------------------------------------------------------------
// A function that decide if a binary 0/1 vector is all zeros, or not.
//--------------------------------------------------------------------------------
inline bool isZero_01(PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  return nupic::isZero_01(begin, end);
}

//--------------------------------------------------------------------------------
// A function that sums the elements in a dense range, faster than numpy and C++.
// Uses SIMD instructions in asm.
//--------------------------------------------------------------------------------
inline nupic::Real32 dense_vector_sum(PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  return nupic::sum(begin, end);
}

//--------------------------------------------------------------------------------
// A function that binarizes a dense vector.
//--------------------------------------------------------------------------------
inline PyObject* binarize_with_threshold(nupic::Real32 threshold, PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  nupic::NumpyVectorT<nupic::Real32> y(end - begin);
  nupic::UInt32 c =
    nupic::binarize_with_threshold(threshold, begin, end, y.begin(), y.end());
  PyObject* toReturn = PyTuple_New(2);
  PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(c));
  PyTuple_SET_ITEM(toReturn, 1, y.forPython());
  return toReturn;
}

//--------------------------------------------------------------------------------
// Functions on 2D dense arrays of 0/1
//--------------------------------------------------------------------------------
inline PyObject* 
nonZeroRowsIndicator_01(nupic::UInt32 nrows, nupic::UInt32 ncols, PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  nupic::NumpyVectorT<nupic::UInt32> ind(nrows);
  nupic::nonZeroRowsIndicator_01(nrows, ncols, begin, end, ind.begin(), ind.end());
  return ind.forPython();
}

inline PyObject* 
nonZeroColsIndicator_01(nupic::UInt32 nrows, nupic::UInt32 ncols, PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  nupic::NumpyVectorT<nupic::UInt32> ind(ncols);
  nupic::nonZeroColsIndicator_01(nrows, ncols, begin, end, ind.begin(), ind.end());
  return ind.forPython();
}

inline nupic::UInt32 nNonZeroRows_01(nupic::UInt32 nrows, nupic::UInt32 ncols, PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  return nupic::nNonZeroRows_01(nrows, ncols, begin, end);
}

inline nupic::UInt32 nNonZeroCols_01(nupic::UInt32 nrows, nupic::UInt32 ncols, PyObject* py_x)
{
  PyArrayObject* x = (PyArrayObject*) py_x;
  nupic::Real32* begin = (nupic::Real32*)(x->data);
  nupic::Real32* end = begin + x->dimensions[0];
  return nupic::nNonZeroCols_01(nrows, ncols, begin, end);
}

//--------------------------------------------------------------------------------
}

//--------------------------------------------------------------------------------
%inline {

  //--------------------------------------------------------------------------------
  PyObject* matrix_entropy(const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& sm, nupic::Real32 s =1.0)
  {
    nupic::NumpyVectorT<nupic::Real32> e_rows(sm.nRows()), e_cols(sm.nCols());
    nupic::SparseMatrixAlgorithms::matrix_entropy(sm,
						e_rows.begin(), e_rows.end(),
						e_cols.begin(), e_cols.end(),
						s);
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, e_rows.forPython());
    PyTuple_SET_ITEM(toReturn, 1, e_cols.forPython());
    return toReturn;
  }

  //--------------------------------------------------------------------------------
  /*
  PyObject* matrix_entropy(const nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& sm, nupic::Real64 s =1.0)
  {
    nupic::NumpyVectorT<nupic::Real64> e_rows(sm.nRows()), e_cols(sm.nCols());
    nupic::SparseMatrixAlgorithms::matrix_entropy(sm,
						e_rows.begin(), e_rows.end(),
						e_cols.begin(), e_cols.end(),
						s);
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, e_rows.forPython());
    PyTuple_SET_ITEM(toReturn, 1, e_cols.forPython());
    return toReturn;
  }
  */

  //--------------------------------------------------------------------------------
  PyObject* smoothVecMaxProd(const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& sm, nupic::Real32 k, PyObject *xIn)
  {
    nupic::NumpyVectorT<nupic::Real32> x(xIn), y(sm.nRows());
    nupic::SparseMatrixAlgorithms::smoothVecMaxProd(sm, k, x.begin(), x.end(), y.begin(), y.end());
    return y.forPython();
  }

  //--------------------------------------------------------------------------------
  PyObject* smoothVecArgMaxProd(const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& sm, nupic::Real32 k, PyObject *xIn)
  {
    nupic::NumpyVectorT<nupic::Real32> x(xIn);
    nupic::NumpyVectorT<nupic::UInt32> y(sm.nRows());
    nupic::SparseMatrixAlgorithms::smoothVecArgMaxProd(sm, k, x.begin(), x.end(), y.begin(), y.end());
    return y.forPython();
  }
  
  //--------------------------------------------------------------------------------
  // LBP
  //--------------------------------------------------------------------------------
  void LBP_piPrime(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& mat, nupic::Real32 min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::LBP_piPrime(mat, min_floor);
  }

  //--------------------------------------------------------------------------------
  /*
  void LBP_piPrime(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& mat, nupic::Real64 min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::LBP_piPrime(mat, min_floor);
  }
  */

  //--------------------------------------------------------------------------------
  void SM_subtractNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A,
			  const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& B, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::subtractNoAlloc(A, B, min_floor);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_subtractNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A,
			  nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& B, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::subtractNoAlloc(A, B, min_floor);
  }
  */

  //--------------------------------------------------------------------------------
  void SM_assignNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A,
		     const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& B)
  {
    nupic::SparseMatrixAlgorithms::assignNoAlloc(A, B);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_assignNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A,
		     nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& B)
  {
    nupic::SparseMatrixAlgorithms::assignNoAlloc(A, B);
  }
  */

  //--------------------------------------------------------------------------------
  void SM_assignNoAllocFromBinary(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A, const nupic::SparseBinaryMatrix<nupic::UInt32,nupic::UInt32>& B)
  {
    nupic::SparseMatrixAlgorithms::assignNoAllocFromBinary(A, B);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_assignNoAllocFromBinary(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A, const nupic::SparseBinaryMatrix<nupic::UInt32,nupic::UInt16>& B)
  {
    nupic::SparseMatrixAlgorithms::assignNoAllocFromBinary(A, B);
  }
  */
	//--------------------------------------------------------------------------------
	void SM_addConstantOnNonZeros(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A,
								  const nupic::SparseBinaryMatrix<nupic::UInt32,nupic::UInt32>& B,
								  double cval)
	{
		nupic::SparseMatrixAlgorithms::addConstantOnNonZeros(A, B, cval);
	}
	
	//--------------------------------------------------------------------------------
	/*
	 void SM_addConstantOnNonZeros(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A,
								   const nupic::SparseBinaryMatrix<nupic::UInt32,nupic::UInt32>& B,
								   nupic::Real32 cval)
	 {
	 nupic::SparseMatrixAlgorithms::addConstantOnNonZeros(A, B, cval);
	 }
	 */

  //--------------------------------------------------------------------------------
  void SM_logSumNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A,
			const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& B, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::logSumNoAlloc(A, B, min_floor);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_logSumNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A,
		     nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& B, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::logSumNoAlloc(A, B, min_floor);
  }
  */

 //--------------------------------------------------------------------------------
  void SM_logAddValNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A, double val, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::logAddValNoAlloc(A, val, min_floor);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_logAddValNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A, double val, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::logAddValNoAlloc(A, val, min_floor);
  }
  */
 
  //--------------------------------------------------------------------------------
  void SM_logDiffNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A,
		     nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& B, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::logDiffNoAlloc(A, B, min_floor);
  }

  /*
  //--------------------------------------------------------------------------------
  void SM_logDiffNoAlloc(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A,
		     nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& B, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::logDiffNoAlloc(A, B, min_floor);
  }
  */

  //--------------------------------------------------------------------------------
  void SM_addToNZOnly(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A, double v, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::addToNZOnly(A, v, min_floor);
  }
  /*
  //--------------------------------------------------------------------------------
  void SM_addToNZOnly(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A, double v, double min_floor =0)
  {
    nupic::SparseMatrixAlgorithms::addToNZOnly(A, v, min_floor);
  }
  */

  //--------------------------------------------------------------------------------
  void SM_addToNZDownCols(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A, PyObject* py_x, double min_floor =0)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    nupic::SparseMatrixAlgorithms::addToNZDownCols(A, x.begin(), x.end(), min_floor);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_addToNZDownCols(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A, PyObject* py_x, double min_floor =0)
  {
    nupic::NumpyVectorT<nupic::Real64> x(py_x);
    nupic::SparseMatrixAlgorithms::addToNZDownCols(A, x.begin(), x.end(), min_floor);
  }
  */

  //--------------------------------------------------------------------------------
  void SM_addToNZAcrossRows(nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > >& A, PyObject* py_x, double min_floor =0)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    nupic::SparseMatrixAlgorithms::addToNZAcrossRows(A, x.begin(), x.end(), min_floor);
  }

  //--------------------------------------------------------------------------------
  /*
  void SM_addToNZAcrossRows(nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > >& A, PyObject* py_x, double min_floor =0)
  {
    nupic::NumpyVectorT<nupic::Real64> x(py_x);
    nupic::SparseMatrixAlgorithms::addToNZAcrossRows(A, x.begin(), x.end(), min_floor);
  }
  */
}

//--------------------------------------------------------------------------------
/*
%pythoncode %{

def SM_assignNoAlloc(sm, right):
  if hasattr(right, 'logicalAnd'):
    # This does doesnt look right. Since we are in the bindings module, 
    # I think we can just call SM_assignNoAllocFromBinary directly - wcs

    nupic.bindings.math.SM_assignNoAllocFromBinary(sm, right)
  else:
    # Not updating for NuPIC2 because it looks like it leads to an infinite loop - wcs
    nupic.bindings.math.SM_assignNoAlloc(sm, right)
     
%}
*/

//--------------------------------------------------------------------------------
%extend nupic::LogSumApprox
{
  // For unit testing
  inline nupic::Real32 logSum(nupic::Real32 x, nupic::Real32 y) const
  {
    return self->sum_of_logs(x, y);
  }

  inline nupic::Real32 fastLogSum(nupic::Real32 x, nupic::Real32 y) const
  {
    return self->fast_sum_of_logs(x, y);
  }

}

//--------------------------------------------------------------------------------
%extend nupic::LogDiffApprox
{
  // For unit testing
  inline nupic::Real32 logDiff(nupic::Real32 x, nupic::Real32 y) const
  {
    return self->diff_of_logs(x, y);
  }

  inline nupic::Real32 fastLogDiff(nupic::Real32 x, nupic::Real32 y) const
  {
    return self->fast_diff_of_logs(x, y);
  }

}

//--------------------------------------------------------------------------------
// END LBP
//--------------------------------------------------------------------------------

%inline 
{
  //--------------------------------------------------------------------------------
  // Count the number of elements greater than the passed in threshold in the given
  // range.
  //--------------------------------------------------------------------------------
  inline nupic::UInt32 count_gt(PyObject* py_x, nupic::Real32 threshold)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    return nupic::count_gt(x_begin, x_end, threshold);
  }

  //--------------------------------------------------------------------------------
  // Count the number of elements greater than or equal to the passed in 
  //  threshold in the given range.
  //--------------------------------------------------------------------------------
  inline nupic::UInt32 count_gte(PyObject* py_x, nupic::Real32 threshold)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    return nupic::count_gte(x_begin, x_end, threshold);
  }

  //--------------------------------------------------------------------------------
  // Count the number of elements less than the passed in threshold in the given
  // range.
  //--------------------------------------------------------------------------------
  inline nupic::UInt32 count_lt(PyObject* py_x, nupic::Real32 threshold)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    return nupic::count_lt(x_begin, x_end, threshold);
  }

  //--------------------------------------------------------------------------------
  // A partial argsort that can use an already allocated buffer to avoid creating 
  // a data structure each time it's called. Assumes that the elements to be sorted
  // are nupic::Real32, or at least that they have the same size.
  //
  // A partial sort is much faster than a full sort. The elements after the k first
  // in the result are not sorted, except that they are greater (or lesser) than
  // all the k first elements. If direction is -1, the sort is in decreasing order.
  // If direction is 1, the sort is in increasing order.
  //
  // The result is returned in the first k positions of the buffer for speed.
  // 
  // Uses a pre-allocated buffer to avoid allocating memory each time a sort
  // is needed.
  //--------------------------------------------------------------------------------
  inline void 
    partialArgsort(size_t k, PyObject* py_x, PyObject* py_r, int direction =-1)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    PyArrayObject* r = (PyArrayObject*) py_r;
    nupic::UInt32* r_begin = (nupic::UInt32*)(r->data);
    nupic::UInt32* r_end = r_begin + r->dimensions[0];

    nupic::partial_argsort(k, x_begin, x_end, r_begin, r_end, direction);
  }

  //--------------------------------------------------------------------------------
  /**
   * Specialized partial argsort with selective random tie breaking, only for the 
   * non-zeros of the original coincidence (passed in which).
   * See partial_argsort_sel_rnd_tie_break for more details.
   */
  inline void 
    positiveLearningPartialArgsort(size_t k, 
                                   PyObject* py_x, PyObject* py_r,
                                   nupic::Random& rng,
                                   bool real_random =false)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    PyArrayObject* r = (PyArrayObject*) py_r;
    nupic::UInt32* r_begin = (nupic::UInt32*)(r->data);
    nupic::UInt32* r_end = r_begin + r->dimensions[0];

    nupic::partial_argsort_rnd_tie_break(k,
                                       x_begin, x_end, 
                                       r_begin, r_end, 
                                       rng, real_random);
  }

  //--------------------------------------------------------------------------------
  // A function to replace numpy logical_and.
  // numpy logical_and doesn't use the SSE, so this asm function is *much* faster.
  //
  // For each corresponding elements of x and y, put the logical and of those two
  // elements at the corresponding position in z.
  //
  // x, y and z are arrays of floats, but with 0/1 values.
  //--------------------------------------------------------------------------------
  inline PyObject* logicalAnd(PyObject* py_x, PyObject* py_y)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    PyArrayObject* y = (PyArrayObject*) py_y;
    nupic::Real32* y_begin = (nupic::Real32*)(y->data);
    nupic::Real32* y_end = y_begin + y->dimensions[0];

    nupic::NumpyVectorT<nupic::Real32> z(x_end - x_begin);

    nupic::logical_and(x_begin, x_end, y_begin, y_end, z.begin(), z.end());

    return z.forPython();
  }

  //--------------------------------------------------------------------------------
  //
  // A version of logicalAnd that puts the result of x && y in y directly.
  // This is supposed to be faster, because z is not allocated as a separate
  // vector: the memory already allocated for y is reused instead.
  //
  //--------------------------------------------------------------------------------
  inline void logicalAnd2(PyObject* py_x, PyObject* py_y)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];

    PyArrayObject* y = (PyArrayObject*) py_y;
    nupic::Real32* y_begin = (nupic::Real32*)(y->data);
    nupic::Real32* y_end = y_begin + y->dimensions[0];

    nupic::in_place_logical_and(x_begin, x_end, y_begin, y_end);
  }
}

//--------------------------------------------------------------------------------
%pythoncode %{

  def asType(input, smType=_SparseMatrix32):
    if isinstance(input, smType): return input # No-op.
    output = smType()
    converter = "_copyFrom_" + input.__class__.__name__
    funcs = globals()
    if converter in funcs:
      funcs[converter](input, output)
    else:
      output.copy(input)
    return output

  def outer(a, b, smType=_SparseMatrix32):
    sm = smType()
    sm.setFromOuter(a, b)
    return sm

  # For backward compatibility in pickling
  _SparseMatrix = _SparseMatrix32

  SM32 = _SparseMatrix32
  #SM64 = _SparseMatrix64
  #SM128 = _SparseMatrix128

  def SparseMatrix(*args, **keywords):
    """
    See help(nupic.bindings.math.SM32).
    """
    if 'dtype' not in keywords:
      return _SparseMatrix32(*args)
    dtype = keywords.pop('dtype')
    assert not keywords
    if dtype == 'Float32':
      return _SparseMatrix32(*args)
    #elif dtype == 'Float64':
    #  return _SparseMatrix64(*args) 
    #elif dtype == 'Float128':
    #  return _SparseMatrix128(*args)
    else:
      raise Exception('Unsupported type' + dtype)
%}

//--------------------------------------------------------------------------------
%include <nupic/math/NearestNeighbor.hpp>

//--------------------------------------------------------------------------------
// k-NN
//--------------------------------------------------------------------------------

// Need those typemaps *BEFORE* %template
%typemap(in) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > >::size_type {
  $1 = (nupic::UInt32) PyLong_AsLong($input);
 }

%typemap(in) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > >::value_type {
  $1 = (nupic::Real32) PyFloat_AsDouble($input);
}

/*
%typemap(in) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > >::size_type {
  $1 = (nupic::UInt32) PyLong_AsLong($input);
 }

%typemap(in) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > >::value_type {
  $1 = (nupic::Real64) PyFloat_AsDouble($input);
}

#ifdef NTA_QUAD_PRECISION
%typemap(in) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real128,nupic::Int32,nupic::Real128,nupic::DistanceToZero<nupic::Real128 > > >::size_type {
  $1 = (nupic::UInt32) PyLong_AsLong($input);
}

%typemap(in) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real128,nupic::Int32,nupic::Real128,nupic::DistanceToZero<nupic::Real128 > > >::value_type {
  $1 = (nupic::Real128) PyFloat_AsDouble($input);
}
#endif
*/
//--------------------------------------------------------------------------------
%template(_NearestNeighbor32) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > >;

/*
%template(_NearestNeighbor64) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > >;

#ifdef NTA_QUAD_PRECISION
%template(_NearestNeighbor128) nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt32,nupic::Real128,nupic::Int32,nupic::Real128,nupic::DistanceToZero<nupic::Real128 > > >;
#endif
*/
//--------------------------------------------------------------------------------
%define NearestNeighbor_(N1, N2, N3, N4)

%extend nupic::NearestNeighbor<nupic::SparseMatrix<nupic::UInt ## N1,nupic::Real ## N2,nupic::Int ## N3,nupic::Real ## N4,nupic::DistanceToZero<nupic::Real ## N2 > > >
{
%pythoncode %{

def __init__(self, *args): 
  """
  Constructs a new NearestNeighbor from the following available arguments:
                NearestNeighbor(): An empty sparse matrix with 0 rows and columns.
    NearestNeighbor(nrows, ncols): A zero sparse matrix with the 
                                   specified rows and columns.
    NearestNeighbor(NearestNeighbor): Copies an existing sparse matrix.
          NearestNeighbor(string): Loads a NearestNeighbor from its serialized form.
     NearestNeighbor(numpy.array): Loads a NearestNeighbor from a numpy array.
     NearestNeighbor([[...],[...]]): Creates an array from a list of lists.
  """
  serialized = None
  dense = None
  toCopy = None
  if (len(args) == 1):
    if isinstance(args[0], basestring):
      serialized = args[0]
      args = tuple() 
    elif isinstance(args[0], numpy.ndarray):
      dense = args[0] 
      args = tuple() 
    elif isinstance(args[0], _SparseMatrix ## N2):
      toCopy = args[0]
      args = tuple()
    elif hasattr(args[0], '__iter__'):
      dense = args[0] 
      args = tuple() 
  this = _MATH.new__NearestNeighbor ## N2(*args)
  try: 
    self.this.append(this)
  except: 
    self.this = this
  if toCopy is not None: self.copy(toCopy)
  elif serialized is not None: 
    s = serialized.split(None, 1)
    if s[0] != 'csr' and s[0] != 'sm_csr_1.5':
      raise "Wrong CSR format, should start with 'csr' or 'sm_csr_1.5'"
    self.fromPyString(serialized)
  elif dense is not None:
    self.fromDense(numpy.asarray(dense,dtype=GetNumpyDataType('NTA_Real' + #N2)))

def __getstate__(self):
  """
  Used by the pickling mechanism to get state that will be saved.
  """
  return (self.toPyString(),)

def __setstate__(self,tup):
  """
  Used by the pickling mechanism to restore state that was saved.
  """
  self.this = _MATH.new__NearestNeighbor ## N2(1, 1)
  self.thisown = 1
  self.fromPyString(tup[0])

def __str__(self):
  return self.toDense().__str__()
%}

  nupic::Real rowDist(int row, PyObject *xIn) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    return self->rowL2Dist(row, x.addressOf(0));
  }

  PyObject* vecLpDist(nupic::Real ## N2 p, PyObject *xIn, bool take_root =true) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(xIn);
    nupic::NumpyVectorT<nupic::Real ## N2> output(self->nRows());
    self->LpDist(p, x.addressOf(0), output.addressOf(0), take_root);
    return output.forPython();
  }
	
  PyObject *LpNearest(nupic::Real ## N2 p, PyObject *row,
		      nupic::UInt ## N1 k =1, bool take_root =true) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(row);
    std::vector<std::pair<nupic::UInt ## N1, nupic::Real ## N2> > nn(k);
    self->LpNearest(p, x.begin(), nn.begin(), k, take_root);
    PyObject* toReturn = PyTuple_New(k);
    for (nupic::UInt ## N1 i = 0; i != k; ++i)
      PyTuple_SET_ITEM(toReturn, i, nupic::createPair ## N2(nn[i].first, nn[i].second));
    return toReturn;
  }

  PyObject *closestLp_w(nupic::Real ## N2 p, PyObject *row)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(row);
    std::pair<int, nupic::Real ## N2> nn;
    self->LpNearest_w(p, x.addressOf(0), &nn, true);
    return Py_BuildValue("(if)", nn.first, nn.second);
  }

  PyObject *closestDot(PyObject *row)
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(row);
    std::pair<int, nupic::Real ## N2> r = self->dotNearest(x.addressOf(0));
    return Py_BuildValue("(if)", r.first, r.second);
  }

  PyObject* projLpNearest(nupic::Real ## N2 p, PyObject* py_x,
			  nupic::UInt ## N1 k =1, bool take_root =false) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(py_x);
    std::vector<std::pair<nupic::UInt ## N1, nupic::Real ## N2> > nn(k);
    self->projLpNearest(p, x.begin(), nn.begin(), k, take_root);
    PyObject* toReturn = PyTuple_New(k);
    for (nupic::UInt ## N1 i = 0; i != k; ++i)
      PyTuple_SET_ITEM(toReturn, i, nupic::createPair ## N2(nn[i].first, nn[i].second));
    return toReturn;
  }

  PyObject* 
    projRbf(nupic::Real ## N2 p, nupic::Real ## N2 k, PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::Real ## N2> x(py_x), y(self->nRows());
    self->projRbf(p, k, x.begin(), y.begin());
    return y.forPython();
  }
}
%enddef // End def macro NearestNeighbor_

//--------------------------------------------------------------------------------
NearestNeighbor_(32, 32, 32, 64)
//NearestNeighbor_(64, 64, 64, 64)
//NearestNeighbor_(64, 128, 64, 128)

//--------------------------------------------------------------------------------
%pythoncode %{

  NN32 = _NearestNeighbor32
  #NN64 = _NearestNeighbor64

  def NearestNeighbor(*args, **keywords):
    if 'dtype' not in keywords:
      return _NearestNeighbor32(*args)
    dtype = keywords.pop('dtype')
    if dtype == 'Float32':
      return _NearestNeighbor32(*args)
    #elif dtype == 'Float64':
    #  return _NearestNeighbor64(*args)
    else:
      raise Exception('Unknown type' + dtype)

%}

//--------------------------------------------------------------------------------
// GRAPH ALGORITHMS
//--------------------------------------------------------------------------------
/*
%inline 
{
  //--------------------------------------------------------------------------------
  PyObject* enumerate_sequences(nupic::Real threshold,
                                PyObject* g, 
                                int cr=0, 
                                int ns=0) 
  {
    try {
      void* argp1 = SWIG_Python_GetSwigThis(g)->ptr; 
      nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > *arg1 = reinterpret_cast< nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > * >(argp1);

      std::list<std::vector<nupic::UInt32> > sequences;
      nupic::EnumerateSequences(threshold, *arg1, sequences, ns);
      nupic::UInt32 N = sequences.size();
      PyObject* toReturn = PyList_New(N);
      std::list<std::vector<nupic::UInt32> >::const_iterator it;
      nupic::UInt32 i = 0;
      for (it = sequences.begin(); it != sequences.end(); ++it, ++i) {
	const std::vector<nupic::UInt32>& seq = *it;
	nupic::UInt32 M = it->size();
	PyObject* py_seq = PyList_New(M);
	for (nupic::UInt32 j = 0; j != M; ++j)
	  PyList_SET_ITEM(py_seq, j, PyInt_FromLong(seq[j]));
	PyList_SET_ITEM(toReturn, i, py_seq);
      }
      return toReturn;

    } catch(...) {
      PyErr_SetString(PyExc_RuntimeError, const_cast<char *>("Unknown error in enumerate_sequences"));
      return NULL;
    }
  }

  //--------------------------------------------------------------------------------
  PyObject* find_connected_components(nupic::Real threshold,
                                      PyObject* g)
  {
    try {
      void* argp1 = SWIG_Python_GetSwigThis(g)->ptr; 
      nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > *arg1 = reinterpret_cast< nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > * >(argp1);

      std::list<std::vector<nupic::UInt32> > comps;
      nupic::FindConnectedComponents(threshold, *arg1, comps);
      nupic::UInt32 N = comps.size();
      PyObject* toReturn = PyList_New(N);
      std::list<std::vector<nupic::UInt32> >::const_iterator it;
      nupic::UInt32 i = 0;
      for (it = comps.begin(); it != comps.end(); ++it, ++i) {
        const std::vector<nupic::UInt32>& comp = *it;
        nupic::UInt32 M = it->size();
        PyObject* py_comp = PyList_New(M);
        for (nupic::UInt32 j = 0; j != M; ++j)
          PyList_SET_ITEM(py_comp, j, PyInt_FromLong(comp[j]));
        PyList_SET_ITEM(toReturn, i, py_comp);
      }
      return toReturn;

    } catch(...) {
      PyErr_SetString(PyExc_RuntimeError, const_cast<char *>("Unknown error in enumerate_sequences"));
      return NULL;
    }
  }
} // End inline.

%{
template<typename TSM>
inline PyObject *_find_connected_components2(const TSM &sm)
{
  std::list<std::vector<nupic::UInt32> > comps;
  nupic::FindConnectedComponents_boost(sm, comps);
  nupic::UInt32 N = comps.size();
  // PyRequiredRef toReturn(PyList_New(N));
  PyObject *toReturn = PyList_New(N);
  std::list<std::vector<nupic::UInt32> >::const_iterator it;
  nupic::UInt32 i = 0;
  for (it = comps.begin(); it != comps.end(); ++it, ++i) {
    const std::vector<nupic::UInt32>& comp = *it;
    nupic::UInt32 M = it->size();
    PyObject* py_comp = PyList_New(M);
    for (nupic::UInt32 j = 0; j != M; ++j)
      PyList_SET_ITEM(py_comp, j, PyInt_FromLong(comp[j]));
    PyList_SET_ITEM(toReturn, i, py_comp);
  }
  return toReturn;
  // return toReturn.toReturn();
}

%}
*/

%inline {
  /*
  //--------------------------------------------------------------------------------
  // PyObject* find_connected_components2(PyObject* g)
  PyObject* find_connected_components2(const nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > &sm)
      { return _find_connected_components2(sm); }

  PyObject* find_connected_components2(const nupic::SparseMatrix<nupic::UInt32,nupic::Real64,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real64 > > &sm)
      { return _find_connected_components2(sm); }

  //--------------------------------------------------------------------------------
  PyObject* cuthill_mckee(PyObject* g)
  {
    try {
      void* argp1 = SWIG_Python_GetSwigThis(g)->ptr; 
      nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > *arg1 = reinterpret_cast< nupic::SparseMatrix<nupic::UInt32,nupic::Real32,nupic::Int32,nupic::Real64,nupic::DistanceToZero<nupic::Real32 > > * >(argp1);

      nupic::NumpyVectorT<nupic::UInt32> p(arg1->nRows());
      nupic::NumpyVectorT<nupic::UInt32> rp(arg1->nRows());
      nupic::CuthillMcKeeOrdering(*arg1, p.begin(), rp.begin());
      PyObject* toReturn = PyList_New(2);
      PyList_SET_ITEM(toReturn, 0, p.forPython());
      PyList_SET_ITEM(toReturn, 1, rp.forPython());
      return toReturn;

    } catch(...) {
      PyErr_SetString(PyExc_RuntimeError, const_cast<char *>("Unknown error in enumerate_sequences"));
      return NULL;
    }
  }
 */
  //--------------------------------------------------------------------------------
  PyObject* min_score_per_category(nupic::UInt32 maxCategoryIdx, PyObject* c_py,
            PyObject* d_py)
  {
    nupic::NumpyVectorT<nupic::UInt32> c(c_py);
    nupic::NumpyVectorT<nupic::Real32> d(d_py);

    int n = int(maxCategoryIdx + 1);
    nupic::NumpyVectorT<nupic::Real32> s(n, std::numeric_limits<nupic::Real32>::max());

    int nScores = int(c.end() - c.begin());
    for (int i = 0; i != nScores; ++i) 
      s.set(c.get(i), std::min(s.get(c.get(i)), d.get(i)));

    return s.forPython();
 }
}

//--------------------------------------------------------------------------------
// BINARY MATRIX
//--------------------------------------------------------------------------------
 /*
%extend nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt16>
{
%pythoncode %{

def __init__(self, *args): 
    if isinstance(args[0], basestring):
        self.this = _MATH.new__SM_01_32_16(1)
        self.fromCSR(args[0])
    elif isinstance(args[0], numpy.ndarray) or hasattr(args[0], '__iter__'):
        self.this = _MATH.new__SM_01_32_16(1)
        self.fromDense(numpy.asarray(args[0]))
    elif isinstance(args[0], int):
        self.this = _MATH.new__SM_01_32_16(args[0])
    elif isinstance(args[0], _SM_01_32_16):
        self.this = _MATH.new__SM_01_32_16(1)
        self.copy(args[0])
  
def __str__(self):
    return self.toDense().__str__()

def __setstate__(self, inString):
    self.this = _MATH.new__SM_01_32_16(1)
    self.thisown = 1
    self.fromCSR(inString)
%}

  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  inline void readState(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw 
	std::runtime_error("Failed to read SparseBinaryMatrix state from string.");
    }
  }

  inline void set(nupic::UInt32 i, nupic::UInt16 j, nupic::Real32 v)
  {
    self->set(i, j, v);
  }

  inline void set(nupic::UInt32 row, PyObject* py_indices, nupic::Real32 v)
  {
    nupic::NumpyVectorT<nupic::UInt16> indices(py_indices);
    self->set(row, indices.begin(), indices.end(), v);
  }

  inline void setForAllRows(PyObject* py_indices, nupic::Real32 v)
  {
    nupic::NumpyVectorT<nupic::UInt16> indices(py_indices);
    self->setForAllRows(indices.begin(), indices.end(), v);
  }

  inline PyObject* getAllNonZeros(bool two_lists =false) const
  {
    const nupic::UInt32 nnz = self->nNonZeros();
    nupic::NumpyVectorT<nupic::UInt32> rows(nnz), cols(nnz);

    self->getAllNonZeros(rows.begin(), cols.begin());

    PyObject* toReturn = NULL;

    if (!two_lists) {
      // Return one list of triples
      toReturn = PyTuple_New(nnz);
      for (nupic::UInt32 i = 0; i != nnz; ++i) {
	PyObject* tuple = PyTuple_New(2);
	PyTuple_SET_ITEM(tuple, 0, PyInt_FromLong(rows.get(i)));
	PyTuple_SET_ITEM(tuple, 1, PyInt_FromLong(cols.get(i)));
	PyTuple_SET_ITEM(toReturn, i, tuple);
      }
    } else {
      // Return two lists
      toReturn = PyTuple_New(2);
      PyTuple_SET_ITEM(toReturn, 0, rows.forPython());
      PyTuple_SET_ITEM(toReturn, 1, cols.forPython());
    }

    return toReturn;
  } 

  inline void setAllNonZeros(nupic::UInt32 nrows, nupic::UInt16 ncols,
		      PyObject* py_i, PyObject* py_j, bool sorted =true)
  {
    nupic::NumpyVectorT<nupic::UInt32> i(py_i);
    nupic::NumpyVectorT<nupic::UInt16> j(py_j);
    self->setAllNonZeros(nrows, ncols, i.begin(), i.end(), j.begin(), j.end(), sorted);
  }

  inline void setSlice(nupic::UInt32 i_begin, nupic::UInt32 j_begin,
                       const SparseBinaryMatrix<nupic::UInt32,nupic::UInt16>& other)
  {
    self->setSlice(i_begin, j_begin, other);
  }

  inline void setSlice(nupic::UInt32 i_begin, nupic::UInt32 j_begin, PyObject* py_other)
  {
    nupic::NumpyMatrixT<nupic::Real32> other(py_other);
    self->setSlice(i_begin, j_begin, other);
  }

  inline PyObject* getCol(nupic::UInt32 col) const
  {
    const nupic::UInt32 nrows = self->nRows();
    nupic::NumpyVectorT<nupic::UInt32> dense_col(nrows);
    self->getColToDense(col, dense_col.begin(), dense_col.end());
    return dense_col.forPython();
  }

  inline PyObject* zeroRowsIndicator() const
  {
    nupic::NumpyVectorT<nupic::UInt32> res(self->nRows());
    nupic::UInt32 count = self->zeroRowsIndicator(res.begin(), res.end());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(count));
    PyTuple_SET_ITEM(toReturn, 1, res.forPython());
    return toReturn;
  }

  inline PyObject* nonZeroRowsIndicator() const
  {
    nupic::NumpyVectorT<nupic::UInt32> res(self->nRows());
    nupic::UInt32 count = self->nonZeroRowsIndicator(res.begin(), res.end());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(count));
    PyTuple_SET_ITEM(toReturn, 1, res.forPython());
    return toReturn;
  }

  inline PyObject* nNonZerosPerRow() const
  {
    nupic::NumpyVectorT<nupic::UInt16> x(self->nRows());
    self->nNonZerosPerRow(x.begin(), x.end());
    return x.forPython();
  }

  inline PyObject* nNonZerosPerCol() const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nCols());
    self->nNonZerosPerCol(x.begin(), x.end());
    return x.forPython();
  }
  
  inline nupic::SparseMatrix<nupic::UInt32,nupic::Real32>
    nNonZerosPerBox(PyObject* box_i, PyObject* box_j) const
    {
      nupic::NumpyVectorT<nupic::UInt32> bounds_i(box_i);
      nupic::NumpyVectorT<nupic::UInt32> bounds_j(box_j);
      nupic::SparseMatrix<nupic::UInt32,nupic::Real32> result(bounds_i.size(), bounds_j.size());
      self->nNonZerosPerBox(bounds_i.begin(), bounds_i.end(),
			    bounds_j.begin(), bounds_j.end(), 
			    result);
      return result;
    }
  
  inline PyObject* rowSums() const
  {
    nupic::NumpyVectorT<nupic::UInt16> x(self->nRows());
    self->rowSums(x.begin(), x.end());
    return x.forPython();
  }

  inline PyObject* colSums() const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nCols());
    self->colSums(x.begin(), x.end());
    return x.forPython();
  }

  inline PyObject* overlap(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    nupic::NumpyVectorT<nupic::UInt32> y(self->nRows());
    self->overlap(x.begin(), x.end(), y.begin(), y.end());
    return y.forPython();
  }

  inline bool maxAllowedOverlap(nupic::Real32 maxDistance, PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    return self->maxAllowedOverlap(maxDistance, x.begin(), x.end());
  }

  inline void appendSparseRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::UInt16> x(py_x);
    self->appendSparseRow(x.begin(), x.end());
  }

  inline void appendDenseRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->appendDenseRow(x.begin(), x.end());
  }

  inline void appendSparseCol(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    self->appendSparseCol(x.begin(), x.end());
  }

  inline PyObject* getRowSparse(nupic::UInt16 row) const
  {
    nupic::NumpyVectorT<nupic::UInt16> x(self->nNonZerosOnRow(row));
    const nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt16>::Row& _row =
      self->getSparseRow(row);
    for (nupic::UInt16 i = 0; i != _row.size(); ++i)
      x.set(i,_row[i]);
    return x.forPython();
  }

  inline void replaceSparseRow(nupic::UInt32 row, PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::UInt16> x(py_x);
    self->replaceSparseRow(row, x.begin(), x.end());
  }

  inline nupic::UInt32 findRowSparse(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt16> x(py_x);
    return self->findRowSparse(x.begin(), x.end());
  }

  inline nupic::UInt32 findRowDense(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt16> x(py_x);
    return self->findRowDense(x.begin(), x.end());
  }

  inline void fromDense(PyObject* py_m)
  {
    nupic::NumpyMatrixT<nupic::UInt32> m(py_m);
    self->fromDense(m.rows(), m.columns(), 
		    m.addressOf(0,0), m.addressOf(0,0) + m.rows() * m.columns());
  }

  inline PyObject* toDense() const 
  {
    int dims[] = { self->nRows(), self->nCols() };
    nupic::NumpyMatrixT<nupic::UInt32> out(dims);
    self->toDense(out.addressOf(0, 0), out.addressOf(0, 0) + dims[0] * dims[1]);
    return out.forPython();
  }

  inline PyObject* toCSR() const
  {
    std::ostringstream s;
    self->toCSR(s);
    std::string str = s.str();
    return PyString_FromStringAndSize(str.data(), str.size());
  }

  inline void fromCSR(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); // Reference-neutral.
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseBinaryMatrix state from string.");
    }
  }

  inline void CSRSaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toCSR(save_file);
    save_file.close();
  }

  inline void CSRLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromCSR(load_file);
    load_file.close();
  }

  inline void binarySaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toBinary(save_file);
    save_file.close();
  }

  inline void binaryLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromBinary(load_file);
    load_file.close();
  }

  inline void write(PyObject* pyBuilder) const
  {
    SparseBinaryMatrixProto::Builder proto =
        nupic::getBuilder<SparseBinaryMatrixProto>(pyBuilder);
    self->write(proto);
  }

  inline void read(PyObject* pyReader)
  {
    SparseBinaryMatrixProto::Reader proto =
        nupic::getReader<SparseBinaryMatrixProto>(pyReader);
    self->read(proto);
  }

  inline void fromSparseVector(nupic::UInt32 nrows, nupic::UInt16 ncols,
			       PyObject *py_x, nupic::UInt16 offset =0)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    self->fromSparseVector(nrows, ncols, x.begin(), x.end(), offset);
  }

  inline PyObject* toSparseVector(nupic::UInt32 offset =0)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nNonZeros());
    self->toSparseVector(x.begin(), x.end(), offset);
    return x.forPython();
  }

  inline void rowFromDense(nupic::UInt32 row, PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->rowFromDense(row, x.begin(), x.end());
  }

  inline PyObject* rowToDense(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->rowToDense(row, x.begin(), x.end());
    return x.forPython();
  }
  
  inline PyObject* getRow(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->getRow(row, x.begin(), x.end());
    return x.forPython();
  }

  // Matrix vector multiplication on the right side, optimized
  // to skip the actual multiplications, because all the non-zeros
  // have the same value: 1.
  inline PyObject* rightVecSumAtNZ(PyObject* py_x) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    nupic::NumpyVectorT<nupic::Real32> y(self->nRows());
    self->rightVecSumAtNZ(x_begin, x_end, y.begin(), y.end());
    return y.forPython();
  }

  // Same as rightVecSumAtNZ, but doesn't allocate its result, assumes
  // that the vector of the correct size (number of columns) is passed
  // in for the result.
  inline void rightVecSumAtNZ_fast(PyObject* py_x, PyObject* py_y) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    PyArrayObject* y = (PyArrayObject*) py_y;
    nupic::Real32* y_begin = (nupic::Real32*)(y->data);
    nupic::Real32* y_end = y_begin + y->dimensions[0];
    self->rightVecSumAtNZ(x_begin, x_end, y_begin, y_end);
  }

  // Matrix vector multiplication on the left side, optimized
  // to skip the actual multiplications, because all the non-zeros
  // have the same value: 1.
  inline PyObject* leftVecSumAtNZ(PyObject* py_x) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    nupic::NumpyVectorT<nupic::Real32> y(self->nCols());
    self->leftVecSumAtNZ(x_begin, x_end, y.begin(), y.end());
    return y.forPython();
  }

  // Same as leftVecSumAtNZ, but doesn't allocate its result, assumes
  // that the vector of the correct size (number of rows) is passed
  // in for the result.
  inline void leftVecSumAtNZ_fast(PyObject* py_x, PyObject* py_y) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    PyArrayObject* y = (PyArrayObject*) py_y;
    nupic::Real32* y_begin = (nupic::Real32*)(y->data);
    nupic::Real32* y_end = y_begin + y->dimensions[0];
    self->leftVecSumAtNZ(x_begin, x_end, y_begin, y_end);
  }

  PyObject* rightDenseMatMaxAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real32> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nRows();
    nupic::NumpyMatrixT<nupic::Real32> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->rightVecMaxAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  PyObject* leftDenseMatSumAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real32> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real32> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecSumAtNZ(m.begin(i), m.end(i), r.begin(i), r.end(i));
    return r.forPython();
  }

  PyObject* leftDenseMatMaxAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real32> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real32> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecMaxAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  inline PyObject* minHammingDistance(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    std::pair<nupic::UInt32, nupic::UInt32> r =
      self->minHammingDistance(x.begin(), x.end());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(r.first));
    PyTuple_SET_ITEM(toReturn, 1, PyInt_FromLong(r.second));
    return toReturn;
  }

  inline PyObject* firstRowCloserThan(PyObject* py_x, nupic::UInt16 distance) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    nupic::UInt32 i = self->firstRowCloserThan(x.begin(), x.end(), distance);
    return PyInt_FromLong(i);
  }

  inline PyObject* firstRowCloserThan_dense(PyObject* py_x, nupic::UInt16 distance) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    nupic::UInt32 i = self->firstRowCloserThan_dense(x.begin(), x.end(), distance);
    return PyInt_FromLong(i);
  }

  inline PyObject* vecMaxProd(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::Real64> x(py_x), y(self->nRows());
    self->vecMaxProd(x.begin(), x.end(), y.begin(), y.end());
    return y.forPython();
  }

  inline bool __eq__(const nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt16>& other) const
  { 
    return self->equals(other); 
  }
  
  inline bool __ne__(const nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt16>& other) const
  { 
    return ! self->equals(other); 
  }

} // end extend nupic::SparseBinaryMatrix
*/

//--------------------------------------------------------------------------------
%extend nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt32>
{
%pythoncode %{
def __init__(self, *args): 
    if isinstance(args[0], basestring):
        self.this = _MATH.new__SM_01_32_32(1)
        self.fromCSR(args[0])
    elif isinstance(args[0], numpy.ndarray) or hasattr(args[0], '__iter__'):
        self.this = _MATH.new__SM_01_32_32(1)
        self.fromDense(numpy.asarray(args[0]))
    elif isinstance(args[0], int):
        self.this = _MATH.new__SM_01_32_32(args[0])
    elif isinstance(args[0], _SM_01_32_32):
        self.this = _MATH.new__SM_01_32_32(1)
        self.copy(args[0])
    elif isinstance(args[0], _SparseMatrix32):
        self.this = _MATH.new__SM_01_32_32(1)
        nz_i,nz_j,nz_v = args[0].getAllNonZeros(True)
        self.setAllNonZeros(args[0].nRows(), args[0].nCols(), nz_i, nz_j)
  
def __str__(self):
    return self.toDense().__str__()

def __setstate__(self, inString):
    self.this = _MATH.new__SM_01_32_32(1)
    self.thisown = 1
    self.fromCSR(inString)
%}

  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  inline void readState(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw 
	std::runtime_error("Failed to read SparseBinaryMatrix state from string.");
    }
  }

  inline void set(nupic::UInt32 i, nupic::UInt32 j, nupic::Real32 v)
  {
    self->set(i, j, v);
  }

  inline void set(nupic::UInt32 row, PyObject* py_indices, nupic::Real32 v)
  {
    nupic::NumpyVectorT<nupic::UInt32> indices(py_indices);
    self->set(row, indices.begin(), indices.end(), v);
  }

  inline void setForAllRows(PyObject* py_indices, nupic::Real32 v)
  {
    nupic::NumpyVectorT<nupic::UInt32> indices(py_indices);
    self->setForAllRows(indices.begin(), indices.end(), v);
  }

  inline PyObject* getAllNonZeros(bool two_lists =false) const
  {
    const nupic::UInt32 nnz = self->nNonZeros();
    nupic::NumpyVectorT<nupic::UInt32> rows(nnz), cols(nnz);

    self->getAllNonZeros(rows.begin(), cols.begin());

    PyObject* toReturn = NULL;

    if (!two_lists) {
      // Return one list of triples
      toReturn = PyTuple_New(nnz);
      for (nupic::UInt32 i = 0; i != nnz; ++i) {
	PyObject* tuple = PyTuple_New(2);
	PyTuple_SET_ITEM(tuple, 0, PyInt_FromLong(rows.get(i)));
	PyTuple_SET_ITEM(tuple, 1, PyInt_FromLong(cols.get(i)));
	PyTuple_SET_ITEM(toReturn, i, tuple);
      }
    } else {
      // Return two lists
      toReturn = PyTuple_New(2);
      PyTuple_SET_ITEM(toReturn, 0, rows.forPython());
      PyTuple_SET_ITEM(toReturn, 1, cols.forPython());
    }

    return toReturn;
  } 

  inline void setAllNonZeros(nupic::UInt32 nrows, nupic::UInt32 ncols,
		      PyObject* py_i, PyObject* py_j, bool sorted =true)
  {
    nupic::NumpyVectorT<nupic::UInt32> i(py_i), j(py_j);
    self->setAllNonZeros(nrows, ncols, i.begin(), i.end(), j.begin(), j.end(), sorted);
  }

  inline void setSlice(nupic::UInt32 i_begin, nupic::UInt32 j_begin,
                       const SparseBinaryMatrix<nupic::UInt32,nupic::UInt32>& other)
  {
    self->setSlice(i_begin, j_begin, other);
  }

  inline void setSlice(nupic::UInt32 i_begin, nupic::UInt32 j_begin, PyObject* py_other)
  {
    nupic::NumpyMatrixT<nupic::Real32> other(py_other);
    self->setSlice(i_begin, j_begin, other);
  }

  inline PyObject* getCol(nupic::UInt32 col) const
  {
    const nupic::UInt32 nrows = self->nRows();
    nupic::NumpyVectorT<nupic::UInt32> dense_col(nrows);
    self->getColToDense(col, dense_col.begin(), dense_col.end());
    return dense_col.forPython();
  }

  inline PyObject* zeroRowsIndicator() const
  {
    nupic::NumpyVectorT<nupic::UInt32> res(self->nRows());
    nupic::UInt32 count = self->zeroRowsIndicator(res.begin(), res.end());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(count));
    PyTuple_SET_ITEM(toReturn, 1, res.forPython());
    return toReturn;
  }

  inline PyObject* nonZeroRowsIndicator() const
  {
    nupic::NumpyVectorT<nupic::UInt32> res(self->nRows());
    nupic::UInt32 count = self->nonZeroRowsIndicator(res.begin(), res.end());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(count));
    PyTuple_SET_ITEM(toReturn, 1, res.forPython());
    return toReturn;
  }

  inline PyObject* nNonZerosPerRow() const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nRows());
    self->nNonZerosPerRow(x.begin(), x.end());
    return x.forPython();
  }

  inline PyObject* nNonZerosPerCol() const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nCols());
    self->nNonZerosPerCol(x.begin(), x.end());
    return x.forPython();
  }

  inline nupic::SparseMatrix<nupic::UInt32,nupic::Real32>
   nNonZerosPerBox(PyObject* box_i, PyObject* box_j) const
    {
      nupic::NumpyVectorT<nupic::UInt32> bounds_i(box_i);
      nupic::NumpyVectorT<nupic::UInt32> bounds_j(box_j);
      nupic::SparseMatrix<nupic::UInt32,nupic::Real32> result(bounds_i.size(), bounds_j.size());
      self->nNonZerosPerBox(bounds_i.begin(), bounds_i.end(),
			    bounds_j.begin(), bounds_j.end(), 
			    result);
      return result;
    }

  inline PyObject* rowSums() const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nRows());
    self->rowSums(x.begin(), x.end());
    return x.forPython();
  }

  inline PyObject* colSums() const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nCols());
    self->colSums(x.begin(), x.end());
    return x.forPython();
  }

  inline PyObject* overlap(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    nupic::NumpyVectorT<nupic::UInt32> y(self->nRows());
    self->overlap(x.begin(), x.end(), y.begin(), y.end());
    return y.forPython();
  }

  inline bool maxAllowedOverlap(nupic::Real32 maxDistance, PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    return self->maxAllowedOverlap(maxDistance, x.begin(), x.end());
  }

  inline void appendSparseRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    self->appendSparseRow(x.begin(), x.end());
  }

  inline void appendDenseRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->appendDenseRow(x.begin(), x.end());
  }

  inline void replaceSparseRow(nupic::UInt32 row, PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    self->replaceSparseRow(row, x.begin(), x.end());
  }

  inline void appendSparseCol(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    self->appendSparseCol(x.begin(), x.end());
  }

  inline PyObject* getRowSparse(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nNonZerosOnRow(row));
    const nupic::SparseBinaryMatrix<nupic::UInt32>::Row& _row =
      self->getSparseRow(row);
    for (nupic::UInt32 i = 0; i != _row.size(); ++i)
      x.set(i, _row[i]);
    return x.forPython();
  }

  inline nupic::UInt32 findRowSparse(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    return self->findRowSparse(x.begin(), x.end());
  }

  inline nupic::UInt32 findRowDense(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    return self->findRowDense(x.begin(), x.end());
  }

  inline void fromDense(PyObject* py_m)
  {
    nupic::NumpyMatrixT<nupic::UInt32> m(py_m);
    self->fromDense(m.rows(), m.columns(), 
		    m.addressOf(0,0), m.addressOf(0,0) + m.rows() * m.columns());
  }

  inline PyObject* toDense() const 
  {
    int dims[] = { static_cast<int>(self->nRows()), static_cast<int>(self->nCols()) };
    nupic::NumpyMatrixT<nupic::UInt32> out(dims);
    self->toDense(out.addressOf(0, 0), out.addressOf(0, 0) + dims[0] * dims[1]);
    return out.forPython();
  }

  inline PyObject* toCSR() const
  {
    std::ostringstream s;
    self->toCSR(s);
    std::string str = s.str();
    return PyString_FromStringAndSize(str.data(), str.size());
  }

  inline void fromCSR(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); // Reference-neutral.
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseBinaryMatrix state from string.");
    }
  }

  PyObject* toPyString() const
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  bool fromPyString(PyObject *s) 
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(s, &buf, &n); // Reference-neutral.
    if((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
      return true;
    }
    else {
      throw std::runtime_error("Failed to read SparseBinaryMatrix state from string.");
      return false;
    }
  }

  inline void CSRSaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toCSR(save_file);
    save_file.close();
  }

  inline void CSRLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromCSR(load_file);
    load_file.close();
  }

  inline void binarySaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toBinary(save_file);
    save_file.close();
  }

  inline void binaryLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromBinary(load_file);
    load_file.close();
  }

  inline void write(PyObject* pyBuilder) const
  {
    SparseBinaryMatrixProto::Builder proto =
        nupic::getBuilder<SparseBinaryMatrixProto>(pyBuilder);
    self->write(proto);
  }

  inline void read(PyObject* pyReader)
  {
    SparseBinaryMatrixProto::Reader proto =
        nupic::getReader<SparseBinaryMatrixProto>(pyReader);
    self->read(proto);
  }

  inline void fromSparseVector(nupic::UInt32 nrows, nupic::UInt32 ncols,
			       PyObject *py_x, nupic::UInt32 offset =0)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    self->fromSparseVector(nrows, ncols, x.begin(), x.end(), offset);
  }

  inline PyObject* toSparseVector(nupic::UInt32 offset =0)
  {
    nupic::NumpyVectorT<nupic::UInt32> x(self->nNonZeros());
    self->toSparseVector(x.begin(), x.end(), offset);
    return x.forPython();
  }

  inline PyObject* getRow(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->getRow(row, x.begin(), x.end());
    return x.forPython();
  }

  inline void rowFromDense(nupic::UInt32 row, PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->rowFromDense(row, x.begin(), x.end());
  }

  inline PyObject* rowToDense(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->rowToDense(row, x.begin(), x.end());
    return x.forPython();
  }

  // Matrix vector multiplication on the right side, optimized
  // to skip the actual multiplications, because all the non-zeros
  // have the same value: 1.
  inline PyObject* rightVecSumAtNZ(PyObject* py_x) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    nupic::NumpyVectorT<nupic::Real32> y(self->nRows());
    self->rightVecSumAtNZ(x_begin, x_end, y.begin(), y.end());
    return y.forPython();
  }

  // Same as rightVecSumAtNZ, but doesn't allocate its result, assumes
  // that the vector of the correct size (number of columns) is passed
  // in for the result.
  inline void rightVecSumAtNZ_fast(PyObject* py_x, PyObject* py_y) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    PyArrayObject* y = (PyArrayObject*) py_y;
    nupic::Real32* y_begin = (nupic::Real32*)(y->data);
    nupic::Real32* y_end = y_begin + y->dimensions[0];
    self->rightVecSumAtNZ(x_begin, x_end, y_begin, y_end);
  }

  // Matrix vector multiplication on the left side, optimized
  // to skip the actual multiplications, because all the non-zeros
  // have the same value: 1.
  inline PyObject* leftVecSumAtNZ(PyObject* py_x) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    nupic::NumpyVectorT<nupic::Real32> y(self->nCols());
    self->leftVecSumAtNZ(x_begin, x_end, y.begin(), y.end());
    return y.forPython();
  }

  // Same as leftVecSumAtNZ, but doesn't allocate its result, assumes
  // that the vector of the correct size (number of rows) is passed
  // in for the result.
  inline void leftVecSumAtNZ_fast(PyObject* py_x, PyObject* py_y) const
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nupic::Real32* x_begin = (nupic::Real32*)(x->data);
    nupic::Real32* x_end = x_begin + x->dimensions[0];
    PyArrayObject* y = (PyArrayObject*) py_y;
    nupic::Real32* y_begin = (nupic::Real32*)(y->data);
    nupic::Real32* y_end = y_begin + y->dimensions[0];
    self->leftVecSumAtNZ(x_begin, x_end, y_begin, y_end);
  }

  PyObject* rightDenseMatMaxAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real32> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nRows();
    nupic::NumpyMatrixT<nupic::Real32> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->rightVecMaxAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }
  
  PyObject* leftDenseMatSumAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real32> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real32> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecSumAtNZ(m.begin(i), m.end(i), r.begin(i), r.end(i));
    return r.forPython();
  }

  PyObject* leftDenseMatMaxAtNZ(PyObject* mIn) const
  {
    nupic::NumpyMatrixT<nupic::Real32> m(mIn);
    int nRowsCols[2];
    nRowsCols[0] = m.nRows();
    nRowsCols[1] = self->nCols();
    nupic::NumpyMatrixT<nupic::Real32> r(nRowsCols);
    for (int i = 0; i != m.nRows(); ++i)
      self->leftVecMaxAtNZ(m.begin(i), r.begin(i));
    return r.forPython();
  }

  inline PyObject* minHammingDistance(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    std::pair<nupic::UInt32, nupic::UInt32> r =
      self->minHammingDistance(x.begin(), x.end());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, PyInt_FromLong(r.first));
    PyTuple_SET_ITEM(toReturn, 1, PyInt_FromLong(r.second));
    return toReturn;
  }

  inline PyObject* firstRowCloserThan(PyObject* py_x, nupic::UInt32 distance) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    nupic::UInt32 i = self->firstRowCloserThan(x.begin(), x.end(), distance);
    return PyInt_FromLong(i);
  }

  inline PyObject* firstRowCloserThan_dense(PyObject* py_x, nupic::UInt32 distance) const
  {
    nupic::NumpyVectorT<nupic::UInt32> x(py_x);
    nupic::UInt32 i = self->firstRowCloserThan_dense(x.begin(), x.end(), distance);
    return PyInt_FromLong(i);
  }

  inline PyObject* vecMaxProd(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x), y(self->nRows());
    self->vecMaxProd(x.begin(), x.end(), y.begin(), y.end());
    return y.forPython();
  }

  inline PyObject* rightVecArgMaxAtNZ(PyObject* py_x) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x), y(self->nRows());
    self->rightVecArgMaxAtNZ(x.begin(), y.begin());
    return y.forPython();
  }

  inline bool __eq__(const nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt32>& other) const
  { 
    return self->equals(other); 
  }
  
  inline bool __ne__(const nupic::SparseBinaryMatrix<nupic::UInt32, nupic::UInt32>& other) const
  { 
    return ! self->equals(other); 
  }

} // end extend nupic::SparseBinaryMatrix

%pythoncode %{
  
  #SM_01_32_16 = _SM_01_32_16
  SM_01_32_32 = _SM_01_32_32
  SparseBinaryMatrix = _SM_01_32_32

  def SparseBinaryMatrix(*args, **keywords):
    return _SM_01_32_32(*args)
%}

//--------------------------------------------------------------------------------
// SPARSE RLE MATRIX
//--------------------------------------------------------------------------------
/*
%extend nupic::SparseRLEMatrix<nupic::UInt16, unsigned char>
{
%pythoncode %{

def __init__(self, *args): 
    if len(args) == 1:
        if isinstance(args[0], basestring):
            self.this = _MATH.new__SM_RLE_16_8()
            self.fromCSR(args[0])
        elif isinstance(args[0], numpy.ndarray) or hasattr(args[0], '__iter__'):
            self.this = _MATH.new__SM_RLE_16_8()
            self.fromDense(numpy.asarray(args[0]))
    else:
        self.this = _MATH.new__SM_RLE_16_8()	    
  
def __str__(self):
    return self.toDense().__str__()

def __setstate__(self, inString):
    self.this = _MATH.new__SM_RLE_16_8()
    self.thisown = 1
    self.fromCSR(inString)
%}

  inline PyObject* __getstate__() const
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  inline void readState(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseRLEMatrix state from string.");
    }
  }

  inline void appendRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->appendRow(x.begin(), x.end());
  }

  inline PyObject* getRowToDense(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->getRowToDense(row, x.begin(), x.end());
    return x.forPython();
  }

  inline nupic::UInt16 firstRowCloserThan(PyObject* py_x, nupic::Real32 d) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    return self->firstRowCloserThan(x.begin(), x.end(), d);
  }

  inline void fromDense(PyObject* py_m)
  {
    nupic::NumpyMatrixT<nupic::Real32> m(py_m);
    self->fromDense(m.rows(), m.columns(), 
		    m.addressOf(0,0), m.addressOf(0,0) + m.rows() * m.columns());
  }

  inline PyObject* toDense() const 
  {
    int dims[] = { self->nRows(), self->nCols() };
    nupic::NumpyMatrixT<nupic::Real32> out(dims);
    self->toDense(out.addressOf(0, 0), out.addressOf(0, 0) + dims[0] * dims[1]);
    return out.forPython();
  }

  inline PyObject* toCSR() const
  {
    std::ostringstream s;
    self->toCSR(s);
    std::string str = s.str();
    return PyString_FromStringAndSize(str.data(), str.size());
  }

  inline void fromCSR(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseRLEMatrix state from string.");
    }
  }

  inline void CSRSaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toCSR(save_file);
    save_file.close();
  }

  inline void CSRLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromCSR(load_file);
    load_file.close();
  }

} // end extend nupic::SparseRLEMatrix

//--------------------------------------------------------------------------------
%extend nupic::SparseRLEMatrix<nupic::UInt16, nupic::UInt16>
{
%pythoncode %{

def __init__(self, *args): 
    if len(args) == 1:
        if isinstance(args[0], basestring):
            self.this = _MATH.new__SM_RLE_16_16()
            self.fromCSR(args[0])
        elif isinstance(args[0], numpy.ndarray) or hasattr(args[0], '__iter__'):
            self.this = _MATH.new__SM_RLE_16_16()
            self.fromDense(numpy.asarray(args[0]))
    else:
        self.this = _MATH.new__SM_RLE_16_16()	    
  
def __str__(self):
    return self.toDense().__str__()

def __setstate__(self, inString):
    self.this = _MATH.new__SM_RLE_16_16()
    self.thisown = 1
    self.fromCSR(inString)
%}

  inline PyObject* __getstate__() const
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  inline void readState(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseRLEMatrix state from string.");
    }
  }

  inline void appendRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->appendRow(x.begin(), x.end());
  }

  inline PyObject* getRowToDense(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->getRowToDense(row, x.begin(), x.end());
    return x.forPython();
  }

  inline nupic::UInt16 firstRowCloserThan(PyObject* py_x, nupic::Real32 d) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    return self->firstRowCloserThan(x.begin(), x.end(), d);
  }

  inline void fromDense(PyObject* py_m)
  {
    nupic::NumpyMatrixT<nupic::Real32> m(py_m);
    self->fromDense(m.rows(), m.columns(), 
		    m.addressOf(0,0), m.addressOf(0,0) + m.rows() * m.columns());
  }

  inline PyObject* toDense() const 
  {
    int dims[] = { self->nRows(), self->nCols() };
    nupic::NumpyMatrixT<nupic::Real32> out(dims);
    self->toDense(out.addressOf(0, 0), out.addressOf(0, 0) + dims[0] * dims[1]);
    return out.forPython();
  }

  inline PyObject* toCSR() const
  {
    std::ostringstream s;
    self->toCSR(s);
    std::string str = s.str();
    return PyString_FromStringAndSize(str.data(), str.size());
  }

  inline void fromCSR(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseRLEMatrix state from string.");
    }
  }

  inline void CSRSaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toCSR(save_file);
    save_file.close();
  }

  inline void CSRLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromCSR(load_file);
    load_file.close();
  }

} // end extend nupic::SparseRLEMatrix
*/

//--------------------------------------------------------------------------------
 /*
%extend nupic::SparseRLEMatrix<nupic::UInt32, nupic::Real32>
{
%pythoncode %{

def __init__(self, *args): 
    if len(args) == 1:
        if isinstance(args[0], basestring):
            self.this = _MATH.new__SM_RLE_32_32()
            self.fromCSR(args[0])
        elif isinstance(args[0], numpy.ndarray) or hasattr(args[0], '__iter__'):
            self.this = _MATH.new__SM_RLE_32_32()
            self.fromDense(numpy.asarray(args[0]))
    else:
        self.this = _MATH.new__SM_RLE_32_32()	    
  
def __str__(self):
    return self.toDense().__str__()

def __setstate__(self, inString):
    self.this = _MATH.new__SM_RLE_32_32()
    self.thisown = 1
    self.fromCSR(inString)
%}

  inline PyObject* __getstate__() const
  {
    SharedPythonOStream py_s(self->CSRSize());
    std::ostream& s = py_s.getStream();
    self->toCSR(s);
    return py_s.close();
  }

  inline void readState(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseRLEMatrix state from string.");
    }
  }

  inline void appendRow(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    self->appendRow(x.begin(), x.end());
  }

  inline PyObject* getRowToDense(nupic::UInt32 row) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(self->nCols());
    self->getRowToDense(row, x.begin(), x.end());
    return x.forPython();
  }

  inline nupic::UInt32 firstRowCloserThan(PyObject* py_x, nupic::Real32 d) const
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    return self->firstRowCloserThan(x.begin(), x.end(), d);
  }

  inline void fromDense(PyObject* py_m)
  {
    nupic::NumpyMatrixT<nupic::Real32> m(py_m);
    self->fromDense(m.rows(), m.columns(), 
		    m.addressOf(0,0), m.addressOf(0,0) + m.rows() * m.columns());
  }

  inline PyObject* toDense() const 
  {
    int dims[] = { self->nRows(), self->nCols() };
    nupic::NumpyMatrixT<nupic::Real32> out(dims);
    self->toDense(out.addressOf(0, 0), out.addressOf(0, 0) + dims[0] * dims[1]);
    return out.forPython();
  }

  inline PyObject* toCSR() const
  {
    std::ostringstream s;
    self->toCSR(s);
    std::string str = s.str();
    return PyString_FromStringAndSize(str.data(), str.size());
  }

  inline void fromCSR(PyObject* str)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(str, &buf, &n); 
    if ((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->fromCSR(s);
    } else {
      throw std::runtime_error("Failed to read SparseRLEMatrix state from string.");
    }
  }

  inline void CSRSaveToFile(const std::string& filename) const
  {
    std::ofstream save_file(filename.c_str());
    self->toCSR(save_file);
    save_file.close();
  }

  inline void CSRLoadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->fromCSR(load_file);
    load_file.close();
  }

} // end extend nupic::SparseRLEMatrix

%pythoncode %{
  
  #SM_RLE_16_8 = _SM_RLE_16_8
  #SM_RLE_16_16 = _SM_RLE_16_16
  SM_RLE = _SM_RLE_32_32
  SparseRLEMatrix = _SM_RLE_32_32
  SM_RLE_32_32 = _SM_RLE_32_32

  def SparseRLEMatrix(*args, **keywords):
    return _SM_RLE_32_32(*args)
%}
*/

//--------------------------------------------------------------------------------
// Fast functions from our math library
//--------------------------------------------------------------------------------
%inline {

  inline nupic::Real32 l2_norm(PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    return nupic::l2_norm(x.begin(), x.end());
  }
 }

//--------------------------------------------------------------------------------
// GAUSSIAN 2D
//--------------------------------------------------------------------------------
%template(_Gaussian2D_32) nupic::Gaussian2D<nupic::Real32>;

%extend nupic::Gaussian2D<nupic::Real32>
{
  %pythoncode %{
    
    def __init__(self, *args): 
      this = _MATH.new__Gaussian2D_32(*args)
      try:
        self.this.append(this)
      except:
        self.this = this

    def __call__(self, x, y):
      return self.eval(x, y)
  %}

  inline nupic::Real32 eval(nupic::Real32 x, nupic::Real32 y) const
  {
    return self->operator()(x, y);
  }

} // end extend nupic::Gaussian2D

%pythoncode %{
  
  Gaussian_2D = _Gaussian2D_32

  def Gaussian2D(*args, **keywords):
    return _Gaussian2D_32(*args)
%}

//--------------------------------------------------------------------------------
// SET
//--------------------------------------------------------------------------------
%{
#include <nupic/math/Set.hpp>
%}

%include <nupic/math/Set.hpp>

%template (_Set) nupic::Set<nupic::UInt32>;

%extend nupic::Set<nupic::UInt32>
{
  %pythoncode %{
    
    def __init__(self, *args): 
      this = _MATH.new__Set()
      try:
        self.this.append(this)
      except:
        self.this = this
      self.construct(args[0], args[1])
  %}

  inline void construct(nupic::UInt32 m, PyObject* py_a)
  {
    PyArrayObject* _a = (PyArrayObject*) py_a;
    nupic::UInt32* a = (nupic::UInt32*)(_a->data);
    nupic::UInt32 n = _a->dimensions[0];
    self->construct(m, n, a);
  }

  inline nupic::UInt32 intersection(PyObject* py_s2, PyObject* py_r) const
  {
    PyArrayObject* _s2 = (PyArrayObject*) py_s2;
    nupic::UInt32* s2 = (nupic::UInt32*)(_s2->data);
    nupic::UInt32 n2 = _s2->dimensions[0];
    PyArrayObject* _r = (PyArrayObject*) py_r;
    nupic::UInt32* r = (nupic::UInt32*)(_r->data);

    return self->intersection(n2, s2, r);
  }

} // end extend nupic::Set

%pythoncode %{
  
  Set = _Set

  def Set(*args, **keywords):
    return _Set(*args)
%}

//--------------------------------------------------------------------------------
