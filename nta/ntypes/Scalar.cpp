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
 * Implementation of the Scalar class
 * 
 * A Scalar object is an instance of an NTA_BasicType -- essentially a union
 * It is used internally in the conversion of YAML strings to C++ objects. 
 */

#include <nta/ntypes/Scalar.hpp>
#include <nta/utils/Log.hpp> 

using namespace nta;

Scalar::Scalar(NTA_BasicType theTypeParam)
{
  theType_ = theTypeParam;
  value.uint64 = 0;
}

NTA_BasicType 
Scalar::getType()
{
  return theType_;
}

// gcc 4.2 complains about the template specializations 
// in a different namespace if we don't include this
namespace nta {
  
  template <> Handle Scalar::getValue<Handle>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Handle);
    return value.handle;
  }
  template <> Byte Scalar::getValue<Byte>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Byte);
    return value.byte;
  }
  template <> UInt16 Scalar::getValue<UInt16>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_UInt16);
    return value.uint16;
  }
  template <> Int16 Scalar::getValue<Int16>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Int16);
    return value.int16;
  }
  template <> UInt32 Scalar::getValue<UInt32>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_UInt32);
    return value.uint32;
  }
  template <> Int32 Scalar::getValue<Int32>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Int32);
    return value.int32;
  }
  template <> UInt64 Scalar::getValue<UInt64>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_UInt64);
    return value.uint64;
  }
  template <> Int64 Scalar::getValue<Int64>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Int64);
    return value.int64;
  }
  template <> Real32 Scalar::getValue<Real32>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Real32);
    return value.real32;
  }
  template <> Real64 Scalar::getValue<Real64>() const
  {
    NTA_CHECK(theType_ == NTA_BasicType_Real64);
    return value.real64;
  }
}




