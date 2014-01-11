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

/**
 * @file
 */


#include "EnvTest.hpp"

using namespace nta;

EnvTest::EnvTest() {};

EnvTest::~EnvTest() {};


void EnvTest::RunTests()
{
  std::string name;
  std::string value;
  bool result;
  
  // get value that is not set
  value = "DONTCHANGEME";
  result = Env::get("NOTDEFINED", value);
  TESTEQUAL2("get not set result", false, result);
  TESTEQUAL2("get not set value", "DONTCHANGEME", value.c_str());
  
  // get value that should be set
  value = "";
  result = Env::get("PATH", value);
  TESTEQUAL2("get PATH result", true, result);
  TEST2("get path value", value.length() > 0);
  
  // set a value
  name = "myname";
  value = "myvalue";
  Env::set(name, value);
  
  // retrieve it
  value = "";
  result = Env::get(name, value);
  TESTEQUAL2("get value just set -- result", true, result);
  TESTEQUAL2("get value just set -- value", "myvalue", value.c_str());
  
  // set it to something different
  value = "mynewvalue";
  Env::set(name, value);
  
  // retrieve the new value
  result = Env::get(name, value);
  TESTEQUAL2("get second value just set -- result", true, result);
  TESTEQUAL2("get second value just set -- value", "mynewvalue", value.c_str());
  
  // delete the value
  value = "DONTCHANGEME";
  Env::unset(name);
  result = Env::get(name, value);
  TESTEQUAL2("get after delete -- result", false, result);
  TESTEQUAL2("get after delete -- value", "DONTCHANGEME", value.c_str());
  
  // delete a value that is not set
  // APR response is not documented. Will see a warning if 
  // APR reports an error. 
  // Is there any way to do an actual test here? 
  Env::unset(name);
}

