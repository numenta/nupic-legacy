#!/usr/bin/env python

# ----------------------------------------------------------------------
#  Copyright (C) 2007 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""
## @file
This file contains tests for the k Nearest Neighbor classifier.
"""
import sys
import numpy
import time
import cPickle
import random
from nupic.regions.PyRegion import RealNumpyDType
from nupic.bindings.math import NearestNeighbor
from nupic.algorithms.KNNClassifier import KNNClassifier

import pca_knn_data

#---------------------------------------------------------------------------------
def testKMoreThanOne():
  """A small test with k=3"""

  failures = ""
  print "Testing the sparse KNN Classifier with k=3"
  knn = KNNClassifier(k=3)

  v = numpy.zeros((6,2))
  v[0] = [1.0,0.0]
  v[1] = [1.0,0.2]
  v[2] = [1.0,0.2]
  v[3] = [1.0,2.0]
  v[4] = [1.0,4.0]
  v[5] = [1.0,4.5]
  knn.learn(v[0], 0)
  knn.learn(v[1], 0)
  knn.learn(v[2], 0)
  knn.learn(v[3], 1)
  knn.learn(v[4], 1)
  knn.learn(v[5], 1)

  winner, inferenceResult, dist, categoryDist = knn.infer(v[0])
  if winner != 0: failures += "Inference failed with k=3\n"

  winner, inferenceResult, dist, categoryDist = knn.infer(v[2])
  if winner != 0: failures += "Inference failed with k=3\n"

  winner, inferenceResult, dist, categoryDist = knn.infer(v[3])
  if winner != 0: failures += "Inference failed with k=3\n"

  winner, inferenceResult, dist, categoryDist = knn.infer(v[5])
  if winner != 1: failures += "Inference failed with k=3\n"

  if len(failures) == 0: print "Tests passed."
  return failures


#---------------------------------------------------------------------------------
def testClassifier(knn, patternDict, testName):
  """Train this classifier instance with the given patterns."""

  failures = ""
  numPatterns = len(patternDict)

  print "Training the classifier"
  tick = time.time()
  for i in patternDict.keys():
    knn.learn(patternDict[i]['pattern'], patternDict[i]['category'])
  tock = time.time()
  print "Time Elapsed", tock-tick
  knnString = cPickle.dumps(knn)
  print "Size of the classifier is", len(knnString)

  print "Testing the classifier on the training set"
  error_count = 0
  tick = time.time()
  print "Number of patterns: %s" % len(patternDict)
  for i in patternDict.keys():
    # print "Testing %s - %s %s" % (len(i), patternDict[i]['category'], len(patternDict[i]['pattern']))
    print "Testing %s - %s %s" % (i, patternDict[i]['category'], len(patternDict[i]['pattern']))
    winner, inferenceResult, dist, categoryDist \
      = knn.infer(patternDict[i]['pattern'])
    if winner != patternDict[i]['category']:
      error_count += 1
  tock = time.time()
  print "Time Elapsed", tock-tick

  error_rate = float(error_count)/numPatterns
  print "Error rate is ", error_rate

  if error_rate == 0:
    print testName + " passed"
  else:
    print testName + " failed"
    failures += testName + " failed\n"

  return failures


#---------------------------------------------------------------------------------
def getNumTestPatterns(short=0):
  """Return the number of patterns and classes the test should use."""

  if short==0:
    print "Running short tests"
    numPatterns = numpy.random.randint(300,600)
    numClasses = numpy.random.randint(50,150)
  elif short==1:
    print "\nRunning medium tests"
    numPatterns = numpy.random.randint(500,1500)
    numClasses = numpy.random.randint(50,150)
  else:
    print "\nRunning long tests"
    numPatterns = numpy.random.randint(500,3000)
    numClasses = numpy.random.randint(30,1000)

  print "number of patterns is", numPatterns
  print "number of classes is ", numClasses
  return numPatterns, numClasses


#---------------------------------------------------------------------------------
def testKNNClassifier(short = 0):
  """ Test the KNN classifier in this module. short can be:
      0 (short), 1 (medium), or 2 (long)
  """

  failures = ""
  if short != 2:
    numpy.random.seed(42)
  else:
    seed_value = int(time.time())
    # seed_value = 1276437656
    #seed_value = 1277136651
    numpy.random.seed(seed_value)
    print 'Seed used: %d' %seed_value
    f = open('seedval', 'a')
    f.write(str(seed_value))
    f.write('\n')
    f.close()
  failures += testKMoreThanOne()


  print "\nTesting KNN Classifier on dense patterns"
  numPatterns, numClasses = getNumTestPatterns(short)
  patterns = numpy.random.rand(numPatterns,100)
  patternDict = dict()

  # Assume there are no repeated patterns -- if there are, then
  # numpy.random would be completely broken.
  for i in xrange(numPatterns):
    randCategory = numpy.random.randint(0,numClasses-1)
    patternDict[i] = dict()
    patternDict[i]['pattern'] = patterns[i]
    patternDict[i]['category'] = randCategory

  # for i in patterns:
  #   iString = str(i.tolist())
  #   if not patternDict.has_key(iString):
  #     randCategory = numpy.random.randint(0,numClasses-1)
  #     patternDict[iString] = dict()
  #     patternDict[iString]['pattern'] = i
  #     patternDict[iString]['category'] = randCategory


  print "\nTesting KNN Classifier with L2 norm"

  knn = KNNClassifier(k=1)
  failures += testClassifier(knn, patternDict, "KNN Classifier with L2 norm test")


  return
  print "\nTesting KNN Classifier with L1 norm"

  knnL1 = KNNClassifier(k=1, distanceNorm=1.0)
  failures += testClassifier(knnL1, patternDict, "KNN Classifier with L1 norm test")


  numPatterns, numClasses = getNumTestPatterns(short)
  patterns = (numpy.random.rand(numPatterns,25) > 0.7).astype(RealNumpyDType)
  patternDict = dict()

  for i in patterns:
    iString = str(i.tolist())
    if not patternDict.has_key(iString):
      randCategory = numpy.random.randint(0,numClasses-1)
      patternDict[iString] = dict()
      patternDict[iString]['pattern'] = i
      patternDict[iString]['category'] = randCategory


  print "\nTesting KNN on sparse patterns"

  knnDense = KNNClassifier(k=1)
  failures += testClassifier(knnDense, patternDict, "KNN Classifier on sparse pattern test")

  if len(failures) != 0:
    raise Exception("Tests failed: \n" + failures)
  f = open('seedval', 'a')
  f.write('Pass\n')
  f.close()


#---------------------------------------------------------------------------------
def test_pca_knn(short = 0):

  print '\nTesting PCA/k-NN classifier'
  print 'Mode=', short,

  numDims = 10
  numClasses = 10
  k = 10
  numPatternsPerClass = 100
  numPatterns = int(.9 * numClasses * numPatternsPerClass)
  numTests = numClasses * numPatternsPerClass - numPatterns
  numSVDSamples = int(.1 * numPatterns)
  keep = 1

  train_data, train_class, test_data, test_class = \
      pca_knn_data.generate(numDims, numClasses, k, numPatternsPerClass,
                            numPatterns, numTests, numSVDSamples, keep)

  pca_knn = KNNClassifier(k=k,numSVDSamples=numSVDSamples,
                          numSVDDims=keep)

  knn = KNNClassifier(k=k)


  print 'Training PCA k-NN'

  for i in range(numPatterns):
    knn.learn(train_data[i], train_class[i])
    pca_knn.learn(train_data[i], train_class[i])


  print 'Testing PCA k-NN'

  numWinnerFailures = 0
  numInferenceFailures = 0
  numDistFailures = 0
  numAbsErrors = 0

  for i in range(numTests):

    winner, inference, dist, categoryDist = knn.infer(test_data[i])
    pca_winner, pca_inference, pca_dist, pca_categoryDist \
      = pca_knn.infer(test_data[i])

    if 0:
      print '>>', test_class[i], winner, pca_winner,
      if winner != test_class[i]:
        print 'k-NN wrong',
      if pca_winner != test_class[i]:
        print 'PCA/k-NN wrong',
      print

    if winner != test_class[i]:
      numAbsErrors += 1

    if pca_winner != winner:
      numWinnerFailures += 1

    if (numpy.abs(pca_inference - inference) > 1e-4).any():
      numInferenceFailures += 1

    if (numpy.abs(pca_dist - dist) > 1e-4).any():
      numDistFailures += 1

  s0 = 100*float(numTests - numAbsErrors) / float(numTests)
  s1 = 100*float(numTests - numWinnerFailures) / float(numTests)
  s2 = 100*float(numTests - numInferenceFailures) / float(numTests)
  s3 = 100*float(numTests - numDistFailures) / float(numTests)

  print 'PCA/k-NN success rate=', s0, '%'
  print 'Winner success=', s1, '%'
  print 'Inference success=', s2, '%'
  print 'Distance success=', s3, '%'

  if s1 != 100.0:
    raise Exception("PCA/k-NN test failed")
  else:
    print 'PCA/-kNN test passed'


#===============================================================================
# When invoked from command line, run the tests
#===============================================================================
if __name__ == '__main__':
  testKNNClassifier(0)
  test_pca_knn(0)
  testKNNClassifier(1)
  test_pca_knn(1)


#---------------------------------------------------------------------------------