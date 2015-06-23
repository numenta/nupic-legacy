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


  def setup(self):
    self.intDtype = np.int32


  def test1(self):
    params = {"distanceMethod": "rawOverlap"}
    classifier = KNNClassifier(**params)

    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=self.intDtype)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=self.intDtype)
    dimensionality = 40

    patterns = classifier.learn(a, 0, isSparse=dimensionality)
    print "{0} stored patterns".format(patterns)

    patterns = classifier.learn(b, 1, isSparse=dimensionality)

    # self.assertEquals(len(result), 1)
    # self.assertEquals(result[0], 4)


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


def main(self):
    params = {"k": 1,
              "distanceMethod": "rawOverlap",
              "distThreshold": 0.01,
              "verbosity": 0}
    classifier = KNNClassifier(**params)

    intDType = np.int32
    a = np.array([1, 3, 7, 11, 13, 17, 19, 23, 29], dtype=intDType)
    b = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30], dtype=intDType)
    # c = np.array([2, 4, 8, 12, 14, 18, 20, 28, 30]).astype(intDType)

    dimensionality = 40

    print "\nLearn {0} is {1}".format(a, 0)
    patterns = classifier.learn(a, 0, isSparse=dimensionality)
    print "{0} stored patterns".format(patterns)

    print "\nLearn {0} is {1}".format(b, 1)
    patterns = classifier.learn(b, 1, isSparse=dimensionality)
    print "{0} stored patterns".format(patterns)

    print "\nExample classifications"
    denseA = np.zeros(dimensionality)
    denseA[a] = 1.0

    denseB = np.zeros(dimensionality)
    denseB[b] = 1.0

    self.classifyAndPrint(classifier, denseA)
    self.classifyAndPrint(classifier, denseB)



def classifyAndPrint(self, classifier, pattern):
    winningCategory, inferenceResult, dist, categoryDist = classifier.infer(
      pattern)
    print ("\nPattern: {0}\nWinner: {1}\ninferenceResult: {1}\ndist: "
           "{1}\ncategoryDist: {1}\n").format(pattern, winningCategory,
                                            inferenceResult, dist, categoryDist)


if __name__ == "__main__":
  unittest.main()
