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
    FastCLAClassifier c = FastCLAClassifier(steps, 0.1, 0.1, 0);

    // Create a vector of input bit indices
    vector<UInt> input1;
    input1.push_back(1);
    input1.push_back(5);
    input1.push_back(9);
    ClassifierResult result1;
    c.fastCompute(0, input1, 4, 34.7, false, true, true, &result1);

    // Create a vector of input bit indices
    vector<UInt> input2;
    input2.push_back(1);
    input2.push_back(5);
    input2.push_back(9);
    ClassifierResult result2;
    c.fastCompute(1, input2, 4, 34.7, false, true, true, &result2);

    {
      bool foundMinus1 = false;
      bool found1 = false;
      for (map<Int, vector<Real64>*>::const_iterator it = result2.begin();
           it != result2.end(); ++it)
      {
        if (it->first == -1)
        {
          // The -1 key is used for the actual values
          TESTEQUAL2("already found key -1 in classifier result",
                     false, foundMinus1);
          foundMinus1 = true;
          TESTEQUAL2("Expected five buckets since it has only seen bucket 4 "
                     "(so it has buckets 0-4).", 5, it->second->size());
          TEST2("Incorrect actual value for bucket 4",
                fabs(it->second->at(4) - 34.7) < 0.000001);
        } else if (it->first == 1) {
          // Check the one-step prediction
          TESTEQUAL2("already found key 1 in classifier result", false, found1);
          found1 = true;
          TESTEQUAL2("expected five bucket predictions", 5, it->second->size());
          TEST2("incorrect prediction for bucket 0",
                fabs(it->second->at(0) - 0.2) < 0.000001);
          TEST2("incorrect prediction for bucket 1",
                fabs(it->second->at(1) - 0.2) < 0.000001);
          TEST2("incorrect prediction for bucket 2",
                fabs(it->second->at(2) - 0.2) < 0.000001);
          TEST2("incorrect prediction for bucket 3",
                fabs(it->second->at(3) - 0.2) < 0.000001);
          TEST2("incorrect prediction for bucket 4",
                fabs(it->second->at(4) - 0.2) < 0.000001);
        }
      }
      TESTEQUAL2("key -1 not found in classifier result", true, foundMinus1);
      TESTEQUAL2("key 1 not found in classifier result", true, found1);
    }
  }

} // end namespace nta
