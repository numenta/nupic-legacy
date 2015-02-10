#ifdef NTA_PYTHON_SUPPORT

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

/** @file
 */



//#define NO_IMPORT_ARRAY
#include <Python.h>

#include <numpy/arrayobject.h>

// workaround for change in numpy config.h for python2.5 on windows
// Must come after python includes.
#ifndef SIZEOF_FLOAT
#define SIZEOF_FLOAT 32
#endif

#ifndef SIZEOF_DOUBLE
#define SIZEOF_DOUBLE 64
#endif

#include <py_support/NumpyVector.hpp>

#include <stdexcept>
#include <iostream>

using namespace std;
using namespace nupic;

// --------------------------------------------------------------
// Auto-convert a compile-time type to a Numpy dtype.
// --------------------------------------------------------------

template<typename T>
class NumpyDTypeTraits {};

template<typename T>
int LookupNumpyDTypeT(const T *)
  { return NumpyDTypeTraits<T>::numpyDType; }

#define NTA_DEF_NUMPY_DTYPE_TRAIT(a, b) \
template<> class NumpyDTypeTraits<a> { public: enum { numpyDType=b }; }; \
int nupic::LookupNumpyDType(const a *p) { return LookupNumpyDTypeT(p); }

NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Byte, PyArray_BYTE);
NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Int16, PyArray_INT16);
NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::UInt16, PyArray_UINT16);

#if defined(NTA_ARCH_64) && (defined(NTA_OS_LINUX) || defined(NTA_OS_DARWIN) || defined(NTA_OS_SPARC))
NTA_DEF_NUMPY_DTYPE_TRAIT(size_t, PyArray_UINT64);
#else
NTA_DEF_NUMPY_DTYPE_TRAIT(size_t, PyArray_UINT32);
#endif

NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Int32, PyArray_INT32);

#if !(defined(NTA_ARCH_32) && defined(NTA_OS_LINUX))
// size_t (above) is the same as UInt32 on linux32
NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::UInt32, PyArray_UINT32);
#endif

NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Int64, PyArray_INT64);

#if !(defined(NTA_ARCH_64) && (defined(NTA_OS_LINUX) || defined(NTA_OS_DARWIN) || defined(NTA_OS_SPARC)))
NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::UInt64, PyArray_UINT64);
#endif


NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Real32, PyArray_FLOAT32);
NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Real64, PyArray_FLOAT64);

#ifdef NTA_QUAD_PRECISION
NTA_DEF_NUMPY_DTYPE_TRAIT(nupic::Real128, PyArray_FLOAT128);
#endif

// --------------------------------------------------------------


void NumpyArray::init()
{
  int rc = _import_array();
  if (rc < 0) {
    throw std::runtime_error("NumpyArray::init(): "
      "numpy.core.multiarray failed to import.");
  }
}

inline void CheckInit()
  { NumpyArray::init(); }

NumpyArray::NumpyArray(int nd, const int *ndims, int dtype)
  : p_(0), dtype_(dtype)
{

  // declare static to avoid new/delete with every call
  static npy_intp ndims_intp[NPY_MAXDIMS];

  CheckInit();

  if(nd < 0)
    throw runtime_error("Negative dimensioned arrays not supported.");

  if (nd > NPY_MAXDIMS)
    throw runtime_error("Too many dimensions specified for NumpyArray()");

  /* copy into array with elements that are the correct size.
   * npy_intp is an integer that can hold a pointer. On 64-bit
   * systems this is not the same as an int.
   */
  for (int i = 0; i < nd; i++)
  {
    ndims_intp[i] = (npy_intp)ndims[i];
  }

  p_ = (PyArrayObject *) PyArray_SimpleNew(nd, ndims_intp, dtype);

}

NumpyArray::NumpyArray(PyObject *p, int dtype, int requiredDimension)
  : p_(0), dtype_(dtype)
{
  CheckInit();

  PyObject *contiguous = PyArray_ContiguousFromObject(p, PyArray_NOTYPE, 0, 0);
  if(!contiguous)
    throw std::runtime_error("Array could not be made contiguous.");
  if(!PyArray_Check(contiguous))
    throw std::logic_error("Failed to convert to array.");

  PyObject *casted = PyArray_Cast((PyArrayObject *) contiguous, dtype);
  Py_CLEAR(contiguous);

  if(!casted) throw std::runtime_error("Array could not be cast to requested type.");
  if(!PyArray_Check(casted)) throw std::logic_error("Array is not contiguous.");
  PyArrayObject *final = (PyArrayObject *) casted;
  if((requiredDimension != 0) && (final->nd != requiredDimension))
    throw std::runtime_error("Array is not of the required dimension.");
  p_ = final;
}

NumpyArray::~NumpyArray()
{
  PyObject *generic = (PyObject *) p_;
  p_ = 0;
  Py_CLEAR(generic);
}

int NumpyArray::getRank() const
{
  if(!p_) throw runtime_error("Null NumpyArray.");
  return p_->nd;
}

int NumpyArray::dimension(int i) const
{
  if(!p_) throw runtime_error("Null NumpyArray.");
  if(i < 0) throw runtime_error("Negative dimension requested.");
  if(i >= p_->nd) throw out_of_range("Dimension exceeds number available.");
  return int(p_->dimensions[i]);
}

void NumpyArray::getDims(int *out) const
{
  if(!p_) throw runtime_error("Null NumpyArray.");
  int n = p_->nd;
  for(int i=0; i<n; ++i) out[i] = int(p_->dimensions[i]); // npy_intp? New type in latest numpy headers.
}

const char *NumpyArray::addressOf0() const
{
  if(!p_) throw runtime_error("Null NumpyArray.");
  return p_->data;
}
char *NumpyArray::addressOf0()
{
  if(!p_) throw runtime_error("Numpy NumpyArray.");
  return p_->data;
}

int NumpyArray::stride(int i) const
{
  if(!p_) throw runtime_error("Numpy NumpyArray.");
  return int(p_->strides[i]); // npy_intp? New type in latest numpy headers.
}

PyObject *NumpyArray::forPython() {
  if(p_) {
    Py_XINCREF(p_);
    PyObject *toReturn = PyArray_Return((PyArrayObject *)p_);
    return toReturn;
  }
  else return 0;
}

#endif // NTA_PYTHON_SUPPORT


