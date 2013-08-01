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
 * Implementation of unit tests for NearestNeighbor
 */

#include <iostream>

#include <nta/algorithms/classifier_result.hpp>
#include <nta/algorithms/fast_cla_classifier.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>
#include "FastCLAClassifierTest.hpp"

using namespace std;
using namespace nta::algorithms::cla_classifier;

namespace nta {

  void FastCLAClassifierTest::RunTests()
  {
    testBasic();
  }

  void FastCLAClassifierTest::testBasic()
  {
    vector<UInt> steps;
    steps.push_back(1);
    FastCLAClassifier* c = new FastCLAClassifier(steps, 0.1, 0.1, 0);

    vector<UInt> input1;
    input1.push_back(1);
    input1.push_back(5);
    input1.push_back(9);
    ClassifierResult result1;
    c->fastCompute(0, input1, 4, 34.7, false, true, true, &result1);

    vector<UInt> input2;
    input2.push_back(1);
    input2.push_back(5);
    input2.push_back(9);
    ClassifierResult result2;
    c->fastCompute(1, input2, 4, 34.7, false, true, true, &result2);

    bool found0 = false;
    bool found1 = false;
    for (map<Int, vector<Real64>*>::const_iterator it = result2.begin();
         it != result2.end(); ++it)
    {
      if (it->first == 0)
      {
        NTA_CHECK(found0 == false);
        found0 = true;
        NTA_CHECK(it->second->size() == 5);
        NTA_CHECK(fabs(it->second->at(4) - 34.7) < 0.000001);
      } else if (it->first == 1) {
        NTA_CHECK(found1 == false);
        found1 = true;
        NTA_CHECK(it->second->size() == 5);
      }
    }

    delete c;
  }

} // end namespace nta
