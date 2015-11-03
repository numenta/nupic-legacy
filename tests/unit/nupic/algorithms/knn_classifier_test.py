#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import numpy as np
import unittest

from nupic.algorithms.KNNClassifier import KNNClassifier



class KNNClassifierTest(unittest.TestCase):


  def testDistanceMetrics(self):
    classifier = KNNClassifier(distanceMethod="norm", distanceNorm=2.0)
  
    dimensionality = 40
    protoA = np.array([0, 1, 3, 7, 11], dtype=np.int32)
    protoB = np.array([20, 28, 30], dtype=np.int32)
    
    classifier.learn(protoA, 0, isSparse=dimensionality)
    classifier.learn(protoB, 0, isSparse=dimensionality)
    
    # input is an arbitrary point, close to protoA, orthogonal to protoB
    input = np.zeros(dimensionality)
    input[:4] = 1.0
    # input0 is used to test that the distance from a point to itself is 0
    input0 = np.zeros(dimensionality)
    input0[protoA] = 1.0

    # Test l2 norm metric
    _, _, dist, _ = classifier.infer(input)
    l2Distances = [0.65465367,  1.0]
    for actual, predicted in zip(l2Distances, dist):
      self.assertAlmostEqual(
        actual, predicted, places=5,
        msg="l2 distance norm is not calculated as expected.")
  
    _, _, dist0, _ = classifier.infer(input0)
    self.assertEqual(
      0.0, dist0[0], msg="l2 norm did not calculate 0 distance as expected.")

    # Test l1 norm metric
    classifier.distanceNorm = 1.0
    _, _, dist, _ = classifier.infer(input)
    l1Distances = [0.42857143,  1.0]
    for actual, predicted in zip(l1Distances, dist):
      self.assertAlmostEqual(
        actual, predicted, places=5,
        msg="l1 distance norm is not calculated as expected.")
    
    _, _, dist0, _ = classifier.infer(input0)
    self.assertEqual(
      0.0, dist0[0], msg="l1 norm did not calculate 0 distance as expected.")
  
    # Test raw overlap metric
    classifier.distanceMethod = "rawOverlap"
    _, _, dist, _ = classifier.infer(input)
    rawOverlaps = [1, 4]
    for actual, predicted in zip(rawOverlaps, dist):
      self.assertEqual(
        actual, predicted, msg="Raw overlap is not calculated as expected.")

    _, _, dist0, _ = classifier.infer(input0)
    self.assertEqual(
      0.0, dist0[0],
      msg="Raw overlap did not calculate 0 distance as expected.")

    # Test pctOverlapOfInput metric
    classifier.distanceMethod = "pctOverlapOfInput"
    _, _, dist, _ = classifier.infer(input)
    pctOverlaps = [0.25, 1.0]
    for actual, predicted in zip(pctOverlaps, dist):
      self.assertAlmostEqual(
        actual, predicted, places=5,
        msg="pctOverlapOfInput is not calculated as expected.")
   
    _, _, dist0, _ = classifier.infer(input0)
    self.assertEqual(
      0.0, dist0[0],
      msg="pctOverlapOfInput did not calculate 0 distance as expected.")

    # Test pctOverlapOfProto metric
    classifier.distanceMethod = "pctOverlapOfProto"
    _, _, dist, _ = classifier.infer(input)
    pctOverlaps = [0.40, 1.0]
    for actual, predicted in zip(pctOverlaps, dist):
      self.assertAlmostEqual(
        actual, predicted, places=5,
        msg="pctOverlapOfProto is not calculated as expected.")

    _, _, dist0, _ = classifier.infer(input0)
    self.assertEqual(
      0.0, dist0[0],
      msg="pctOverlapOfProto did not calculate 0 distance as expected.")

    # Test pctOverlapOfLarger metric
    classifier.distanceMethod = "pctOverlapOfLarger"
    _, _, dist, _ = classifier.infer(input)
    pctOverlaps = [0.40, 1.0]
    for actual, predicted in zip(pctOverlaps, dist):
      self.assertAlmostEqual(
      actual, predicted, places=5,
        msg="pctOverlapOfLarger is not calculated as expected.")

    _, _, dist0, _ = classifier.infer(input0)
    self.assertEqual(
      0.0, dist0[0],
      msg="pctOverlapOfLarger did not calculate 0 distance as expected.")


  def testOverlapDistanceMethodStandard(self):
    """Tests standard learning case for raw overlap"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=np.int32)

    numPatterns = classifier.learn(a, 0, isSparse=dimensionality)
    self.assertEquals(numPatterns, 1)

    numPatterns = classifier.learn(b, 1, isSparse=dimensionality)
    self.assertEquals(numPatterns, 2)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0
    cat, _, _, _ = classifier.infer(denseA)
    self.assertEquals(cat, 0)

    denseB = np.zeros(dimensionality)
    denseB[b] = 1.0
    cat, _, _, _ = classifier.infer(denseB)
    self.assertEquals(cat, 1)


  def testOverlapDistanceMethodBadSparsity(self):
    """Sparsity (input dimensionality) less than input array"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)

    # Learn with incorrect dimensionality, less than some bits (23, 29)
    with self.assertRaises(RuntimeError):
      classifier.learn(a, 0, isSparse=20)


  def testOverlapDistanceMethodInconsistentDimensionality(self):
    """Inconsistent sparsity (input dimensionality)"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)

    # Learn with incorrect dimensionality, greater than largest ON bit, but
    # inconsistent when inferring
    numPatterns = classifier.learn(a, 0, isSparse=31)
    self.assertEquals(numPatterns, 1)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0

    cat, _, _, _ = classifier.infer(denseA)
    self.assertEquals(cat, 0)



  def testOverlapDistanceMethodStandardUnsorted(self):
    """If sparse representation indices are unsorted expect error."""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([29, 3, 7, 11, 13, 17, 19, 23, 1], dtype=np.int32)
    b = np.array([2, 4, 20, 12, 14, 18, 8, 28, 30], dtype=np.int32)

    with self.assertRaises(RuntimeError):
      classifier.learn(a, 0, isSparse=dimensionality)

    with self.assertRaises(RuntimeError):
      classifier.learn(b, 1, isSparse=dimensionality)


  def testOverlapDistanceMethodEmptyArray(self):
    """Tests case where pattern has no ON bits"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([], dtype=np.int32)

    numPatterns = classifier.learn(a, 0, isSparse=dimensionality)
    self.assertEquals(numPatterns, 1)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0
    cat, _, _, _ = classifier.infer(denseA)
    self.assertEquals(cat, 0)


  @unittest.skip("Finish when infer has options for sparse and dense "
                 "https://github.com/numenta/nupic/issues/2198")
  def testOverlapDistanceMethod_ClassifySparse(self):
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=np.int32)

    classifier.learn(a, 0, isSparse=dimensionality)
    classifier.learn(b, 1, isSparse=dimensionality)

    # TODO Test case where infer is passed a sparse representation after
    # infer() has been extended to handle sparse and dense
    cat, _, _, _ = classifier.infer(a)
    self.assertEquals(cat, 0)

    cat, _, _, _ = classifier.infer(b)
    self.assertEquals(cat, 1)



if __name__ == "__main__":
  unittest.main()
