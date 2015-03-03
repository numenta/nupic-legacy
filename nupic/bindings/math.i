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

%module(package="nupic.bindings") math
%include <nupic/bindings/exception.i>

%pythoncode %{
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

_MATH = _math

%}

%{
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

#include <cmath>
#include <nupic/types/Types.hpp>
#include <nupic/math/Utils.hpp>
#include <nupic/math/Math.hpp>
#include <nupic/math/Functions.hpp>
#include <nupic/math/ArrayAlgo.hpp>
#include <nupic/proto/RandomProto.capnp.h>
#include <nupic/utils/Random.hpp>
#include <numpy/arrayobject.h>

#include <py_support/PyCapnp.hpp>
%}

%naturalvar;

%{
#define SWIG_FILE_WITH_INIT
%}

%include <nupic/bindings/numpy.i> // %import does not work.

%init %{

// Perform necessary library initialization (in C++).
import_array();
  
%}

%include <nupic/bindings/types.i>
%include <nupic/bindings/reals.i>

///////////////////////////////////////////////////////////////////
/// Utility functions that are expensive in Python but fast in C.
///////////////////////////////////////////////////////////////////


%include <nupic/bindings/sparse_matrix.i>
%include <nupic/bindings/sparse_tensor.i>

//--------------------------------------------------------------------------------
%inline {

  nupic::Real64 lgamma(nupic::Real64 x)
  {
    return nupic::lgamma(x);
  }

  nupic::Real64 digamma(nupic::Real64 x)
  {
    return nupic::digamma(x);
  }

  nupic::Real64 beta(nupic::Real64 x, nupic::Real64 y)
  {
    return nupic::beta(x, y);
  }

  nupic::Real64 erf(nupic::Real64 x)
  {
    return nupic::erf(x);
  }

  bool nearlyZeroRange(PyObject* py_x, nupic::Real32 eps =nupic::Epsilon)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    return nupic::nearlyZeroRange(x.begin(), x.end(), eps);
  }

  bool nearlyEqualRange(PyObject* py_x, PyObject* py_y, nupic::Real32 eps =nupic::Epsilon)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x), y(py_y);
    return nupic::nearlyEqualRange(x.begin(), x.end(), y.begin(), y.end(), eps);
  }

  bool positive_less_than(PyObject* py_x, nupic::Real32 eps =nupic::Epsilon)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    return nupic::positive_less_than(x.begin(), x.end(), eps);
  }

  /*
  inline PyObject* quantize_255(PyObject* py_x, nupic::Real32 x_min, nupic::Real32 x_max)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x), y(x.size());
    nupic::quantize(x.begin(), x.end(), y.begin(), y.end(),
		  x_min, x_max, 1, 255);
    return y.forPython();
  }

  inline PyObject* quantize_65535(PyObject* py_x, nupic::Real32 x_min, nupic::Real32 x_max)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x), y(x.size());
    nupic::quantize(x.begin(), x.end(), y.begin(), y.end(),
		  x_min, x_max, 1, 65535);
    return y.forPython();
  }
  */			 

  PyObject* winnerTakesAll_3(size_t k, size_t seg_size, PyObject* py_x)
  {
    nupic::NumpyVectorT<nupic::Real32> x(py_x);
    std::vector<int> ind;
    std::vector<nupic::Real32> nz;
    nupic::winnerTakesAll3(k, seg_size, x.begin(), x.end(),
		    std::back_inserter(ind), std::back_inserter(nz));
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nupic::PyInt32Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, nupic::PyFloatVector(nz.begin(), nz.end()));
    return toReturn;
  }
}

//--------------------------------------------------------------------------------

%include <nupic/math/Functions.hpp>

// ----- Random -----

%include <nupic/utils/LoggingException.hpp>
%include <nupic/utils/Random.hpp>

%extend nupic::Random {

// For unpickling.
%pythoncode %{
def __setstate__(self, state):
  self.this = _MATH.new_Random(1)
  self.thisown = 1
  self.setState(state)
%}

// For pickling (should be compatible with setState()).
std::string __getstate__()
{
  std::stringstream ss;
  ss << *self;
  return ss.str();
}

// For Python standard library 'random' interface.
std::string getState()
{
  std::stringstream ss;
  ss << *self;
  return ss.str();
}

// For Python standard library 'random' interface.
void setState(const std::string &s)
{
  std::stringstream ss(s);
  ss >> *self;
}

void setSeed(PyObject *x)
{
  long seed_ = PyObject_Hash(x);
  *self = nupic::Random(seed_);
}

void jumpAhead(unsigned int n)
{ // WARNING: Slow!
  while(n) { self->getUInt32(nupic::Random::MAX32); --n; }
}

inline void initializeUInt32Array(PyObject* py_array, nupic::UInt32 max_value)
{
  PyArrayObject* array = (PyArrayObject*) py_array;
  nupic::UInt32* array_data = (nupic::UInt32*) array->data;
  nupic::UInt32 size = array->dimensions[0];
  for (nupic::UInt32 i = 0; i != size; ++i)
    array_data[i] = self->getUInt32() % max_value;
}

inline void initializeReal32Array(PyObject* py_array)
{
  PyArrayObject* array = (PyArrayObject*) py_array;
  nupic::Real32* array_data = (nupic::Real32*) array->data;
  nupic::UInt32 size = array->dimensions[0];
  for (nupic::UInt32 i = 0; i != size; ++i)
    array_data[i] = (nupic::Real32) self->getReal64();
}

inline void initializeReal32Array_01(PyObject* py_array, nupic::Real32 proba)
{
  PyArrayObject* array = (PyArrayObject*) py_array;
  nupic::Real32* array_data = (nupic::Real32*) array->data;
  nupic::Real32 size = array->dimensions[0];
  for (nupic::UInt32 i = 0; i != size; ++i)
    array_data[i] = (nupic::Real32)(self->getReal64() <= proba ? 1.0 : 0.0);
}

inline PyObject* sample(PyObject* population, PyObject* choices)
{
  if (PyArray_Check(population) && PyArray_Check(choices))
  {
    PyArrayObject* values = (PyArrayObject*) population;
    PyArrayObject* result = (PyArrayObject*) choices;

    if (values->nd != 1 || result->nd != 1)
    {
      PyErr_SetString(PyExc_ValueError,
                     "Only one dimensional arrays are supported.");
      return NULL;
    }

    if (PyArray_DESCR(values)->type_num != PyArray_DESCR(result)->type_num)
    {
      PyErr_SetString(
          PyExc_ValueError,
          "Type of value in polation and choices arrays must match.");
      return NULL;
    }

    try
    {
      if (PyArray_DESCR(values)->type_num == NPY_UINT32)
      {
        nupic::UInt32* valuesStart = (nupic::UInt32*) values->data;
        nupic::UInt32 valuesSize = values->dimensions[0];

        nupic::UInt32* resultStart = (nupic::UInt32*) result->data;
        nupic::UInt32 resultSize = result->dimensions[0];

        self->sample(valuesStart, valuesSize, resultStart, resultSize);
      } else if (PyArray_DESCR(values)->type_num == NPY_UINT64) {
        nupic::UInt64* valuesStart = (nupic::UInt64*) values->data;
        nupic::UInt64 valuesSize = values->dimensions[0];

        nupic::UInt64* resultStart = (nupic::UInt64*) result->data;
        nupic::UInt64 resultSize = result->dimensions[0];

        self->sample(valuesStart, valuesSize, resultStart, resultSize);
      } else {
        PyErr_SetString(PyExc_TypeError,
                       "Unexpected array dtype. Expected 'uint32' or 'uint64'.");
        return NULL;
      }
    }
    catch (nupic::LoggingException& exception)
    {
      PyErr_SetString(PyExc_ValueError, exception.getMessage());
      return NULL;
    }
  } else {
    PyErr_SetString(PyExc_TypeError,
                   "Unsupported type. Expected Numpy array.");
    return NULL;
  }

  Py_INCREF(choices);
  return choices;
}

inline PyObject* shuffle(PyObject* obj)
{
  if (PyArray_Check(obj))
  {
    PyArrayObject* arr = (PyArrayObject*) obj;

    if (arr->nd != 1)
    {
      PyErr_SetString(PyExc_ValueError,
                     "Only one dimensional arrays are supported.");
      return NULL;
    }

    if (PyArray_DESCR(arr)->type_num == NPY_UINT32)
    {
      nupic::UInt32* arrStart = (nupic::UInt32*) arr->data;
      nupic::UInt32* arrEnd = arrStart + arr->dimensions[0];

      self->shuffle(arrStart, arrEnd);
    } else if (PyArray_DESCR(arr)->type_num == NPY_UINT64) {
      nupic::UInt64* arrStart = (nupic::UInt64*) arr->data;
      nupic::UInt64* arrEnd = arrStart + arr->dimensions[0];

      self->shuffle(arrStart, arrEnd);
    } else {
      PyErr_SetString(PyExc_ValueError,
                     "Unexpected array dtype. Expected 'uint32' or 'uint64'.");
      return NULL;
    }
  } else {
    PyErr_SetString(PyExc_TypeError,
                   "Unsupported type. Expected Numpy array.");
    return NULL;
  }

  Py_INCREF(obj);
  return obj;
}

inline void write(PyObject* pyBuilder) const
{
  RandomProto::Builder proto = nupic::getBuilder<RandomProto>(pyBuilder);
  self->write(proto);
}

inline void read(PyObject* pyReader)
{
  RandomProto::Reader proto = nupic::getReader<RandomProto>(pyReader);
  self->read(proto);
}

} // End extend nupic::Random.
