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
 * Implementation for DynamicLibrary test
 */


#include <nta/os/DynamicLibrary.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/Env.hpp>

#include "DynamicLibraryTest.hpp"

#include <iostream>

using namespace std;
using namespace nta;


static Path getPath(const std::string & s)
{
  // find a path relative to the installation directory
  // Assume testeverything is in <nupic-root>/bin/testeverything
  std::string mypath = Path::makeAbsolute(Path::getExecutablePath());
  std::string rootdir = Path::getParent(Path::getParent(mypath));
  return Path(Path::join(rootdir, s));
}

void DynamicLibraryTest::RunTests()
{
  DynamicLibrary * d = NULL;

  // Try to load "empty" library
  {
    string errorString;
    d = DynamicLibrary::load("", errorString);
    TEST2("Shouldn't be able to load \"\" library", d == NULL); 
    TEST2("Should have non-empty error string", errorString.size() != 0);
  }
   
  // Try to load non-existent library
  string s("non_exisiting_file");
  Path path(s);
  
  TEST2("Make sure file doesn't exist", !path.exists());
 
  { 
    string errorString;
    d = DynamicLibrary::load(s, errorString);
  }

  TEST2("Shouldn't be able to load non-existent library", d == NULL);
  delete d; // just to satisfy coverity, not really needed, but harmless

  // Try to load corrupt library (this source file)
#ifdef WIN32
  s = "lib\\cpp_region.dll";
  path = getPath(s);
#else
  s = "share/test/data/fake.dynamic.library";
  path = getPath(s);
  TEST2("Make sure \"corrupt\" file exists", path.exists());  

  {
    string errorString;
    d = DynamicLibrary::load(std::string(path), errorString);
  }
  TEST2("Shouldn't be able to load corrupt library", d == NULL);

  // Load good library (very inelegant way to handle different suffix on mac and linux)
  s = "lib/libcpp_region.dylib";
  path = getPath(s);
  if (!path.exists())
  {
    s = "lib/libcpp_region.so";
    path = getPath(s);
  }
#endif

  std::cout << "Looking for path '" << path << "'\n";
  TEST2("Make sure file exists", path.exists());
  {
    string errorString;
    d = DynamicLibrary::load(std::string(path), errorString);
    TEST2("Should be able to load good library", d != NULL);
    TEST2("Should have empty error string", errorString.empty());
    if (!errorString.empty())
    {
      std::cout << "Error String: " << errorString << "\n";
    }
  }
  
  
  if (d) {
    // Get existing symbol
    void * sym = d->getSymbol("NTA_initPython");
    TEST2("Should be able to get 'NTA_initPython' symbol", sym != NULL);
    
    // Get non-existing symbol
    sym = d->getSymbol("non exisitng symbol");
    TEST2("Should NOT be able to get 'non exisitng symbol' symbol", sym == NULL);
    delete d;    
  }
}

