/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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

/** @file 
 */

#ifdef _PY27 
#include <python2.7/Python.h>
#else
#include <python2.6/Python.h>
#endif

#include <lang/py/support/NumpyVector.hpp>
#include <py/bindings/math/PySparseTensor.hpp>

using namespace std;
using namespace nta;

typedef nta::SparseTensor<PyTensorIndex, nta::Real> STBase;

PySparseTensor::PySparseTensor(PyObject *numpyArray)
  // TODO: Switch to rank 0 (or at least dimension 0) default.
  : tensor_(PyTensorIndex(1))
{
  NumpyNDArray a(numpyArray);
  int rank = a.getRank();
  if(rank > PYSPARSETENSOR_MAX_RANK)
    throw invalid_argument("Array rank exceeds max rank for SparseTensor bindings.");
  int dims[PYSPARSETENSOR_MAX_RANK]; // Never larger than max ND array rank.
  a.getDims(dims);
  tensor_ = STBase(PyTensorIndex(rank, dims));
  tensor_.fromDense(a.getData());
}

void PySparseTensor::set(const PyTensorIndex &i, PyObject *x)
{
  PyObject *num = PyNumber_Float(x);
  if(!num) throw std::invalid_argument("value is not a float.");
  nta::Real y = (nta::Real) PyFloat_AsDouble(num);
  Py_CLEAR(num);
  set(i, y);
}

PyObject *PySparseTensor::toDense() const
{
  const PyTensorIndex &bounds = tensor_.getBounds();
  int rank = bounds.size();
  int dims[PYSPARSETENSOR_MAX_RANK];
  if(rank > PYSPARSETENSOR_MAX_RANK)
    throw std::logic_error("Rank exceeds max rank.");
  for(int i=0; i<rank; ++i)
    dims[i] = bounds[i];
  NumpyNDArray a(rank, dims);
  tensor_.toDense(a.getData());
  return a.forPython();
}

PyObject *PySparseTensor::__str__() const
{
  PyObject *a = toDense();
  PyObject *s = PyObject_Str(a);
  Py_CLEAR(a);
  return s;
}

string PySparseTensor::__getstate__() const
{
#if 1
  stringstream s;
  tensor_.toStream(s);
  return s.str();
#else
  stringstream s;
  PyTensorIndex bounds = tensor_.getBounds();
  size_t n = bounds.size();
  s << n << " ";
  for(size_t i=0; i<n; ++i)
    s << bounds[i] << " ";
  s << "\n";
  size_t nz = tensor_.getNNonZeros();
  s << nz << "\n";
  STBase::const_iterator i = tensor_.begin();
  STBase::const_iterator end = tensor_.end();
  for(; i!=end; ++i) {
    const PyTensorIndex &key = i->first;
    const nta::Real &value = i->second;
    for(size_t j=0; j<n; ++j)
      s << key[j] << " ";
    s << value << "\n";
  }
  return s.str();
#endif
}

#if 1
inline STBase SparseTensorFromString(const string &s) {
  size_t rank = 0;
  {
    stringstream forRank(s);
    forRank.exceptions(ios::failbit | ios::badbit);
    forRank >> rank;
  };
  PyTensorIndex index(rank, (const size_t *) 0);
  for(size_t i=0; i<rank; ++i) {
    index[i] = 1;
  }
  STBase tensor(index);
  stringstream toRead(s);
  tensor.fromStream(toRead);
  return tensor;
}

PySparseTensor::PySparseTensor(const string &s)
  : tensor_(SparseTensorFromString(s))
{}

#else
inline STBase SparseTensorFromStream(istream &s)
{
  size_t n = 0;
  s >> n;
  PyTensorIndex bounds(n, (const size_t *) 0);
  for(size_t i=0; i<n; ++i) {
    bounds[i] = 0;
    s >> bounds[i];
  }
  STBase tensor(bounds);
  size_t m = 0;
  s >> m;
  PyTensorIndex key(n, (const size_t *) 0);
  for(size_t i=0; i<m; ++i) {
    for(size_t j=0; j<n; ++j) {
      key[j] = 0;
      s >> key[j];
    }
    nta::Real value = 0;
    s >> value;
    tensor.set(key, value);
  }
  return tensor;
}

template<typename T>
struct PtrMgr
{
  T *p_;
  PtrMgr(T *p) : p_(p) {}
  ~PtrMgr() { delete p_; }
  operator T &() const { return *p_; }
};

PySparseTensor::PySparseTensor(const string &s)
  : tensor_(SparseTensorFromStream(
      PtrMgr<istream>(new stringstream(s))
    ))
{}
#endif

double PySparseTensor::marginalize() const
{
  return tensor_.sum();
}

PyTensorIndex PySparseTensor::argmax() const
{
  return tensor_.max().first;
}

nta::Real PySparseTensor::max() const
{
  return tensor_.max().second;
}

PySparseTensor PySparseTensor::__mul__(const nta::Real& x) const
{
  PySparseTensor out(tensor_.getBounds());
  tensor_.multiply(x, out.tensor_);
  return out;
}

