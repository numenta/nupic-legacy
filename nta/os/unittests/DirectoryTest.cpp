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


#include <nta/os/Directory.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/OS.hpp>
#include <nta/os/FStream.hpp>
#include "DirectoryTest.hpp"
#include <apr-1/apr.h>

#ifdef WIN32
  #include <windows.h>
#else
  #include <unistd.h>
#endif

#include <algorithm> // sort
using namespace std;
using namespace nta;

static std::string getCurrDir()
{
    char buff[APR_PATH_MAX+1];
#ifdef WIN32
  DWORD res = ::GetCurrentDirectoryA(APR_PATH_MAX, (LPSTR)buff);
  NTA_CHECK(res > 0) << OS::getErrorMessage();

#else
  char * s = ::getcwd(buff, APR_PATH_MAX);
  NTA_CHECK(s != NULL) << OS::getErrorMessage();
#endif
  return buff;  
}

void DirectoryTest::RunTests()
{

  std::string sep(Path::sep);
  
  // Test exists
  {
    
    TEST(!Directory::exists("No such dir"));
    if (Directory::exists("dir_0"))
      Directory::removeTree("dir_0");
    Directory::create("dir_0");
    TEST(Directory::exists("dir_0"));    
    Directory::removeTree("dir_0");
  }
  
  // Test setCWD
  {
    Directory::create("dir_1");
    
    std::string baseDir = Path::makeAbsolute(getCurrDir());
    Directory::setCWD("dir_1");
    std::string cwd1 = Path::makeAbsolute(getCurrDir());    

    std::string cwd2 = Path::makeAbsolute(baseDir + Path::sep + std::string("dir_1"));
    TESTEQUAL2("makeAbsolute",  cwd1, cwd2);
    
    Directory::setCWD(baseDir);
    TESTEQUAL2("setCWD", baseDir, getCurrDir());
    Directory::removeTree("dir_1");
  }
  
  // Test getCWD
  {
    TESTEQUAL2("getCWD2", getCurrDir(), Directory::getCWD());
  }
  
  // Test removeTree and create
  {
  
    std::string p = Path::makeAbsolute(std::string("someDir"));
    std::string d = Path::join(p, "someSubDir");
    if (Path::exists(p))
      Directory::removeTree(p);
    TEST(!Path::exists(p));
    SHOULDFAIL(Directory::create(d)); // nonrecursive create should fail
    Directory::create(d, false, true /* recursive */);
    TEST(Path::exists(d));
    Directory::removeTree(p);
    TEST(!Path::exists(d));
    TEST(!Path::exists(p));
  }


  // Test copyTree
  {
    std::string p = Path::makeAbsolute(std::string("someDir"));
    std::string a = Path::join(p, "A");
    std::string b = Path::join(p, "B");
    
    if (Path::exists(p))
      Directory::removeTree(p);
    TEST(!Path::exists(p));

    Directory::create(a, false, true /* recursive */);
    TEST(Path::exists(a));



    Directory::create(b);
    TEST(Path::exists(b));

    std::string src(Path::join(b, "1.txt"));
    if (Path::exists(src))
      Path::remove(src);
    TEST(!Path::exists(src));
    
    {
      OFStream f(src.c_str());
      f << "12345";
      f.close();
    }
    TEST(Path::exists(src));

    std::string dest = Path::join(a, "B", "1.txt");

    TEST(!Directory::exists(Path::normalize(Path::join(a, "B"))));
    Directory::copyTree(b, a);
    TEST(Directory::exists(Path::normalize(Path::join(a, "B"))));

    TEST(Path::exists(dest));

    {
      std::string s;
      IFStream f(dest.c_str());
      f >> s;
      TEST(s == "12345");
      f.close();
    }

    Directory::removeTree(p);
    TEST(!Path::exists(p));
  }
  
  // Test Iterator
  {
    if (Directory::exists("A"))
      Directory::removeTree("A");
    Directory::create("A");
    Directory::create("A" + sep + "B");
    Directory::create("A" + sep + "C");
    
    {
      Directory::Iterator di("A");
      Directory::Entry entry;
      Directory::Entry * e = NULL;

      vector<string> subdirs;
      e = di.next(entry);
      TEST(e != NULL);
      TEST(e->type == Directory::Entry::DIRECTORY);
      subdirs.push_back(e->path);
      string first = e->path;
      
      e = di.next(entry);
      TEST(e != NULL);
      TEST(e->type == Directory::Entry::DIRECTORY);
      subdirs.push_back(e->path);
      
      e = di.next(entry);
      TEST(e == NULL);
      
      // Get around different directory iteration orders on different platforms
      std::sort(subdirs.begin(), subdirs.end());
      TEST(subdirs[0] == "B");
      TEST(subdirs[1] == "C");
      
      // check that after reset first entry is returned again
      di.reset();
      e = di.next(entry);
      TEST(e != NULL);
      TEST(e->type == Directory::Entry::DIRECTORY);
      TEST(e->path == first);		
    }  	

    // Cleanup test dirs
    TEST(Path::exists("A"));
    Directory::removeTree("A");
    TEST(!Path::exists("A"));
  }
}

