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
 * Implementation of unit tests for SpatialPooler
 */     

#include <iostream>
#include <nta/algorithms/spatial_pooler.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>
#include <cstring>
#include "SpatialPoolerTest.hpp"

using namespace std;
using namespace nta::algorithms::spatial_pooler;

namespace nta {  

  bool SpatialPoolerTest::check_vector_eq(UInt arr[], vector<UInt> vec)
  {
    for (UInt i = 0; i < vec.size(); i++)
      if (arr[i] != vec[i])
        return false;
    return true;
  }

  bool SpatialPoolerTest::check_vector_eq(Real arr[], vector<Real> vec)
  {
    for (UInt i = 0; i < vec.size(); i++) {
      Real diff = arr[i] - vec[i];
      if (diff < -1e-5 || diff > 1e-5 )
        return false;
    }
    return true;
  }

  void SpatialPoolerTest::setup(SpatialPooler& sp, UInt numInputs, UInt numColumns)
  {
    vector<UInt> inputDim; 
    vector<UInt> columnDim;
    inputDim.push_back(numInputs);
    columnDim.push_back(numColumns);
    sp.initialize(inputDim,columnDim);
  }

	void SpatialPoolerTest::RunTests() 
	{
    testRaisePermanencesToThreshold();
		testMapPotential();
    testInitPermConnected();
    testInitPermUnconnected();
    testInitPermanence();
    testUpdatePermanencesForColumn();
    testUpdateInhibitionRadius();
    testUpdateMinDutyCycles();
    testUpdateMinDutyCyclesGlobal();
    testUpdateMinDutyCyclesLocal();
    testUpdateDutyCycles();
    testAvgColumnsPerInput();
    testAvgConnectedSpanForColumn1D();
    testAvgConnectedSpanForColumn2D();
    testAvgConnectedSpanForColumnND();
    testAdaptSynapses();
    testBumpUpWeakColumns();          
    testUpdateDutyCyclesHelper();
    testUpdateBoostFactors();
    testUpdateBookeepingVars();
    testCalculateOverlap();
    testCalculateOverlapPct();
    testInhibitColumns();
    testInhibitColumnsGlobal();
    testInhibitColumnsLocal();
    testGetNeighbors1D();
    testGetNeighbors2D();
    testGetNeighborsND();  
    testIsUpdateRound();
	}  

  void SpatialPoolerTest::testUpdateInhibitionRadius() {}
  void SpatialPoolerTest::testUpdateMinDutyCycles() {}
  void SpatialPoolerTest::testUpdateMinDutyCyclesGlobal() {}
  void SpatialPoolerTest::testUpdateMinDutyCyclesLocal() {}
  void SpatialPoolerTest::testUpdateDutyCycles() {}
  void SpatialPoolerTest::testAvgColumnsPerInput() {}
  void SpatialPoolerTest::testAvgConnectedSpanForColumn1D() {}
  void SpatialPoolerTest::testAvgConnectedSpanForColumn2D() {}
  void SpatialPoolerTest::testAvgConnectedSpanForColumnND() {}
  void SpatialPoolerTest::testAdaptSynapses() {}
  void SpatialPoolerTest::testBumpUpWeakColumns() {}
  void SpatialPoolerTest::testUpdateDutyCyclesHelper() {}
  void SpatialPoolerTest::testUpdateBoostFactors() {}
  void SpatialPoolerTest::testUpdateBookeepingVars() {}
  void SpatialPoolerTest::testCalculateOverlap() {}
  void SpatialPoolerTest::testCalculateOverlapPct() {}
  void SpatialPoolerTest::testInhibitColumns() {}
  void SpatialPoolerTest::testInhibitColumnsGlobal() {}
  void SpatialPoolerTest::testInhibitColumnsLocal() {}
  void SpatialPoolerTest::testGetNeighbors1D() {}
  void SpatialPoolerTest::testGetNeighbors2D() {}
  void SpatialPoolerTest::testGetNeighborsND() {}
  bool SpatialPoolerTest::testIsUpdateRound() {}

  void SpatialPoolerTest::testRaisePermanencesToThreshold()
  {
    SpatialPooler sp;
    UInt stimulusThreshold = 3;
    Real synPermConnected = 0.1;
    Real synPermBelowStimulusInc = 0.01;
    UInt numInputs = 5;
    UInt numColumns = 7;
    setup(sp,numInputs,numColumns);
    sp.setStimulusThreshold(stimulusThreshold);
    sp.setSynPermConnected(synPermConnected);
    sp.setSynPermBelowStimulusInc(synPermBelowStimulusInc);
    
    UInt potentialArr[7][5] =
      {{ 1, 1, 1, 1, 1 },
       { 1, 1, 1, 1, 1 },
       { 1, 1, 1, 1, 1 },
       { 1, 1, 1, 1, 1 },
       { 1, 1, 1, 1, 1 },
       { 1, 1, 0, 0, 1 },
       { 0, 1, 1, 1, 0 }};


    Real permArr[7][5] = 
      {{ 0.0,   0.11,   0.095, 0.092, 0.01  },
       { 0.12,  0.15,   0.02,  0.12,  0.09  },
       { 0.51,  0.081,  0.025, 0.089, 0.31  },
       { 0.18,  0.0601, 0.11,  0.011, 0.03  },
       { 0.011, 0.011,  0.011, 0.011, 0.011 },
       { 0.12,  0.056,  0,     0,     0.078 },
       { 0,     0.061,   0.07,   0.14,  0   }}; 

    Real truePerm[7][5] = 
      {{  0.01, 0.12, 0.105, 0.102, 0.02      },  // incremented once
       {  0.12, 0.15, 0.02, 0.12, 0.09      },  // no change
       {  0.53, 0.101, 0.045, 0.109, 0.33     },  // increment twice
       {  0.22, 0.1001, 0.15, 0.051, 0.07   },  // increment four times
       {  0.101, 0.101, 0.101, 0.101, 0.101 },  // increment 9 times
       {  0.17,  0.106, 0,     0,     0.128 },  // increment 5 times
       {  0,     0.101, 0.11,    0.18,  0     }}; // increment 4 times


    UInt trueConnectedCount[7] =
      {3, 3, 4, 3, 5, 3, 3};

    for (UInt i = 0; i < numColumns; i++)
    {
      vector<Real> perm;
      vector<UInt> potential;
      perm.assign(&permArr[i][0],&permArr[i][numInputs]);
      potential.assign(&potentialArr[i][0],&potentialArr[i][numInputs]);
      UInt connected = 
        sp.raisePermanencesToThreshold_(perm, potential);
      NTA_CHECK(check_vector_eq(truePerm[i],perm));
      NTA_CHECK(connected == trueConnectedCount[i]);
    }

  }

  void SpatialPoolerTest::testUpdatePermanencesForColumn()
  {
    vector<UInt> inputDim; 
    vector<UInt> columnDim;

    SpatialPooler sp;
    setup(sp,5,5);
    Real synPermTrimThreshold = 0.05;
    sp.setSynPermTrimThreshold(synPermTrimThreshold);

    Real permArr[5][5] = 
      {{ -0.10, 0.500, 0.400, 0.010, 0.020 },
       { 0.300, 0.010, 0.020, 0.120, 0.090 },
       { 0.070, 0.050, 1.030, 0.190, 0.060 },
       { 0.180, 0.090, 0.110, 0.010, 0.030 },
       { 0.200, 0.101, 0.050, -0.09, 1.100 }};

    Real truePerm[5][5] = 
       {{ 0.000, 0.500, 0.400, 0.000, 0.000},
        // Clip     -     -      Trim   Trim
        {0.300, 0.000, 0.000, 0.120, 0.090},
         // -    Trim   Trim   -     -
        {0.070, 0.050, 1.000, 0.190, 0.060},
        // -     -   Clip   -     -
        {0.180, 0.090, 0.110, 0.000, 0.000},
        // -     -    -      Trim   Trim
        {0.200, 0.101, 0.050, 0.000, 1.000}};
        // -      -     -      Clip   Clip
    
    UInt trueConnectedSynapses[5][5] = 
      {{0, 1, 1, 0, 0},
       {1, 0, 0, 1, 0},
       {0, 0, 1, 1, 0},
       {1, 0, 1, 0, 0},
       {1, 1, 0, 0, 1 }};
    
    UInt trueConnectedCount[5] = {2, 2, 2, 2, 3};

    for (UInt i = 0; i < 5; i ++) 
    {
      vector<Real> perm(&permArr[i][0], &permArr[i][5]);
      sp.updatePermanencesForColumn_(perm, i, false);
      NTA_CHECK(check_vector_eq(truePerm[i], sp.getPermanence(i)));
      NTA_CHECK(check_vector_eq(trueConnectedSynapses[i],sp.getConnected(i)));
      NTA_CHECK(trueConnectedCount[i] == sp.getConnectedCounts().at(i));
    }

  }

  void SpatialPoolerTest::testInitPermanence() 
  {
    vector<UInt> inputDim; 
    vector<UInt> columnDim;
    inputDim.push_back(8);
    columnDim.push_back(2);

    SpatialPooler sp;
    Real synPermConnected = 0.2;
    Real synPermTrimThreshold = 0.1;
    Real synPermActiveInc = 0.05;
    sp.initialize(inputDim,columnDim);
    sp.setSynPermConnected(synPermConnected);
    sp.setSynPermTrimThreshold(synPermTrimThreshold);
    sp.setSynPermActiveInc(synPermActiveInc);

    UInt arr[8] = { 0, 1, 1 , 0, 0, 1, 0, 1 };
    vector<UInt> potential(&arr[0], &arr[8]); 
    vector<Real> perm = sp.initPermanence_(potential, 1.0);
    for (UInt i = 0; i < 8; i++) 
      if (potential[i])
        NTA_CHECK(perm[i] >= synPermConnected);
      else
        NTA_CHECK(perm[i] < 1e-5);

    perm = sp.initPermanence_(potential, 0);
    for (UInt i = 0; i < 8; i++)
      if (potential[i])
        NTA_CHECK(perm[i] <= synPermConnected);
      else
        NTA_CHECK(perm[i] < 1e-5);

    inputDim[0] = 100;
    sp.initialize(inputDim,columnDim);
    sp.setSynPermConnected(synPermConnected);
    sp.setSynPermTrimThreshold(synPermTrimThreshold);
    sp.setSynPermActiveInc(synPermActiveInc);
    potential.clear();
    
    for(UInt i = 0; i < 100; i++)
      potential.push_back(1);

    perm = sp.initPermanence_(potential, 0.5);
    int count = 0;
    for (UInt i = 0; i < 100; i++)
    {
      NTA_CHECK(perm[i] < 1e-5 || perm[i] >= synPermTrimThreshold);
      if (perm[i] >= synPermConnected)
        count++;
    }
    NTA_CHECK(count > 5 && count < 95);
  }

  void SpatialPoolerTest::testInitPermConnected()
  { 
    SpatialPooler sp;
    Real synPermConnected = 0.2;
    Real synPermActiveInc = 0.05;
    sp.setSynPermConnected(synPermConnected);
    sp.setSynPermActiveInc(synPermActiveInc);
    for (UInt i = 0; i < 100; i++) {
      Real permVal = sp.initPermConnected_();
      NTA_CHECK(permVal >= synPermConnected &&
                permVal <= synPermConnected + synPermActiveInc / 4.0);
    }
  }

  void SpatialPoolerTest::testInitPermUnconnected()
  { 
    SpatialPooler sp;
    Real synPermConnected = 0.2;
    sp.setSynPermConnected(synPermConnected);
    for (UInt i = 0; i < 100; i++) {
      Real permVal = sp.initPermUnconnected_();
      NTA_CHECK(permVal >= 0 &&
                permVal <= synPermConnected);
    }
  }

	void SpatialPoolerTest::testMapPotential() 
	{
    vector<UInt> inputDim; 
    vector<UInt> columnDim;
    inputDim.push_back(10);
    columnDim.push_back(10);
    SpatialPooler sp;
    UInt potentialRadius = 1;
    Real potentialPct = 1.0;
    sp.initialize(inputDim,columnDim);
    sp.setPotentialRadius(potentialRadius);
    sp.setPotentialPct(potentialPct);

    UInt truePotential1[10][10] = 
    {{ 1, 1, 0, 0, 0, 0, 0, 0, 0, 1 },
     { 1, 1, 1, 0, 0, 0, 0, 0, 0, 0 },
     { 0, 1, 1, 1, 0, 0, 0, 0, 0, 0 },
     { 0, 0, 1, 1, 1, 0, 0, 0, 0, 0 },
     { 0, 0, 0, 1, 1, 1, 0, 0, 0, 0 },
     { 0, 0, 0, 0, 1, 1, 1, 0, 0, 0 },
     { 0, 0, 0, 0, 0, 1, 1, 1, 0, 0 },
     { 0, 0, 0, 0, 0, 0, 1, 1, 1, 0 },
     { 0, 0, 0, 0, 0, 0, 0, 1, 1, 1 },
     { 1, 0, 0, 0, 0, 0, 0, 0, 1, 1 }};

    for (UInt i = 0; i < 10; i++)
		  NTA_CHECK(check_vector_eq(truePotential1[i],
                sp.mapPotential1D_(i, true)));

    inputDim[0] = 12;
    columnDim[0] = 12;
    potentialRadius = 3;
    potentialPct = 1.0;
    sp.initialize(inputDim,columnDim);
    sp.setPotentialRadius(potentialRadius);
    sp.setPotentialPct(potentialPct);

    UInt truePotential2[12][12] = 
    {{ 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1 },
     { 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1 },
     { 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1 },
     { 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0 },
     { 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0 },
     { 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0 },
     { 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0 },
     { 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0 },
     { 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1 },
     { 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1 },
     { 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1 },
     { 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1 }};

    for (UInt i = 0; i < 12; i++)
      NTA_CHECK(check_vector_eq(truePotential2[i], 
                sp.mapPotential1D_(i, true)));

    inputDim[0] = 5;
    columnDim[0] = 15;
    potentialRadius = 1;
    potentialPct = 1.0;
    sp.initialize(inputDim,columnDim);
    sp.setPotentialRadius(potentialRadius);
    sp.setPotentialPct(potentialPct);

    UInt truePotential3[15][5] = 
    {{1, 1, 0, 0, 1},
     {1, 1, 1, 0, 0},
     {0, 1, 1, 1, 0},
     {0, 0, 1, 1, 1},
     {1, 0, 0, 1, 1},
     {1, 1, 0, 0, 1},
     {1, 1, 1, 0, 0},
     {0, 1, 1, 1, 0},
     {0, 0, 1, 1, 1},
     {1, 0, 0, 1, 1},
     {1, 1, 0, 0, 1},
     {1, 1, 1, 0, 0},
     {0, 1, 1, 1, 0},
     {0, 0, 1, 1, 1},
     {1, 0, 0, 1, 1}};

    for (UInt i = 0; i < 15; i++)
      NTA_CHECK(check_vector_eq(truePotential3[i],
                sp.mapPotential1D_(i, true)));

    inputDim[0] = 5;
    columnDim[0] = 5;
    potentialRadius = 5;
    potentialPct = 0;
    sp.initialize(inputDim,columnDim);
    sp.setPotentialRadius(potentialRadius);
    sp.setPotentialPct(potentialPct);

    UInt truePotential4[5] = {0, 0, 0, 0, 0};

    for (UInt i = 0; i < 5; i++)
      NTA_CHECK(check_vector_eq(truePotential4,
                sp.mapPotential1D_(i, true)));
  }
    
} // end namespace nta
