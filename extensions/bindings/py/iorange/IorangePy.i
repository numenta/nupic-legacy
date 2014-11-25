%module(package="nupic.bindings") iorange

%include <bindings/py/Exception.i>

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
%}

///////////////////////////////////////////////////////////////////
/// Includes necessary to compile the C wrappers
///////////////////////////////////////////////////////////////////

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

#include <numpy/arrayobject.h>
#include <py_support/NumpyVector.hpp>
#include <bindings/py/iorange/WrappedVector.hpp>
#include <nta/ntypes/ArrayBase.hpp>

%}

%naturalvar;

%include <bindings/py/Exception.i>
%include <bindings/py/Numpy.i>
%include <bindings/py/Types.i>
%include <bindings/py/Reals.i>

// An easy-to-wrap vector class that is designed to 
// look like a Python container.

%ignore nupic::WrappedVectorIter::operator[];
%ignore nupic::WrappedVectorIter::operator++;
%ignore nupic::WrappedVectorIter::operator--;
%ignore nupic::WrappedVector::operator=;

%include <py_support/NumpyVector.hpp>
%include <bindings/py/iorange/WrappedVector.hpp>
%template(WrappedVectorList) std::vector<nupic::WrappedVector>;

%extend nupic::WrappedVector {

  // Used by NuPIC 2 to directly wrap an array object
  void setFromArray(PyObject* parray)
  {
    if (!PyCObject_Check(parray))
    {
      throw std::invalid_argument("setFromArray -- object is not a CObject");
    }
    nupic::ArrayBase* array = (nupic::ArrayBase*)PyCObject_AsVoidPtr(parray);
    if (array->getType() != NTA_BasicType_Real32)
    {
      throw std::invalid_argument("setFromArray -- array datatype is not Real32");
    }
    self->setPointer(array->getCount(), (nupic::Real*)array->getBuffer());
  }


void copyFromPointer(size_t n, PyObject * obj) {
  nupic::Real * p = (nupic::Real *) PyCObject_AsVoidPtr(obj);
  if (n != self->__len__())
    throw std::invalid_argument("Sizes must match.");
  self->copyFromT(n, 1, p);
}

void copyFromArray(PyObject *obj) {
  nupic::NumpyVector v(obj);
  nupic::Size n = v.size();
  if(!(n == self->__len__())) throw std::invalid_argument("Sizes must match.");
  self->copyFromT(n, v.incr(), v.addressOf(0));
}

nupic::WrappedVector __getslice__(long long i, long long j) const {
  self->adjust(i);
  self->adjust(j);
  return self->slice(i, j);
}

void __setslice__(long long i, long long j, PyObject *obj) {
  self->adjust(i);
  self->adjust(j);
  nupic::NumpyVector v(obj);
  nupic::Size n = v.size();
  nupic::WrappedVector toSet = self->slice(i, j);
  if(!(n == toSet.__len__())) {
    char errBuffer[256];
    snprintf(errBuffer, 256-1, 
        "Expected to set slice of size %d but received %d inputs.",
        (int) toSet.__len__(), (int) n);
    throw std::invalid_argument(errBuffer);
  }
  toSet.copyFromT(n, v.incr(), v.addressOf(0));
}

PyObject *array() const {
  int n = self->__len__();
  nupic::NumpyVector v(n);
  self->copyIntoT(n, v.incr(), v.addressOf(0));
  return v.forPython();
}

}

