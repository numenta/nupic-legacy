%module net_internal

# Exception classhes with System.Exception
%rename (BaseException) Exception;

%include "Exception.i"



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

#include <nta2/types2/types.hpp>
#include <nta2/types2/types.h>
#include <nta2/types2/BasicType.hpp>
#include <nta2/types2/Exception.hpp>
#include <nta2/ntypes/Dimensions.hpp>
#include <nta2/ntypes/Array.hpp>
#include <nta2/ntypes/Collection.hpp>

#include <nta2/utils2/Log.hpp>
#include <nta2/utils2/LogItem.hpp>
#include <nta2/utils2/LoggingException.hpp>

#include <py_support/PyArray.hpp>

#include <nta2/net/NuPIC.hpp>
#include <nta2/net/Network.hpp>

#include <nta2/net/Node.hpp>
#include <nta2/net/Spec.hpp>
#include <nta2/utils2/Watcher.hpp>
#include <nta2/net/Region.hpp>
#include <nta2/os2/Timer.hpp>
%}



//include "std/std_pair.i"

%include "std/std_string.i"

/* 
//%include "std/std_vector.i"
//%include "std/std_map.i"
//%include "std/std_set.i" 
//%template(StringVec) std::vector<std::string>;

//%include <nta2/types2/types.h>
//%include <nta2/types2/types.hpp>
//%include <nta2/types2/BasicType.hpp>
//%include <nta2/types2/Exception.hpp>

// For Network::get/setPhases()
%template(UInt32Set) std::set<nta::UInt32>;


%template(Dimset) std::vector<size_t>;
%include <nta2/ntypes/Dimensions.hpp>
%include <nta2/ntypes/Array.hpp>

%include <nta2/ntypes/Collection.hpp>
%template(InputCollection) nta::Collection<nta::InputSpec>;
%template(OutputCollection) nta::Collection<nta::OutputSpec>;
%template(ParameterCollection) nta::Collection<nta::ParameterSpec>;
%template(CommandCollection) nta::Collection<nta::CommandSpec>;
%template(RegionCollection) nta::Collection<nta::Region *>;

%include <nta2/net/NuPIC.hpp>
%include <nta2/net/Network.hpp>
%include <nta2/net/Node.hpp>
%include <nta2/net/Region.hpp>
%include <nta2/utils2/Watcher.hpp>
%include <nta2/net/Spec.hpp>

%template(InputPair) std::pair<std::string, nta::InputSpec>;
%template(OutputPair) std::pair<std::string, nta::OutputSpec>;
%template(ParameterPair) std::pair<std::string, nta::ParameterSpec>;
%template(CommandPair) std::pair<std::string, nta::CommandSpec>;
%template(RegionPair) std::pair<std::string, nta::Region *>;

%include <nta2/os2/Timer.hpp>

*/
