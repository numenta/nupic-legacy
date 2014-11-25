
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

#define SWIG_FILE_WITH_INIT


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
%template(UInt32Set) std::set<nta::UInt32>;


//32bit fix -  Already seen by swig on linux32 where size_t is the same size as unsigned int
#if !defined(NTA_PLATFORM_linux32) && !defined(NTA_PLATFORM_linux32arm)  && !defined(NTA_PLATFORM_linux32armv7)
%template(Dimset) std::vector<size_t>;
#endif

%include <nupic/ntypes/Dimensions.hpp>
%include <nupic/ntypes/Array.hpp>
%include <nupic/ntypes/ArrayRef.hpp>

%include <nupic/ntypes/Collection.hpp>
%template(InputCollection) nta::Collection<nta::InputSpec>;
%template(OutputCollection) nta::Collection<nta::OutputSpec>;
%template(ParameterCollection) nta::Collection<nta::ParameterSpec>;
%template(CommandCollection) nta::Collection<nta::CommandSpec>;
%template(RegionCollection) nta::Collection<nta::Region *>;

%include <nupic/engine/NuPIC.hpp>
%include <nupic/engine/Network.hpp>
%ignore nta::Region::getInputData;
%ignore nta::Region::getOutputData;
%include <nupic/engine/Region.hpp>
%include <nupic/utils/Watcher.hpp>
%include <nupic/engine/Spec.hpp>

%template(InputPair) std::pair<std::string, nta::InputSpec>;
%template(OutputPair) std::pair<std::string, nta::OutputSpec>;
%template(ParameterPair) std::pair<std::string, nta::ParameterSpec>;
%template(CommandPair) std::pair<std::string, nta::CommandSpec>;
%template(RegionPair) std::pair<std::string, nta::Region *>;

%include <nupic/os/Timer.hpp>

  
