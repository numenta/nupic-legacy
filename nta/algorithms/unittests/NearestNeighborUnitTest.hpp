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
 * Definitions for NearestNeighborUnitTest
 */

//----------------------------------------------------------------------

#include <nta/math/unittests/SparseMatrixUnitTest.hpp>

//----------------------------------------------------------------------

#ifndef NTA_NEAREST_NEIGHBOR
#define NTA_NEAREST_NEIGHBOR

namespace nta {

  //----------------------------------------------------------------------
  class NearestNeighborUnitTest : public SparseMatrixUnitTest
  {
  public:
    NearestNeighborUnitTest()
      : SparseMatrixUnitTest()
    {}

    virtual ~NearestNeighborUnitTest()
    {}
    
    // Run all appropriate tests
    virtual void RunTests();

  private:
    //void unit_test_rowLpDist();
    //void unit_test_LpDist();
    //void unit_test_LpNearest();
    //void unit_test_dotNearest();

    // Default copy ctor and assignment operator forbidden by default
    NearestNeighborUnitTest(const NearestNeighborUnitTest&);
    NearestNeighborUnitTest& operator=(const NearestNeighborUnitTest&);

  }; // end class NearestNeighborUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_NEAREST_NEIGHBOR



