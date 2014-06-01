%module engine_internal

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


%include <bindings/py/Exception.i>

%include "bindings/common/EngineInternalCommon.i"

%include "bindings/py/Numpy.i"
 
%init %{
 import_array();
%}


%include <py_support/PyArray.hpp>
%template(ByteArray) nta::PyArray<nta::Byte>;
%template(Int16Array) nta::PyArray<nta::Int16>;
%template(UInt16Array) nta::PyArray<nta::UInt16>;
%template(Int32Array) nta::PyArray<nta::Int32>;
%template(UInt32Array) nta::PyArray<nta::UInt32>;
%template(Int64Array) nta::PyArray<nta::Int64>;
%template(UInt64Array) nta::PyArray<nta::UInt64>;
%template(Real32Array) nta::PyArray<nta::Real32>;
%template(Real64Array) nta::PyArray<nta::Real64>;

%template(ByteArrayRef) nta::PyArrayRef<nta::Byte>;
%template(Int16ArrayRef) nta::PyArrayRef<nta::Int16>;
%template(UInt16ArrayRef) nta::PyArrayRef<nta::UInt16>;
%template(Int32ArrayRef) nta::PyArrayRef<nta::Int32>;
%template(UInt32ArrayRef) nta::PyArrayRef<nta::UInt32>;
%template(Int64ArrayRef) nta::PyArrayRef<nta::Int64>;
%template(UInt64ArrayRef) nta::PyArrayRef<nta::UInt64>;
%template(Real32ArrayRef) nta::PyArrayRef<nta::Real32>;
%template(Real64ArrayRef) nta::PyArrayRef<nta::Real64>;


%extend nta::Timer
{
  // Extend here (engine_internal) rather than nupic.engine because
  // in order to have properties, we would have to define a wrapper
  // class, and explicitly forward all methods to the contained class
  %pythoncode %{
    def __str__(self):
      return self.toString()

    elapsed = property(getElapsed)
    startCount = property(getStartCount)
  %}
}

%extend nta::Region
{
  PyObject * getSelf()
  {
    nta::Handle h = self->getParameterHandle("self");
    PyObject * p = (PyObject *)h;
    return p;
  }
  
  PyObject * getInputArray(std::string name)
  {
    return nta::PyArrayRef<nta::Byte>(self->getInputData(name)).asNumpyArray();
  }

  PyObject * getOutputArray(std::string name)
  {
    return nta::PyArrayRef<nta::Byte>(self->getOutputData(name)).asNumpyArray();
  }
}


%{
#include <nta/os/OS.hpp>
%}

// magic swig incantation
// provides: (real, virtual) = OS.getProcessMemoryUsage()
%include <typemaps.i>
class nta::OS
{
public:
  static void OS::getProcessMemoryUsage(size_t& OUTPUT, size_t& OUTPUT);
};


