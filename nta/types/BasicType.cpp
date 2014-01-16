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
#include <nta/types/Exception.hpp>

using namespace nta;

bool BasicType::isValid(NTA_BasicType t)
{
  return (t >= 0) && (t < NTA_BasicType_Last);
}

const char * BasicType::getName(NTA_BasicType t)
{
  static const char *names[] = 
    {
      "Byte", 
      "Int16",
      "UInt16",
      "Int32", 
      "UInt32", 
      "Int64", 
      "UInt64", 
      "Real32", 
      "Real64",
      "Handle",
    };
  
  if (!isValid(t))
    throw Exception(__FILE__, __LINE__, "BasicType::getName -- Basic type is not valid");

  return names[t];
}


// gcc 4.2 requires (incorrectly) these to be defined inside a namespace
namespace nta 
{
  // getName<T>
  template <> const char* BasicType::getName<Byte>()
  {
    return getName(NTA_BasicType_Byte);
  }

  template <> const char* BasicType::getName<Int16>()
  {
    return getName(NTA_BasicType_Int16);
  }

  template <> const char* BasicType::getName<UInt16>()
  {
    return getName(NTA_BasicType_UInt16);
  }

  template <> const char* BasicType::getName<Int32>()
  {
    return getName(NTA_BasicType_Int32);
  }

  template <> const char* BasicType::getName<UInt32>()
  {
    return getName(NTA_BasicType_UInt32);
  }

  template <> const char* BasicType::getName<Int64>()
  {
    return getName(NTA_BasicType_Int64);
  }

  template <> const char* BasicType::getName<UInt64>()
  {
    return getName(NTA_BasicType_UInt64);
  }

  template <> const char* BasicType::getName<Real32>()
  {
    return getName(NTA_BasicType_Real32);
  }

  template <> const char* BasicType::getName<Real64>()
  {
    return getName(NTA_BasicType_Real64);
  }

  template <> const char* BasicType::getName<Handle>()
  {
    return getName(NTA_BasicType_Handle);
  }


  // getType<T>
  template <> NTA_BasicType BasicType::getType<Byte>()
  {
    return NTA_BasicType_Byte;
  }

  template <> NTA_BasicType BasicType::getType<Int16>()
  {
    return NTA_BasicType_Int16;
  }

  template <> NTA_BasicType BasicType::getType<UInt16>()
  {
    return NTA_BasicType_UInt16;
  }

  template <> NTA_BasicType BasicType::getType<Int32>()
  {
    return NTA_BasicType_Int32;
  }

  template <> NTA_BasicType BasicType::getType<UInt32>()
  {
    return NTA_BasicType_UInt32;
  }

  template <> NTA_BasicType BasicType::getType<Int64>()
  {
    return NTA_BasicType_Int64;
  }

  template <> NTA_BasicType BasicType::getType<UInt64>()
  {
    return NTA_BasicType_UInt64;
  }

  template <> NTA_BasicType BasicType::getType<Real32>()
  {
    return NTA_BasicType_Real32;
  }

  template <> NTA_BasicType BasicType::getType<Real64>()
  {
    return NTA_BasicType_Real64;
  }

  template <> NTA_BasicType BasicType::getType<Handle>()
  {
    return NTA_BasicType_Handle;
  }
}      

// Return the size in bits of a basic type
size_t BasicType::getSize(NTA_BasicType t)
{
  static size_t basicTypeSizes[] = 
    {
      sizeof(NTA_Byte),
      sizeof(NTA_Int16),
      sizeof(NTA_UInt16),
      sizeof(NTA_Int32),
      sizeof(NTA_UInt32), 
      sizeof(NTA_Int64), 
      sizeof(NTA_UInt64), 
      sizeof(NTA_Real32),
      sizeof(NTA_Real64),
      sizeof(NTA_Handle)
    };
  
  if (!isValid(t))
    throw Exception(__FILE__, __LINE__, "BasicType::getSize -- basic type is not valid");
  return basicTypeSizes[t];
}

NTA_BasicType BasicType::parse(const std::string & s)
{
  if (s == std::string("Byte") || s == std::string("str"))
    return NTA_BasicType_Byte;
  else if (s == std::string("Int16"))
    return NTA_BasicType_Int16;
  else if (s == std::string("UInt16"))
    return NTA_BasicType_UInt16;
  else if (s == std::string("Int32") || s == std::string("int"))
    return NTA_BasicType_Int32;
  else if (s == std::string("UInt32") || s == std::string("bool") || s == std::string("uint"))

    return NTA_BasicType_UInt32;
  else if (s == std::string("Int64"))
    return NTA_BasicType_Int64;
  else if (s == std::string("UInt64"))
    return NTA_BasicType_UInt64;
  else if (s == std::string("Real32") || s == std::string("float"))
    return NTA_BasicType_Real32;
  else if (s == std::string("Real64"))
    return NTA_BasicType_Real64;
  else if (s == std::string("Real"))
    return NTA_BasicType_Real;
  else if (s == std::string("Handle"))
    return NTA_BasicType_Handle;
  else
    throw Exception(__FILE__, __LINE__, std::string("Invalid basic type name: ") + s);
}




