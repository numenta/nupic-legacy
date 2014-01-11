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
 * Notes
 */

#include "MemStreamTest.hpp"
#include <nta/ntypes/MemStream.hpp>
#include <nta/utils/Log.hpp>

#include <stdexcept>
#include <string>
#include <iostream>

namespace nta {

  static size_t memLimitsTest(size_t max)
  {
    OMemStream ms;
  
    // Create a large string to dump the stream
    size_t chunkSize = 0x1000000;  // 16 MByte
    std::string test(chunkSize, 'M');  
  
    /*
      std::string test2 (0x10000000, '1');  
      std::string test3 (0x10000000, '2');  
      std::string test4 (0x10000000, '3');  
      std::string test5 (0x10000000, '4');  
      std::string test6 (0x10000000, '5');  
      std::string test7 (0x10000000, '6');  
      std::string test8 (0x10000000, '7');  
      std::string test9 (0x10000000, '8');  
    */

  
    size_t count = 1;
    while (count * chunkSize <= max) {
      //std::cout << hex << "0x" << count << ".";
      //std::cout.flush();
      try {
        ms << test;
      } catch (std::exception& /* unused */) {
        NTA_DEBUG << "Exceeded memory limit at " << std::hex << "0x" << count * chunkSize << std::dec 
                  << " bytes.";
        break;
      }
      count++;
    }
  
    // Return largest size that worked
    return (count-1) * chunkSize;
  }



  void MemStreamTest::RunTests() 
  {
  
    // -------------------------------------------------------
    // Test input stream
    // -------------------------------------------------------
    {
      std::string test("hi there");  
    
      IMemStream ms((char*)(test.data()), test.size());
      std::stringstream ss(test);
    
      for (int i=0; i<5; i++)
      {
        std::string s1, s2;
        ms >> s1;
        ss >> s2;
        TESTEQUAL2("in", s2, s1);
        TESTEQUAL2("in fail", ss.fail(), ms.fail());
        TESTEQUAL2("in eof", ss.eof(), ms.eof());
      }      


      // Test changing the buffer 
      std::string test2("bye now");  
      ms.str((char*)(test2.data()), test2.size());
      ms.seekg(0);
      ms.clear();
      std::stringstream ss2(test2);
    
      for (int i=0; i<5; i++)
      {
        std::string s1, s2;
        ms >> s1;
        ss2 >> s2;
        TESTEQUAL2("in2", s2, s1);
        TESTEQUAL2("in2 fail", ss2.fail(), ms.fail());
        TESTEQUAL2("in2 eof", ss2.eof(), ms.eof());
      }      
    }


    // -------------------------------------------------------
    // Test setting the buffer on a default input stream
    // -------------------------------------------------------
    {
      std::string test("third test");  
    
      IMemStream ms;
      ms.str((char*)(test.data()), test.size());
      std::stringstream ss(test);
    
      for (int i=0; i<5; i++)
      {
        std::string s1, s2;
        ms >> s1;
        ss >> s2;
        TESTEQUAL2("in2", s2, s1);
        TESTEQUAL2("in2 fail", ss.fail(), ms.fail());
        TESTEQUAL2("in2 eof", ss.eof(), ms.eof());
      }      
    }
  
  
    // -------------------------------------------------------
    // Test output stream
    // -------------------------------------------------------
    {
      OMemStream ms;
      std::stringstream ss;
    
      for (int i=0; i<500; i++)
      {
        ms << i << " ";
        ss << i << " ";
      }
        
      const char* dataP = ms.str();
      size_t size = ms.pcount();
      std::string msStr(dataP, size);
      std::string ssStr = ss.str();
      TESTEQUAL2("out data", msStr, ssStr);
      TESTEQUAL2("out eof", ms.eof(), ss.eof());
      TESTEQUAL2("out fail", ms.fail(), ss.fail());
    }
  
    // -------------------------------------------------------
    // Test memory limits
    // -------------------------------------------------------
    // Set max at 0x10000000 for day to day testing so that test doesn't take too long.
    // To determine the actual memory limits, change this max to something very large and
    // see where we break. 
  
    size_t max = 0x10000000L;
    size_t sizeLimit = memLimitsTest(max);
    TESTEQUAL2("maximum stream size", sizeLimit >= max, true);  
  }






} // namespace nta
