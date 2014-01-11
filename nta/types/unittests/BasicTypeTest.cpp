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
 * Implementation of BasicType test
 */

#include "BasicTypeTest.hpp"
#include <nta/types/BasicType.hpp>

namespace nta
{
  void BasicTypeTest::RunTests()
  {
    // Test isValid()
    {
      TEST(BasicType::isValid(NTA_BasicType_Byte));
      TEST(BasicType::isValid(NTA_BasicType_Int16));
      TEST(BasicType::isValid(NTA_BasicType_UInt16));
      TEST(BasicType::isValid(NTA_BasicType_Int32));
      TEST(BasicType::isValid(NTA_BasicType_UInt32));
      TEST(BasicType::isValid(NTA_BasicType_Int64));
      TEST(BasicType::isValid(NTA_BasicType_UInt64));
      TEST(BasicType::isValid(NTA_BasicType_Real32));
      TEST(BasicType::isValid(NTA_BasicType_Real64));
      TEST(BasicType::isValid(NTA_BasicType_Real));
      TEST(BasicType::isValid(NTA_BasicType_Handle));

      
      TEST(!BasicType::isValid(NTA_BasicType_Last));
      TEST(!(BasicType::isValid(NTA_BasicType(NTA_BasicType_Last + 777))));
      TEST(!(BasicType::isValid(NTA_BasicType(-1))));
    }

    // Test getSize()
    {
      TEST(BasicType::getSize(NTA_BasicType_Byte) == 1);
      TEST(BasicType::getSize(NTA_BasicType_Int16) == 2);
      TEST(BasicType::getSize(NTA_BasicType_UInt16) == 2);
      TEST(BasicType::getSize(NTA_BasicType_Int32) == 4);
      TEST(BasicType::getSize(NTA_BasicType_UInt32) == 4);
      TEST(BasicType::getSize(NTA_BasicType_Int64) == 8);
      TEST(BasicType::getSize(NTA_BasicType_UInt64) == 8);
      TEST(BasicType::getSize(NTA_BasicType_Real32) == 4);
      TEST(BasicType::getSize(NTA_BasicType_Real64) == 8);        
      #ifdef NTA_DOUBLE_PRECISION
        TEST(BasicType::getSize(NTA_BasicType_Real) == 8); // Real64
      #else
        TEST(BasicType::getSize(NTA_BasicType_Real) == 4); // Real32
      #endif
      TEST(BasicType::getSize(NTA_BasicType_Handle) == sizeof(void *));
    }

    // Test getName()
    {
      TEST(BasicType::getName(NTA_BasicType_Byte) == std::string("Byte"));
      TEST(BasicType::getName(NTA_BasicType_Int16) == std::string("Int16"));
      TEST(BasicType::getName(NTA_BasicType_UInt16) == std::string("UInt16"));
      TEST(BasicType::getName(NTA_BasicType_Int32) == std::string("Int32"));
      TEST(BasicType::getName(NTA_BasicType_UInt32) == std::string("UInt32"));
      TEST(BasicType::getName(NTA_BasicType_Int64) == std::string("Int64"));
      TEST(BasicType::getName(NTA_BasicType_UInt64) == std::string("UInt64"));
      TEST(BasicType::getName(NTA_BasicType_Real32) == std::string("Real32"));
      TEST(BasicType::getName(NTA_BasicType_Real64) == std::string("Real64"));
      #ifdef NTA_DOUBLE_PRECISION
        TEST(BasicType::getName(NTA_BasicType_Real) == std::string("Real64"));
      #else
        TEST(BasicType::getName(NTA_BasicType_Real) == std::string("Real32"));
      #endif      
      TEST(BasicType::getName(NTA_BasicType_Handle) == std::string("Handle"));
    }

    // Test parse()
    {
      TEST(BasicType::parse("Byte") == NTA_BasicType_Byte);
      TEST(BasicType::parse("Int16") == NTA_BasicType_Int16);
      TEST(BasicType::parse("UInt16") == NTA_BasicType_UInt16);
      TEST(BasicType::parse("Int32") == NTA_BasicType_Int32);
      TEST(BasicType::parse("UInt32") == NTA_BasicType_UInt32);
      TEST(BasicType::parse("Int64") == NTA_BasicType_Int64);
      TEST(BasicType::parse("UInt64") == NTA_BasicType_UInt64);
      TEST(BasicType::parse("Real32") == NTA_BasicType_Real32);
      TEST(BasicType::parse("Real64") == NTA_BasicType_Real64);
      TEST(BasicType::parse("Real") == NTA_BasicType_Real);
      TEST(BasicType::parse("Handle") == NTA_BasicType_Handle);
    }
  }
}

