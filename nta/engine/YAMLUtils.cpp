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

#include <nta/types/BasicType.hpp>
#include <nta/engine/YAMLUtils.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/Collection.hpp>
#include <nta/ntypes/MemStream.hpp>
#include <nta/engine/Spec.hpp>
#include <string.h> // strlen
#include <yaml-cpp/yaml.h>

#include <sstream>

namespace nta
{
namespace YAMLUtils
{

/*
 * These functions are used internally by toValue and toValueMap
 */
static void _toScalar(const YAML::Node& node, boost::shared_ptr<Scalar>& s);
static void _toArray(const YAML::Node& node, boost::shared_ptr<Array>& a);
static Value toValue(const YAML::Node& node, NTA_BasicType dataType);


static void _toScalar(const YAML::Node& node, boost::shared_ptr<Scalar>& s)
{
  NTA_CHECK(node.Type() == YAML::NodeType::Scalar);
  switch(s->getType())
  {
  case NTA_BasicType_Byte:
    // We should have already detected this and gone down the string path
    NTA_THROW << "Internal error: attempting to convert YAML string to scalar of type Byte";
    break;
  case NTA_BasicType_UInt16:
    node >> s->value.uint16;
    break;
  case NTA_BasicType_Int16:
    node >> s->value.int16;
    break;
  case NTA_BasicType_UInt32:
    node >> s->value.uint32;
    break;
  case NTA_BasicType_Int32:
    node >> s->value.int32;
    break;
  case NTA_BasicType_UInt64:
    node >> s->value.uint64;
    break;
  case NTA_BasicType_Int64:
    node >> s->value.int64;
    break;
  case NTA_BasicType_Real32:
    node >> s->value.real32;
    break;
  case NTA_BasicType_Real64:
    node >> s->value.real64;
    break;
  case NTA_BasicType_Handle:
    NTA_THROW << "Attempt to specify a YAML value for a scalar of type Handle";
    break;
  default:
    // should not happen
    std::string val;
    node >> val;
    NTA_THROW << "Unknown data type " << s->getType() << " for yaml node '" << val << "'";
  }
}
    
static void _toArray(const YAML::Node& node, boost::shared_ptr<Array>& a)
{
  NTA_CHECK(node.Type() == YAML::NodeType::Sequence);
      
  a->allocateBuffer(node.size());
  void* buffer = a->getBuffer();
      
  for (size_t i = 0; i < node.size(); i++)
  {
    const YAML::Node& item = node[i];
    NTA_CHECK(item.Type() == YAML::NodeType::Scalar);
    switch(a->getType())
    {
    case NTA_BasicType_Byte:
      // We should have already detected this and gone down the string path
      NTA_THROW << "Internal error: attempting to convert YAML string to array of type Byte";
      break;
    case NTA_BasicType_UInt16:
      item.Read<UInt16>(((UInt16*)buffer)[i]);
      break;
    case NTA_BasicType_Int16:
      item.Read<Int16>(((Int16*)buffer)[i]);
      break;
    case NTA_BasicType_UInt32:
      item.Read<UInt32>(((UInt32*)buffer)[i]);
      break;
    case NTA_BasicType_Int32:
      item.Read<Int32>(((Int32*)buffer)[i]);
      break;
    case NTA_BasicType_UInt64:
      item.Read<UInt64>(((UInt64*)buffer)[i]);
      break;
    case NTA_BasicType_Int64:
      item.Read<Int64>(((Int64*)buffer)[i]);
      break;
    case NTA_BasicType_Real32:
      item.Read<Real32>(((Real32*)buffer)[i]);
      break;
    case NTA_BasicType_Real64:
      item.Read<Real64>(((Real64*)buffer)[i]);
      break;
    default:
      // should not happen
      NTA_THROW << "Unknown data type " << a->getType();
    }
  }
}

static Value toValue(const YAML::Node& node, NTA_BasicType dataType)
{
  if (node.Type() == YAML::NodeType::Map || node.Type() == YAML::NodeType::Null)
  {
    NTA_THROW << "YAML string does not not represent a value.";
  }
  if (node.Type() == YAML::NodeType::Scalar)
  {
    if (dataType == NTA_BasicType_Byte)
    {
      // node >> *str;
      std::string val;
      node.Read(val);
      boost::shared_ptr<std::string> str(new std::string(val));
      Value v(str);
      return v;
    } else {
      boost::shared_ptr<Scalar> s(new Scalar(dataType));
      _toScalar(node, s);
      Value v(s);
      return v;
    }
  } else {
    // array
    boost::shared_ptr<Array> a(new Array(dataType));
    _toArray(node, a);
    Value v(a);
    return v;
  }
}


/* 
 * For converting default values specified in nodespec
 */
Value toValue(const std::string& yamlstring, NTA_BasicType dataType)
{
  // IMemStream s(yamlstring, ::strlen(yamlstring));

  // yaml-cpp bug: append a space if it is only one character
  // This is very inefficient, but should be ok since it is 
  // just used at construction time for short strings
  std::string paddedstring(yamlstring);
  if (paddedstring.size() < 2)
    paddedstring = paddedstring + " ";
  std::stringstream s(paddedstring);

  // TODO -- return value? exceptions?
  bool success = false;
  YAML::Node doc;
  try
  {
    YAML::Parser parser(s);
    success = parser.GetNextDocument(doc);
    // } catch(YAML::ParserException& e) {
  } catch(...) {
    success = false;
  }
  if (!success)
  {
    std::string ys(paddedstring);
    if (ys.size() > 30)
    {
      ys = ys.substr(0, 30) + "...";
    }
    NTA_THROW << "Unable to parse YAML string '" << ys << "' for a scalar value";
  }
  Value v = toValue(doc, dataType);
  return v;
}

/* 
 * For converting param specs for Regions and LinkPolicies
 */
ValueMap toValueMap(const char* yamlstring, 
                               Collection<ParameterSpec>& parameters,
                               const std::string & nodeType,
                               const std::string & regionName)
{
    
  ValueMap vm;

  // yaml-cpp bug: append a space if it is only one character
  // This is very inefficient, but should be ok since it is 
  // just used at construction time for short strings
  std::string paddedstring(yamlstring);
  // TODO: strip white space to determine if empty
  bool empty = (paddedstring.size() == 0);

  if (paddedstring.size() < 2)
    paddedstring = paddedstring + " ";
  std::stringstream s(paddedstring);
  // IMemStream s(yamlstring, ::strlen(yamlstring));

  // TODO: utf-8 compatible?
  YAML::Node doc;
  if (!empty)
  {
    YAML::Parser parser(s);
    bool success = parser.GetNextDocument(doc);

    if (!success)
      NTA_THROW << "Unable to find document in YAML string";

    // A ValueMap is specified as a dictionary
    if (doc.Type() != YAML::NodeType::Map)
    {
      std::string ys(yamlstring);
      if (ys.size() > 30)
      {
        ys = ys.substr(0, 30) + "...";
      }
      NTA_THROW << "YAML string '" << ys 
                << "' does not not specify a dictionary of key-value pairs. "
                << "Region and Link parameters must be specified at a dictionary";
    }
  }

  // Grab each value out of the YAML dictionary and put into the ValueMap
  // if it is allowed by the nodespec.
  YAML::Iterator i;
  for (i = doc.begin(); i != doc.end(); i++)
  {
    const std::string key = i.first().to<std::string>();
    if (!parameters.contains(key))
    {
      std::stringstream ss;
      for (UInt j = 0; j < parameters.getCount(); j++)
      {
        ss << "   " << parameters.getByIndex(j).first << "\n";
      }
            
      if (nodeType == std::string(""))
      {
        NTA_THROW << "Unknown parameter '" << key << "'\n" 
                  << "Valid parameters are:\n" << ss.str();
      }
      else
      {
        NTA_CHECK(regionName != std::string(""));
        NTA_THROW << "Unknown parameter '" << key << "' for region '"
                  << regionName << "' of type '" << nodeType << "'\n" 
                  << "Valid parameters are:\n" << ss.str();
      }
    }
    if (vm.contains(key))
      NTA_THROW << "Parameter '" << key << "' specified more than once in YAML document";
    ParameterSpec spec = parameters.getByName(key);
    try
    {
      Value v = toValue(i.second(), spec.dataType);
      if (v.isScalar() && spec.count != 1)
      {
        throw std::runtime_error("Expected array value but got scalar value");
      }
      if (!v.isScalar() && spec.count == 1)
      {
        throw std::runtime_error("Expected scalar value but got array value");
      }
      vm.add(key, v);
    } catch (std::runtime_error& e) {
      NTA_THROW << "Unable to set parameter '" << key << "'. " << e.what();
    }
  }

  // Populate ValueMap with default values if they were not specified in the YAML dictionary.
  for (size_t i = 0; i < parameters.getCount(); i++)
  {
    std::pair<std::string, ParameterSpec>& item = parameters.getByIndex(i);
    if (!vm.contains(item.first))
    {
      ParameterSpec & ps = item.second;
      if (ps.defaultValue != "")
      {
        // TODO: This check should be uncommented after dropping NuPIC 1.x nodes (which don't comply)
        // if (ps.accessMode != ParameterSpec::CreateAccess)
        // {
        //   NTA_THROW << "Default value for non-create parameter: " << item.first;
        // }
        
        try {
#ifdef YAMLDEBUG
          NTA_DEBUG << "Adding default value '" << ps.defaultValue 
                    << "' to parameter " << item.first
                    << " of type " << BasicType::getName(ps.dataType) 
                    << " count " << ps.count;
#endif
          Value v = toValue(ps.defaultValue, ps.dataType);
          vm.add(item.first, v);
        } catch (...) {
          NTA_THROW << "Unable to set default value for item '" 
                    << item.first << "' of datatype " 
                    << BasicType::getName(ps.dataType) 
                    <<" with value '" << ps.defaultValue << "'";
        }
      }
    }
  }

  return vm;
}

} // end of YAMLUtils namespace

} // end of nta namespace

