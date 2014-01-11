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


#include <nta/engine/Spec.hpp>

/*
 * We need to import the code from Collection.cpp 
 * in order to instantiate all the methods in the classes
 * instantiated below. 
 */
#include <nta/ntypes/Collection.hpp>
#include <nta/ntypes/Collection.cpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Network.hpp>

using namespace nta;


// Explicit instantiations of the collection classes used by Spec
template class nta::Collection<OutputSpec>;
template class nta::Collection<InputSpec>;
template class nta::Collection<ParameterSpec>;
template class nta::Collection<CommandSpec>;
template class nta::Collection<Region*>;
template class nta::Collection<Network::callbackItem>;

