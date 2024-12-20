# Copyright 2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import unittest

import numpy as np

from nupic.bindings.math import GetNTAReal
from nupic.bindings.algorithms import SpatialPooler
# Uncomment below line to use python SpatialPooler
# from nupic.algorithms.spatial_pooler import SpatialPooler



uintDType = "uint32"
realDType = GetNTAReal()



class SpatialPoolerTest(unittest.TestCase):
  """Unit Tests for C++ SpatialPooler class."""


  def testCalculateOverlap(self):
    sp = SpatialPooler(inputDimensions = [10],
                       columnDimensions = [5])

    permanences = [
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      [0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
      [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
      [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]
    ]
    inputVectors = [
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
      [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    ]
    expectedOverlaps = [
      [0,  0,  0,  0,  0],
      [10, 8,  6,  4,  2],
      [5,  4,  3,  2,  1],
      [5,  3,  1,  0,  0],
      [1,  1,  1,  1,  1]
    ]

    for column, permanence in enumerate(permanences):
      sp.setPermanence(column, np.array(permanence, dtype=realDType))

    for inputVector, expectedOverlap in zip(inputVectors, expectedOverlaps):
      inputVector = np.array(inputVector, dtype=uintDType)
      overlap = set(sp._calculateOverlap(inputVector))
      expected = set(expectedOverlap)
      self.assertSetEqual(overlap, expected,
                          "Input: {0}\tExpected: {1}\tActual: {2}".format(
                            inputVector, expected, overlap))


  def testInhibitColumnsGlobal(self):
    sp = SpatialPooler(inputDimensions = [10],
                       columnDimensions = [10],
                       globalInhibition = True,
                       numActiveColumnsPerInhArea = 10)

    overlaps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expectedActive = set([5, 6, 7, 8, 9])

    active = sp._inhibitColumns(np.array(overlaps, dtype=realDType))
    active = set(active)

    self.assertSetEqual(active, expectedActive,
                        "Input: {0}\tExpected: {1}\tActual: {2}".format(
                          overlaps, expectedActive, active))


  def testUpdatePermanencesForColumn(self):
    sp = SpatialPooler(inputDimensions = [5],
                       columnDimensions = [5])
    sp.setSynPermTrimThreshold(0.05)

    permanencesList = [
      [ -0.10, 0.500, 0.400, 0.010, 0.020 ],
      [ 0.300, 0.010, 0.020, 0.120, 0.090 ],
      [ 0.070, 0.050, 1.030, 0.190, 0.060 ],
      [ 0.180, 0.090, 0.110, 0.010, 0.030 ],
      [ 0.200, 0.101, 0.050, -0.09, 1.100 ]]

    expectedPermanencesList = [
      [ 0.000, 0.500, 0.400, 0.000, 0.000],
       # Clip     -     -      Trim   Trim
      [0.300, 0.000, 0.000, 0.120, 0.090],
       # -    Trim   Trim   -     -
      [0.070, 0.050, 1.000, 0.190, 0.060],
       # -     -   Clip   -     -
      [0.180, 0.090, 0.110, 0.000, 0.000],
       # -     -    -      Trim   Trim
      [0.200, 0.101, 0.050, 0.000, 1.000]]
       # -      -     -      Clip   Clip

    expectedConnectedSynapsesList = [
      [0, 1, 1, 0, 0],
      [1, 0, 0, 1, 0],
      [0, 0, 1, 1, 0],
      [1, 0, 1, 0, 0],
      [1, 1, 0, 0, 1]]

    expectedConnectedCounts = [2, 2, 2, 2, 3]

    for i in xrange(5):
      permanences = np.array(permanencesList[i], dtype=realDType)
      expectedPermanences = np.array(expectedPermanencesList[i],
                                     dtype=realDType)
      expectedConnectedSynapses = expectedConnectedSynapsesList[i]

      sp._updatePermanencesForColumn(permanences, i, False)

      updatedPermanences = np.zeros(5, dtype=realDType)
      connectedSynapses = np.zeros(5, dtype=uintDType)
      connectedCounts = np.zeros(5, dtype=uintDType)

      sp.getPermanence(i, updatedPermanences)
      sp.getConnectedSynapses(i, connectedSynapses)
      sp.getConnectedCounts(connectedCounts)

      np.testing.assert_almost_equal(updatedPermanences, expectedPermanences)
      self.assertEqual(list(connectedSynapses), expectedConnectedSynapses)
      self.assertEqual(connectedCounts[i], expectedConnectedCounts[i])


  def testUpdateDutyCycles(self):
    sp = SpatialPooler(inputDimensions = [5],
                       columnDimensions = [5])

    initOverlapArr1 = np.array([1, 1, 1, 1, 1], dtype=realDType)
    sp.setOverlapDutyCycles(initOverlapArr1);
    overlaps = np.array([1, 5, 7, 0, 0], dtype=uintDType)
    active = np.array([0, 0, 0, 0, 0], dtype=uintDType)

    sp.setIterationNum(2)
    sp._updateDutyCycles(overlaps, active);

    resultOverlapArr1 = np.zeros(5, dtype=realDType)
    sp.getOverlapDutyCycles(resultOverlapArr1)

    trueOverlapArr1 = np.array([1, 1, 1, 0.5, 0.5], dtype=realDType)
    self.assertEqual(list(resultOverlapArr1), list(trueOverlapArr1))

    sp.setOverlapDutyCycles(initOverlapArr1);
    sp.setIterationNum(2000);
    sp.setUpdatePeriod(1000);
    sp._updateDutyCycles(overlaps, active);

    resultOverlapArr2 = np.zeros(5, dtype=realDType)
    sp.getOverlapDutyCycles(resultOverlapArr2);
    trueOverlapArr2 = np.array([1, 1, 1, 0.999, 0.999], dtype=realDType)

    self.assertEqual(list(resultOverlapArr2), list(trueOverlapArr2))


  def testComputeParametersValidation(self):
    sp = SpatialPooler(inputDimensions=[5], columnDimensions=[5])
    inputGood = np.ones(5, dtype=uintDType)
    outGood = np.zeros(5, dtype=uintDType)
    inputBad = np.ones(5, dtype=realDType)
    inputBad2D = np.ones((5, 5), dtype=realDType)
    outBad = np.zeros(5, dtype=realDType)
    outBad2D = np.zeros((5, 5), dtype=realDType)

    # Validate good parameters
    sp.compute(inputGood, False, outGood)

    # Validate bad parameters
    with self.assertRaises(RuntimeError):
      sp.compute(inputBad, False, outBad)

    # Validate bad input
    with self.assertRaises(RuntimeError):
      sp.compute(inputBad, False, outGood)

    # Validate bad 2d input
    with self.assertRaises(RuntimeError):
      sp.compute(inputBad2D, False, outGood)

    # Validate bad output
    with self.assertRaises(RuntimeError):
      sp.compute(inputGood, False, outBad)

    # Validate bad 2d output
    with self.assertRaises(RuntimeError):
      sp.compute(inputGood, False, outBad2D)


if __name__ == "__main__":
  unittest.main()
