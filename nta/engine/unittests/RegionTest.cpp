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
 * Implementation of Region test
 */

#include "RegionTest.hpp"
#include <nta/engine/Network.hpp>
#include <nta/engine/Region.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>


#include "NetworkTest.hpp"

using namespace nta;

void RegionTest::RunTests()
{
  testWithNodeType("TestNode");
  testWithNodeType("py.TestNode");

  // test the static Region::getSpecFromType
  Region::getSpecFromType("py.CLARegion");

  // test getNetwork()
  {
    Region r1("r", "TestNode", "");
    TEST(r1.getNetwork() == NULL);

    Network * net = (Network *)1234;
    Region r2("r", "TestNode", "", net);
    TEST(r2.getNetwork() == net);
  }
}

void RegionTest::testWithNodeType(const std::string& nodeType)
{

  Region *rP = NULL;

  SHOULDFAIL ( rP = new Region("r1", "nosuchnode", "") );
  
  Region r("r1", nodeType, "");

  TEST(r.getName() == "r1");

  TEST(r.getType() == nodeType);

  Dimensions d = r.getDimensions();
  TEST(d.isUnspecified());

  d.clear();
  d.push_back(3);
  d.push_back(2);
  r.setDimensions(d);
  
  Dimensions d2 = r.getDimensions();
  TEST(d2.size() == 2);
  TEST(d2[0] == 3);
  TEST(d2[1] == 2);

  TEST(d2.getCount() == 6);
  
  // Parameter testing
  {
    {
      Int32 val = -(1 << 24);
      TESTEQUAL((Int32)32, r.getParameterInt32("int32Param"));
      r.setParameterInt32("int32Param", val);
      TESTEQUAL(val, r.getParameterInt32("int32Param"));
    }

    {
      UInt32 val = 1 << 24;
      TESTEQUAL((UInt32)33, r.getParameterUInt32("uint32Param"));
      r.setParameterUInt32("uint32Param", val);
      TESTEQUAL(val, r.getParameterUInt32("uint32Param"));
    }

    {
      Int64 val = -((Int64)1 << 44);
      TESTEQUAL((Int64)64, r.getParameterInt64("int64Param"));
      r.setParameterInt64("int64Param", val);
      TESTEQUAL(val, r.getParameterInt64("int64Param"));
    }

    {
      UInt64 val = (UInt64)1 << 45;
      TESTEQUAL((UInt64)65, r.getParameterUInt64("uint64Param"));
      r.setParameterUInt64("uint64Param", val);
      TESTEQUAL(r.getParameterUInt64("uint64Param"), val);
    }

    {
      Real32 val = 23456.7;
      TESTEQUAL((Real32)32.1, r.getParameterReal32("real32Param"));
      r.setParameterReal32("real32Param", val);
      TESTEQUAL(r.getParameterReal32("real32Param"), val);
    }

    {
      Real64 val = 23456.789;
      TESTEQUAL((Real64)64.1, r.getParameterReal64("real64Param"));
      r.setParameterReal64("real64Param", val);
      TESTEQUAL(r.getParameterReal64("real64Param"), val);
    }

    {
      Array a(NTA_BasicType_Int64);
      r.getParameterArray("int64ArrayParam", a);
      // check default values
      TESTEQUAL((size_t)4, a.getCount());
      Int64 *buf = (Int64*) a.getBuffer();
      TEST(buf != NULL);
      for (UInt64 i = 0; i < 4; i++)
        TESTEQUAL((Int64)(i*64), buf[i]);
      
      // set our own value
      buf[0] = 100;
      r.setParameterArray("int64ArrayParam", a);
      // make sure we retrieve the value just set
      buf[0] = 0;
      r.getParameterArray("int64ArrayParam", a);
      TEST(buf == a.getBuffer());
      TESTEQUAL((Int64)100, buf[0]);
    }

    {
      std::string s = r.getParameterString("stringParam");
      TESTEQUAL("nodespec value", s);
      s = "new value";
      r.setParameterString("stringParam", s);
      s = r.getParameterString("stringParam");
      TESTEQUAL("new value", s);
    }

  }  
  

}


  

  
  

