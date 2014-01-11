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
 * Notes
 */

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>

//----------------------------------------------------------------------

#ifndef NTA_COND_PROB_TABLE_TEST_HPP
#define NTA_COND_PROB_TABLE_TEST_HPP

namespace nta {
  class CondProbTable;

  //----------------------------------------------------------------------
  class CondProbTableTest : public Tester
  {
  public:
    CondProbTableTest();
    virtual ~CondProbTableTest();

    // Run all appropriate tests
    virtual void RunTests();

  private:
    // Compare 2 vectors using printed output, this works even for round-off errors
    void testVectors(const std::string& testName, const std::vector<Real>& v1,
                const std::vector<Real>& v2);
                
    // Run tests on the given table
    void testTable (const std::string& testName, CondProbTable& table, 
      const std::vector<std::vector<Real> > & rows);
    
    // Size of the table we construct
    Size numRows() {return 4;}
    Size numCols() {return 3;}
  
    // Default copy ctor and assignment operator forbidden by default
    CondProbTableTest(const CondProbTableTest&);
    CondProbTableTest& operator=(const CondProbTableTest&);

  }; // end class OnlineKMeansCDTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_COND_PROB_TABLE_TEST_HPP



