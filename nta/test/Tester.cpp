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
    Implementation of Tester
*/

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <nta/test/Tester.hpp>
#include <nta/utils/Log.hpp>

#include <nta/os/Directory.hpp>
#include <nta/os/Path.hpp>

using namespace std;
namespace nta {
	
  bool Tester::disableNegativeTests_ = false;

  /* static members */
  std::string Tester::testInputDir_;
  std::string Tester::testOutputDir_;

  Tester::Tester():
    testCount_(0),
    hardFailCount_(0),
    disabledCount_(0),
    criticalFailureOccurred_(false),
    name_("Name has not been set yet")
  {
    
  }

  Tester::~Tester()
  {
    // free up all of the testResult structures that have been allocated
    for (unsigned int i = 0; i < allTestResults_.size(); i++) {
      delete allTestResults_[i];
    }
  }

  void Tester::init(bool disableNegativeTests) {
    /* the following functions implicitly set these options if not
     * already set. 
     */
    // TODO -- fix me! needed for finding test data
    testInputDir_ = "/does/not/exist";
    testOutputDir_ = Path::makeAbsolute("testeverything.out");

    // Create if it doesn't exist
    if (!Path::exists(testOutputDir_)) {
      std::cout << "Tester -- creating testoutput directory " << std::string(testOutputDir_) << "\n";
      // will throw if unsuccessful. 
      Directory::create(string(testOutputDir_));
    } 
    disableNegativeTests_ = disableNegativeTests;
  }
  
  void Tester::runTestsWithExceptionHandling()
  {
    try 
    {
      RunTests();
    }
    catch (std::exception& e)
    {
      std::cout << "WARNING: Caught exception: " << e.what() << "\n";
      failHard();
      criticalFailureOccurred_ = true;
      criticalFailureMsg_ = e.what();
    }
    catch (...)
    {
      std::cout << "WARNING: Caught unknown exception" << "\n";
      failHard();
      criticalFailureOccurred_ = true;
      criticalFailureMsg_ = "Unknown exception";
    }
  }

  void Tester::logTestResult(testResult* r) {
    if (r->disabled)
    {
      std::cout << "DISABLED  ";
    } else {
      std::cout << (r->pass == true ? "PASS  " : "FAIL  ");
    }
    std::cout << r->name;
    
    if (!r->disabled) {
      std::cout << "\n      Expected result: " << r->expectedValue << "\n";
      std::cout << "      Actual result:   " << r->actualValue;
    }
    std::cout << "\n";

  }
  

  void Tester::report(bool showall)
  {	
    std::cout << "======= Tests for " << name_ << " ==============\n";
    std::cout << "Total tests: " << testCount() << 
      ", Failures:      " << hardFailCount() <<
      ", Disabled     : " << disabledCount() << "\n";
  
    if (criticalFailureOccurred())
    {
      std::cout << "WARNING: Critical failure ocurred\n";
      showall = true;
    }
  
    for(unsigned int i= 0; i < allTestResults_.size(); i++)
    {
      testResult* r = allTestResults_[i];
      if (showall == true || r->pass == false || r->disabled == true) {
        logTestResult(r);
      }
    }
    if (!criticalFailureOccurred() && testCount() == passCount() && disabledCount() == 0) {
      std::cout << "All tests passed\n";
    }
    std::cout << "======= Done with " << name_ << " tests ===========\n\n";
  }


  std::string Tester::fromTestInputDir(const std::string& path) {
    
    Path testinputpath(testInputDir_);
    if (path != "")
      testinputpath += path;
    
    return string(testinputpath);
  }

  std::string Tester::fromTestOutputDir(const std::string& path) {
    
    Path testoutputpath(testOutputDir_);
    if (path != "")
      testoutputpath += path;
    
    return std::string(testoutputpath);
  }

} // end namespace nta

