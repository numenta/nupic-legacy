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

#include "MemParserTest.hpp"
#include <nta/ntypes/MemParser.hpp>

#include <stdexcept>
#include <string>
#include <iostream>

namespace nta {

void MemParserTest::RunTests() 
{
  // -------------------------------------------------------
  // Test using get methods
  // -------------------------------------------------------
  {
    std::stringstream ss; 
    
    // Write one of each type to the stream
    unsigned long a = 10;
    long b = -20;
    double c = 1.5;
    float d = 1.6f;
    std::string e = "hello";
    
    ss << a << " " 
       << b << " "
       << c << " "
       << d << " "
       << e << " ";
    
    // Read back 
    MemParser in(ss, (UInt32)ss.str().size());
    
    unsigned long test_a = 0;
    in.get(test_a);
    TESTEQUAL2("get ulong", a, test_a);
    
    long test_b = 0;
    in.get(test_b);
    TESTEQUAL2("get long", b, test_b);
    
    double test_c = 0;
    in.get(test_c);
    TESTEQUAL2("get double", c, test_c);
    
    float test_d = 0;
    in.get(test_d);
    TESTEQUAL2("get float", d, test_d);
    
    std::string test_e = "";
    in.get(test_e);
    TESTEQUAL2("get string", e, test_e);
    

    // Test EOF
    SHOULDFAIL(in.get(test_e));
  }

 
  // -------------------------------------------------------
  // Test passing in -1 for the size to read in entire stream
  // -------------------------------------------------------
  {
    std::stringstream ss; 
    
    // Write one of each type to the stream
    unsigned long a = 10;
    long b = -20;
    double c = 1.5;
    float d = 1.6f;
    std::string e = "hello";
    
    ss << a << " " 
       << b << " "
       << c << " "
       << d << " "
       << e << " ";
    
    // Read back 
    MemParser in(ss);
    
    unsigned long test_a = 0;
    in.get(test_a);
    TESTEQUAL2("get ulong b", a, test_a);
    
    long test_b = 0;
    in.get(test_b);
    TESTEQUAL2("get long b", b, test_b);
    
    double test_c = 0;
    in.get(test_c);
    TESTEQUAL2("get double b", c, test_c);
    
    float test_d = 0;
    in.get(test_d);
    TESTEQUAL2("get float b", d, test_d);
    
    std::string test_e = "";
    in.get(test_e);
    TESTEQUAL2("get string b", e, test_e);
    

    // Test EOF
    SHOULDFAIL(in.get(test_e));
  }

 
  // -------------------------------------------------------
  // Test using >> operator
  // -------------------------------------------------------
  {
    std::stringstream ss; 
    
    // Write one of each type to the stream
    unsigned long a = 10;
    long b = -20;
    double c = 1.5;
    float d = 1.6f;
    std::string e = "hello";
    
    ss << a << " " 
       << b << " "
       << c << " "
       << d << " "
       << e << " ";
    
    // Read back 
    MemParser in(ss, (UInt32)ss.str().size());
    
    unsigned long test_a = 0;
    long test_b = 0;
    double test_c = 0;
    float test_d = 0;
    std::string test_e = "";
    in >> test_a >> test_b >> test_c >> test_d >> test_e;
    TESTEQUAL2(">> ulong", a, test_a);
    TESTEQUAL2(">> long", b, test_b);
    TESTEQUAL2(">> double", c, test_c);
    TESTEQUAL2(">> float", d, test_d);
    TESTEQUAL2(">> string", e, test_e);
    

    // Test EOF
    SHOULDFAIL(in >> test_e);
  }

 
  // -------------------------------------------------------
  // Test reading trying to read an int when we have a string
  // -------------------------------------------------------
  {
    std::stringstream ss; 
    ss << "hello";
        
    // Read back 
    MemParser in(ss, (UInt32)ss.str().size());
    
    // Test EOF
    long  v;
    SHOULDFAIL(in.get(v));
  } 
}






} // namespace nta
