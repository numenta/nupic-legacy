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

/** @file 
 * Implementation of Region methods related to inputs and outputs
 */

#include <nta/engine/Region.hpp>
#include <nta/engine/RegionImpl.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Input.hpp>
#include <nta/utils/Log.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>
#include <nta/types/BasicType.hpp>

namespace nta
{




// Internal methods called by RegionImpl. 

Output* Region::getOutput(const std::string& name) const
{
  OutputMap::const_iterator o = outputs_.find(name);
  if (o == outputs_.end())
    return NULL;
  return o->second;
}


Input* Region::getInput(const std::string& name) const
{
  InputMap::const_iterator i = inputs_.find(name);
  if (i == inputs_.end())
    return NULL;
  return i->second;
}


// Called by Network during serialization
const std::map<const std::string, Input*>& 
Region::getInputs() const
{
  return inputs_;
}

const std::map<const std::string, Output*>& 
Region::getOutputs() const
{
  return outputs_;
}

size_t
Region::getOutputCount(const std::string& outputName) const
{
  OutputMap::const_iterator oi = outputs_.find(outputName);
  if (oi == outputs_.end())
    NTA_THROW << "getOutputSize -- unknown output '" << outputName << "' on region " << getName();
  return oi->second->getData().getCount();
}


size_t
Region::getInputCount(const std::string& inputName) const
{
  InputMap::const_iterator ii = inputs_.find(inputName);
  if (ii == inputs_.end())
    NTA_THROW << "getInputSize -- unknown input '" << inputName << "' on region " << getName();
  return ii->second->getData().getCount();
}


ArrayRef
Region::getOutputData(const std::string& outputName) const
{
  OutputMap::const_iterator oi = outputs_.find(outputName);
  if (oi == outputs_.end())
    NTA_THROW << "getOutputData -- unknown output '" << outputName << "' on region " << getName();

  const Array & data = oi->second->getData();
  ArrayRef a(data.getType());
  a.setBuffer(data.getBuffer(), data.getCount());
  return a;
}

ArrayRef
Region::getInputData(const std::string& inputName) const
{
  InputMap::const_iterator ii = inputs_.find(inputName);
  if (ii == inputs_.end())
    NTA_THROW << "getInput -- unknown input '" << inputName << "' on region " << getName();

  const Array & data = ii->second->getData();
  ArrayRef a(data.getType());
  a.setBuffer(data.getBuffer(), data.getCount());
  return a;
}

void
Region::prepareInputs()
{
  // Ask each input to prepare itself
  for (InputMap::const_iterator i = inputs_.begin();
       i != inputs_.end(); i++)
  {
    i->second->prepare();
  }

}


}


