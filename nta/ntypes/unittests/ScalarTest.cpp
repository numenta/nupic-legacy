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
 * Implementation of Scalar test
 */

#include <nta/ntypes/unittests/ScalarTest.hpp>
#include <nta/ntypes/Scalar.hpp>

using namespace nta;

void ScalarTest::RunTests()
{
  Scalar a(NTA_BasicType_UInt16);

  //Test UInt16
  a = Scalar(NTA_BasicType_UInt16);
  SHOULDFAIL(a.getValue<UInt64>());
  TESTEQUAL((UInt16)0, a.getValue<UInt16>());
  TESTEQUAL(NTA_BasicType_UInt16, a.getType());
  a.value.uint16 = 10;
  TESTEQUAL((UInt16)10, a.getValue<UInt16>());
  
  //Test UInt32
  a = Scalar(NTA_BasicType_UInt32);
  SHOULDFAIL(a.getValue<UInt64>());
  TESTEQUAL((UInt32)0, a.getValue<UInt32>());
  TESTEQUAL(NTA_BasicType_UInt32, a.getType());
  a.value.uint32 = 10;
  TESTEQUAL((UInt32)10, a.getValue<UInt32>());

  //Test UInt64
  a = Scalar(NTA_BasicType_UInt64);
  SHOULDFAIL(a.getValue<UInt32>());
  TESTEQUAL((UInt64)0, a.getValue<UInt64>());
  TESTEQUAL(NTA_BasicType_UInt64, a.getType());
  a.value.uint64 = 10;
  TESTEQUAL((UInt64)10, a.getValue<UInt64>());
  
  //Test Int16
  a = Scalar(NTA_BasicType_Int16);
  SHOULDFAIL(a.getValue<Int32>());
  TESTEQUAL((Int16)0, a.getValue<Int16>());
  TESTEQUAL(NTA_BasicType_Int16, a.getType());
  a.value.int16 = 10;
  TESTEQUAL((Int16)10, a.getValue<Int16>());

  //Test Int32
  a = Scalar(NTA_BasicType_Int32);
  SHOULDFAIL(a.getValue<Int64>());
  TESTEQUAL((Int32)0, a.getValue<Int32>());
  TESTEQUAL(NTA_BasicType_Int32, a.getType());
  a.value.int32 = 10;
  TESTEQUAL((Int32)10, a.getValue<Int32>());

  //Test Int64
  a = Scalar(NTA_BasicType_Int64);
  SHOULDFAIL(a.getValue<UInt32>());
  TESTEQUAL((Int64)0, a.getValue<Int64>());
  TESTEQUAL(NTA_BasicType_Int64, a.getType());
  a.value.int64 = 10;
  TESTEQUAL((Int64)10, a.getValue<Int64>());

  //Test Real32
  a = Scalar(NTA_BasicType_Real32);
  SHOULDFAIL(a.getValue<UInt64>());
  TESTEQUAL((Real32)0, a.getValue<Real32>());
  TESTEQUAL(NTA_BasicType_Real32, a.getType());
  a.value.real32 = 10;
  TESTEQUAL((Real32)10, a.getValue<Real32>());

  //Test Real64
  a = Scalar(NTA_BasicType_Real64);
  SHOULDFAIL(a.getValue<UInt64>());
  TESTEQUAL((Real64)0, a.getValue<Real64>());
  TESTEQUAL(NTA_BasicType_Real64, a.getType());
  a.value.real64 = 10;
  TESTEQUAL((Real64)10, a.getValue<Real64>());

  //Test Handle
  a = Scalar(NTA_BasicType_Handle);
  SHOULDFAIL(a.getValue<UInt64>());
  TESTEQUAL((Handle)0, a.getValue<Handle>());
  TESTEQUAL(NTA_BasicType_Handle, a.getType());
  int x = 10;
  a.value.handle = &x;
  int* p = (int*)(a.getValue<Handle>());
  TESTEQUAL(&x, a.getValue<Handle>());
  TESTEQUAL(x, *p);
  (*p)++;
  TESTEQUAL(11, *p);
  
  //Test Byte
  a = Scalar(NTA_BasicType_Byte);
  SHOULDFAIL(a.getValue<UInt64>());
  TESTEQUAL((Byte)0, a.getValue<Byte>());
  TESTEQUAL(NTA_BasicType_Byte, a.getType());
  a.value.byte = 'a';
  TESTEQUAL('a', a.getValue<Byte>());
  a.value.byte++;
  TESTEQUAL('b', a.getValue<Byte>());
}
