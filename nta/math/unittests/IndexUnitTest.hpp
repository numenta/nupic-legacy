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
 * Declaration of class IndexUnitTest
 */

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>
#include <nta/math/Index.hpp>

//----------------------------------------------------------------------

#ifndef NTA_INDEX_UNIT_TEST_HPP
#define NTA_INDEX_UNIT_TEST_HPP

namespace nta {

  //----------------------------------------------------------------------
  class IndexUnitTest : public Tester
  {
  public:
    IndexUnitTest() {}
    virtual ~IndexUnitTest() {}

    // Run all appropriate tests
    virtual void RunTests();

  private:
    typedef Index<UInt, 1> I1;
    typedef Index<UInt, 2> I2;
    typedef Index<UInt, 3> I3;
    typedef Index<UInt, 4> I4;
    typedef Index<UInt, 5> I5;
    typedef Index<UInt, 6> I6;

    //void unitTestFixedIndex();
    //void unitTestDynamicIndex();

    // Default copy ctor and assignment operator forbidden by default
    IndexUnitTest(const IndexUnitTest&);
    IndexUnitTest& operator=(const IndexUnitTest&);

  }; // end class IndexUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_INDEX_UNIT_TEST_HPP



