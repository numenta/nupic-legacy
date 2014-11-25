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


#include <nta/engine/NuPIC.hpp>
#include <nta/engine/Network.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/engine/Input.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Link.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>
#include <nta/types/Exception.hpp>
#include <nta/os/OS.hpp> // memory leak detection
#include <nta/os/Env.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/Timer.hpp>

#include <string>
#include <vector>
#include <cmath> // fabs/abs
#include <cstdlib> // exit
#include <iostream>
#include <stdexcept>

bool ignore_negative_tests = false;
#define SHOULDFAIL(statement) \
  { \
    if (!ignore_negative_tests) \
    { \
      bool caughtException = false; \
      try { \
        statement; \
      } catch(std::exception& ) { \
        caughtException = true; \
        std::cout << "Caught exception as expected: " # statement "" << std::endl;  \
      } \
      if (!caughtException) { \
        NTA_THROW << "Operation '" #statement "' did not fail as expected"; \
      } \
    } \
  }

using namespace nupic;

bool verbose = false;

struct MemoryMonitor
{
  MemoryMonitor()
  {
    OS::getProcessMemoryUsage(initial_vmem, initial_rmem);
  }

  ~MemoryMonitor()
  {
    if (hasMemoryLeaks())
    {
      NTA_DEBUG 
        << "Memory leaks detected. " 
        << "Real Memory: " << diff_rmem
        << ", Virtual Memory: " << diff_vmem;
    }
  }

  void update()
  {
    OS::getProcessMemoryUsage(current_vmem, current_rmem);
    diff_vmem = current_vmem - initial_vmem;
    diff_rmem = current_rmem - initial_rmem;
  }

  bool hasMemoryLeaks()
  {
    update();
    return diff_vmem > 0 || diff_rmem > 0;
  }

  size_t initial_vmem;
  size_t initial_rmem;
  size_t current_vmem;
  size_t current_rmem;
  size_t diff_rmem;
  size_t diff_vmem;
};

void testExceptionBug()
{
  Network n;
  Region *l1 = n.addRegion("l1", "py.TestNode", "");
  //Dimensions d(1);
  Dimensions d(1);
  l1->setDimensions(d);
  bool caughtException = false;
  try
  {
    n.run(1);
  } catch (std::exception& e) {
    NTA_DEBUG << "Caught exception as expected: '" << e.what() << "'";
    caughtException = true;
  }
  if (caughtException)
  {
    NTA_DEBUG << "testExceptionBug passed";
  } else {
    NTA_THROW << "testExceptionBug did not throw an exception as expected";
  }
    
}


void testPynodeInputOutputAccess(Region * level2)
{
  // --- input/output access for level 2 (Python py.TestNode) ---
  SHOULDFAIL(level2->getOutputData("doesnotexist") );

  // getting access via zero-copy
  std::cout << "Getting output for zero-copy access" << std::endl;
  ArrayRef output = level2->getOutputData("bottomUpOut");
  std::cout << "Element count in bottomUpOut is " << output.getCount() << "" << std::endl;
  Real64 *data_actual = (Real64*)output.getBuffer();
  // set the actual output
  data_actual[12] = 54321;  
}

void testPynodeArrayParameters(Region * level2)
{
  // Array a is not allocated by us. Will be allocated inside getParameter
  Array a(NTA_BasicType_Int64);
  level2->getParameterArray("int64ArrayParam", a);
  std::cout << "level2.int64ArrayParam size = " << a.getCount() << std::endl;
  std::cout << "level2.int64ArrayParam = [ ";
  Int64 * buff = (Int64 *)a.getBuffer();
  for (int i = 0; i < int(a.getCount()); ++i)
    std::cout << buff[i] << " ";
  std::cout << "]" << std::endl;
  
  // --- test setParameterInt64Array ---
  std::cout << "Setting level2.int64ArrayParam to [ 1 2 3 4 ]" << std::endl;
  std::vector<Int64> v(4);
  for (int i = 0; i < 4; ++i)
    v[i] = i+1  ;
  Array newa(NTA_BasicType_Int64, &v[0], v.size());
  level2->setParameterArray("int64ArrayParam", newa);

  // get the value of intArrayParam after the setParameter call.
  a.releaseBuffer();
  a.allocateBuffer(4);
  level2->getParameterArray("int64ArrayParam", a);
  std::cout << "level2.int64ArrayParam size = " << a.getCount() << std::endl;
  std::cout << "level2.int64ArrayParam = [ ";
  buff = (Int64 *)a.getBuffer();
  for (int i = 0; i < int(a.getCount()); ++i)
    std::cout << buff[i] << " ";
  std::cout << "]" << std::endl;
}


void testPynodeLinking()
{
  Network net = Network();

  Region * region1 = net.addRegion("region1", "TestNode", "");
  Region * region2 = net.addRegion("region2", "py.TestNode", "");
  std::cout << "Linking region 1 to region 2" << std::endl;
  net.link("region1", "region2", "TestFanIn2", "");

  std::cout << "Setting region1 dims to (6,4)" << std::endl;
  Dimensions r1dims;
  r1dims.push_back(6);
  r1dims.push_back(4);
  region1->setDimensions(r1dims);

  std::cout << "Initializing network..." << std::endl;
  net.initialize();

  const Dimensions& r2dims = region2->getDimensions();
  NTA_CHECK(r2dims.size() == 2) << " actual dims: " << r2dims.toString();
  NTA_CHECK(r2dims[0] == 3) << " actual dims: " << r2dims.toString();
  NTA_CHECK(r2dims[1] == 2) << " actual dims: " << r2dims.toString();
  
  ArrayRef r1OutputArray = region1->getOutputData("bottomUpOut");

  region1->compute();

  std::cout << "Checking region1 output after first iteration..." << std::endl;
  Real64 *buffer = (Real64*) r1OutputArray.getBuffer();

  for (size_t i = 0; i < r1OutputArray.getCount(); i++)
  {
    if (verbose)
      std::cout << "  " << i << "    " << buffer[i] << "" << std::endl;
    if (i%2 == 0)
      NTA_CHECK(buffer[i] == 0);
    else
      NTA_CHECK(buffer[i] == (i-1)/2);
  }

  region2->prepareInputs();
  ArrayRef r2InputArray = region2->getInputData("bottomUpIn");
  std::cout << "Region 2 input after first iteration:" << std::endl;
  Real64 *buffer2 = (Real64*) r2InputArray.getBuffer();
  NTA_CHECK(buffer != buffer2);

  for (size_t i = 0; i < r2InputArray.getCount(); i++)
  {
    if (verbose)
      std::cout << "  " << i << "    " << buffer2[i] << "" << std::endl;

    if (i%2 == 0)
      NTA_CHECK(buffer[i] == 0);
    else
      NTA_CHECK(buffer[i] == (i-1)/2);
  }

  std::cout << "Region 2 input by node" << std::endl;
  std::vector<Real64> r2NodeInput;

  for (size_t node = 0; node < 6; node++)
  {
    region2->getInput("bottomUpIn")->getInputForNode(node, r2NodeInput);
    if (verbose)
    {
      std::cout << "Node " << node << ": ";
      for (size_t i = 0; i < r2NodeInput.size(); i++)
      {
        std::cout << r2NodeInput[i] << " ";
      }
      std::cout << "" << std::endl;
    }
    // 4 nodes in r1 fan in to 1 node in r2
    int row = node/3;
    int col = node - (row * 3);
    NTA_CHECK(r2NodeInput.size() == 8);
    NTA_CHECK(r2NodeInput[0] == 0);
    NTA_CHECK(r2NodeInput[2] == 0);
    NTA_CHECK(r2NodeInput[4] == 0);
    NTA_CHECK(r2NodeInput[6] == 0);
    // these values are specific to the fanin2 link policy
    NTA_CHECK(r2NodeInput[1] == row * 12    + col * 2) 
      << "row: " << row << " col: " << col << " val: " << r2NodeInput[1];
    NTA_CHECK(r2NodeInput[3] == row * 12    + col * 2 + 1)
      << "row: " << row << " col: " << col << " val: " << r2NodeInput[3];
    NTA_CHECK(r2NodeInput[5] == row * 12 + 6 + col * 2)
      << "row: " << row << " col: " << col << " val: " << r2NodeInput[5];
    NTA_CHECK(r2NodeInput[7] == row * 12 + 6 + col * 2 + 1)
      << "row: " << row << " col: " << col << " val: " << r2NodeInput[7];
  }

  region2->compute();
}

//static void loadSingleImage(Region & r)
//{
//  // Load an image of the 'bed' (from pictures/clean) into the image sensor
//  std::vector<std::string> args;
//  std::string imagePath = Path::makeAbsolute("bed.bmp");
//  if (!Path::exists(imagePath))
//  {
//    bool rc = Env::get("NUPIC", imagePath);
//    NTA_CHECK(rc);
//    imagePath = Path::join(imagePath, "examples/vision/data/pictures/clean/bed/bed.bmp");
//    NTA_CHECK(Path::exists(imagePath));
//  }
//
//  args.push_back("loadSingleImage");
//  args.push_back(imagePath);
//  r.executeCommand(args);
//}

//void testPynode1xLinking()
//{
//  // IM + PCA
//  {
//    Network net;
//
//    // Create a ImgeSensor region with dims 4x4
//    Region * r1 = net.addRegion("sensor", "py.ImageSensor", "{width: 4, height: 4}");
//    {
//      Dimensions d;
//      d.push_back(4);
//      d.push_back(4);
//      r1->setDimensions(d);
//    }
//
//    // Load image into the image sensor
//    loadSingleImage(*r1);
//
//    // Create a PCA region with dims 1x1
//    /*Region * r2 = */net.addRegion("pca", "py.PCANode", "{bottomUpCount: 1}");
//
//    // Link the sensor's dataOut to the PCA node's bottomUpIn
//    net.link(
//      "sensor", "pca", 
//      "UniformLink", "{mapping: in, rfSize: [4, 4]}",
//      "dataOut", "bottomUpIn");
//
//    net.initialize();
//
//    net.run(1);
//  }
//
//  // IM + KNN
//  {
//    Network net;
//
//    // Create a ImgeSensor region with dims 4x4
//    Region * r1 = net.addRegion("sensor", "py.ImageSensor", "{width: 4, height: 4}");
//    {
//      Dimensions d;
//      d.push_back(4);
//      d.push_back(4);
//      r1->setDimensions(d);
//    }
//
//    // Load image into the image sensor
//    loadSingleImage(*r1);
//
//    // ---
//    // Create a KNN classififer region with dims 1
//    // (classifier dimensionality collapse will handle dimensionality)
//    // ---
//    Region * r2 = net.addRegion("classifier", "py.KNNClassifierNode2", "{maxCategoryCount: 2, k: 3}");
//    {
//      Dimensions d;
//      d.push_back(1);
//      d.push_back(1);
//      r2->setDimensions(d);
//    }
//
//    // Link the sensor's dataOut to the classifier's bottomUpIn
//    net.link(
//      "sensor", "classifier", 
//      "UniformLink", "{mapping: in, rfSize: [4, 4]}",
//      "dataOut", "bottomUpIn");
//
//    // ---
//    // Link the sensor's categoryOut to the classifier's categoryIn
//    // (region level linking does not require any parameters)
//    // ---
//    net.link(
//      "sensor", "classifier", 
//      "UniformLink", "",
//      "categoryOut", "categoryIn");
//
//    net.initialize();
//
//    net.run(1);
//  }
//
//
//  //ArrayRef r1OutputArray(NTA_BasicType_Real64);
//  //region1->getOutputData("bottomUpOut", /* copy: */ false, r1OutputArray);
//
//  //region1->compute();
//  //std::cout << "Checking region1 output after first iteration..." << std::endl;
//  //Real64 *buffer = (Real64*) r1OutputArray.getBuffer();
//
//  //for (size_t i = 0; i < r1OutputArray.getCount(); i++)
//  //{
//  //  if (verbose)
//  //    std::cout << "  " << i << "    " << buffer[i] << "" << std::endl;
//  //  if (i%2 == 0)
//  //    NTA_CHECK(buffer[i] == 0);
//  //  else
//  //    NTA_CHECK(buffer[i] == (i-1)/2);
//  //}
//
//
//  //region2->prepareInputs();
//  //ArrayBase r2InputArray(NTA_BasicType_Real64);
//  //region2->getInputData("bottomUpIn", false, r2InputArray);
//  //std::cout << "Region 2 input after first iteration:" << std::endl;
//  //Real64 *buffer2 = (Real64*) r2InputArray.getBuffer();
//  //NTA_CHECK(buffer != buffer2);
//
//  //for (size_t i = 0; i < r2InputArray.getCount(); i++)
//  //{
//  //  if (verbose)
//  //    std::cout << "  " << i << "    " << buffer2[i] << "" << std::endl;
//
//  //  if (i%2 == 0)
//  //    NTA_CHECK(buffer[i] == 0);
//  //  else
//  //    NTA_CHECK(buffer[i] == (i-1)/2);
//  //}
//
//  //std::cout << "Region 2 input by node" << std::endl;
//  //std::vector<Real64> r2NodeInput;
//
//  //for (size_t node = 0; node < 6; node++)
//  //{
//  //  region2->getInput("bottomUpIn")->getInputForNode(node, r2NodeInput);
//  //  if (verbose)
//  //  {
//  //    std::cout << "Node " << node << ": ";
//  //    for (size_t i = 0; i < r2NodeInput.size(); i++)
//  //    {
//  //      std::cout << r2NodeInput[i] << " ";
//  //    }
//  //    std::cout << "" << std::endl;
//  //  }
//  //  // 4 nodes in r1 fan in to 1 node in r2
//  //  int row = node/2;
//  //  int col = node - (row * 2);
//  //  NTA_CHECK(r2NodeInput.size() == 8);
//  //  NTA_CHECK(r2NodeInput[0] == 0);
//  //  NTA_CHECK(r2NodeInput[2] == 0);
//  //  NTA_CHECK(r2NodeInput[4] == 0);
//  //  NTA_CHECK(r2NodeInput[6] == 0);
//  //  // these values should match the fanin2 test link policy
//  //  NTA_CHECK(r2NodeInput[1] == row * 8     + col * 2) 
//  //    << "row: " << row << " col: " << col << " val: " << r2NodeInput[1];
//  //  NTA_CHECK(r2NodeInput[3] == row * 8     + col * 2 + 1)
//  //    << "row: " << row << " col: " << col << " val: " << r2NodeInput[3];
//  //  NTA_CHECK(r2NodeInput[5] == row * 8 + 4 + col * 2)
//  //    << "row: " << row << " col: " << col << " val: " << r2NodeInput[5];
//  //  NTA_CHECK(r2NodeInput[7] == row * 8 + 4 + col * 2 + 1)
//  //    << "row: " << row << " col: " << col << " val: " << r2NodeInput[7];
//  //}
//}



void testSecondTimeLeak()
{
  Network n;
  n.addRegion("r1", "py.TestNode", "");
  n.addRegion("r2", "py.TestNode", "");
}


//void testNuPIC1x()
//{
//  // Test image sensor
//  {
//    Network n;
//    Region * r = n.addRegion("r", "py.ImageSensor", "{width: 4, height: 4}");
//    
//    Dimensions d;
//    d.push_back(4);
//    d.push_back(4);
//    r->setDimensions(d);
//
//    loadSingleImage(*r);
//
//    Int32 w = r->getParameterInt32("width");
//    NTA_CHECK(w == 4);
//
//    n.run(1);
//  }
//
//}


int realmain(bool leakTest)
{
  // verbose == true turns on extra output that is useful for
  // debugging the test (e.g. when the TestNode compute() 
  // algorithm changes)


  std::cout << "Creating network..." << std::endl;
  Network n;
  
  std::cout << "Region count is " << n.getRegions().getCount() << "" << std::endl;

  std::cout << "Adding a PyNode region..." << std::endl;
  Region* level2 = n.addRegion("level2", "py.TestNode", "{int32Param: 444}");

  std::cout << "Region count is " << n.getRegions().getCount() << "" << std::endl;
  std::cout << "Node type: " << level2->getType() << "" << std::endl;
  std::cout << "Nodespec is:\n"  << level2->getSpec()->toString() << "" << std::endl;
  
  Real64 rval;
  std::string int64Param("int64Param");
  std::string real64Param("real64Param");

  // get the value of intArrayParam after the setParameter call.

  // --- Test getParameterReal64 of a PyNode
  rval = level2->getParameterReal64("real64Param");
  NTA_CHECK(rval == 64.1); 
  std::cout << "level2 getParameterReal64() returned: " << rval << std::endl;

  // --- Test setParameterReal64 of a PyNode
  level2->setParameterReal64("real64Param", 77.7);
  rval = level2->getParameterReal64("real64Param");
  NTA_CHECK(rval == 77.7); 

  // should fail because network has not been initialized
  SHOULDFAIL(n.run(1));

  // should fail because network can't be initialized
  SHOULDFAIL (n.initialize() );

  std::cout << "Setting dimensions of level1..." << std::endl;
  Dimensions d;
  d.push_back(4);
  d.push_back(4);


  std::cout << "Setting dimensions of level2..." << std::endl;
  level2->setDimensions(d);

  std::cout << "Initializing again..." << std::endl;
  n.initialize();

  testExceptionBug();
  testPynodeInputOutputAccess(level2);
  testPynodeArrayParameters(level2);
  testPynodeLinking();
  if (!leakTest)
  {
    //testNuPIC1x();
    //testPynode1xLinking();
  }

  std::cout << "Done -- all tests passed" << std::endl;

  return 0;
}

int main(int argc, char *argv[])
{
  
  /* 
   * Without arguments, this program is a simple end-to-end demo
   * of NuPIC 2 functionality, used as a developer tool (when 
   * we add a feature, we add it to this program. 
   * With an integer argument N, runs the same test N times
   * and requires that memory use stay constant -- it can't
   * grow by even one byte. 
   */

  // TODO: real argument parsing
  // Optional arg is number of iterations to do. 
  NTA_CHECK(argc == 1 || argc == 2);
  size_t count = 1;
  if (argc == 2)
  {
    std::stringstream ss(argv[1]);
    ss >> count;
  }
  // Start checking memory usage after this many iterations. 
#ifdef NTA_PLATFORM_win32
  // takes longer to settle down on win32
  size_t memoryLeakStartIter = 6000;
#else
  size_t memoryLeakStartIter = 150;
#endif

  // This determines how frequently we check. 
  size_t memoryLeakDeltaIterCheck = 10;

  size_t minCount = memoryLeakStartIter + 5 * memoryLeakDeltaIterCheck;

  if (count > 1 && count < minCount)
  {
    std::cout << "Run count of " << count << " specified\n";
    std::cout << "When run in leak detection mode, count must be at least " << minCount << "\n";
    ::exit(1);
  }
   

  size_t initial_vmem = 0;
  size_t initial_rmem = 0;
  size_t current_vmem = 0;
  size_t current_rmem = 0;
  try {
    for (size_t i = 0; i < count; i++)
    {
      //MemoryMonitor m;
      NuPIC::init();
      realmain(count > 1);
      //testExceptionBug();
      //testPynode1xLinking();
      // testNuPIC1x();
      //testSecondTimeLeak();
      //testPynodeLinking();
      //testCppLinking("TestFanIn2","");
      NuPIC::shutdown();
      // memory leak detection
      // we check even prior to the initial tracking iteration, because the act
      // of checking potentially modifies our memory usage
      if (i % memoryLeakDeltaIterCheck == 0)
      {
        OS::getProcessMemoryUsage(current_rmem, current_vmem);
        if(i == memoryLeakStartIter)
        {
          initial_rmem = current_rmem;
          initial_vmem = current_vmem;
        }
        std::cout << "Memory usage: " << current_vmem << " (virtual) " 
                  << current_rmem << " (real) at iteration " << i << std::endl;

        if(i >= memoryLeakStartIter)
        {
          if (current_vmem > initial_vmem || current_rmem > initial_rmem)
          {
            std::cout << "Tracked memory usage (iteration "
                      << memoryLeakStartIter << "): " << initial_vmem
                      << " (virtual) " << initial_rmem << " (real)" << std::endl;
            throw std::runtime_error("Memory leak detected");
          }
        }
      }
    }

  } catch (nupic::Exception& e) {
    std::cout 
      << "Exception: " << e.getMessage() 
      << " at: " << e.getFilename() << ":" << e.getLineNumber()
      << std::endl;
    return 1;

  } catch (std::exception& e) {
    std::cout << "Exception: " << e.what() << "" << std::endl;
    return 1;
  }
  catch (...) {
    std::cout << "\nhtmtest is exiting because an exception was thrown" << std::endl;
    return 1;
  }
  if (count > 20)
    std::cout << "Memory leak check passed -- " << count << " iterations" << std::endl;

  std::cout << "--- ALL TESTS PASSED ---" << std::endl;
  return 0;
}
