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
 * Implementation of Value test
 */

#include <nta/ntypes/unittests/ValueTest.hpp>
#include <nta/ntypes/Value.hpp>

using namespace nta;

void ValueTest::RunTests()
{
  // scalar
  {
    boost::shared_ptr<Scalar>  s(new Scalar(NTA_BasicType_Int32));
    s->value.int32 = 10;
    Value v(s);
    TEST(v.isScalar());
    TEST(! v.isString());
    TEST(! v.isArray());
    TESTEQUAL(Value::scalarCategory, v.getCategory());
    TESTEQUAL(NTA_BasicType_Int32, v.getType());
      
    boost::shared_ptr<Scalar> s1 = v.getScalar();
    TEST(s1 == s);
      
    SHOULDFAIL(v.getArray());
    SHOULDFAIL(v.getString());
      
    TESTEQUAL("Scalar of type Int32", v.getDescription());
      
    
    Int32 x = v.getScalarT<Int32>();
    TESTEQUAL(10, x);
    
    SHOULDFAIL(v.getScalarT<UInt32>());

  }

  // array
  {
    boost::shared_ptr<Array>  s(new Array(NTA_BasicType_Int32));
    s->allocateBuffer(10);
    Value v(s);
    TEST(v.isArray());
    TEST(! v.isString());
    TEST(! v.isScalar());
    TESTEQUAL(Value::arrayCategory, v.getCategory());
    TESTEQUAL(NTA_BasicType_Int32, v.getType());
      
    boost::shared_ptr<Array> s1 = v.getArray();
    TEST(s1 == s);
      
    SHOULDFAIL(v.getScalar());
    SHOULDFAIL(v.getString());
    SHOULDFAIL(v.getScalarT<Int32>());

    TESTEQUAL("Array of type Int32", v.getDescription());
  }

  // string
  {
    boost::shared_ptr<std::string> s(new std::string("hello world"));
    Value v(s);
    TEST(! v.isArray());
    TEST(v.isString());
    TEST(! v.isScalar());
    TESTEQUAL(Value::stringCategory, v.getCategory());
    TESTEQUAL(NTA_BasicType_Byte, v.getType());
      
    boost::shared_ptr<std::string> s1 = v.getString();
    TESTEQUAL("hello world", s1->c_str());
      
    SHOULDFAIL(v.getScalar());
    SHOULDFAIL(v.getArray());
    SHOULDFAIL(v.getScalarT<Int32>());
      
    TESTEQUAL("string (hello world)", v.getDescription());
  }

  // ValueMap
  {
    boost::shared_ptr<Scalar> s(new Scalar(NTA_BasicType_Int32));
    s->value.int32 = 10;
    boost::shared_ptr<Array> a(new Array(NTA_BasicType_Real32));
    boost::shared_ptr<std::string> str(new std::string("hello world"));
    
    ValueMap vm;
    vm.add("scalar", s);
    vm.add("array", a);
    vm.add("string", str);
    SHOULDFAIL(vm.add("scalar", s));

    TEST(vm.contains("scalar"));
    TEST(vm.contains("array"));
    TEST(vm.contains("string"));
    TEST(!vm.contains("foo"));
    TEST(!vm.contains("scalar2"));
    TEST(!vm.contains("xscalar"));
    
    boost::shared_ptr<Scalar> s1 = vm.getScalar("scalar");
    TEST(s1 == s);
    
    boost::shared_ptr<Array> a1 = vm.getArray("array");
    TEST(a1 == a);
    
    boost::shared_ptr<Scalar> def(new Scalar(NTA_BasicType_Int32));
    Int32 x = vm.getScalarT("scalar", (Int32)20);
    TESTEQUAL((Int32)10, x);
    
    x = vm.getScalarT("scalar2", (Int32)20);
    TESTEQUAL((Int32)20, x);

    Value v = vm.getValue("array");
    TESTEQUAL(Value::arrayCategory, v.getCategory());
    TEST(v.getArray() == a);
  }
}



