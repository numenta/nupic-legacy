/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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
 * Implementation for Buffer unit tests
 */

#include "BufferTest.hpp"
#include <nta/math/math.hpp>
#include <nta/utils/Log.hpp>
#include <cstring> // strlen

// This test accesses private methods. 
#define private public
#include <nta/ntypes/Buffer.hpp>
#undef private

#include <algorithm>

using namespace nta; 

void BufferTest::testReadBytes_VariableSizeBuffer(Size buffSize)
{
  std::vector<Byte> in;
  std::vector<Byte> out;
  in.resize(buffSize+1);
  out.resize(buffSize+1);
    
  std::fill(in.begin(), in.begin()+in.capacity(), 'I');
  std::fill(out.begin(), out.begin()+out.capacity(), 'O');
  
  for (Size i = 0; i <= buffSize; ++i)
  {
    TEST(in[i] == 'I');
    TEST(out[i] == 'O');
  }
  
  // Populate the ReadBuffer with the input
  ReadBuffer rb(&in[0], buffSize);
    
  // Get the abstract interface
  IReadBuffer & r = rb;
  
  // Prepare for reading from the read buffer in chunks
  const Size CHUNK_SIZE = 10;
  Size size = CHUNK_SIZE;

  // Read chunks until the buffer is exhausted and write everything to out buffer
  Size index = 0;
  while (size == CHUNK_SIZE)
  {
    Int32 res = r.read(&out[index], size);
    TEST(res == 0);
    index += size;
  }
  
  // Verify that last index and last read size are correct
  TEST(index == buffSize);
  TEST(size == buffSize % CHUNK_SIZE);
  
  // Check corner cases
  TEST(out[0] == 'I');
  TEST(out[buffSize-1] == 'I');
  TEST(out[buffSize] == 'O');
  
  // Check that all other values have been read correctly
  Size i;
  for (i = 1; i < buffSize-1; ++i)
    TEST(out[i] == 'I');
}

void BufferTest::testReadBytes_SmallBuffer()
{
  ReadBuffer b((const Byte *)"123", 3);

  IReadBuffer & reader = b;   

  Byte out[5];
  Size size = 0;
  Int32 res = 0;
  
  size = 2;
  res = reader.read(out, size);
  TEST2("BufferTest::testReadBuffer(), reader.read(2) failed", res == 0);
  TEST2("BufferTest::testReadBuffer(), reader.read(2) failed", size == 2);
  TEST2("BufferTest::testReadBuffer(), out[0] should be 1 after reading 1,2", out[0] == '1'); 
  TEST2("BufferTest::testReadBuffer(), out[1] should be 2 after reading 1,2", out[1] == '2');
  
  size = 2;
  res = reader.read(out+2, size);
  TEST2("BufferTest::testReadBuffer(), reader.read(2) failed", res == 0);
  TEST2("BufferTest::testReadBuffer(), reader.read(2) failed", size == 1);
  TEST2("BufferTest::testReadBuffer(), out[0] should be 1 after reading 3", out[0] == '1'); 
  TEST2("BufferTest::testReadBuffer(), out[1] should be 2 after reading 3", out[1] == '2');
  TEST2("BufferTest::testReadBuffer(), out[2] should be 3 after reading 3", out[2] == '3');  
}

void BufferTest::testWriteBytes()
{
  WriteBuffer b;
  Byte out[5] = { 1, 2, 3, 4, 5 };
  IWriteBuffer & writer = b;   
  TEST2("BufferTest::testWriteBuffer(), writer.getSize() should be 0 before putting anything in", writer.getSize() == 0);
  Size size = 3;
  writer.write(out, size);
  TEST2("BufferTest::testWriteBuffer(), writer.getSize() should be 3 after writing 1,2,3", writer.getSize() == 3);
  size = 2;
  writer.write(out+3, size);
  TEST2("BufferTest::testWriteBuffer(), writer.getSize() should be 5 after writing 4,5", writer.getSize() == 5);
  const Byte * s = writer.getData();
  size = writer.getSize();
  //NTA_INFO << "s=" << string(s, size) << ", size=" << size;
  TEST2("BufferTest::testWriteBuffer(), writer.str() == 12345", std::string(s, size) == std::string("\1\2\3\4\5"));
}

void BufferTest::testEvenMoreComplicatedSerialization()
{
  struct X
  {
    X() :  a((Real)3.4)
         , b(6)
         , c('c')
         , e((Real)-0.04)
    {
      for (int i = 0; i < 4; ++i)
        d[i] = 'A' + i;

      for (int i = 0; i < 3; ++i)
        f[i] = 100 + i;    
    }
    
    Real a;
    UInt32 b;
    Byte c;
    Byte d[4];
    Real e;
    Int32  f[3];
  };
  
  X xi[2];

  xi[0].a = (Real)8.8;
  xi[1].a = (Real)4.5;
  xi[1].c = 't';
  xi[1].d[0] = 'X';
  xi[1].e = (Real)3.14;
  xi[1].f[0] = -999;  
  // Write the two Xs to a buffer
  WriteBuffer wb;
  TEST2("BufferTest::testComplicatedSerialization(), empty WriteBuffer should have 0 size", wb.getSize() == 0);
  
  // Write the number of Xs
  UInt32 size = 2;
  wb.write((UInt32 &)size);
  // Write all Xs.
  for (UInt32 i = 0; i < size; ++i)
  {
    wb.write(xi[i].a);
    wb.write(xi[i].b);
    wb.write(xi[i].c);
    Size len = 4;
    wb.write((const Byte *)xi[i].d, len);
    wb.write(xi[i].e);
    len = 3;
    wb.write(xi[i].f, len);  
  }
  
  ReadBuffer rb(wb.getData(), wb.getSize());
  // Read number of Xs
  rb.read(size);
  // Allocate array of Xs
  X * xo = new X[size];
  for (Size i = 0; i < size; ++i)
  {
    rb.read(xo[i].a);
    rb.read(xo[i].b);
    rb.read(xo[i].c);
    Size len = 4;
    Int32 res = rb.read(xo[i].d, len);
    TEST2("BufferTest::testComplicatedSerialization(), rb.read(xi[i].d, 4) failed", res == 0);
    TEST2("BufferTest::testComplicatedSerialization(), rb.read(xi[i].d, 4) == 4", len == 4);
    rb.read(xo[i].e);
    len = 3;
    res = rb.read(xo[i].f, len);
    NTA_INFO << "xo[" << i << "]={" << xo[i].a << " "
             << xo[i].b << " " 
             << xo[i].c << " " 
             << "'" << std::string(xo[i].d, 4) << "'" 
             << " " << xo[i].e << " "
             << "'" << xo[i].f[0] << "," << xo[i].f[1] << "," << xo[i].f[2] << "'" 
             ;
  }
  
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].a == 8.8", nearlyEqual(xo[0].a, nta::Real(8.8)));
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].b == 6", xo[0].b == 6);
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].c == 'c'", xo[0].c == 'c');
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].d == ABCD", std::string(xo[0].d, 4) == std::string("ABCD"));
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].e == -0.04", nearlyEqual(xo[0].e, nta::Real(-0.04)));
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].f[0] == 100", xo[0].f[0] == 100);
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].f[1] == 101", xo[0].f[1] == 101);
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].f[2] == 102", xo[0].f[2] == 102);
  
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].a == 4.5", xo[1].a == nta::Real(4.5));
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].b == 6", xo[1].b == 6);
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].c == 't'", xo[1].c == 't');
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].d == XBCD", std::string(xo[1].d, 4) == std::string("XBCD"));
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].e == 3.14", xo[1].e == nta::Real(3.14));
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].f[0] == -999", xo[1].f[0] == -999);
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].f[1] == 101", xo[1].f[1] == 101);
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].f[2] == 102", xo[1].f[2] == 102);
}

void BufferTest::testComplicatedSerialization()
{
  struct X
  {
    X() :  a((Real)3.4)
         , b(6)
         , c('c')
         , e((Real)-0.04)
    {
      for (int i = 0; i < 4; ++i)
        d[i] = 'A' + i;
    }
    
    Real a;
    UInt32 b;
    Byte c;
    Byte d[4];
    Real e;
  };
  
  X xi[2];

  xi[0].a = (Real)8.8;
  xi[1].a = (Real)4.5;
  xi[1].c = 't';
  xi[1].d[0] = 'X';
  xi[1].e = (Real)3.14;
  
  // Write the two Xs to a buffer
  WriteBuffer wb;
  TEST2("BufferTest::testComplicatedSerialization(), empty WriteBuffer should have 0 size", wb.getSize() == 0);
  
  // Write the number of Xs
  UInt32 size = 2;
  wb.write((UInt32 &)size);
  // Write all Xs.
  for (UInt32 i = 0; i < size; ++i)
  {
    wb.write(xi[i].a);
    wb.write(xi[i].b);
    wb.write(xi[i].c);
    Size len = 4;
    wb.write((const Byte *)xi[i].d, len);
    wb.write(xi[i].e);
  }
  
  ReadBuffer rb(wb.getData(), wb.getSize());
  // Read number of Xs
  rb.read(size);
  // Allocate array of Xs
  X * xo = new X[size];
  for (Size i = 0; i < size; ++i)
  {
    rb.read(xo[i].a);
    rb.read(xo[i].b);
    rb.read(xo[i].c);
    Size size = 4;
    Int32 res = rb.read(xo[i].d, size);
    TEST2("BufferTest::testComplicatedSerialization(), rb.read(xi[i].d, 4) failed", res == 0);
    TEST2("BufferTest::testComplicatedSerialization(), rb.read(xi[i].d, 4) == 4", size == 4);
    rb.read(xo[i].e);
    NTA_INFO << "xo[" << i << "]={" << xo[i].a << " "
             << xo[i].b << " " 
             << xo[i].c << " " 
             << "'" << std::string(xo[i].d, 4) << "'" 
             << " " << xo[i].e
             ;
  }
  
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].a == 8.8", nearlyEqual(xo[0].a, nta::Real(8.8)));
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].b == 6", xo[0].b == 6);
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].c == 'c'", xo[0].c == 'c');
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].d == ABCD", std::string(xo[0].d, 4) == std::string("ABCD"));
  TEST2("BufferTest::testComplicatedSerialization(), xo[0].e == -0.04", nearlyEqual(xo[0].e, nta::Real(-0.04)));

  TEST2("BufferTest::testComplicatedSerialization(), xo[1].a == 4.5", xo[1].a == nta::Real(4.5));
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].b == 6", xo[1].b == 6);
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].c == 't'", xo[1].c == 't');
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].d == XBCD", std::string(xo[1].d, 4) == std::string("XBCD"));
  TEST2("BufferTest::testComplicatedSerialization(), xo[1].e == 3.14", xo[1].e == nta::Real(3.14));
}

void BufferTest::testArrayMethods()
{
  // Test read UInt32 array
  {
    const Byte * s = "1 2 3 444";
    ReadBuffer b(s, (Size)::strlen(s));
    IReadBuffer & reader = b;   

    UInt32 result[4];
    std::fill(result, result+4, 0);
    for (UInt32 i = 0; i < 4; ++i)
    {
      TEST(result[i]== 0);
    }
  
    reader.read((UInt32 *)result, 3);
    for (UInt32 i = 0; i < 3; ++i)
    {
      TEST(result[i] == i+1);
    }

    UInt32 val = 0;
    reader.read(val);
    TEST(val == 444);
  }
  
  // Test read Int32 array
  {
    const Byte * s = "-1 -2 -3 444";
    ReadBuffer b(s, (Size)::strlen(s));
    IReadBuffer & reader = b;   

    Int32 result[4];
    std::fill(result, result+4, 0);
    for (Int32 i = 0; i < 4; ++i)
    {
      TEST(result[i]== 0);
    }
  
    reader.read((Int32 *)result, 3);
    for (Int32 i = 0; i < 3; ++i)
    {
      TEST(result[i] == -i-1);
    }

    Int32 val = 0;
    reader.read(val);
    TEST(val == 444);
  }
  
  // Test read Real32 array
  {
    const Byte * s = "1.5 2.5 3.5 444.555";
    ReadBuffer b(s, (Size)::strlen(s));
    IReadBuffer & reader = b;   

    Real32 result[4];
    std::fill(result, result+4, (Real32)0);
    for (UInt32 i = 0; i < 4; ++i)
    {
      TEST(result[i]== 0);
    }
  
    reader.read((Real32 *)result, 3);
    for (UInt32 i = 0; i < 3; ++i)
    {
      TEST(result[i] == i+1.5);
    }

    Real32 val = 0;
    reader.read(val);
    TEST(nearlyEqual(val, Real32(444.555)));
  }
}

//----------------------------------------------------------------------
void BufferTest::RunTests()
{

  testReadBytes_SmallBuffer();
  testReadBytes_VariableSizeBuffer(5);
//  testReadBytes_VariableSizeBuffer(128);
//  testReadBytes_VariableSizeBuffer(227);
//  testReadBytes_VariableSizeBuffer(228);
//  testReadBytes_VariableSizeBuffer(229);
//  testReadBytes_VariableSizeBuffer(315);
//  testReadBytes_VariableSizeBuffer(482);
//  testReadBytes_VariableSizeBuffer(483);
//  testReadBytes_VariableSizeBuffer(484);
//  testReadBytes_VariableSizeBuffer(512);
//  testReadBytes_VariableSizeBuffer(2000);
//  testReadBytes_VariableSizeBuffer(20000);
  
  
  testWriteBytes();
  testComplicatedSerialization();
  testEvenMoreComplicatedSerialization();
  testArrayMethods();
}
    

