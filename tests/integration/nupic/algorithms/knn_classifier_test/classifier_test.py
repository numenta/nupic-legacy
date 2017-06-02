# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import copy
import logging
import time
import unittest2 as unittest

import cPickle
import numpy

from nupic.bindings.regions.PyRegion import RealNumpyDType
from nupic.algorithms.knn_classifier import KNNClassifier

import pca_knn_data

LOGGER = logging.getLogger(__name__)



class KNNClassifierTest(unittest.TestCase):
  """Tests for k Nearest Neighbor classifier"""


  def runTestKNNClassifier(self, short = 0):
    """ Test the KNN classifier in this module. short can be:
        0 (short), 1 (medium), or 2 (long)
    """

    failures = ""
    if short != 2:
      numpy.random.seed(42)
    else:
      seed_value = int(time.time())
      numpy.random.seed(seed_value)
      LOGGER.info('Seed used: %d', seed_value)
      f = open('seedval', 'a')
      f.write(str(seed_value))
      f.write('\n')
      f.close()
    failures += simulateKMoreThanOne()

    LOGGER.info("\nTesting KNN Classifier on dense patterns")
    numPatterns, numClasses = getNumTestPatterns(short)
    patternSize = 100
    patterns = numpy.random.rand(numPatterns, patternSize)
    patternDict = dict()
    testDict = dict()

    # Assume there are no repeated patterns -- if there are, then
    # numpy.random would be completely broken.
    # Patterns in testDict are identical to those in patternDict but for the
    # first 2% of items.
    for i in xrange(numPatterns):
      patternDict[i] = dict()
      patternDict[i]['pattern'] = patterns[i]
      patternDict[i]['category'] = numpy.random.randint(0, numClasses-1)
      testDict[i] = copy.deepcopy(patternDict[i])
      testDict[i]['pattern'][:int(0.02*patternSize)] = numpy.random.rand()
      testDict[i]['category'] = None

    LOGGER.info("\nTesting KNN Classifier with L2 norm")

    knn = KNNClassifier(k=1)
    failures += simulateClassifier(knn, patternDict, \
      "KNN Classifier with L2 norm test")

    LOGGER.info("\nTesting KNN Classifier with L1 norm")

    knnL1 = KNNClassifier(k=1, distanceNorm=1.0)
    failures += simulateClassifier(knnL1, patternDict, \
      "KNN Classifier with L1 norm test")

    # Test with exact matching classifications.
    LOGGER.info("\nTesting KNN Classifier with exact matching. For testing we "
      "slightly alter the training data and expect None to be returned for the "
      "classifications.")
    knnExact = KNNClassifier(k=1, exact=True)
    failures += simulateClassifier(knnExact,
                                   patternDict,
                                   "KNN Classifier with exact matching test",
                                   testDict=testDict)

    numPatterns, numClasses = getNumTestPatterns(short)
    patterns = (numpy.random.rand(numPatterns, 25) > 0.7).astype(RealNumpyDType)
    patternDict = dict()

    for i in patterns:
      iString = str(i.tolist())
      if not patternDict.has_key(iString):
        randCategory = numpy.random.randint(0, numClasses-1)
        patternDict[iString] = dict()
        patternDict[iString]['pattern'] = i
        patternDict[iString]['category'] = randCategory

    LOGGER.info("\nTesting KNN on sparse patterns")

    knnDense = KNNClassifier(k=1)
    failures += simulateClassifier(knnDense, patternDict, \
      "KNN Classifier on sparse pattern test")

    self.assertEqual(len(failures), 0,
      "Tests failed: \n" + failures)

    if short == 2:
      f = open('seedval', 'a')
      f.write('Pass\n')
      f.close()


  def runTestPCAKNN(self, short = 0):

    LOGGER.info('\nTesting PCA/k-NN classifier')
    LOGGER.info('Mode=%s', short)

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


    LOGGER.info('Training PCA k-NN')

    for i in range(numPatterns):
      knn.learn(train_data[i], train_class[i])
      pca_knn.learn(train_data[i], train_class[i])


    LOGGER.info('Testing PCA k-NN')

    numWinnerFailures = 0
    numInferenceFailures = 0
    numDistFailures = 0
    numAbsErrors = 0

    for i in range(numTests):

      winner, inference, dist, categoryDist = knn.infer(test_data[i])
      pca_winner, pca_inference, pca_dist, pca_categoryDist \
        = pca_knn.infer(test_data[i])

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

    LOGGER.info('PCA/k-NN success rate=%s%s', s0, '%')
    LOGGER.info('Winner success=%s%s', s1, '%')
    LOGGER.info('Inference success=%s%s', s2, '%')
    LOGGER.info('Distance success=%s%s', s3, '%')

    self.assertEqual(s1, 100.0,
      "PCA/k-NN test failed")


  def testKNNClassifierShort(self):
    self.runTestKNNClassifier(0)


  def testPCAKNNShort(self):
    self.runTestPCAKNN(0)


  def testKNNClassifierMedium(self):
    self.runTestKNNClassifier(1)


  def testPCAKNNMedium(self):
    self.runTestPCAKNN(1)


def simulateKMoreThanOne():
  """A small test with k=3"""

  failures = ""
  LOGGER.info("Testing the sparse KNN Classifier with k=3")
  knn = KNNClassifier(k=3)

  v = numpy.zeros((6, 2))
  v[0] = [1.0, 0.0]
  v[1] = [1.0, 0.2]
  v[2] = [1.0, 0.2]
  v[3] = [1.0, 2.0]
  v[4] = [1.0, 4.0]
  v[5] = [1.0, 4.5]
  knn.learn(v[0], 0)
  knn.learn(v[1], 0)
  knn.learn(v[2], 0)
  knn.learn(v[3], 1)
  knn.learn(v[4], 1)
  knn.learn(v[5], 1)

  winner, _inferenceResult, _dist, _categoryDist = knn.infer(v[0])
  if winner != 0:
    failures += "Inference failed with k=3\n"

  winner, _inferenceResult, _dist, _categoryDist = knn.infer(v[2])
  if winner != 0:
    failures += "Inference failed with k=3\n"

  winner, _inferenceResult, _dist, _categoryDist = knn.infer(v[3])
  if winner != 0:
    failures += "Inference failed with k=3\n"

  winner, _inferenceResult, _dist, _categoryDist = knn.infer(v[5])
  if winner != 1:
    failures += "Inference failed with k=3\n"

  if len(failures) == 0:
    LOGGER.info("Tests passed.")

  return failures


def simulateClassifier(knn, patternDict, testName, testDict=None):
  """Train this classifier instance with the given patterns."""

  failures = ""
  numPatterns = len(patternDict)

  LOGGER.info("Training the classifier")
  tick = time.time()
  for i in patternDict.keys():
    knn.learn(patternDict[i]['pattern'], patternDict[i]['category'])
  tock = time.time()
  LOGGER.info("Time Elapsed %s", tock-tick)
  knnString = cPickle.dumps(knn)
  LOGGER.info("Size of the classifier is %s", len(knnString))

  # Run the classifier to infer categories on either the training data, or the
  # test data (of it's provided).
  error_count = 0
  tick = time.time()
  if testDict:
    LOGGER.info("Testing the classifier on the test set")
    for i in testDict.keys():
      winner, _inferenceResult, _dist, _categoryDist \
        = knn.infer(testDict[i]['pattern'])
      if winner != testDict[i]['category']:
        error_count += 1
  else:
    LOGGER.info("Testing the classifier on the training set")
    LOGGER.info("Number of patterns: %s", len(patternDict))
    for i in patternDict.keys():
      LOGGER.info("Testing %s - %s %s", i, patternDict[i]['category'], \
        len(patternDict[i]['pattern']))
      winner, _inferenceResult, _dist, _categoryDist \
        = knn.infer(patternDict[i]['pattern'])
      if winner != patternDict[i]['category']:
        error_count += 1
  tock = time.time()
  LOGGER.info("Time Elapsed %s", tock-tick)

  error_rate = float(error_count) / numPatterns
  LOGGER.info("Error rate is %s", error_rate)

  if error_rate == 0:
    LOGGER.info(testName + " passed")
  else:
    LOGGER.info(testName + " failed")
    failures += testName + " failed\n"

  return failures


def getNumTestPatterns(short=0):
  """Return the number of patterns and classes the test should use."""

  if short==0:
    LOGGER.info("Running short tests")
    numPatterns = numpy.random.randint(300, 600)
    numClasses = numpy.random.randint(50, 150)
  elif short==1:
    LOGGER.info("\nRunning medium tests")
    numPatterns = numpy.random.randint(500, 1500)
    numClasses = numpy.random.randint(50, 150)
  else:
    LOGGER.info("\nRunning long tests")
    numPatterns = numpy.random.randint(500, 3000)
    numClasses = numpy.random.randint(30, 1000)

  LOGGER.info("number of patterns is %s", numPatterns)
  LOGGER.info("number of classes is %s", numClasses)
  return numPatterns, numClasses



if __name__ == "__main__":
  unittest.main()
