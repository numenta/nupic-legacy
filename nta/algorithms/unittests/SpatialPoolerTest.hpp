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
 * Definitions for SpatialPoolerTest
 */

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>
#include <nta/algorithms/spatial_pooler.hpp>
//#include <nta/foundation/TRandom.hpp>

//----------------------------------------------------------------------

#ifndef NTA_SPATIAL_POOLER_TEST
#define NTA_SPATIAL_POOLER_TEST


using namespace nta::algorithms::spatial_pooler;

namespace nta {

  //----------------------------------------------------------------------
  class SpatialPoolerTest : public Tester
  {
  public:
    SpatialPoolerTest() {}
    virtual ~SpatialPoolerTest() {}

    // Run all appropriate tests
    virtual void RunTests();

  private:
    void setup(SpatialPooler& sp, UInt numInputs, UInt numColumns);
    bool check_vector_eq(UInt arr[], vector<UInt> vec);
    bool check_vector_eq(Real arr[], vector<Real> vec);
    bool check_vector_eq(UInt arr1[], UInt arr2[], UInt n);
    bool check_vector_eq(Real arr1[], Real arr2[], UInt n);
    bool check_vector_eq(vector<UInt> vec1, vector<UInt> vec2);
    bool almost_eq(Real a, Real b);
    bool findVector(UInt needle[], UInt n, 
                                     vector<vector<UInt> > haystack);
    void testMapPotential();
    void testInitPermConnected();
    void testInitPermUnconnected();
    void testInitPermanence();
    void testUpdatePermanencesForColumn();
    void testRaisePermanencesToThreshold();
    void testUpdateInhibitionRadius();
    void testUpdateMinDutyCycles();
    void testUpdateMinDutyCyclesGlobal();
    void testUpdateMinDutyCyclesLocal();
    void testUpdateDutyCycles();
    void testAvgColumnsPerInput();
    void testAvgConnectedSpanForColumn1D();
    void testAvgConnectedSpanForColumn2D();
    void testAvgConnectedSpanForColumnND();
    void testAdaptSynapses();
    void testBumpUpWeakColumns();          
    void testUpdateDutyCyclesHelper();
    void testUpdateBoostFactors();
    void testUpdateBookeepingVars();
    void testCalculateOverlap();
    void testCalculateOverlapPct();
    void testIsWinner();
    void testAddToWinners();
    void testInhibitColumns();
    void testInhibitColumnsGlobal();
    void testInhibitColumnsLocal();
    void testGetNeighbors1D();
    void testGetNeighbors2D();
    void testCartesianProduct();
    void testGetNeighborsND();  
    void testIsUpdateRound();

    void print_vec(UInt arr[], UInt n);
    void print_vec(Real arr[], UInt n);
    void print_vec(vector<UInt> vec);
    void print_vec(vector<Real> vec);

  }; // end class SpatialPoolerTest
    
  //----------------------------------------------------------------------
} // end namespace nta


#endif // NTA_SPATIAL_POOLER_TEST