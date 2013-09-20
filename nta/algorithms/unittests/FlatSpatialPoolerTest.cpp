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

#include <cstring>
#include <iostream>
#include <nta/algorithms/flat_spatial_pooler.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>
#include "FlatSpatialPoolerTest.hpp"

using namespace std;
using namespace nta::algorithms::spatial_pooler;

namespace nta {

  void FlatSpatialPoolerTest::print_vec(UInt arr[], UInt n)
  {
    for (UInt i = 0; i < n; i++) {
      cout << arr[i] << " ";
    }
    cout << endl;
  }

  void FlatSpatialPoolerTest::print_vec(Real arr[], UInt n)
  {
    for (UInt i = 0; i < n; i++) {
      cout << arr[i] << " ";
    }
    cout << endl;
  }

  void FlatSpatialPoolerTest::print_vec(vector<UInt> vec)
  {
    for (UInt i = 0; i < vec.size(); i++) {
      cout << vec[i] << " ";
    }
    cout << endl;
  }

  void FlatSpatialPoolerTest::print_vec(vector<Real> vec)
  {
    for (UInt i = 0; i < vec.size(); i++) {
      cout << vec[i] << " ";
    }
    cout << endl;
  }

  bool FlatSpatialPoolerTest::almost_eq(Real a, Real b)
  {
    Real diff = a - b;
    return (diff > -1e-5 && diff < 1e-5);
  }

  bool FlatSpatialPoolerTest::check_vector_eq(UInt arr[], vector<UInt> vec)
  {
    for (UInt i = 0; i < vec.size(); i++) {
      if (arr[i] != vec[i]) {
        return false;
      }
    }
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(Real arr[], vector<Real> vec)
  {
    for (UInt i = 0; i < vec.size(); i++) {
      if (!almost_eq(arr[i],vec[i])) {
        return false;
      }
    }
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(UInt arr1[], UInt arr2[], UInt n)
  {
    for (UInt i = 0; i < n; i++) {
      if (arr1[i] != arr2[i]) {
        return false;
      }
    }
    return true;
  }

  bool FlatSpatialPoolerTest::check_vector_eq(Real arr1[], Real arr2[], UInt n)
  {
    for (UInt i = 0; i < n; i++) {
      if (!almost_eq(arr1[i], arr2[i])) {
        return false;
      }
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
    testAddBonus();
  }

  void FlatSpatialPoolerTest::testAddBonus()
  {
    UInt numInputs = 5;
    UInt numColumns = 7;
    FlatSpatialPooler fsp = FlatSpatialPooler();
    fsp.initializeFlat(numInputs, numColumns);
    vector<UInt> indices;
    vector<Real> vec;
    Real bonus;
    bool replace;

    indices.clear();
    indices.push_back(1);
    indices.push_back(4);
    indices.push_back(6);
    bonus = 5;
    replace = false;
    Real initArray1[] = {10, 10, 10, 10, 10, 10, 10};
    Real trueArray1[] = {10, 15, 10, 10, 15, 10, 15};
    vec.assign(initArray1, initArray1 + numColumns);
    fsp.addBonus_(vec, bonus, indices, replace);
    NTA_CHECK(check_vector_eq(trueArray1, vec));

    indices.clear();
    indices.push_back(1);
    indices.push_back(4);
    indices.push_back(6);
    bonus = 4;
    replace = true;
    Real initArray2[] = {10, 10, 10, 10, 10, 10, 10};
    Real trueArray2[] = {10, 4, 10, 10, 4, 10, 4};
    vec.assign(initArray2, initArray2 + numColumns);
    fsp.addBonus_(vec, bonus, indices, replace);
    NTA_CHECK(check_vector_eq(trueArray2, vec));

    indices.clear();
    indices.push_back(1);
    indices.push_back(2);
    indices.push_back(3);
    indices.push_back(4);
    indices.push_back(6);
    bonus = 5000;
    replace = false;
    Real initArray3[] = {10, 10, 10, 10, 10, 10, 10};
    Real trueArray3[] = {10, 5010, 5010, 5010, 5010, 10, 5010};
    vec.assign(initArray3, initArray3 + numColumns);
    fsp.addBonus_(vec, bonus, indices, replace);
    NTA_CHECK(check_vector_eq(trueArray3, vec));

    indices.clear();
    bonus = 1;
    replace = true;
    Real initArray4[] = {0, 123, 456, 678, 999, 1111, 9834};
    Real trueArray4[] = {0, 123, 456, 678, 999, 1111, 9834};
    vec.assign(initArray4, initArray4 + numColumns);
    fsp.addBonus_(vec, bonus, indices, replace);
    NTA_CHECK(check_vector_eq(trueArray4, vec));

    indices.clear();
    indices.push_back(1);
    indices.push_back(2);
    indices.push_back(3);
    indices.push_back(4);
    indices.push_back(6);
    bonus = 5000;
    replace = false;
    Real initArray5[] = {10, 10, 10, 10, 10, 10, 10};
    Real trueArray5[] = {10, 5010, 5010, 5010, 5010, 10, 5010};
    vec.assign(initArray5, initArray5 + numColumns);
    fsp.addBonus_(vec, bonus, indices, replace);
    NTA_CHECK(check_vector_eq(trueArray5, vec));
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
