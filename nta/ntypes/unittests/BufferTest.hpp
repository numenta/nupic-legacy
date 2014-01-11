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
 * Declarations for Buffer unit tests
 */

#ifndef NTA_BUFFER_TEST_HPP
#define NTA_BUFFER_TEST_HPP

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>

//----------------------------------------------------------------------

#include <nta/types/types.hpp>
namespace nta 
{
  //----------------------------------------------------------------------
  class BufferTest : public Tester
  {
  
  public:
     BufferTest() {}
    
    // Run all appropriate tests
    virtual void RunTests();

  private:
    // Default copy ctor and assignment operator forbidden by default
    BufferTest(const BufferTest&);
    BufferTest& operator=(const BufferTest&);
    
    void testReadBytes_SmallBuffer();
    void testReadBytes_VariableSizeBuffer(Size buffSize);
    void testWriteBytes();
    void testComplicatedSerialization();
    void testEvenMoreComplicatedSerialization();
    void testArrayMethods();

  }; // end class BufferTest
    
    //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_BUFFER_TEST_HPP
