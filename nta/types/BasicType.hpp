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

#ifndef NTA_BASIC_TYPE_HPP
#define NTA_BASIC_TYPE_HPP

#include <nta/types/types.h>
#include <string>

namespace nta
{
  // The BasicType class provides operations on NTA_BasicType as static methods.
  //
  // The supported operations are:
  // - isValid()
  // - getName()
  // - getSize() and parse().
  //
  class BasicType
  {    
  public:
    // Check if the provided basic type os in the proper range.
    //
    // In C++ enums are just glorified integers and you can cast
    // an int to any enum even if the int value is outside of the range of
    // definedenum values. The compiler will say nothing. The NTA_BasicType
    // enum has a special value called NTA_BasicType_Last that marks the end of
    // of the valid rnge of values and isValid() returns true if if the input
    // falls in the range [0, NTA_BasicType_Last) and false otherwise. Note,
    // that NTA_BasicType_Last itself is an invalid value eventhough it is
    // defined in the enum.
    static bool isValid(NTA_BasicType t);

    // Return the name of a basic type (without the "NTA_BasicType_") prefix.
    // For example the name of NTA_BasicType_Int32 is "int32".
    static const char * getName(NTA_BasicType t);

    // Like getName above, but can be used in a templated method
    template <typename T> static const char* getName();

    // To convert <T> -> NTA_BasicType in a templated method
    template <typename T> static NTA_BasicType getType();

    // Return the size in bits of a basic type
    static size_t getSize(NTA_BasicType t);

    // Parse a string and return the corresponding basic type
    //
    // The string should contain the name of the basic type
    // without the "NTA_BasicType_" prefix. For example the name
    // of NTA_BasicType_Int32 is "Int32"
    static NTA_BasicType parse(const std::string & s);

  private:
    BasicType();
    BasicType(const BasicType &);
  };
}

#endif

