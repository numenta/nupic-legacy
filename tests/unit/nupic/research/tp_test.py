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

"""Tests for the Python implementation of the temporal pooler."""

import csv
import cPickle as pickle
import itertools
import os
import random
import shutil
import tempfile
import unittest2 as unittest

import numpy
from pkg_resources import resource_filename

from nupic.research import fdrutilities
from nupic.research.TP import TP

COL_SET = set(range(500))

VERBOSITY = 0



class TPTest(unittest.TestCase):
  """Unit tests for the TP class."""


  def setUp(self):
    self._tmpDir = tempfile.mkdtemp()


  def tearDown(self):
    shutil.rmtree(self._tmpDir)

  
  def testInitDefaultTP(self):
    self.assertTrue(isinstance(TP(), TP))


  def testCheckpointLearned(self):
    # Create a model and give it some inputs to learn.
    tp1 = TP(numberOfCols=100, cellsPerColumn=12, verbosity=VERBOSITY)
    sequences = [self.generateSequence() for _ in xrange(5)]
    train = list(itertools.chain.from_iterable(sequences[:3]))
    for bottomUpInput in train:
      if bottomUpInput is None:
        tp1.reset()
      else:
        tp1.compute(bottomUpInput, True, True)

    # Serialize and deserialized the TP.
    checkpointPath = os.path.join(self._tmpDir, 'a')
    tp1.saveToFile(checkpointPath)
    tp2 = pickle.loads(pickle.dumps(tp1))
    tp2.loadFromFile(checkpointPath)

    # Check that the TPs are the same.
    self.assertTPsEqual(tp1, tp2)

    # Feed some data into the models.
    test = list(itertools.chain.from_iterable(sequences[3:]))
    for bottomUpInput in test:
      if bottomUpInput is None:
        tp1.reset()
        tp2.reset()
      else:
        result1 = tp1.compute(bottomUpInput, True, True)
        result2 = tp2.compute(bottomUpInput, True, True)

        self.assertTPsEqual(tp1, tp2)
        self.assertTrue(numpy.array_equal(result1, result2))


  def testCheckpointMiddleOfSequence(self):
    # Create a model and give it some inputs to learn.
    tp1 = TP(numberOfCols=100, cellsPerColumn=12, verbosity=VERBOSITY)
    sequences = [self.generateSequence() for _ in xrange(5)]
    train = list(itertools.chain.from_iterable(sequences[:3] +
                                               [sequences[3][:5]]))
    for bottomUpInput in train:
      if bottomUpInput is None:
        tp1.reset()
      else:
        tp1.compute(bottomUpInput, True, True)

    # Serialize and deserialized the TP.
    checkpointPath = os.path.join(self._tmpDir, 'a')
    tp1.saveToFile(checkpointPath)
    tp2 = pickle.loads(pickle.dumps(tp1))
    tp2.loadFromFile(checkpointPath)

    # Check that the TPs are the same.
    self.assertTPsEqual(tp1, tp2)

    # Feed some data into the models.
    test = list(itertools.chain.from_iterable([sequences[3][5:]] +
                                              sequences[3:]))
    for bottomUpInput in test:
      if bottomUpInput is None:
        tp1.reset()
        tp2.reset()
      else:
        result1 = tp1.compute(bottomUpInput, True, True)
        result2 = tp2.compute(bottomUpInput, True, True)

        self.assertTPsEqual(tp1, tp2)
        self.assertTrue(numpy.array_equal(result1, result2))


  def testCheckpointMiddleOfSequence2(self):
    """More complex test of checkpointing in the middle of a sequence."""
    tp1 = TP(2048, 32, 0.21, 0.5, 11, 20, 0.1, 0.1, 1.0, 0.0, 14, False, 5, 2,
             False, 1960, 0, False, 3, 10, 5, 0, 32, 128, 32, 'normal')
    tp2 = TP(2048, 32, 0.21, 0.5, 11, 20, 0.1, 0.1, 1.0, 0.0, 14, False, 5, 2,
             False, 1960, 0, False, 3, 10, 5, 0, 32, 128, 32, 'normal')

    with open(resource_filename(__name__, 'data/tp_input.csv'), 'r') as fin:
      reader = csv.reader(fin)
      records = []
      for bottomUpInStr in fin:
        bottomUpIn = numpy.array(eval('[' + bottomUpInStr.strip() + ']'),
                                 dtype='int32')
        records.append(bottomUpIn)

    i = 1
    for r in records[:250]:
      print i
      i += 1
      output1 = tp1.compute(r, True, True)
      output2 = tp2.compute(r, True, True)
      self.assertTrue(numpy.array_equal(output1, output2))

    print 'Serializing and deserializing models.'

    savePath1 = os.path.join(self._tmpDir, 'tp1.bin')
    tp1.saveToFile(savePath1)
    tp3 = pickle.loads(pickle.dumps(tp1))
    tp3.loadFromFile(savePath1)

    savePath2 = os.path.join(self._tmpDir, 'tp2.bin')
    tp2.saveToFile(savePath2)
    tp4 = pickle.loads(pickle.dumps(tp2))
    tp4.loadFromFile(savePath2)

    self.assertTPsEqual(tp1, tp3)
    self.assertTPsEqual(tp2, tp4)

    for r in records[250:]:
      print i
      i += 1
      out1 = tp1.compute(r, True, True)
      out2 = tp2.compute(r, True, True)
      out3 = tp3.compute(r, True, True)
      out4 = tp4.compute(r, True, True)

      self.assertTrue(numpy.array_equal(out1, out2))
      self.assertTrue(numpy.array_equal(out1, out3))
      self.assertTrue(numpy.array_equal(out1, out4))

    self.assertTPsEqual(tp1, tp2)
    self.assertTPsEqual(tp1, tp3)
    self.assertTPsEqual(tp2, tp4)


  def assertTPsEqual(self, tp1, tp2):
    """Asserts that two TP instances are the same.

    This is temporarily disabled since it does not work with the C++
    implementation of the TP.
    """
    self.assertEqual(tp1, tp2, tp1.diff(tp2))
    self.assertTrue(fdrutilities.tpDiff2(tp1, tp2, 1, False))


  @staticmethod
  def generateSequence(n=10, numCols=100, minOnes=21, maxOnes=25):
    """Generates a sequence of n patterns."""
    return [None] + [TPTest.generatePattern(numCols, minOnes, maxOnes)
                     for _ in xrange(n)]


  @staticmethod
  def generatePattern(numCols=100, minOnes=21, maxOnes=25):
    """Generate a single test pattern with given parameters.

    Parameters:
      numCols: Number of columns in each pattern.
      minOnes: The minimum number of 1's in each pattern.
      maxOnes: The maximum number of 1's in each pattern.
    """
    assert minOnes < maxOnes
    assert maxOnes < numCols

    nOnes = random.randint(minOnes, maxOnes)
    ind = random.sample(xrange(numCols), nOnes)
    x = numpy.zeros(numCols, dtype='float32')
    x[ind] = 1

    return x


if __name__ == '__main__':
  unittest.main()
