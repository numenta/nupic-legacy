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
 * Implementation for Directory test
 */


#include <nta/os/regex.hpp>
#include "regexTest.hpp"

using namespace std;
using namespace nta;


void regexTest::RunTests()
{
  
  TEST(regex::match(".*", ""));
  TEST(regex::match(".*", "dddddfsdsgregegr"));
  TEST(regex::match("d.*", "d"));  
  TEST(regex::match("^d.*", "ddsfffdg"));
  TEST(!regex::match("d.*", ""));
  TEST(!regex::match("d.*", "a"));
  TEST(!regex::match("^d.*", "ad"));
  TEST(!regex::match("Sensor", "CategorySensor"));
  
  
  TEST(regex::match("\\\\", "\\"));  
                
//  TEST(regex::match("\\w", "a"));  
//  TEST(regex::match("\\d", "3"));    
//  TEST(regex::match("\\w{3}", "abc"));
//  TEST(regex::match("^\\w{3}$", "abc"));  
//  TEST(regex::match("[\\w]{3}", "abc"));  
  
  TEST(regex::match("[A-Za-z0-9_]{3}", "abc"));
  
  // Invalid expression tests (should throw)
  try
  {
    TEST(regex::match("", ""));
    TEST(false);
  }
  catch (...)
  {
  }
   
  try
  {
    TEST(regex::match("xyz[", ""));
    TEST(false);
  }
  catch (...)
  {
  }
}

