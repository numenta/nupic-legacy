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


  def testSparsifyVector(self):
    classifier = KNNClassifier(distanceMethod="norm", distanceNorm=2.0)
    inputPattern = np.array([0, 1, 3, 7, 11], dtype=np.int32)

    # Each of the 4 tests correspond with the each decisional branch in the
    # sparsifyVector method
    #
    # tests: if not self.relativeThreshold:
    outputPattern = classifier._sparsifyVector(inputPattern, doWinners=True)
    self.assertTrue(np.array_equal(np.array([0, 1, 3, 7, 11], dtype=np.int32),
      outputPattern))

    # tests: elif self.sparseThreshold > 0:
    classifier = KNNClassifier(distanceMethod="norm", distanceNorm=2.0,
      relativeThreshold=True, sparseThreshold=.2)
    outputPattern = classifier._sparsifyVector(inputPattern, doWinners=True)
    self.assertTrue(np.array_equal(np.array([0, 0, 3, 7, 11], dtype=np.int32),
      outputPattern))

    # tests: if doWinners:
    classifier = KNNClassifier(distanceMethod="norm", distanceNorm=2.0,
      relativeThreshold=True, sparseThreshold=.2, numWinners=2)
    outputPattern = classifier._sparsifyVector(inputPattern, doWinners=True)
    self.assertTrue(np.array_equal(np.array([0, 0, 0, 0, 0], dtype=np.int32),
      outputPattern))

    # tests: Do binarization
    classifier = KNNClassifier(distanceMethod="norm", distanceNorm=2.0,
      relativeThreshold=True, sparseThreshold=.2, doBinarization=True)
    outputPattern = classifier._sparsifyVector(inputPattern, doWinners=True)
    self.assertTrue(np.array_equal(np.array(
      [0., 0., 1., 1., 1.], dtype=np.float32), outputPattern))


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


  def testMinSparsity(self):
    """Tests overlap distance with min sparsity"""

    # Require sparsity >= 20%
    params = {"distanceMethod": "rawOverlap", "minSparsity": 0.2}
    classifier = KNNClassifier(**params)

    dimensionality = 30
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 21, 28], dtype=np.int32)

    # This has 20% sparsity and should be inserted
    c = np.array([2, 3, 8, 11, 14, 18], dtype=np.int32)

    # This has 17% sparsity and should NOT be inserted
    d = np.array([2, 3, 8, 11, 18], dtype=np.int32)

    numPatterns = classifier.learn(a, 0, isSparse=dimensionality)
    self.assertEquals(numPatterns, 1)

    numPatterns = classifier.learn(b, 1, isSparse=dimensionality)
    self.assertEquals(numPatterns, 2)

    numPatterns = classifier.learn(c, 1, isSparse=dimensionality)
    self.assertEquals(numPatterns, 3)

    numPatterns = classifier.learn(d, 1, isSparse=dimensionality)
    self.assertEquals(numPatterns, 3)

    # Test that inference ignores low sparsity vectors but not others
    e = np.array([2, 4, 5, 6, 8, 12, 14, 18, 20], dtype=np.int32)
    dense= np.zeros(dimensionality)
    dense[e] = 1.0
    cat, inference, _, _ = classifier.infer(dense)
    self.assertIsNotNone(cat)
    self.assertGreater(inference.sum(),0.0)

    # This has 20% sparsity and should be used for inference
    f = np.array([2, 5, 8, 11, 14, 18], dtype=np.int32)
    dense= np.zeros(dimensionality)
    dense[f] = 1.0
    cat, inference, _, _ = classifier.infer(dense)
    self.assertIsNotNone(cat)
    self.assertGreater(inference.sum(),0.0)

    # This has 17% sparsity and should return null inference results
    g = np.array([2, 3, 8, 11, 19], dtype=np.int32)
    dense= np.zeros(dimensionality)
    dense[g] = 1.0
    cat, inference, _, _ = classifier.infer(dense)
    self.assertIsNone(cat)
    self.assertEqual(inference.sum(),0.0)


  def testPartitionIdExcluded(self):
    """
    Tests that paritionId properly excludes training data points during
    inference
    """
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=np.int32)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0

    denseB = np.zeros(dimensionality)
    denseB[b] = 1.0

    classifier.learn(a, 0, isSparse=dimensionality, partitionId=0)
    classifier.learn(b, 1, isSparse=dimensionality, partitionId=1)

    cat, _, _, _ = classifier.infer(denseA, partitionId=1)
    self.assertEquals(cat, 0)

    cat, _, _, _ = classifier.infer(denseA, partitionId=0)
    self.assertEquals(cat, 1)

    cat, _, _, _ = classifier.infer(denseB, partitionId=0)
    self.assertEquals(cat, 1)

    cat, _, _, _ = classifier.infer(denseB, partitionId=1)
    self.assertEquals(cat, 0)

    # Ensure it works even if you invoke learning again. To make it a bit more
    # complex this time we insert A again but now with Id=2
    classifier.learn(a, 0, isSparse=dimensionality, partitionId=2)

    # Even though first A should be ignored, the second instance of A should
    # not be ignored.
    cat, _, _, _ = classifier.infer(denseA, partitionId=0)
    self.assertEquals(cat, 0)


  def testGetPartitionId(self):
    """
    Test a sequence of calls to KNN to ensure we can retrieve partition Id:
        - We first learn on some patterns (including one pattern with no
          partitionId in the middle) and test that we can retrieve Ids.
        - We then invoke inference and then check partitionId again.
        - We check incorrect indices to ensure we get an exception.
        - We check the case where the partitionId to be ignored is not in
          the list.
        - We learn on one more pattern and check partitionIds again
        - We remove rows and ensure partitionIds still work
    """
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=np.int32)
    c = np.array([1, 2, 3, 14, 16, 19, 22, 24, 33], dtype=np.int32)
    d = np.array([2, 4, 8, 12, 14, 19, 22, 24, 33], dtype=np.int32)
    e = np.array([1, 3, 7, 12, 14, 19, 22, 24, 33], dtype=np.int32)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0

    classifier.learn(a, 0, isSparse=dimensionality, partitionId=433)
    classifier.learn(b, 1, isSparse=dimensionality, partitionId=213)
    classifier.learn(c, 1, isSparse=dimensionality, partitionId=None)
    classifier.learn(d, 1, isSparse=dimensionality, partitionId=433)

    self.assertEquals(classifier.getPartitionId(0), 433)
    self.assertEquals(classifier.getPartitionId(1), 213)
    self.assertEquals(classifier.getPartitionId(2), None)
    self.assertEquals(classifier.getPartitionId(3), 433)

    cat, _, _, _ = classifier.infer(denseA, partitionId=213)
    self.assertEquals(cat, 0)

    # Test with patternId not in classifier
    cat, _, _, _ = classifier.infer(denseA, partitionId=666)
    self.assertEquals(cat, 0)

    # Partition Ids should be maintained after inference
    self.assertEquals(classifier.getPartitionId(0), 433)
    self.assertEquals(classifier.getPartitionId(1), 213)
    self.assertEquals(classifier.getPartitionId(2), None)
    self.assertEquals(classifier.getPartitionId(3), 433)

    # Should return exceptions if we go out of bounds
    with self.assertRaises(RuntimeError):
      classifier.getPartitionId(4)
    with self.assertRaises(RuntimeError):
      classifier.getPartitionId(-1)

    # Learn again
    classifier.learn(e, 4, isSparse=dimensionality, partitionId=413)
    self.assertEquals(classifier.getPartitionId(4), 413)

    # Test getPatternIndicesWithPartitionId
    self.assertItemsEqual(classifier.getPatternIndicesWithPartitionId(433),
                          [0, 3])
    self.assertItemsEqual(classifier.getPatternIndicesWithPartitionId(666),
                          [])
    self.assertItemsEqual(classifier.getPatternIndicesWithPartitionId(413),
                          [4])

    self.assertEquals(classifier.getNumPartitionIds(), 3)

    # Check that the full set of partition ids is what we expect
    self.assertItemsEqual(classifier.getPartitionIdPerPattern(),
                          [433, 213, np.inf, 433, 413])
    self.assertItemsEqual(classifier.getPartitionIdList(),[433, 413, 213])

    # Remove two rows - all indices shift down
    self.assertEquals(classifier._removeRows([0,2]), 2)
    self.assertItemsEqual(classifier.getPatternIndicesWithPartitionId(433),
                          [1])
    self.assertItemsEqual(classifier.getPatternIndicesWithPartitionId(413),
                          [2])

    # Remove another row and check number of partitions have decreased
    classifier._removeRows([0])
    self.assertEquals(classifier.getNumPartitionIds(), 2)

    # Check that the full set of partition ids is what we expect
    self.assertItemsEqual(classifier.getPartitionIdPerPattern(), [433, 413])
    self.assertItemsEqual(classifier.getPartitionIdList(),[433, 413])



  def testGetPartitionIdWithNoIdsAtFirst(self):
    """
    Tests that we can correctly retrieve partition Id even if the first few
    vectors do not have Ids
    """
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=np.int32)
    c = np.array([1, 2, 3, 14, 16, 19, 22, 24, 33], dtype=np.int32)
    d = np.array([2, 4, 8, 12, 14, 19, 22, 24, 33], dtype=np.int32)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0

    denseD = np.zeros(dimensionality)
    denseD[d] = 1.0

    classifier.learn(a, 0, isSparse=dimensionality, partitionId=None)
    classifier.learn(b, 1, isSparse=dimensionality, partitionId=None)
    classifier.learn(c, 2, isSparse=dimensionality, partitionId=211)
    classifier.learn(d, 1, isSparse=dimensionality, partitionId=405)

    cat, _, _, _ = classifier.infer(denseA, partitionId=405)
    self.assertEquals(cat, 0)

    cat, _, _, _ = classifier.infer(denseD, partitionId=405)
    self.assertEquals(cat, 2)

    cat, _, _, _ = classifier.infer(denseD)
    self.assertEquals(cat, 1)


  @unittest.skipUnless(__debug__, "Only applicable when asserts are enabled")
  def testOverlapDistanceMethodBadSparsity(self):
    """Sparsity (input dimensionality) less than input array"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)

    # Learn with incorrect dimensionality, less than some bits (23, 29)
    with self.assertRaises(AssertionError):
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


  @unittest.skipUnless(__debug__, "Only applicable when asserts are enabled")
  def testOverlapDistanceMethodStandardUnsorted(self):
    """If sparse representation indices are unsorted expect error."""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([29, 3, 7, 11, 13, 17, 19, 23, 1], dtype=np.int32)
    b = np.array([2, 4, 20, 12, 14, 18, 8, 28, 30], dtype=np.int32)

    with self.assertRaises(AssertionError):
      classifier.learn(a, 0, isSparse=dimensionality)

    with self.assertRaises(AssertionError):
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
