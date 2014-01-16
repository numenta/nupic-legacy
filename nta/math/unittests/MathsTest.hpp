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
 * Declarations for maths unit tests
 */

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>
//#include <nta/foundation/TRandom.hpp>

//----------------------------------------------------------------------

#ifndef NTA_MATHS_TEST_HPP
#define NTA_MATHS_TEST_HPP

namespace nta {

  //----------------------------------------------------------------------
  class MathsTest : public Tester
  {
  public:
    MathsTest() {
      //rng_ = new TRandom("maths_test");
    }
    virtual ~MathsTest() {
      //delete rng_;
    }

    // Run all appropriate tests
    virtual void RunTests();

  private:
    //void unitTestNearlyZero();
    //void unitTestNearlyEqual();
    //void unitTestNearlyEqualVector();
    //void unitTestNormalize();
    //void unitTestVectorToStream();
    //void unitTestElemOps();
    //void unitTestWinnerTakesAll();
    //void unitTestScale();
    //void unitTestQSI();
    //
    //// Use our own random number generator for reproducibility
    //TRandom *rng_;
		
    // Default copy ctor and assignment operator forbidden by default
    MathsTest(const MathsTest&);
    MathsTest& operator=(const MathsTest&);

  }; // end class MathsTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_MATHS_TEST_HPP



