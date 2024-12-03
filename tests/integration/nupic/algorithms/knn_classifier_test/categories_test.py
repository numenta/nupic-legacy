# Copyright 2014 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import logging
import unittest2 as unittest

import numpy

from nupic.algorithms.knn_classifier import KNNClassifier

LOGGER = logging.getLogger(__name__)



class KNNCategoriesTest(unittest.TestCase):
  """Tests how k Nearest Neighbor classifier handles categories"""


  def testCategories(self):
    # We need determinism!
    #
    # "Life is like a game of cards. The hand you are dealt is determinism; the
    # way you play it is free will." Jawaharlal Nehru
    #
    # What the heck, let's just set the random seed
    numpy.random.seed(42)

    failures, _knn = simulateCategories()

    self.assertEqual(len(failures), 0,
                     "Tests failed: \n" + failures)



def simulateCategories(numSamples=100, numDimensions=500):
  """Simulate running KNN classifier on many disjoint categories"""

  failures = ""
  LOGGER.info("Testing the sparse KNN Classifier on many disjoint categories")
  knn = KNNClassifier(k=1, distanceNorm=1.0, useSparseMemory=True)

  for i in range(0, numSamples):

    # select category randomly and generate vector
    c = 2*numpy.random.randint(0, 50) + 50
    v = createPattern(c, numDimensions)
    knn.learn(v, c)

  # Go through each category and ensure we have at least one from each!
  for i in range(0, 50):
    c = 2*i+50
    v = createPattern(c, numDimensions)
    knn.learn(v, c)

  errors = 0
  for i in range(0, numSamples):

    # select category randomly and generate vector
    c = 2*numpy.random.randint(0, 50) + 50
    v = createPattern(c, numDimensions)

    inferCat, _kir, _kd, _kcd = knn.infer(v)
    if inferCat != c:
      LOGGER.info("Mistake with %s %s %s %s %s", v[v.nonzero()], \
        "mapped to category", inferCat, "instead of category", c)
      LOGGER.info("   %s", v.nonzero())
      errors += 1
  if errors != 0:
    failures += "Failure in handling non-consecutive category indices\n"

  # Test closest methods
  errors = 0
  for i in range(0, 10):

    # select category randomly and generate vector
    c = 2*numpy.random.randint(0, 50) + 50
    v = createPattern(c, numDimensions)

    p = knn.closestTrainingPattern(v, c)
    if not (c in p.nonzero()[0]):
      LOGGER.info("Mistake %s %s", p.nonzero(), v.nonzero())
      LOGGER.info("%s %s", p[p.nonzero()], v[v.nonzero()])
      errors += 1

  if errors != 0:
    failures += "Failure in closestTrainingPattern method\n"

  return failures, knn


def createPattern(c, numDimensions):
  """
  Create a sparse pattern from category c with the given number of dimensions.
  The pattern is created by setting element c to be a high random number.
  Element c-1 and c+1 are set to low random numbers. numDimensions must be > c.
  """

  v = numpy.zeros(numDimensions)
  v[c] = 5*numpy.random.random() + 10
  v[c+1] = numpy.random.random()
  if c > 0:
    v[c-1] = numpy.random.random()
  return v



if __name__ == "__main__":
  unittest.main()
