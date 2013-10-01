#!/usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2009, 2012 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""Unit tests for the SVM classifiers."""

import cPickle as pickle
import hashlib
import os
import unittest2 as unittest

import numpy as np

from nupic.bindings.math import GetNumpyDataType
from nupic.bindings.algorithms import svm_dense, svm_01
from nupic.support.unittesthelpers.testcasebase import (TestCaseBase,
                                                        TestOptionParser)


class SVMTest(TestCaseBase):
  """Unit tests for the SVM classifier."""

  def testGetstateSetstate(self):
    nDims = 32 # need multiple of 8, because of sse
    nClass = 4
    size = 20
    labels = rgen.random_integers(0, nClass - 1, size)
    samples = np.zeros((size, nDims), dtype=dType)

    centers = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])

    for i in range(0, size):
      t = 6.28 * rgen.random_sample()
      samples[i][0] = 2 * centers[labels[i]][0] + 0.5*rgen.rand() * np.cos(t)
      samples[i][1] = 2 * centers[labels[i]][1] + 0.5*rgen.rand() * np.sin(t)

    classifier = svm_dense(0, nDims, seed=SEED, probability = True)

    for y, xList in zip(labels, samples):
      x = np.array(xList, dtype=dType)
      classifier.add_sample(float(y), x)

    classifier.train(gamma=1.0/3.0, C=100, eps=1e-1)
    classifier.cross_validate(2, gamma=0.5, C=10, eps=1e-3)

    s1 = classifier.__getstate__()
    h1 = hashlib.md5(s1).hexdigest()

    classifier2 = svm_dense(0, nDims)
    classifier2.__setstate__(s1)
    s2 = classifier2.__getstate__()
    h2 = hashlib.md5(s2).hexdigest()

    self.assertEqual(h1, h2)

    with open('svm_test.bin', 'wb') as f:
      pickle.dump(classifier, f)
    with open('svm_test.bin', 'rb') as f:
      classifier3 = pickle.load(f)
    s3 = classifier3.__getstate__()
    h3 = hashlib.md5(s3).hexdigest()

    self.assertEqual(h1, h3)

    os.unlink('svm_test.bin')

  def testPersistentSize(self):
    for _ in range(2):
      # Multiple of 8 because of sse.
      nDims = 32

      nClass = rgen.randint(4, 8)
      size = rgen.randint(20, 50)
      labels = rgen.random_integers(0, nClass - 1, size)
      samples = rgen.normal(size=(size, nDims)).astype(dType)

      classifier = svm_dense(0, nDims, seed=SEED, probability=True)

      for y, xList in zip(labels, samples):
        x = np.array(xList, dtype=dType)
        classifier.add_sample(float(y), x)

      classifier.train(gamma=1.0/3.0, C=100, eps=1e-1)
      classifier.cross_validate(2, gamma=0.5, C=10, eps=1e-3)

      s = classifier.__getstate__()
      print 'nDims=', nDims, 'nClass=', nClass, 'n_vectors=', size,
      print 'dense:', len(s), classifier.persistent_size(),
      self.assertEqual(len(s), classifier.persistent_size())

      classifier01 = svm_01(0, nDims, seed=SEED, probability=True)

      for y, xList in zip(labels, samples):
        x = np.array(xList, dtype=dType)
        classifier01.add_sample(float(y), x)

      classifier01.train(gamma=1.0/3.0, C=100, eps=1e-1)
      classifier01.cross_validate(2, gamma=0.5, C=10, eps=1e-3)

      s = classifier01.__getstate__()
      print '0/1', len(s), classifier01.persistent_size()
      self.assertEqual(len(s), classifier01.persistent_size())

  # TODO: Add appropriate assertions and re-enable this test.
  @unittest.skip('Legacy test that is out of date.')
  def testScalability(self):
    # Multiple of 8 for sse.
    nDims = 32
    nClass = 3
    size = 1000
    labels = rgen.random_integers(0, nClass - 1, size)
    samples = np.random.random(size=(size, nDims)).astype(dType)

    classifier = svm_dense(0, nDims, seed=SEED)

    for y, xList in zip(labels, samples):
      x = np.array(xList, dtype=dType)
      classifier.add_sample(float(y), x)

    print 'training'
    classifier.train(gamma=1.0/3.0, C=100, eps=1e-1)

    print 'cross validation'
    classifier.cross_validate(2, gamma=0.5, C=10, eps=1e-3)


if __name__ == '__main__':
  parser = TestOptionParser()
  options, _ = parser.parse_args()

  rgen = np.random.RandomState(options.seed)
  SEED = options.seed

  # 32 bits for sse
  dType = GetNumpyDataType('NTA_Real')

  unittest.main()