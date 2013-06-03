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
 * Notes
 */

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>
#include <nta/algorithms/Grouper.hpp>

//----------------------------------------------------------------------

#ifndef NTA_GROUPER_UNIT_TEST_HPP
#define NTA_GROUPER_UNIT_TEST_HPP

namespace nta {

  //----------------------------------------------------------------------
  class GrouperUnitTest : public Tester
  {
  public:
    GrouperUnitTest() {}
    virtual ~GrouperUnitTest() {}

    // Run all appropriate tests
    virtual void RunTests();

  private:
    //void doOneTestCase(const std::string& tcName, bool diagnose =false);
    //void testInference(Grouper& g, bool diagnose=false);
    //void testTBI(bool diagnose=false);
    //void testSaveReadState();

    // Default copy ctor and assignment operator forbidden by default
    GrouperUnitTest(const GrouperUnitTest&);
    GrouperUnitTest& operator=(const GrouperUnitTest&);

  }; // end class GrouperUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_GROUPER_UNIT_TEST_HPP



