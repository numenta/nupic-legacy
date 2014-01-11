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
 * Implementation of Watcher test
 */

#include <string>
#include <sstream>
#include <exception>

#include <nta/engine/Network.hpp>
#include <nta/engine/NuPIC.hpp>
#include <nta/engine/Region.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/os/FStream.hpp>
#include <nta/os/Path.hpp>

#include <nta/ntypes/ArrayBase.hpp>

#include <nta/utils/Watcher.hpp>

#include "WatcherTest.hpp"

using namespace nta;


void WatcherTest::RunTests()
{
  //generate sample network
  Network n;
  n.addRegion("level1", "TestNode", "");
  n.addRegion("level2", "TestNode", "");
  n.addRegion("level3", "TestNode", "");
  Dimensions d;
  d.push_back(8);
  d.push_back(4);
  n.getRegions().getByName("level1")->setDimensions(d);
  n.link("level1", "level2", "TestFanIn2", "");
  n.link("level2", "level3", "TestFanIn2", "");
  n.initialize();

  //erase any previous contents of testfile
  OFStream o("testfile");
  o.close();
  
  //test creation
  Watcher w("testfile");

  //test uint32Params
  unsigned int id1 = w.watchParam("level1", "uint32Param");
  TESTEQUAL(id1, (unsigned int)1);
  //test uint64Params
  unsigned int id2 = w.watchParam("level1", "uint64Param");
  TESTEQUAL(id2, (unsigned int)2);
  //test int32Params
  w.watchParam("level1", "int32Param");
  //test int64Params
  w.watchParam("level1", "int64Param");
  //test real32Params
  w.watchParam("level1", "real32Param");
  //test real64Params
  w.watchParam("level1", "real64Param");
  //test stringParams
  w.watchParam("level1", "stringParam");
  //test unclonedParams
  w.watchParam("level1", "unclonedParam", 0);
  w.watchParam("level1", "unclonedParam", 1);
  
  //test attachToNetwork()
  w.attachToNetwork(n);

  //test two simultaneous Watchers on the same network with different files
  Watcher* w2 = new Watcher("testfile2");

  //test int64ArrayParam
  w2->watchParam("level1", "int64ArrayParam");
  //test real32ArrayParam
  w2->watchParam("level1", "real32ArrayParam");
  //test output
  w2->watchOutput("level1", "bottomUpOut");
  //test int64ArrayParam, sparse = false
  w2->watchParam("level1", "int64ArrayParam", -1, false);

  w2->attachToNetwork(n);

  //set one of the uncloned parameters to 1 instead of 0
  //n.getRegions().getByName("level1")->getNodeAtIndex(1).setParameterUInt32("unclonedParam", (UInt32)1);
  //n.run(3);
  //see if Watcher notices change in parameter values after 3 iterations
  n.getRegions().getByName("level1")->setParameterUInt64("uint64Param", (UInt64)66);
  n.run(3);

  //test flushFile() - this should produce output
  w.flushFile();

  //test closeFile()
  w.closeFile();

  //test to make sure data is flushed when Watcher is deleted
  delete w2;
  
  //test file output
  IFStream inStream("testfile");
  std::string tempString;
  if (inStream.is_open())
  {
    getline(inStream, tempString);
    TESTEQUAL("Info: watchID, regionName, nodeType, nodeIndex, varName", tempString);
    getline(inStream, tempString);
    TESTEQUAL("1, level1, TestNode, -1, uint32Param", tempString);
    getline(inStream, tempString);
    TESTEQUAL("2, level1, TestNode, -1, uint64Param", tempString);
    getline(inStream, tempString);
    TESTEQUAL("3, level1, TestNode, -1, int32Param", tempString);
    getline(inStream, tempString);
    TESTEQUAL("4, level1, TestNode, -1, int64Param", tempString);
    getline(inStream, tempString);
    TESTEQUAL("5, level1, TestNode, -1, real32Param", tempString);
    getline(inStream, tempString);
    TESTEQUAL("6, level1, TestNode, -1, real64Param", tempString);
    getline(inStream, tempString);
    TESTEQUAL("7, level1, TestNode, -1, stringParam", tempString);
    getline(inStream, tempString);
    TESTEQUAL("8, level1, TestNode, 0, unclonedParam", tempString);
    getline(inStream, tempString);
    TESTEQUAL("9, level1, TestNode, 1, unclonedParam", tempString);
    getline(inStream, tempString);
    TESTEQUAL("Data: watchID, iteration, paramValue", tempString);
    
    unsigned int i = 1;
    while (! inStream.eof() )
    {
      std::stringstream stream;
      std::string value;
      getline(inStream, tempString);
      if (tempString.size() == 0)
      {
        break;
      }
      switch (tempString.at(0))
      {
      case '1':
        stream << "1, " << i << ", 33";
        break;
      case '2':
        stream << "2, " << i;
        if (i < 4)
        {
          stream << ", 66";
        }
        else
        {
          stream << ", 65";
        }
        break;
      case '3':
        stream << "3, " << i << ", 32";
        break;
      case '4':
        stream << "4, " << i << ", 64";
        break;
      case '5':
        stream << "5, " << i << ", 32.1";
        break;
      case '6':
        stream << "6, " << i << ", 64.1";
        break;
      case '7':
        stream << "7, " << i << ", nodespec value";
        break;
      case '8':
        stream << "8, " << i << ", ";
        break;
      case '9':
        stream << "9, " << i << ", ";
        i++;
        break;
      }
    
      value = stream.str();
      TESTEQUAL(value, tempString);
    }
    inStream.close();
  }

  
  
  Path::remove("testfile");

  IFStream inStream2("testfile2");
  if (inStream2.is_open())
  {
    getline(inStream2, tempString);
    TESTEQUAL("Info: watchID, regionName, nodeType, nodeIndex, varName", tempString);
    getline(inStream2, tempString);
    TESTEQUAL("1, level1, TestNode, -1, int64ArrayParam", tempString);
    getline(inStream2, tempString);
    TESTEQUAL("2, level1, TestNode, -1, real32ArrayParam", tempString);
    getline(inStream2, tempString);
    TESTEQUAL("3, level1, TestNode, -1, bottomUpOut", tempString);
    getline(inStream2, tempString);
    TESTEQUAL("4, level1, TestNode, -1, int64ArrayParam", tempString);
    getline(inStream2, tempString);
    TESTEQUAL("Data: watchID, iteration, paramValue", tempString);
    
    unsigned int i = 1;
    while (! inStream2.eof() )
    {
      std::stringstream stream;
      std::string value;
      getline(inStream2, tempString);
      if (tempString.size() == 0)
      {
        break;
      }
      switch (tempString.at(0))
      {
      case '1':
        stream << "1, " << i << ", 4 1 2 3";
        break;
      case '2':
        stream << "2, " << i << ", 8 1 2 3 4 5 6 7";
        break;
      case '3':
        stream << "3, " << i << ", 64";
        if (i == 1)
        {
          for (unsigned int j = 3; j < 64; j+=2)
          {
            stream << " " << j;
          }
        }
        else
        {
          stream << " 0";
          for (unsigned int j = 2; j < 64; j++)
          {
            stream << " " << j;
          }
        }
        break;
      case '4':
        stream << "4, " << i << ", 4 0 64 128 192";
        i++;
        break;
      }
      
      value = stream.str();
      TESTEQUAL(value, tempString);
    }
  }
  inStream2.close();
        
  Path::remove("testfile2");
}
