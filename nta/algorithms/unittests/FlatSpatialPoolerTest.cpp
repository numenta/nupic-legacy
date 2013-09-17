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
#include <nta/algorithms/flat_spatial_pooler.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>
#include <cstring>
#include "FlatSpatialPoolerTest.hpp"

using namespace std;
using namespace nta::algorithms::spatial_pooler;

namespace nta {  

  void FlatSpatialPoolerTest::print_vec(UInt arr[], UInt n)
  {
    for (UInt i = 0; i < n; i++)
      cout << arr[i] << " ";
    cout << endl;
  }

  void FlatSpatialPoolerTest::print_vec(Real arr[], UInt n)
  {
    for (UInt i = 0; i < n; i++)
      cout << arr[i] << " ";
    cout << endl;
  }

  void FlatSpatialPoolerTest::print_vec(vector<UInt> vec)
  {
    for (UInt i = 0; i < vec.size(); i++)
      cout << vec[i] << " ";
    cout << endl;
  }

  void FlatSpatialPoolerTest::print_vec(vector<Real> vec)
  {
    for (UInt i = 0; i < vec.size(); i++)
      cout << vec[i] << " ";
    cout << endl;
  }

  bool FlatSpatialPoolerTest::almost_eq(Real a, Real b)
  {
    Real diff = a - b;
    return (diff > -1e-5 && diff < 1e-5); 
  }

  bool FlatSpatialPoolerTest::check_vector_eq(UInt arr[], vector<UInt> vec)
  {
    for (UInt i = 0; i < vec.size(); i++)
      if (arr[i] != vec[i])
        return false;
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(Real arr[], vector<Real> vec)
  {
    for (UInt i = 0; i < vec.size(); i++) {
      if (!almost_eq(arr[i],vec[i]))
        return false;
    }
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(UInt arr1[], UInt arr2[], UInt n)
  {
    for (UInt i = 0; i < n; i++) {
      if (arr1[i] != arr2[i])
        return false;
    }
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(Real arr1[], Real arr2[], UInt n)
  {
    for (UInt i = 0; i < n; i++) {
      if (!almost_eq(arr1[i], arr2[i]))
        return false;
    }
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(vector<UInt> vec1, vector<UInt> vec2)
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

	void FlatSpatialPoolerTest::RunTests() 
	{
    testSelectVirgin();
    testSelectHighTierColumns();
  }

  void FlatSpatialPoolerTest::testSelectHighTierColumns()
  {
    UInt numInputs = 5;
    UInt numColumns = 10;
    FlatSpatialPooler fsp = FlatSpatialPooler();
    fsp.initializeFlat(numInputs, numColumns);
    vector<UInt> highTier, highTierDense;
    vector<Real> overlapsPct;
    Real minDistance;

    minDistance = 0.1;
    fsp.setMinDistance(minDistance);
    Real overlapsPctArray1[] = {1.0, 0.95, 0.99, 0.88, 0.87, 0.7, 0.1, 0, 0.3, 0.9001};
    UInt trueHighTier1[] = {1,   1,     1,    0,    0,   0,    0,  0,  0,   1};
    overlapsPct.assign(overlapsPctArray1,overlapsPctArray1 + numColumns);

    fsp.selectHighTierColumns_(overlapsPct, highTier);
    highTierDense.assign(numColumns, 0);
    for (UInt i = 0; i < highTier.size(); i++) {
      highTierDense[highTier[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueHighTier1, highTierDense));

    minDistance = 0.25;
    fsp.setMinDistance(minDistance);
    Real overlapsPctArray2[] = {1.0, 0.05, 0.19, 0.88, 0.77, 0.81, 0.61, 0.64, 0.73, 0.8001};
    UInt trueHighTier2[] =     {1,   0,     0,    1,    1,   1,     0,     0,    0,   1};
    overlapsPct.assign(overlapsPctArray2,overlapsPctArray2 + numColumns);

    fsp.selectHighTierColumns_(overlapsPct, highTier);
    highTierDense.assign(numColumns, 0);
    for (UInt i = 0; i < highTier.size(); i++) {
      highTierDense[highTier[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueHighTier2, highTierDense));

    minDistance = 1.0;
    fsp.setMinDistance(minDistance);
    Real overlapsPctArray3[] = {1.0, 0.05, 0.19, 0.88, 0.77, 0.81, 0.61, 0.64, 0.73, 0.8001};
    UInt trueHighTier3[] =     {1,   1,     1,    1,    1,   1,     1,     1,    1,   1};
    overlapsPct.assign(overlapsPctArray3,overlapsPctArray3 + numColumns);

    fsp.selectHighTierColumns_(overlapsPct, highTier);
    highTierDense.assign(numColumns, 0);
    for (UInt i = 0; i < highTier.size(); i++) {
      highTierDense[highTier[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueHighTier3, highTierDense));

    minDistance = 0;
    fsp.setMinDistance(minDistance);
    Real overlapsPctArray4[] = {1.0, 0.05, 0.99, 0.98, 1.0, 0, 1.0, 0.64, 0.73, 0.8001};
    UInt trueHighTier4[] =     {1,   0,     0,    0,    1,   0, 1,    0,    0,   0};
    overlapsPct.assign(overlapsPctArray4,overlapsPctArray4 + numColumns);

    fsp.selectHighTierColumns_(overlapsPct, highTier);
    highTierDense.assign(numColumns, 0);
    for (UInt i = 0; i < highTier.size(); i++) {
      highTierDense[highTier[i]] = 1;
    }
    NTA_CHECK(check_vector_eq(trueHighTier4, highTierDense));

  }

  void FlatSpatialPoolerTest::testSelectVirgin() 
  {
    UInt numInputs = 5;
    UInt numColumns = 10;
    FlatSpatialPooler fsp = FlatSpatialPooler();
    fsp.initializeFlat(numInputs, numColumns);
    vector<UInt> virgin;

    Real activeDutyArr1[] = {0.9, 0.8, 0.7, 0, 0.6, 0.001, 0, 0.01, 0, 0.09};
    UInt trueVirgin1[] = {3,6,8};
    fsp.setActiveDutyCycles(activeDutyArr1);

    fsp.selectVirginColumns_(virgin);
    NTA_CHECK(check_vector_eq(trueVirgin1, virgin));

    Real activeDutyArr2[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    UInt trueVirgin2[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    fsp.setActiveDutyCycles(activeDutyArr2);

    fsp.selectVirginColumns_(virgin);
    NTA_CHECK(check_vector_eq(trueVirgin2, virgin));

    Real activeDutyArr3[] = {0.9, 0.8, 0.7, 0.3, 0.6, 0.001, 0.003, 0.01, 0.12, 0.09};
    fsp.setActiveDutyCycles(activeDutyArr3);

    fsp.selectVirginColumns_(virgin);
    NTA_CHECK(virgin.size() == 0);

  }
    
} // end namespace nta
