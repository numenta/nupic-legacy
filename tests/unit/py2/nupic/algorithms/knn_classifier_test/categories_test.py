#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

"""
## @file
This file contains a test of how k Nearest Neighbor classifier handles
categories.
"""
import sys
import numpy
from nupic.algorithms.KNNClassifier import KNNClassifier

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

#---------------------------------------------------------------------------------
def testCategories(numSamples = 100, numDimensions = 500):
  """A small test """

  failures = ""
  print "Testing the sparse KNN Classifier on many disjoint categories"
  knn = KNNClassifier(k=1, distanceNorm=1.0, useSparseMemory = True)

  for i in range(0,numSamples):

    # select category randomly and generate vector
    c = 2*numpy.random.randint(0,50) + 50
    v = createPattern(c, numDimensions)
    knn.learn(v, c)

  # Go through each category and ensure we have at least one from each!
  for i in range(0,50):
    c = 2*i+50
    v = createPattern(c, numDimensions)
    knn.learn(v, c)

  errors = 0
  for i in range(0,numSamples):

    # select category randomly and generate vector
    c = 2*numpy.random.randint(0,50) + 50
    v = createPattern(c, numDimensions)

    inferCat, kir, kd, kcd = knn.infer(v)
    if inferCat != c:
      print "Mistake with",v[v.nonzero()],"mapped to category",inferCat,\
            "instead of category",c
      print "   ",v.nonzero()
      errors += 1
  if errors != 0:
    failures += "Failure in handling non-consecutive category indices\n"

  # Test closest methods
  errors = 0
  for i in range(0,10):

    # select category randomly and generate vector
    c = 2*numpy.random.randint(0,50) + 50
    v = createPattern(c, numDimensions)

    p = knn.closestTrainingPattern(v,c)
    if not (c in p.nonzero()[0]):
      print "Mistake",p.nonzero(), v.nonzero()
      print p[p.nonzero()], v[v.nonzero()]
      errors += 1

  if errors != 0:
    failures += "Failure in closestTrainingPattern method\n"

  return failures,knn

#===============================================================================
# When invoked from command line, run the tests
#===============================================================================
if __name__ == '__main__':

  # We need determinism!
  #
  # "Life is like a game of cards. The hand you are dealt is determinism; the
  # way you play it is free will." Jawaharlal Nehru
  #
  # What the heck, let's just set the random seed
  numpy.random.seed(42)

  if len(sys.argv)==2 and sys.argv[1]=="--long":
    failures,knn = testCategories(10000,10000)
  else:
    failures,knn = testCategories()

  if len(failures) != 0:
    raise Exception("Tests failed: \n" + failures)
  else: print "Tests passed."


#---------------------------------------------------------------------------------