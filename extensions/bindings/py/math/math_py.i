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
%include <bindings/py/exception.i>

///////////////////////////////////////////////////////////////////
/// Includes necessary to compile the C wrappers
///////////////////////////////////////////////////////////////////

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
#include <nta/types/types.hpp>
#include <nta/math/utils.hpp>
#include <nta/math/math.hpp>
#include <nta/math/functions.hpp>
#include <nta/math/array_algo.hpp>
#include <nta/utils/Random.hpp>
%}

%naturalvar;

%{
#define SWIG_FILE_WITH_INIT
%}

%include <bindings/py/numpy.i> // %import does not work.

%init %{

// Perform necessary library initialization (in C++).
  
%}

%include <bindings/py/types.i>
%include <bindings/py/reals.i>

///////////////////////////////////////////////////////////////////
/// Utility functions that are expensive in Python but fast in C.
///////////////////////////////////////////////////////////////////


%include <bindings/py/math/SparseMatrix.i>
%include <bindings/py/math/SparseTensor.i>

//--------------------------------------------------------------------------------
%inline {

  inline nta::Real64 lgamma(nta::Real64 x)
  {
    return nta::lgamma(x);
  }

  inline nta::Real64 digamma(nta::Real64 x)
  {
    return nta::digamma(x);
  }

  inline nta::Real64 beta(nta::Real64 x, nta::Real64 y)
  {
    return nta::beta(x, y);
  }

  inline nta::Real64 erf(nta::Real64 x)
  {
    return nta::erf(x);
  }

  bool nearlyZeroRange(PyObject* py_x, nta::Real32 eps =nta::Epsilon)
  {
    nta::NumpyVectorT<nta::Real32> x(py_x);
    return nta::nearlyZeroRange(x.begin(), x.end(), eps);
  }

  bool nearlyEqualRange(PyObject* py_x, PyObject* py_y, nta::Real32 eps =nta::Epsilon)
  {
    nta::NumpyVectorT<nta::Real32> x(py_x), y(py_y);
    return nta::nearlyEqualRange(x.begin(), x.end(), y.begin(), y.end(), eps);
  }

  bool positive_less_than(PyObject* py_x, nta::Real32 eps =nta::Epsilon)
  {
    nta::NumpyVectorT<nta::Real32> x(py_x);
    return nta::positive_less_than(x.begin(), x.end(), eps);
  }

  /*
  inline PyObject* quantize_255(PyObject* py_x, nta::Real32 x_min, nta::Real32 x_max)
  {
    nta::NumpyVectorT<nta::Real32> x(py_x), y(x.size());
    nta::quantize(x.begin(), x.end(), y.begin(), y.end(),
		  x_min, x_max, 1, 255);
    return y.forPython();
  }

  inline PyObject* quantize_65535(PyObject* py_x, nta::Real32 x_min, nta::Real32 x_max)
  {
    nta::NumpyVectorT<nta::Real32> x(py_x), y(x.size());
    nta::quantize(x.begin(), x.end(), y.begin(), y.end(),
		  x_min, x_max, 1, 65535);
    return y.forPython();
  }
  */			 

  PyObject* winnerTakesAll_3(size_t k, size_t seg_size, PyObject* py_x)
  {
    nta::NumpyVectorT<nta::Real32> x(py_x);
    std::vector<int> ind;
    std::vector<nta::Real32> nz;
    nta::winnerTakesAll3(k, seg_size, x.begin(), x.end(),
		    std::back_inserter(ind), std::back_inserter(nz));
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, nta::PyInt32Vector(ind.begin(), ind.end()));
    PyTuple_SET_ITEM(toReturn, 1, nta::PyFloatVector(nz.begin(), nz.end()));
    return toReturn;
  }
}

//--------------------------------------------------------------------------------

%include <nta/math/functions.hpp>

// ----- Random -----

%include <nta/utils/Random.hpp>

%extend nta::Random {

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
  *self = nta::Random(seed_);
}

void jumpAhead(unsigned int n)
{ // WARNING: Slow!
  while(n) { self->getUInt32(nta::Random::MAX32); --n; }
}

inline void initializeUInt32Array(PyObject* py_array, nta::UInt32 max_value)
{
  PyArrayObject* array = (PyArrayObject*) py_array;
  nta::UInt32* array_data = (nta::UInt32*) array->data;
  nta::UInt32 size = array->dimensions[0];
  for (nta::UInt32 i = 0; i != size; ++i)
    array_data[i] = self->getUInt32() % max_value;
}

inline void initializeReal32Array(PyObject* py_array)
{
  PyArrayObject* array = (PyArrayObject*) py_array;
  nta::Real32* array_data = (nta::Real32*) array->data;
  nta::UInt32 size = array->dimensions[0];
  for (nta::UInt32 i = 0; i != size; ++i)
    array_data[i] = (nta::Real32) self->getReal64();
}

inline void initializeReal32Array_01(PyObject* py_array, nta::Real32 proba)
{
  PyArrayObject* array = (PyArrayObject*) py_array;
  nta::Real32* array_data = (nta::Real32*) array->data;
  nta::Real32 size = array->dimensions[0];
  for (nta::UInt32 i = 0; i != size; ++i)
    array_data[i] = (nta::Real32)(self->getReal64() <= proba ? 1.0 : 0.0);
}

inline void getUInt32Sample(PyObject* py_values, PyObject* py_result, bool sorted =false)
{
  PyArrayObject* values = (PyArrayObject*) py_values;
  nta::UInt32* values_beg = (nta::UInt32*) values->data;
  nta::UInt32* values_end = values_beg + values->dimensions[0];

  PyArrayObject* result = (PyArrayObject*) py_result;
  nta::UInt32* result_beg = (nta::UInt32*) result->data;
  nta::UInt32* result_end = result_beg + result->dimensions[0];

  std::random_shuffle(values_beg, values_end, *self);
  std::copy(values_beg, values_beg + (result_end - result_beg), result_beg);

  if (sorted) 
    std::sort(result_beg, result_end);
}

} // End extend nta::Random.

%pythoncode %{
import random
class StdRandom(random.Random):
  """An adapter for nta::Random that allows use of inherited samplers 
  from the Python standard library 'random' module."""
  def __init__(self, *args, **keywords):
    self.rgen = Random(*args, **keywords)
  def random(self): return self.rgen.getReal64()
  def setstate(self, state): self.rgen.setState(state)
  def getstate(self): return self.rgen.getState()
  def jumpahead(self, n): self.rgen.jumpAhead(n)
  def seed(self, seed=None):
    if seed is None: self.rgen.setSeed(0)
    else: self.rgen.setSeed(seed)
%}


