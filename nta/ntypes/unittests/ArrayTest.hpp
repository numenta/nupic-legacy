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
 * ArrayBase unit tests
 */

#ifndef NTA_ARRAY_TEST_HPP
#define NTA_ARRAY_TEST_HPP

#include <nta/test/Tester.hpp>

#include <map>

namespace nta
{
  struct ArrayTestParameters
  {
    NTA_BasicType dataType;
    unsigned int dataTypeSize;
    int allocationSize; //We intentionally use an int instead of a size_t for
                        //these tests.  This is so that we can check test usage
                        //by a naive user who might use an int and accidentally
                        //pass negative values.
    std::string dataTypeText;
    bool testUsesInvalidParameters;
    
    ArrayTestParameters() :
      dataType((NTA_BasicType) -1),
      dataTypeSize(0),
      allocationSize(0),
      dataTypeText(""),
      testUsesInvalidParameters(true) {}
      
    ArrayTestParameters(NTA_BasicType dataTypeParam,
                        unsigned int dataTypeSizeParam,
                        int allocationSizeParam,
                        std::string dataTypeTextParam,
                        bool testUsesInvalidParametersParam) :
      dataType(dataTypeParam),
      dataTypeSize(dataTypeSizeParam),
      allocationSize(allocationSizeParam),
      dataTypeText(dataTypeTextParam),
      testUsesInvalidParameters(testUsesInvalidParametersParam) { }
  };

  struct ArrayTest : public Tester
  {
    virtual ~ArrayTest() {}
    virtual void RunTests();
        
private:
    std::map<std::string,ArrayTestParameters> testCases_;

    typedef std::map<std::string,ArrayTestParameters>::iterator
      TestCaseIterator;
    
#ifdef NTA_INSTRUMENTED_MEMORY_GUARDED
    void testMemoryOperations();
#endif

    void testArrayCreation();
    void testBufferAllocation();
    void testBufferAssignment();
    void testBufferRelease();
    void testArrayTyping();
  };
}

#endif // NTA_ARRAY_TEST_HPP
