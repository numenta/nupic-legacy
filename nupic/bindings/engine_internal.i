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

%module engine_internal
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
 * ----------------------------------------------------------------------
*/


#include <nupic/types/Types.hpp>
#include <nupic/types/Types.h>
#include <nupic/types/BasicType.hpp>
#include <nupic/types/Exception.hpp>
#include <nupic/ntypes/Dimensions.hpp>
#include <nupic/ntypes/Array.hpp>
#include <nupic/ntypes/ArrayRef.hpp>
#include <nupic/ntypes/Collection.hpp>

#include <nupic/utils/Log.hpp>
#include <nupic/utils/LogItem.hpp>
#include <nupic/utils/LoggingException.hpp>



#include <py_support/PyArray.hpp>

#include <nupic/engine/NuPIC.hpp>
#include <nupic/engine/Network.hpp>

#include <nupic/engine/Spec.hpp>
#include <nupic/utils/Watcher.hpp>
#include <nupic/engine/Region.hpp>
#include <nupic/os/Timer.hpp>
%}

%include "std_pair.i"
%include "std_string.i"
%include "std_vector.i"
%include "std_map.i"
%include "std_set.i"
%template(StringVec) std::vector<std::string>;


%include <nupic/types/Types.h>
%include <nupic/types/Types.hpp>
%include <nupic/types/BasicType.hpp>
%include <nupic/types/Exception.hpp>

// For Network::get/setPhases()
%template(UInt32Set) std::set<nupic::UInt32>;


//32bit fix -  Already seen by swig on linux32 where size_t is the same size as unsigned int
#if !(defined(NTA_ARCH_32) && defined(NTA_OS_LINUX))
%template(Dimset) std::vector<size_t>;
#endif

%include <nupic/ntypes/Dimensions.hpp>
%include <nupic/ntypes/Array.hpp>
%include <nupic/ntypes/ArrayRef.hpp>

%include <nupic/ntypes/Collection.hpp>
%template(InputCollection) nupic::Collection<nupic::InputSpec>;
%template(OutputCollection) nupic::Collection<nupic::OutputSpec>;
%template(ParameterCollection) nupic::Collection<nupic::ParameterSpec>;
%template(CommandCollection) nupic::Collection<nupic::CommandSpec>;
%template(RegionCollection) nupic::Collection<nupic::Region *>;

%include <nupic/engine/NuPIC.hpp>
%include <nupic/engine/Network.hpp>
%ignore nupic::Region::getInputData;
%ignore nupic::Region::getOutputData;
%include <nupic/engine/Region.hpp>
%include <nupic/utils/Watcher.hpp>
%include <nupic/engine/Spec.hpp>

%template(InputPair) std::pair<std::string, nupic::InputSpec>;
%template(OutputPair) std::pair<std::string, nupic::OutputSpec>;
%template(ParameterPair) std::pair<std::string, nupic::ParameterSpec>;
%template(CommandPair) std::pair<std::string, nupic::CommandSpec>;
%template(RegionPair) std::pair<std::string, nupic::Region *>;

%include <nupic/os/Timer.hpp>

%include <nupic/bindings/numpy.i>


%include <py_support/PyArray.hpp>
%template(ByteArray) nupic::PyArray<nupic::Byte>;
%template(Int16Array) nupic::PyArray<nupic::Int16>;
%template(UInt16Array) nupic::PyArray<nupic::UInt16>;
%template(Int32Array) nupic::PyArray<nupic::Int32>;
%template(UInt32Array) nupic::PyArray<nupic::UInt32>;
%template(Int64Array) nupic::PyArray<nupic::Int64>;
%template(UInt64Array) nupic::PyArray<nupic::UInt64>;
%template(Real32Array) nupic::PyArray<nupic::Real32>;
%template(Real64Array) nupic::PyArray<nupic::Real64>;

%template(ByteArrayRef) nupic::PyArrayRef<nupic::Byte>;
%template(Int16ArrayRef) nupic::PyArrayRef<nupic::Int16>;
%template(UInt16ArrayRef) nupic::PyArrayRef<nupic::UInt16>;
%template(Int32ArrayRef) nupic::PyArrayRef<nupic::Int32>;
%template(UInt32ArrayRef) nupic::PyArrayRef<nupic::UInt32>;
%template(Int64ArrayRef) nupic::PyArrayRef<nupic::Int64>;
%template(UInt64ArrayRef) nupic::PyArrayRef<nupic::UInt64>;
%template(Real32ArrayRef) nupic::PyArrayRef<nupic::Real32>;
%template(Real64ArrayRef) nupic::PyArrayRef<nupic::Real64>;


%extend nupic::Timer
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

%extend nupic::Region
{
  PyObject * getSelf()
  {
    nupic::Handle h = self->getParameterHandle("self");
    PyObject * p = (PyObject *)h;
    return p;
  }

  PyObject * getInputArray(std::string name)
  {
    return nupic::PyArrayRef<nupic::Byte>(self->getInputData(name)).asNumpyArray();
  }

  PyObject * getOutputArray(std::string name)
  {
    return nupic::PyArrayRef<nupic::Byte>(self->getOutputData(name)).asNumpyArray();
  }
}


%{
#include <nupic/os/OS.hpp>
%}

// magic swig incantation
// provides: (real, virtual) = OS.getProcessMemoryUsage()
%include <typemaps.i>
class nupic::OS
{
public:
  static void OS::getProcessMemoryUsage(size_t& OUTPUT, size_t& OUTPUT);
};
