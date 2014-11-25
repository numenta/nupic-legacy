
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


#include <nta/types/Types.hpp>
#include <nta/types/Types.h>
#include <nta/types/BasicType.hpp>
#include <nta/types/Exception.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>
#include <nta/ntypes/Collection.hpp>

#include <nta/utils/Log.hpp>
#include <nta/utils/LogItem.hpp>
#include <nta/utils/LoggingException.hpp>



#include <py_support/PyArray.hpp>

#include <nta/engine/NuPIC.hpp>
#include <nta/engine/Network.hpp>

#include <nta/engine/Spec.hpp>
#include <nta/utils/Watcher.hpp>
#include <nta/engine/Region.hpp>
#include <nta/os/Timer.hpp>
%}

%include "std_pair.i"
%include "std_string.i"
%include "std_vector.i"
%include "std_map.i"
%include "std_set.i" 
%template(StringVec) std::vector<std::string>;


%include <nta/types/Types.h>
%include <nta/types/Types.hpp>
%include <nta/types/BasicType.hpp>
%include <nta/types/Exception.hpp>

// For Network::get/setPhases()
%template(UInt32Set) std::set<nupic::UInt32>;


//32bit fix -  Already seen by swig on linux32 where size_t is the same size as unsigned int
#if !defined(NTA_PLATFORM_linux32) && !defined(NTA_PLATFORM_linux32arm)  && !defined(NTA_PLATFORM_linux32armv7)
%template(Dimset) std::vector<size_t>;
#endif

%include <nta/ntypes/Dimensions.hpp>
%include <nta/ntypes/Array.hpp>
%include <nta/ntypes/ArrayRef.hpp>

%include <nta/ntypes/Collection.hpp>
%template(InputCollection) nupic::Collection<nupic::InputSpec>;
%template(OutputCollection) nupic::Collection<nupic::OutputSpec>;
%template(ParameterCollection) nupic::Collection<nupic::ParameterSpec>;
%template(CommandCollection) nupic::Collection<nupic::CommandSpec>;
%template(RegionCollection) nupic::Collection<nupic::Region *>;

%include <nta/engine/NuPIC.hpp>
%include <nta/engine/Network.hpp>
%ignore nupic::Region::getInputData;
%ignore nupic::Region::getOutputData;
%include <nta/engine/Region.hpp>
%include <nta/utils/Watcher.hpp>
%include <nta/engine/Spec.hpp>

%template(InputPair) std::pair<std::string, nupic::InputSpec>;
%template(OutputPair) std::pair<std::string, nupic::OutputSpec>;
%template(ParameterPair) std::pair<std::string, nupic::ParameterSpec>;
%template(CommandPair) std::pair<std::string, nupic::CommandSpec>;
%template(RegionPair) std::pair<std::string, nupic::Region *>;

%include <nta/os/Timer.hpp>

  
