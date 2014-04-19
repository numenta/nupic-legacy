%module(package="nupic.bindings") iorange

%include <lang/py/bindings/Exception.i>

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
#include <lang/py/support/NumpyVector.hpp>
#include <py/bindings/iorange/WrappedVector.hpp>
#include <nta/ntypes/ArrayBase.hpp>

%}

%naturalvar;

%include <lang/py/bindings/Exception.i>
%include <lang/py/bindings/Numpy.i>
%include <py/bindings/Types.i>
%include <py/bindings/Reals.i>

// An easy-to-wrap vector class that is designed to 
// look like a Python container.

%ignore nta::WrappedVectorIter::operator[];
%ignore nta::WrappedVectorIter::operator++;
%ignore nta::WrappedVectorIter::operator--;
%ignore nta::WrappedVector::operator=;

%include <lang/py/support/NumpyVector.hpp>
%include <py/bindings/iorange/WrappedVector.hpp>
%template(WrappedVectorList) std::vector<nta::WrappedVector>;

%extend nta::WrappedVector {

  // Used by NuPIC 2 to directly wrap an array object
  void setFromArray(PyObject* parray)
  {
    if (!PyCObject_Check(parray))
    {
      throw std::invalid_argument("setFromArray -- object is not a CObject");
    }
    nta::ArrayBase* array = (nta::ArrayBase*)PyCObject_AsVoidPtr(parray);
    if (array->getType() != NTA_BasicType_Real32)
    {
      throw std::invalid_argument("setFromArray -- array datatype is not Real32");
    }
    self->setPointer(array->getCount(), (nta::Real*)array->getBuffer());
  }


void copyFromPointer(size_t n, PyObject * obj) {
  nta::Real * p = (nta::Real *) PyCObject_AsVoidPtr(obj);
  if (n != self->__len__())
    throw std::invalid_argument("Sizes must match.");
  self->copyFromT(n, 1, p);
}

void copyFromArray(PyObject *obj) {
  nta::NumpyVector v(obj);
  nta::Size n = v.size();
  if(!(n == self->__len__())) throw std::invalid_argument("Sizes must match.");
  self->copyFromT(n, v.incr(), v.addressOf(0));
}

nta::WrappedVector __getslice__(long long i, long long j) const {
  self->adjust(i);
  self->adjust(j);
  return self->slice(i, j);
}

void __setslice__(long long i, long long j, PyObject *obj) {
  self->adjust(i);
  self->adjust(j);
  nta::NumpyVector v(obj);
  nta::Size n = v.size();
  nta::WrappedVector toSet = self->slice(i, j);
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
  nta::NumpyVector v(n);
  self->copyIntoT(n, v.incr(), v.addressOf(0));
  return v.forPython();
}

}

