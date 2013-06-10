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

/**
 * @file
 */

#include <unistd.h>
#include "OSTest.hpp"
#include <nta/os/Env.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/Directory.hpp>

using namespace nta;

OSTest::OSTest() {};

OSTest::~OSTest() {};


void OSTest::RunTests()
{
#ifdef WIN32

#else
  // save the parts of the environment we'll be changing
  std::string savedHOME;
  bool isHomeSet = Env::get("HOME", savedHOME);
  
  Env::set("HOME", "/home1/myhome");
  Env::set("USER", "user1");
  Env::set("LOGNAME", "logname1");
  
  TESTEQUAL2("OS::getHomeDir", "/home1/myhome", OS::getHomeDir());
  bool caughtException = false;
  Env::unset("HOME");
  std::string dummy;
  try {
    dummy = OS::getHomeDir();
  } catch (...) {
    caughtException = true;
  }
  TEST2("getHomeDir -- HOME not set", caughtException == true);
  // restore HOME
  if (isHomeSet) {
    Env::set("HOME", savedHOME);
  }


#endif

  // Test getUserName()
  {
#ifdef WIN32
    Env::set("USERNAME", "123");
    TEST(OS::getUserName() == "123");    
#else
    // case 1 - USER defined
    Env::set("USER", "123");
    TEST(OS::getUserName() == "123");

    // case 2 - USER not defined, LOGNAME defined
    Env::unset("USER");
    Env::set("LOGNAME", "456");
    TEST(OS::getUserName() == "456");

    // case 3 - USER and LOGNAME not defined
    Env::unset("LOGNAME");
    
    std::stringstream ss("");
    ss << getuid();
    TEST(OS::getUserName() == ss.str());
#endif
  }
  

  // Test getStackTrace()
  {
#ifdef WIN32
//    std::string stackTrace = OS::getStackTrace();
//    TEST(!stackTrace.empty());  
//
//    stackTrace = OS::getStackTrace();
//    TEST(!stackTrace.empty());
#endif  
  }
}

