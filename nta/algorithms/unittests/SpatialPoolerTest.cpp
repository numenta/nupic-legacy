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

  void SpatialPoolerTest::print_vec(UInt arr[], UInt n)
  {
    for (UInt i = 0; i < n; i++)
      cout << arr[i] << " ";
    cout << endl;
  }

  void SpatialPoolerTest::print_vec(Real arr[], UInt n)
  {
    for (UInt i = 0; i < n; i++)
      cout << arr[i] << " ";
    cout << endl;
  }

  void SpatialPoolerTest::print_vec(vector<UInt> vec)
  {
    for (UInt i = 0; i < vec.size(); i++)
      cout << vec[i] << " ";
    cout << endl;
  }

  void SpatialPoolerTest::print_vec(vector<Real> vec)
  {
    for (UInt i = 0; i < vec.size(); i++)
      cout << vec[i] << " ";
    cout << endl;
  }

  bool SpatialPoolerTest::almost_eq(Real a, Real b)
  {
    Real diff = a - b;
    return (diff > -1e-5 && diff < 1e-5); 
  }

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
      if (!almost_eq(arr[i],vec[i]))
        return false;
    }
    return true;
  }

  bool SpatialPoolerTest::check_vector_eq(vector<UInt> vec1, vector<UInt> vec2)
  {
    if (vec1.size() != vec2.size()) {
      return false;
    }
    for (UInt i = 0; i < vec1.size(); i++) {
      if (vec1[i] != vec2[i]) {
        return false;
      }
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
    testIsWinner();
    testAddToWinners();
    testInhibitColumnsGlobal();
    testInhibitColumnsLocal();
    testGetNeighbors1D();
    testGetNeighbors2D();
    testCartesianProduct();
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
  void SpatialPoolerTest::testCalculateOverlap() 
  {
    SpatialPooler sp;
    UInt numInputs = 10;
    UInt numColumns = 5;
    UInt numTrials = 5;
    setup(sp,numInputs,numColumns);
    sp.setStimulusThreshold(0);

    Real permArr[5][10] = 
      {{1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
       {0, 0, 1, 1, 1, 1, 1, 1, 1, 1},
       {0, 0, 0, 0, 1, 1, 1, 1, 1, 1},
       {0, 0, 0, 0, 0, 0, 1, 1, 1, 1},
       {0, 0, 0, 0, 0, 0, 0, 0, 1, 1}};


    UInt inputs[5][10] = 
      {{0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
       {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
       {0, 1, 0, 1, 0, 1, 0, 1, 0, 1},
       {1, 1, 1, 1, 1, 0, 0, 0, 0, 0},
       {0, 0, 0, 0, 0, 0, 0, 0, 0, 1}};

    UInt trueOverlaps[5][5] = 
      {{ 0,  0,  0,  0,  0},
       {10,  8,  6,  4,  2},
       { 5,  4,  3,  2,  1},
       { 5,  3,  1,  0,  0},
       { 1,  1,  1,  1,  1}};

    for (UInt i = 0; i < numColumns; i++)
    {
      vector<Real> perm;
      perm.assign(&permArr[i][0],&permArr[i][numInputs]);
      sp.setPermanence(i,perm);
    }

    for (UInt i = 0; i < numTrials; i++)
    {
      vector<UInt> inputVector;
      vector<UInt> overlaps;
      inputVector.assign(&inputs[i][0],&inputs[i][numInputs]);
      sp.calculateOverlap_(inputVector,overlaps);
      // cout << "input:  " << endl; print_vec(inputVector);
      // cout << "return: " << endl; print_vec(overlaps);
      // cout << "true:   " << endl; print_vec(trueOverlaps[i],numColumns);
      NTA_CHECK(check_vector_eq(trueOverlaps[i],overlaps));
    }


  }

  void SpatialPoolerTest::testCalculateOverlapPct() 
  {
    SpatialPooler sp;
    UInt numInputs = 10;
    UInt numColumns = 5;
    UInt numTrials = 5;
    setup(sp,numInputs,numColumns);
    sp.setStimulusThreshold(0);

    Real permArr[5][10] = 
      {{1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
       {0, 0, 1, 1, 1, 1, 1, 1, 1, 1},
       {0, 0, 0, 0, 1, 1, 1, 1, 1, 1},
       {0, 0, 0, 0, 0, 0, 1, 1, 1, 1},
       {0, 0, 0, 0, 0, 0, 0, 0, 1, 1}};


    UInt overlapsArr[5][10] =
     {{ 0,  0,  0,  0,  0},
       {10,  8,  6,  4,  2},
       { 5,  4,  3,  2,  1},
       { 5,  3,  1,  0,  0},
       { 1,  1,  1,  1,  1}}; 

    Real trueOverlapsPct[5][5] = 
      {{0.0, 0.0, 0.0, 0.0, 0.0},
       {1.0, 1.0, 1.0, 1.0, 1.0},
       {0.5, 0.5, 0.5, 0.5, 0.5},
       {0.5, 3.0/8, 1.0/6,  0,  0},
       { 1.0/10,  1.0/8,  1.0/6,  1.0/4,  1.0/2}};

    for (UInt i = 0; i < numColumns; i++)
    {
      vector<Real> perm;
      perm.assign(&permArr[i][0],&permArr[i][numInputs]);
      sp.setPermanence(i,perm);
    }

    for (UInt i = 0; i < numTrials; i++)
    {
      vector<Real> overlapsPct;
      vector<UInt> overlaps;
      overlaps.assign(&overlapsArr[i][0],&overlapsArr[i][numColumns]);
      sp.calculateOverlapPct_(overlaps,overlapsPct);
      // cout << "overlaps:  " << endl; print_vec(overlaps);
      // cout << "overlapsPct: " << endl; print_vec(overlapsPct);
      // cout << "trueOverlapsPct:   " << endl; print_vec(trueOverlapsPct[i],numColumns);
      NTA_CHECK(check_vector_eq(trueOverlapsPct[i],overlapsPct));
    }


  }
  void SpatialPoolerTest::testIsWinner() 
  {
    SpatialPooler sp;
    vector<scoreCard> winners;

    UInt numWinners = 3;
    Real score = -5;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    score = 0;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));

    scoreCard sc1; sc1.index = 1;  sc1.score = 32;
    scoreCard sc2; sc2.index = 2;  sc2.score = 27;
    scoreCard sc3; sc3.index = 17; sc3.score = 19.5;
    winners.push_back(sc1);
    winners.push_back(sc2);
    winners.push_back(sc3);

    numWinners = 3;
    score = -5;
    NTA_CHECK(!sp.is_winner_(score,winners,numWinners));
    score = 18;
    NTA_CHECK(!sp.is_winner_(score,winners,numWinners));
    score = 18;
    numWinners = 4;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    numWinners = 3;
    score = 20;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    score = 30;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    score = 40;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    score = 40;
    numWinners = 6;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));

    scoreCard sc4; sc4.index = 34; sc4.score = 17.1;
    scoreCard sc5; sc5.index = 51; sc5.score = 1.2;
    scoreCard sc6; sc6.index = 19; sc6.score = 0.3;
    winners.push_back(sc4);
    winners.push_back(sc5);
    winners.push_back(sc6);

    score = 40;
    numWinners = 6;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    score = 12;
    numWinners = 6;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
    score = 0.1;
    numWinners = 6;
    NTA_CHECK(!sp.is_winner_(score,winners,numWinners));
    score = 0.1;
    numWinners = 7;
    NTA_CHECK(sp.is_winner_(score,winners,numWinners));
  }

  void SpatialPoolerTest::testAddToWinners() 
  {
    SpatialPooler sp;
    vector<scoreCard> winners;
    
    UInt index;
    Real score;

    index = 17; score = 19.5;
    sp.add_to_winners_(index,score,winners);
    index = 1; score = 32;
    sp.add_to_winners_(index,score,winners);
    index = 2; score = 27;
    sp.add_to_winners_(index,score,winners);

    NTA_CHECK(winners[0].index == 1);
    NTA_CHECK(almost_eq(winners[0].score,32));
    NTA_CHECK(winners[1].index == 2);
    NTA_CHECK(almost_eq(winners[1].score,27));
    NTA_CHECK(winners[2].index == 17);
    NTA_CHECK(almost_eq(winners[2].score,19.5));

    index = 15; score = 20.5;
    sp.add_to_winners_(index,score,winners);
    NTA_CHECK(winners[0].index == 1);
    NTA_CHECK(almost_eq(winners[0].score,32));
    NTA_CHECK(winners[1].index == 2);
    NTA_CHECK(almost_eq(winners[1].score,27));
    NTA_CHECK(winners[2].index == 15);
    NTA_CHECK(almost_eq(winners[2].score,20.5));
    NTA_CHECK(winners[3].index == 17);
    NTA_CHECK(almost_eq(winners[3].score,19.5));

    index = 7; score = 100;
    sp.add_to_winners_(index,score,winners);
    NTA_CHECK(winners[0].index == 7);
    NTA_CHECK(almost_eq(winners[0].score,100));
    NTA_CHECK(winners[1].index == 1);
    NTA_CHECK(almost_eq(winners[1].score,32));
    NTA_CHECK(winners[2].index == 2);
    NTA_CHECK(almost_eq(winners[2].score,27));
    NTA_CHECK(winners[3].index == 15);
    NTA_CHECK(almost_eq(winners[3].score,20.5));
    NTA_CHECK(winners[4].index == 17);
    NTA_CHECK(almost_eq(winners[4].score,19.5));

    index = 22; score = 1;
    sp.add_to_winners_(index,score,winners);
    NTA_CHECK(winners[0].index == 7);
    NTA_CHECK(almost_eq(winners[0].score,100));
    NTA_CHECK(winners[1].index == 1);
    NTA_CHECK(almost_eq(winners[1].score,32));
    NTA_CHECK(winners[2].index == 2);
    NTA_CHECK(almost_eq(winners[2].score,27));
    NTA_CHECK(winners[3].index == 15);
    NTA_CHECK(almost_eq(winners[3].score,20.5));
    NTA_CHECK(winners[4].index == 17);
    NTA_CHECK(almost_eq(winners[4].score,19.5));
    NTA_CHECK(winners[5].index == 22);
    NTA_CHECK(almost_eq(winners[5].score,1));

  }

  void SpatialPoolerTest::testInhibitColumns() 
  {
    SpatialPooler sp;
    setup(sp, 10,10);

    vector<Real> overlapsReal;
    vector<UInt> overlaps;
    vector<UInt> activeColumns;
    vector<UInt> activeColumnsGlobal;
    vector<UInt> activeColumnsLocal;
    Real density;
    UInt inhibitionRadius;
    UInt numColumns;
    UInt numColumnsPerInhArea;

    density = 0.3;
    inhibitionRadius = 5;
    numColumns = 10;
    Real overlapsArray[10] = {10,21,34,4,18,3,12,5,7,1};
    
    overlapsReal.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumnsGlobal_(overlapsReal, density,activeColumnsGlobal);
    overlapsReal.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumnsLocal_(overlapsReal, density, activeColumnsLocal);
    
    sp.setInhibitionRadius(5);
    sp.setGlobalInhibition(true);
    sp.setLocalAreaDensity(density);

    overlaps.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumns_(overlaps, activeColumns);

    NTA_CHECK(check_vector_eq(activeColumns, activeColumnsGlobal));
    NTA_CHECK(!check_vector_eq(activeColumns, activeColumnsLocal));

    sp.setGlobalInhibition(false);
    sp.setInhibitionRadius(numColumns + 1);

    overlaps.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumns_(overlaps, activeColumns);

    NTA_CHECK(check_vector_eq(activeColumns, activeColumnsGlobal));
    NTA_CHECK(!check_vector_eq(activeColumns, activeColumnsLocal));

    inhibitionRadius = 2;
    numColumnsPerInhArea = 2;
    density = 2.0 / 5;

    sp.setInhibitionRadius(inhibitionRadius);
    sp.setNumActiveColumnsPerInhArea(2);
    sp.setLocalAreaDensity(-1);
    sp.setGlobalInhibition(false);

    overlapsReal.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumnsGlobal_(overlapsReal, density,activeColumnsGlobal);
    overlapsReal.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumnsLocal_(overlapsReal, density, activeColumnsLocal);

    overlaps.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumns_(overlaps, activeColumns);

    NTA_CHECK(!check_vector_eq(activeColumns, activeColumnsGlobal));
    NTA_CHECK(check_vector_eq(activeColumns, activeColumnsLocal));
  }

  void SpatialPoolerTest::testInhibitColumnsGlobal() 
  {
    SpatialPooler sp;
    UInt numInputs = 10;
    UInt numColumns = 10;
    setup(sp,numInputs,numColumns);
    vector<Real> overlaps;
    vector<UInt> activeColumns;
    vector<UInt> trueActive;
    vector<UInt> active;
    Real density;

    density = 0.3;
    Real overlapsArray[10] = {1,2,1,4,8,3,12,5,4,1};
    overlaps.assign(&overlapsArray[0],&overlapsArray[numColumns]);
    sp.inhibitColumnsGlobal_(overlaps,density,activeColumns);
    UInt trueActiveArray1[3] = {4,6,7}; 

    trueActive.assign(numColumns, 0);
    active.assign(numColumns, 0);

    for (UInt i = 0; i < 3; i++) {
      trueActive[trueActiveArray1[i]] = 1;
    }

    for (UInt i = 0; i < activeColumns.size(); i++) {
      active[activeColumns[i]] = 1;
    }

    NTA_CHECK(check_vector_eq(trueActive,active));


    density = 0.5;
    UInt overlapsArray2[10] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    overlaps.assign(&overlapsArray2[0],&overlapsArray2[numColumns]);
    sp.inhibitColumnsGlobal_(overlaps, density, activeColumns);
    UInt trueActiveArray2[5] = {5,6,7,8,9};

    for (UInt i = 0; i < 5; i++) {
      trueActive[trueActiveArray2[i]] = 1;
    }

    for (UInt i = 0; i < activeColumns.size(); i++) {
      active[activeColumns[i]] = 1;
    }

    NTA_CHECK(check_vector_eq(trueActive,active));
  }

  void SpatialPoolerTest::testInhibitColumnsLocal() 
  {
    SpatialPooler sp;
    setup(sp,10,10);
    Real density;
    UInt inhibitionRadius;

    vector<Real> overlaps;
    vector<UInt> active;

    Real overlapsArray1[10] = { 1, 2, 7, 0, 3, 4, 16, 1, 1.5, 1.7};
                            //  L  W  W  L  L  W  W   L   L    W

    inhibitionRadius = 2;
    density = 0.5;
    overlaps.assign(&overlapsArray1[0], &overlapsArray1[10]);
    UInt trueActive[5] = {1, 2, 5, 6, 9};
    sp.setInhibitionRadius(inhibitionRadius);
    sp.inhibitColumnsLocal_(overlaps, density, active);
    NTA_CHECK(active.size() == 5);
    NTA_CHECK(check_vector_eq(trueActive, active));

    Real overlapsArray2[10] = {1, 2, 7, 0, 3, 4, 16, 1, 1.5, 1.7};
                          //   L  W  W  L  L  W   W  L   L    W
    overlaps.assign(&overlapsArray2[0], &overlapsArray2[10]);
    UInt trueActive2[6] = {1, 2, 4, 5, 6, 9};
    inhibitionRadius = 3;
    density = 0.5;
    sp.setInhibitionRadius(inhibitionRadius);
    sp.inhibitColumnsLocal_(overlaps, density, active);
    NTA_CHECK(active.size() == 6);
    NTA_CHECK(check_vector_eq(trueActive2, active));

    // Test arbitration

    Real overlapsArray3[10] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
                            // W  L  W  L  W  L  W  L  L  L  
    overlaps.assign(&overlapsArray3[0], &overlapsArray3[10]);
    UInt trueActive3[4] = {0, 2, 4, 6};
    inhibitionRadius = 3;
    density = 0.25;
    sp.setInhibitionRadius(inhibitionRadius);
    sp.inhibitColumnsLocal_(overlaps, density, active);

    NTA_CHECK(active.size() == 4);
    NTA_CHECK(check_vector_eq(trueActive3, active));

  }

  void SpatialPoolerTest::testGetNeighbors1D() 
  {

    SpatialPooler sp;
    UInt numInputs = 5;
    UInt numColumns = 8;
    setup(sp,numInputs,numColumns);

    UInt column;
    UInt radius;
    vector<UInt> dimensions;
    vector<UInt> neighbors;
    bool wrapAround;
    vector<UInt> neighborsMap(numColumns, 0);

    column = 3;
    radius = 1;
    wrapAround = true;
    dimensions.push_back(8);
    UInt trueNeighborsMap1[8] = {0, 0, 1, 0, 1, 0, 0, 0};
    sp.getNeighbors1D_(column, dimensions, radius, wrapAround,
                          neighbors);
    neighborsMap.clear();
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap1, neighborsMap));

    column = 3;
    radius = 2;
    wrapAround = false;
    UInt trueNeighborsMap2[8] = {0, 1, 1, 0, 1, 1, 0, 0};
    sp.getNeighbors1D_(column, dimensions, radius, wrapAround,
                          neighbors);
    neighborsMap.clear();
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap2, neighborsMap));

    column = 0;
    radius = 2;
    wrapAround = true;
    UInt trueNeighborsMap3[8] = {0, 1, 1, 0, 0, 0, 1, 1};
    sp.getNeighbors1D_(column, dimensions, radius, wrapAround,
                          neighbors);
    neighborsMap.clear();
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap3, neighborsMap));
  }

  void SpatialPoolerTest::testGetNeighbors2D() 
  {
    UInt numColumns = 30;
    vector<UInt> dimensions;
    dimensions.push_back(6);
    dimensions.push_back(5);
    SpatialPooler sp;
    vector<UInt> neighbors;
    UInt column;
    UInt radius;
    bool wrapAround;
    vector<UInt> neighborsMap;

    UInt trueNeighborsMap1[30] =
      {0, 0, 0, 0, 0,
       0, 0, 0, 0, 0,
       0, 1, 1, 1, 0,
       0, 1, 0, 1, 0,
       0, 1, 1, 1, 0,
       0, 0, 0, 0, 0};

    column = 3*5+2;
    radius = 1;
    wrapAround = false;
    sp.getNeighbors2D_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap1, neighborsMap));

    UInt trueNeighborsMap2[30] =
      {0, 0, 0, 0, 0,
       1, 1, 1, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 0, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 1, 1, 1};

    column = 3*5+2;
    radius = 2;
    wrapAround = false;
    sp.getNeighbors2D_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap2, neighborsMap));

    UInt trueNeighborsMap3[30] =
      {1, 1, 1, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 0, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 1, 1, 1};

    column = 3*5+2;
    radius = 3;
    wrapAround = false;
    sp.getNeighbors2D_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap3, neighborsMap));

    UInt trueNeighborsMap4[30] =
      {1, 0, 0, 1, 1,
       0, 0, 0, 0, 0,
       0, 0, 0, 0, 0,
       0, 0, 0, 0, 0,
       1, 0, 0, 1, 1,
       1, 0, 0, 1, 0};

    column = 29;
    radius = 1;
    wrapAround = true;
    sp.getNeighbors2D_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap4, neighborsMap));


  }

  bool SpatialPoolerTest::findVector(UInt needle[], UInt n, 
                                     vector<vector<UInt> > haystack)
  {
    for (UInt i = 0; i < haystack.size(); i++) {
      vector<UInt> hay = haystack[i];
      if (hay.size() != n) {
        continue;
      }

      bool match = true;
      for (UInt j = 0; j < hay.size(); j++) {
        if (hay[j] != needle[j]) {
          match = false;
          break;
        }
      }

      if (match) {
        return true;
      }
    }
    return false;
  }

  void SpatialPoolerTest::testCartesianProduct()
  {

    vector<vector<UInt> > vecs;
    vector<vector<UInt> > prod;
    UInt needle[3];
    vector<UInt> v1, v2, v3;
    SpatialPooler sp;

    sp.cartesianProduct_(vecs, prod);
    NTA_CHECK(prod.size() == 0);

    v1.push_back(2);
    v1.push_back(4);

    v2.push_back(1);
    v2.push_back(3);

    vecs.push_back(v2);
    vecs.push_back(v1);

    sp.cartesianProduct_(vecs,prod);
    NTA_CHECK(prod.size() == 4);
    needle[0] = 2; needle[1] = 1;
    NTA_CHECK(findVector(needle, 2, prod));
    needle[0] = 2; needle[1] = 3;
    NTA_CHECK(findVector(needle, 2, prod));
    needle[0] = 4; needle[1] = 1;
    NTA_CHECK(findVector(needle, 2, prod));
    needle[0] = 4; needle[1] = 3;
    NTA_CHECK(findVector(needle, 2, prod));


    v1.clear(); 
    v2.clear();
    vecs.clear();
    prod.clear();

    v1.push_back(1); 
    v1.push_back(2);
    v1.push_back(3);

    v2.push_back(4); 
    v2.push_back(5);
    v2.push_back(6);

    v3.push_back(7); 
    v3.push_back(8);
    v3.push_back(9);

    vecs.push_back(v3);
    vecs.push_back(v2);
    vecs.push_back(v1);

    sp.cartesianProduct_(vecs, prod);
    NTA_CHECK(prod.size() == 27);
    needle[0] = 1; needle[1] = 4; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 1; needle[1] = 4; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 1; needle[1] = 4; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 1; needle[1] = 5; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 1; needle[1] = 5; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 1; needle[1] = 5; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 1; needle[1] = 6; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 1; needle[1] = 6; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 1; needle[1] = 6; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 2; needle[1] = 4; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 2; needle[1] = 4; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 2; needle[1] = 4; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 2; needle[1] = 5; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 2; needle[1] = 5; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 2; needle[1] = 5; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 2; needle[1] = 6; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 2; needle[1] = 6; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 2; needle[1] = 6; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 3; needle[1] = 4; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 3; needle[1] = 4; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 3; needle[1] = 4; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 3; needle[1] = 5; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 3; needle[1] = 5; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 3; needle[1] = 5; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

    needle[0] = 3; needle[1] = 6; needle[2] = 7;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 3; needle[1] = 6; needle[2] = 8;
    NTA_CHECK(findVector(needle,3,prod));
    needle[0] = 3; needle[1] = 6; needle[2] = 9;
    NTA_CHECK(findVector(needle,3,prod));

  }

  void SpatialPoolerTest::testGetNeighborsND() 
  {
    SpatialPooler sp;
    UInt column;
    vector<UInt> dimensions;
    vector<UInt> nums;
    vector<UInt> neighbors;
    bool wrapAround;
    UInt numColumns;

    UInt radius;
    UInt x,y,z,w;
    dimensions.clear();
    dimensions.push_back(4);
    dimensions.push_back(5);
    dimensions.push_back(7);
    
    vector<UInt> neighborsMap;
    UInt trueNeighbors1[4][5][7];
    radius = 1;
    wrapAround = false;
    z = 1;
    y = 2;
    x = 5;
    numColumns = (4 * 5 * 7);

    for (UInt i = 0; i < 4; i++) {
      for (UInt j = 0; j < 5; j++) {
        for (UInt k = 0; k < 7; k++) {
          trueNeighbors1[i][j][k] = 0;
        }
      }
    }

    for (Int i = -(Int)radius; i <= (Int)radius; i++) {
      for (Int j = -(Int)radius; j <= (Int)radius; j++) {
        for (Int k = -(Int)radius; k <= (Int)radius; k++) {
          Int zc = (z + i + dimensions[0]) % dimensions[0];
          Int yc = (y + j + dimensions[1]) % dimensions[1];
          Int xc = (x + k + dimensions[2]) % dimensions[2];
          if (i == 0 && j == 0 && k == 0) {
            continue;
          }
          trueNeighbors1[zc][yc][xc] = 1;
        }
      }
    }

    column = (UInt) (&trueNeighbors1[z][y][x] - &trueNeighbors1[0][0][0]);
    sp.getNeighborsND_(column, dimensions, radius, wrapAround, 
                       neighbors);

    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }

    NTA_CHECK(check_vector_eq((UInt *) trueNeighbors1, neighborsMap));

    neighborsMap.clear();
    w = 4;
    z = 1;
    y = 6;
    x = 3;
    dimensions.clear();
    dimensions.push_back(5);
    dimensions.push_back(6);
    dimensions.push_back(8);
    dimensions.push_back(4);
    
    UInt trueNeighbors2[5][6][8][4];
    UInt trueNeighbors2Wrap[5][6][8][4];
    radius = 2;
    numColumns = (5 * 6 * 8 * 4);

    for (UInt i = 0; i < numColumns; i++) {
      ((UInt *)trueNeighbors2)[i] = 0;
      ((UInt *)trueNeighbors2Wrap)[i] = 0;      
    }

    for (Int i = -(Int)radius; i <= (Int)radius; i++) {
      for (Int j = -(Int)radius; j <= (Int)radius; j++) {
        for (Int k = -(Int)radius; k <= (Int)radius; k++) {
          for (Int m = -(Int) radius; m <= (Int) radius; m++) {
            Int wc = (w + i);
            Int zc = (z + j);
            Int yc = (y + k);
            Int xc = (x + m);

            Int wc_ = (w + i + (Int) dimensions[0]) % dimensions[0]; 
            Int zc_ = (z + j + (Int) dimensions[1]) % dimensions[1]; 
            Int yc_ = (y + k + (Int) dimensions[2]) % dimensions[2]; 
            Int xc_ = (x + m + (Int) dimensions[3]) % dimensions[3]; 

            if (i == 0 && j == 0 && k == 0 && m == 0) {
              continue;
            }

            trueNeighbors2Wrap[wc_][zc_][yc_][xc_] = 1;

            if (wc < 0 || wc >= dimensions[0] || 
                zc < 0 || zc >= dimensions[1] ||
                yc < 0 || yc >= dimensions[2] ||
                xc < 0 || xc >= dimensions[3]) {
              continue;
            }

            trueNeighbors2[wc][zc][yc][xc] = 1;

          }
        }
      }
    }

    column = (UInt) (&trueNeighbors2[w][z][y][x] - &trueNeighbors2[0][0][0][0]);
    sp.getNeighborsND_(column, dimensions, radius, false, 
                       neighbors);

    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }

    NTA_CHECK(check_vector_eq((UInt *) trueNeighbors2, neighborsMap));

    sp.getNeighborsND_(column, dimensions, radius, true, 
                       neighbors);

    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }

    NTA_CHECK(check_vector_eq((UInt *) trueNeighbors2Wrap, neighborsMap));


    // 2D tests repeated here
    dimensions.clear();
    dimensions.push_back(6);
    dimensions.push_back(5);
    numColumns = 30;
    UInt trueNeighborsMap3[30] =
      {0, 0, 0, 0, 0,
       0, 0, 0, 0, 0,
       0, 1, 1, 1, 0,
       0, 1, 0, 1, 0,
       0, 1, 1, 1, 0,
       0, 0, 0, 0, 0};

    column = 3*5+2;
    radius = 1;
    wrapAround = false;
    sp.getNeighborsND_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap3, neighborsMap));

    UInt trueNeighborsMap4[30] =
      {0, 0, 0, 0, 0,
       1, 1, 1, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 0, 1, 1,
       1, 1, 1, 1, 1,
       1, 1, 1, 1, 1};

    column = 3*5+2;
    radius = 2;
    wrapAround = false;
    sp.getNeighborsND_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap4, neighborsMap));

    UInt trueNeighborsMap5[30] =
      {1, 0, 0, 1, 1,
       0, 0, 0, 0, 0,
       0, 0, 0, 0, 0,
       0, 0, 0, 0, 0,
       1, 0, 0, 1, 1,
       1, 0, 0, 1, 0};

    column = 29;
    radius = 1;
    wrapAround = true;
    sp.getNeighborsND_(column, dimensions, radius, wrapAround, neighbors);
    neighborsMap.assign(numColumns, 0);
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueNeighborsMap5, neighborsMap));


    column = 3;
    radius = 1;
    wrapAround = true;
    dimensions.clear();
    dimensions.push_back(8);
    UInt trueNeighborsMap6[8] = {0, 0, 1, 0, 1, 0, 0, 0};
    sp.getNeighborsND_(column, dimensions, radius, wrapAround,
                          neighbors);
    neighborsMap.clear();
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }

    NTA_CHECK(check_vector_eq(trueNeighborsMap6, neighborsMap));

    column = 3;
    radius = 2;
    wrapAround = false;
    dimensions.clear();
    dimensions.push_back(8);
    UInt trueNeighborsMap7[8] = {0, 1, 1, 0, 1, 1, 0, 0};
    sp.getNeighborsND_(column, dimensions, radius, wrapAround,
                          neighbors);
    neighborsMap.clear();
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }

    NTA_CHECK(check_vector_eq(trueNeighborsMap7, neighborsMap));

    column = 0;
    radius = 2;
    wrapAround = true;
    dimensions.clear();
    dimensions.push_back(8);
    UInt trueNeighborsMap8[8] = {0, 1, 1, 0, 0, 0, 1, 1};
    sp.getNeighborsND_(column, dimensions, radius, wrapAround,
                          neighbors);
    neighborsMap.clear();
    for (UInt i = 0; i < neighbors.size(); i++) {
      neighborsMap[neighbors[i]] = 1;
    }

    NTA_CHECK(check_vector_eq(trueNeighborsMap8, neighborsMap));

  }

  bool SpatialPoolerTest::testIsUpdateRound() { return true; }

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
