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
 * Declarations for unit tester interface.
 */

#ifndef NTA_TESTER_HPP
#define NTA_TESTER_HPP

//----------------------------------------------------------------------

#include <sstream>
#include <vector>
#include <cmath> // fabs
#include <nta/utils/Log.hpp>

//----------------------------------------------------------------------

namespace nta {




  /** Abstract base class for unit testers.
   *
   * This class specifies a simple interface for unit testing all Numenta classes.
   * A unit test is created by subclassing from Tester and implementing RunTests().
   * Clients use the unit test by callling runTestsWithExceptionHandling() 
   * followed by Report()
   * 
   */
  class Tester  {
  public:

    /**
     * Initialize testinputdir, testoutputdir, testLogger
     */
    static void init(bool disableNegativeTests);

    /** Default constructor	 */
    Tester();
    
    void setName(const std::string& name) { name_ = name; }

    virtual ~Tester();
    
    /// Calls RunTests. If an exception occurs, then a critical
    /// failure will be logged and testing of this category will end.
    /// This is the main method that clients should call to run the tests.
    void runTestsWithExceptionHandling();
    
    /// This is the main method that subclasses should implement.
    /// It is expected that this method will thoroughly test the target class by calling
    /// each method and testing boundary conditions.
    /// @todo change capitalization. Must be changed in all tests. 
    virtual void RunTests() {}
    
    /// Generate a report on the results of the testing to date.
    /// Subclasses may override this method for custom reports.
    virtual void report(bool showall = false);
    
    /// Query number of tests run so far
    long testCount() { return testCount_; }
    
    /// Query number of tests failed so far
    long hardFailCount() { return hardFailCount_; }
    
    long disabledCount() { return disabledCount_; }
    
    /// Query number of tests succeeded so far
    long passCount() { return testCount_ - hardFailCount_ - disabledCount_; }
    
    /// Query name of the set of tests represented by this object
    std::string getName() { return name_; }

    /// Query whether a critical failure ocurred
    bool criticalFailureOccurred() { return criticalFailureOccurred_; }
    
    std::string getCriticalFailureMsg() {
      if (criticalFailureOccurred_) {
        return criticalFailureMsg_;
      } else {
        return std::string("No critical failure occured");
      }
    }

  protected:

    typedef struct {
      std::string name;
      
      // True if test is disabled (failure not counted)
      bool disabled;
      
      // true if test passed
      bool pass;
      
      std::string testName;
      
      std::string expectedValue;
      std::string actualValue;

    } testResult;
      
  public: 
    /*
     * All tests have access to a standard input dir (read only) and output dir
     * Make these static so that they can be accessed even if you don't have a tester object.
     */
    static std::string testInputDir_;
    static std::string testOutputDir_;
    static std::string fromTestInputDir(const std::string& path);
    static std::string fromTestOutputDir(const std::string& path);

    /// Report a test result. 
    /// The test logs a failure if the `expectedResult' is not identical to `result'
    template <class T1, class T2> 
    void testEqual(const char *testName, const char* file, int line, 
                   const T1& expectedValue, const T2& actualValue) 
    { 
      testResult* result = new testResult;
      result->disabled = false;

      std::stringstream ss;
      ss << testName << " (line: " << line << ")";
      result->name = ss.str();
      
      std::stringstream strs;
      strs << expectedValue;
      result->expectedValue = strs.str();
     
      strs.str("");
      strs << actualValue;
      result->actualValue = strs.str();
      
      if (expectedValue != actualValue) 
      {
        failHard();
        result->pass = false;
      }
      else 
      {
        result->pass = true;
      } 
      allTestResults_.push_back(result);
      testCount_++;
    }
    
    
    // Same, but test name is a string not char*
    template <class T1, class T2> 
    void testEqual(const std::string &testName, const char*file, int line, 
                   const T1& expectedValue, const T2& actualValue=true) 
    {
      testEqual(testName.c_str(), file, line, expectedValue, actualValue);
    }

    // specialization for char* values, where we want to compare strings, not pointers
    void testEqual(const char *testName, const char *file, int line, 
                   const char *expectedValue, const char *actualValue)
    {
      std::string ev(expectedValue);
      std::string av(actualValue);
      testEqual(testName, file, line, ev, av);
    }

    void disable(const std::string& testName, const char* file, int line)
    {
      testResult* result = new testResult;
      result->disabled = true;

      std::stringstream ss;
      ss << testName << " (line: " << line << ")";
      result->name = ss.str();
      
      result->pass = false;
      allTestResults_.push_back(result);
      testCount_++;
      disabledCount_++;
    }


  protected:
    static bool disableNegativeTests_;

  private:
    long testCount_;              //< Count of number of tests
    long hardFailCount_;          //< Number of tests that failed
    long disabledCount_;          //< Number of soft test failures
    bool criticalFailureOccurred_;   //< True if an exception, occurred during testing.
    std::string criticalFailureMsg_; //  exception message from critical failure
    std::string name_;              //< A description of this category of tests
    std::vector<testResult*> allTestResults_;
    
    // helper method for report()
    void logTestResult(testResult* t);
    
    // Default copy ctor and assignment operator forbidden by default
    Tester(const Tester&);
    Tester& operator=(const Tester&);

    void failHard() { ++hardFailCount_; }
    
  }; // end class Tester
  

} // end namespace nta

#define TESTEQUAL(expected, actual) testEqual(#expected " == " #actual, __FILE__, __LINE__, expected, actual)
#define TESTEQUAL_FLOAT(expected, actual) testEqual(#expected " == " #actual, __FILE__, __LINE__, true, ::fabs(expected - actual) < 0.000001)
#define TESTEQUAL2(name, expected, actual) testEqual(name, __FILE__, __LINE__, expected, actual)
#define TEST(condition) testEqual(#condition,  __FILE__, __LINE__, true, (condition))
#define TEST2(name, condition) testEqual(name ":" #condition, __FILE__, __LINE__, true, (condition))
#define SHOULDFAIL(statement) \
  { \
    if (!disableNegativeTests_) \
    { \
      bool caughtException = false; \
      try { \
        statement; \
      } catch(std::exception& ) { \
        caughtException = true; \
      } \
      testEqual("statement '" #statement "' should fail", __FILE__, __LINE__, true, caughtException); \
    } else { \
      disable("statement '" #statement "' should fail", __FILE__, __LINE__); \
    } \
  }

#define SHOULDFAIL_WITH_MESSAGE(statement, message)     \
  { \
    if (!disableNegativeTests_) \
    { \
      bool caughtException = false; \
      try { \
        statement; \
      } catch(nta::LoggingException& e) { \
        caughtException = true; \
        testEqual("statement '" #statement "' exception message", __FILE__, __LINE__, message, e.getMessage()); \
      } catch(...) { \
        testEqual("statement '" #statement "' did not generate a logging exception", __FILE__, __LINE__, true, false); \
      } \
      testEqual("statement '" #statement "' should fail", __FILE__, __LINE__, true, caughtException); \
    } else { \
      disable("statement '" #statement "' should fail", __FILE__, __LINE__); \
      disable("statement '" #statement "' exception message", __FILE__, __LINE__); \
    } \
  }
#endif // NTA_TESTER_HPP

