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
 * Implementation of YAMLUtils test
 */

#include "YAMLUtilsTest.hpp"
#include <nta/engine/Network.hpp>
#include <nta/engine/YAMLUtils.hpp>
#include <nta/engine/Spec.hpp>

#include "NetworkTest.hpp"

using namespace nta;

void YAMLUtilsTest::RunTests()
{
  // toValue tests
  {
    const char* s1 = "10";
    Value v = YAMLUtils::toValue(s1, NTA_BasicType_Int32);
    TEST(v.isScalar());
    TESTEQUAL(v.getType(), NTA_BasicType_Int32);
    Int32 i = v.getScalarT<Int32>();
    TESTEQUAL(10, i);
    boost::shared_ptr<Scalar> s = v.getScalar();
    i = s->value.int32;
    TESTEQUAL(10, i);
  }

  {
    const char* s1 = "10.1";
    Value v = YAMLUtils::toValue(s1, NTA_BasicType_Real32);
    TEST(v.isScalar());
    TESTEQUAL(v.getType(), NTA_BasicType_Real32);
    Real32 x = v.getScalarT<Real32>();
    TESTEQUAL_FLOAT(10.1, x);
    boost::shared_ptr<Scalar> s = v.getScalar();
    x = s->value.real32;
    TESTEQUAL_FLOAT(10.1, x);
    
  }
  
  {
    const char* s1 = "this is a string";
    Value v = YAMLUtils::toValue(s1, NTA_BasicType_Byte);
    TEST(!v.isScalar());
    TEST(v.isString());
    TESTEQUAL(v.getType(), NTA_BasicType_Byte);
    std::string s = *v.getString();
    TESTEQUAL(s1, s.c_str());
  }

  {
    Collection<ParameterSpec> ps;
    ps.add(
      "int32Param", 
      ParameterSpec(
        "Int32 scalar parameter",  // description
        NTA_BasicType_Int32,
        1,                         // elementCount
        "",                        // constraints
        "32",                      // defaultValue
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "uint32Param", 
      ParameterSpec(
        "UInt32 scalar parameter", // description
        NTA_BasicType_UInt32, 
        1,                         // elementCount
        "",                        // constraints
        "33",                      // defaultValue
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "int64Param", 
      ParameterSpec(
        "Int64 scalar parameter",  // description
        NTA_BasicType_Int64, 
        1,                         // elementCount
        "",                        // constraints
        "64",                       // defaultValue
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "uint64Param", 
      ParameterSpec(
        "UInt64 scalar parameter", // description
        NTA_BasicType_UInt64,
        1,                         // elementCount
        "",                        // constraints
        "65",                       // defaultValue
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "real32Param", 
      ParameterSpec(
        "Real32 scalar parameter",  // description
        NTA_BasicType_Real32,
        1,                         // elementCount
        "",                        // constraints
        "32.1",                    // defaultValue
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "real64Param", 
      ParameterSpec(
        "Real64 scalar parameter",  // description
        NTA_BasicType_Real64,
        1,                         // elementCount
        "",                        // constraints
        "64.1",                    // defaultValue
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "real32ArrayParam",
      ParameterSpec(
        "int32 array parameter", 
        NTA_BasicType_Real32,
        0, // array
        "", 
        "",
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "int64ArrayParam",
      ParameterSpec(
        "int64 array parameter", 
        NTA_BasicType_Int64,
        0, // array
        "", 
        "",
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "computeCallback",
      ParameterSpec(
        "address of a function that is called at every compute()",
        NTA_BasicType_Handle, 
        1,
        "", 
        "",  // handles must not have a default value
        ParameterSpec::ReadWriteAccess));

    ps.add(
      "stringParam", 
      ParameterSpec(
        "string parameter", 
        NTA_BasicType_Byte, 
        0, // length=0 required for strings
        "", 
        "default value", 
        ParameterSpec::ReadWriteAccess));
  
    NTA_DEBUG << "ps count: " << ps.getCount();

    ValueMap vm = YAMLUtils::toValueMap("", ps);
    TEST(vm.contains("int32Param"));
    TESTEQUAL((Int32)32, vm.getScalarT<Int32>("int32Param"));
    
    // disabled until we fix default string params
    // TEST(vm.contains("stringParam"));
    // TESTEQUAL("default value", vm.getString("stringParam")->c_str());

    // Test error message in case of invalid parameter with and without nodeType and regionName    
    try
    {
      YAMLUtils::toValueMap("{ blah: True }", ps, "nodeType", "regionName");
    }
    catch (nta::Exception & e)
    {
      std::string s("Unknown parameter 'blah' for region 'regionName'");
      TEST(std::string(e.getMessage()).find(s) == 0);
    }

    try
    {
      YAMLUtils::toValueMap("{ blah: True }", ps);
    }
    catch (nta::Exception & e)
    {
      std::string s("Unknown parameter 'blah'\nValid");
      TEST(std::string(e.getMessage()).find(s) == 0);
    }

  }


}

  

  
  

