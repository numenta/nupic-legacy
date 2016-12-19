# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for the SVM classifiers."""

import cPickle as pickle
import hashlib
import os

import numpy as np
import unittest2 as unittest

from nupic.bindings.algorithms import svm_dense, svm_01
from nupic.bindings.math import GetNumpyDataType

_SEED = 42
_RGEN = np.random.RandomState(_SEED)
# 32 bits for sse
_DTYPE = GetNumpyDataType("NTA_Real")


class SVMTest(unittest.TestCase):
  """Unit tests for the SVM classifier."""


  def testGetstateSetstate(self):
    nDims = 32 # need multiple of 8, because of sse
    nClass = 4
    size = 20
    labels = _RGEN.random_integers(0, nClass - 1, size)
    samples = np.zeros((size, nDims), dtype=_DTYPE)

    centers = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])

    for i in range(0, size):
      t = 6.28 * _RGEN.random_sample()
      samples[i][0] = 2 * centers[labels[i]][0] + 0.5*_RGEN.rand() * np.cos(t)
      samples[i][1] = 2 * centers[labels[i]][1] + 0.5*_RGEN.rand() * np.sin(t)

    classifier = svm_dense(0, nDims, seed=_SEED, probability = True)

    for y, xList in zip(labels, samples):
      x = np.array(xList, dtype=_DTYPE)
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

    with open("svm_test.bin", "wb") as f:
      pickle.dump(classifier, f)
    with open("svm_test.bin", "rb") as f:
      classifier3 = pickle.load(f)
    s3 = classifier3.__getstate__()
    h3 = hashlib.md5(s3).hexdigest()

    self.assertEqual(h1, h3)

    os.unlink("svm_test.bin")


  def testPersistentSize(self):
    for _ in range(2):
      # Multiple of 8 because of sse.
      nDims = 32

      nClass = _RGEN.randint(4, 8)
      size = _RGEN.randint(20, 50)
      labels = _RGEN.random_integers(0, nClass - 1, size)
      samples = _RGEN.normal(size=(size, nDims)).astype(_DTYPE)

      classifier = svm_dense(0, nDims, seed=_SEED, probability=True)

      for y, xList in zip(labels, samples):
        x = np.array(xList, dtype=_DTYPE)
        classifier.add_sample(float(y), x)

      classifier.train(gamma=1.0/3.0, C=100, eps=1e-1)
      classifier.cross_validate(2, gamma=0.5, C=10, eps=1e-3)

      s = classifier.__getstate__()
      print "nDims=", nDims, "nClass=", nClass, "n_vectors=", size,
      print "dense:", len(s), classifier.persistent_size(),
      self.assertEqual(len(s), classifier.persistent_size())

      classifier01 = svm_01(0, nDims, seed=_SEED, probability=True)

      for y, xList in zip(labels, samples):
        x = np.array(xList, dtype=_DTYPE)
        classifier01.add_sample(float(y), x)

      classifier01.train(gamma=1.0/3.0, C=100, eps=1e-1)
      classifier01.cross_validate(2, gamma=0.5, C=10, eps=1e-3)

      s = classifier01.__getstate__()
      print "0/1", len(s), classifier01.persistent_size()
      self.assertEqual(len(s), classifier01.persistent_size())


  # TODO: Add appropriate assertions and re-enable this test.
  @unittest.skip("Legacy test that is out of date.")
  def testScalability(self):
    # Multiple of 8 for sse.
    nDims = 32
    nClass = 3
    size = 1000
    labels = _RGEN.random_integers(0, nClass - 1, size)
    samples = np.random.random(size=(size, nDims)).astype(_DTYPE)

    classifier = svm_dense(0, nDims, seed=_SEED)

    for y, xList in zip(labels, samples):
      x = np.array(xList, dtype=_DTYPE)
      classifier.add_sample(float(y), x)

    print "training"
    classifier.train(gamma=1.0/3.0, C=100, eps=1e-1)

    print "cross validation"
    classifier.cross_validate(2, gamma=0.5, C=10, eps=1e-3)



if __name__ == "__main__":
  unittest.main()
