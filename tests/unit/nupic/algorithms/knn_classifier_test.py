#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import unittest

import numpy as np

from nupic.algorithms.KNNClassifier import KNNClassifier



class KNNClassifierTest(unittest.TestCase):


  def testOverlapDistanceMethod_Standard(self):
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
    cat, inferenceResult, dist, categoryDist = classifier.infer(denseA)
    self.assertEquals(cat, 0)

    denseB = np.zeros(dimensionality)
    denseB[b] = 1.0
    cat, inferenceResult, dist, categoryDist = classifier.infer(denseB)
    self.assertEquals(cat, 1)


  def testOverlapDistanceMethod_BadSparsity(self):
    """Sparsity (input dimensionality) less than input array"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)

    # Learn with incorrect dimensionality, less than some bits (23, 29)
    with self.assertRaises(RuntimeError):
      classifier.learn(a, 0, isSparse=20)


  def testOverlapDistanceMethod_InconsistentSparsity(self):
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

    cat, inferenceResult, dist, categoryDist = classifier.infer(denseA)
    self.assertEquals(cat, 0)



  def testOverlapDistanceMethod_StandardUnsorted(self):
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


  def testOverlapDistanceMethod_EmptyArray(self):
    """Tests case where pattern has no ON bits"""
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    dimensionality = 40
    a = np.array([], dtype=np.int32)

    numPatterns = classifier.learn(a, 0, isSparse=dimensionality)
    self.assertEquals(numPatterns, 1)

    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0
    cat, inferenceResult, dist, categoryDist = classifier.infer(denseA)
    self.assertEquals(cat, 0)


  # def testOverlapDistanceMethod_ClassifySparse(self):
  #   params = {"distanceMethod": "rawOverlap"}
  #   classifier = KNNClassifier(**params)
  #
  #   dimensionality = 40
  #   a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=np.int32)
  #   b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=np.int32)
  #
  #   classifier.learn(a, 0, isSparse=dimensionality)
  #   classifier.learn(b, 1, isSparse=dimensionality)
  #
  #   # TODO detect and throw error
  #   cat, inferenceResult, dist, categoryDist = classifier.infer(a)
  #   self.assertEquals(cat, 0)
  #
  #   cat, inferenceResult, dist, categoryDist = classifier.infer(b)
  #   self.assertEquals(cat, 1)

  # winner: The category with the greatest number of nearest neighbors within
  #               the kth nearest neighbors
  # inferenceResult: A list of length numCategories, each entry contains the
  #               number of neighbors within the top K neighbors that are in that
  #               category
  # dist: A list of length numPrototypes. Each entry is the distance from
  #               the unknown to that prototype. All distances are between 0 and
  #               1.0
  # categoryDist: A list of length numCategories. Each entry is the distance
  #               from the unknown to the nearest prototype of that category. All
  #               distances are between 0 and 1.0.


if __name__ == "__main__":
  unittest.main()
