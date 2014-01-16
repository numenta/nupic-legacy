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
Implementation of Spec API
*/

#include <nta/engine/Spec.hpp>
#include <nta/utils/Log.hpp>
#include <nta/types/BasicType.hpp>

namespace nta
{




Spec::Spec() : singleNodeOnly(false), description("") 
{
}


std::string Spec::getDefaultInputName() const
{
  if (inputs.getCount() == 0)
    return "";
  if (inputs.getCount() == 1)
    return inputs.getByIndex(0).first;

  // search for default input, but detect multple defaults
  bool found = false;
  std::string name;

  for (size_t i = 0; i < inputs.getCount(); ++i)
  {
    const std::pair<std::string, InputSpec> & p = inputs.getByIndex(i);
    if (p.second.isDefaultInput)
    {
      NTA_CHECK(!found) << "Internal error -- multiply-defined default inputs in Spec";
      found = true;
      name = p.first;
    }
  }
  NTA_CHECK(found) << "Internal error -- multiple inputs in Spec but no default";
  return name;
}

std::string Spec::getDefaultOutputName() const
{
  if (outputs.getCount() == 0)
    return "";
  if (outputs.getCount() == 1)
    return outputs.getByIndex(0).first;

  // search for default output, but detect multple defaults
  bool found = false;
  std::string name;

  for (size_t i = 0; i < outputs.getCount(); ++i)
  {
    const std::pair<std::string, OutputSpec> & p = outputs.getByIndex(i);
    if (p.second.isDefaultOutput)
    {
      NTA_CHECK(!found) << "Internal error -- multiply-defined default outputs in Spec";
      found = true;
      name = p.first;
    }
  }
  NTA_CHECK(found) << "Internal error -- multiple outputs in Spec but no default";
  return name;
}


InputSpec::InputSpec(const std::string& description, 
                     NTA_BasicType  dataType, 
                     UInt32 count,
                     bool required, 
                     bool regionLevel, 
                     bool isDefaultInput,
                     bool requireSplitterMap) :
  description(description), 
  dataType(dataType), 
  count(count), 
  required(required), 
  regionLevel(regionLevel), 
  isDefaultInput(isDefaultInput), 
  requireSplitterMap(requireSplitterMap)
{ 
}

OutputSpec::OutputSpec(const std::string& description, 
                       NTA_BasicType dataType, 
                       size_t count,
                       bool regionLevel, 
                       bool isDefaultOutput) :
  description(description), dataType(dataType), count(count), 
  regionLevel(regionLevel), isDefaultOutput(isDefaultOutput)
{
}


CommandSpec::CommandSpec(const std::string& description) :
  description(description)
{
}


ParameterSpec::ParameterSpec(const std::string& description,
                             NTA_BasicType dataType, 
                             size_t count, 
                             const std::string& constraints, 
                             const std::string& defaultValue, 
                             AccessMode accessMode) :
  description(description), dataType(dataType), count(count),
  constraints(constraints), defaultValue(defaultValue), 
  accessMode(accessMode)
{
  // Parameter of type byte is not supported;
  // Strings are specified as type byte, length = 0
  if (dataType == NTA_BasicType_Byte && count > 0)
    NTA_THROW << "Parameters of type 'byte' are not supported";
}



std::string Spec::toString() const
{
  // TODO -- minimal information here; fill out with the rest of 
  // the parameter spec information
  std::stringstream ss;
  ss << "Spec:" << "\n";
  ss << "Description:" << "\n" 
     << this->description << "\n" << "\n";

  ss << "Parameters:" << "\n";
  for (size_t i = 0; i < parameters.getCount(); ++i)
  {
    const std::pair<std::string, ParameterSpec>& item = parameters.getByIndex(i);
    ss << "  " << item.first << "\n"
       << "     description: " << item.second.description << "\n"
       << "     type: " << BasicType::getName(item.second.dataType) << "\n"
       << "     count: " << item.second.count << "\n"; 
  }

  ss << "Inputs:" << "\n";
  for (size_t i = 0; i < inputs.getCount(); ++i)
  {
    ss << "  " << inputs.getByIndex(i).first << "\n";
  }

  ss << "Outputs:" << "\n";
  for (size_t i = 0; i < outputs.getCount(); ++i)
  {
    ss << "  " << outputs.getByIndex(i).first << "\n";
  }

  ss << "Commands:" << "\n";
  for (size_t i = 0; i < commands.getCount(); ++i)
  {
    ss << "  " << commands.getByIndex(i).first << "\n";
  }
  
  return ss.str();
}


}

