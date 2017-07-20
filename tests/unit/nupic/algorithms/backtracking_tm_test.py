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

"""Tests for the Python implementation of the temporal memory."""

import cPickle as pickle
import csv
import itertools
import numpy
import os
import random
import shutil
import tempfile
import unittest2 as unittest

try:
  import capnp
except ImportError:
  capnp = None
from pkg_resources import resource_filename

from nupic.algorithms import fdrutilities
from nupic.algorithms.backtracking_tm import BacktrackingTM

COL_SET = set(range(500))

VERBOSITY = 0



class BacktrackingTMTest(unittest.TestCase):
  """Unit tests for the TM class."""


  def setUp(self):
    self._tmpDir = tempfile.mkdtemp()


  def tearDown(self):
    shutil.rmtree(self._tmpDir)


  def testInitDefaultTM(self):
    self.assertTrue(isinstance(BacktrackingTM(), BacktrackingTM))


  @unittest.skipUnless(capnp, "pycapnp not installed")
  def testSerializationLearned(self):
    # Create a model and give it some inputs to learn.
    tm1 = BacktrackingTM(numberOfCols=100, cellsPerColumn=12,
                         verbosity=VERBOSITY)
    sequences = [self.generateSequence() for _ in xrange(5)]
    train = list(itertools.chain.from_iterable(sequences[:3]))
    for bottomUpInput in train:
      if bottomUpInput is None:
        tm1.reset()
      else:
        tm1.compute(bottomUpInput, True, True)

    # Serialize and deserialized the TM.
    tmProto = BacktrackingTM.getSchema().new_message()
    tm1.write(tmProto)
    checkpointPath = os.path.join(self._tmpDir, 'a')
    with open(checkpointPath, "wb") as f:
      tmProto.write(f)
    with open(checkpointPath, "rb") as f:
      tmProto = BacktrackingTM.getSchema().read(f)
    tm2 = BacktrackingTM.read(tmProto)

    # Check that the TMs are the same.
    self.assertTMsEqual(tm1, tm2)

    # Feed some data into the models.
    test = list(itertools.chain.from_iterable(sequences[3:]))
    for bottomUpInput in test:
      if bottomUpInput is None:
        tm1.reset()
        tm2.reset()
      else:
        result1 = tm1.compute(bottomUpInput, True, True)
        result2 = tm2.compute(bottomUpInput, True, True)

        self.assertTMsEqual(tm1, tm2)
        self.assertTrue(numpy.array_equal(result1, result2))


  @unittest.skipUnless(capnp, "pycapnp not installed")
  def testSerializationMiddleOfSequence(self):
    # Create a model and give it some inputs to learn.
    tm1 = BacktrackingTM(numberOfCols=100, cellsPerColumn=12,
                         verbosity=VERBOSITY)
    sequences = [self.generateSequence() for _ in xrange(5)]
    train = list(itertools.chain.from_iterable(sequences[:3] +
                                               [sequences[3][:5]]))
    for bottomUpInput in train:
      if bottomUpInput is None:
        tm1.reset()
      else:
        tm1.compute(bottomUpInput, True, True)

    # Serialize and deserialized the TM.
    tmProto = BacktrackingTM.getSchema().new_message()
    tm1.write(tmProto)
    checkpointPath = os.path.join(self._tmpDir, 'a')
    with open(checkpointPath, "wb") as f:
      tmProto.write(f)
    with open(checkpointPath, "rb") as f:
      tmProto = BacktrackingTM.getSchema().read(f)
    tm2 = BacktrackingTM.read(tmProto)

    # Check that the TMs are the same.
    self.assertTMsEqual(tm1, tm2)

    # Feed some data into the models.
    test = list(itertools.chain.from_iterable([sequences[3][5:]] +
                                              sequences[3:]))
    for bottomUpInput in test:
      if bottomUpInput is None:
        tm1.reset()
        tm2.reset()
      else:
        result1 = tm1.compute(bottomUpInput, True, True)
        result2 = tm2.compute(bottomUpInput, True, True)

        self.assertTMsEqual(tm1, tm2)
        self.assertTrue(numpy.array_equal(result1, result2))


  @unittest.skipUnless(capnp, "pycapnp not installed")
  def testSerializationMiddleOfSequence2(self):
    """More complex test of checkpointing in the middle of a sequence."""
    tm1 = BacktrackingTM(2048, 32, 0.21, 0.5, 11, 20, 0.1, 0.1, 1.0, 0.0, 14,
                         False, 5, 2, False, 1960, 0, False, 3, 10, 5, 0, 32,
                         128, 32, 'normal')
    tm2 = BacktrackingTM(2048, 32, 0.21, 0.5, 11, 20, 0.1, 0.1, 1.0, 0.0, 14,
                         False, 5, 2, False, 1960, 0, False, 3, 10, 5, 0, 32,
                         128, 32, 'normal')

    with open(resource_filename(__name__, 'data/tm_input.csv'), 'r') as fin:
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
      output1 = tm1.compute(r, True, True)
      output2 = tm2.compute(r, True, True)
      self.assertTrue(numpy.array_equal(output1, output2))

    print 'Serializing and deserializing models.'

    savePath1 = os.path.join(self._tmpDir, 'tm1.bin')
    tmProto1 = BacktrackingTM.getSchema().new_message()
    tm1.write(tmProto1)
    with open(savePath1, "wb") as f:
      tmProto1.write(f)
    with open(savePath1, "rb") as f:
      tmProto3 = BacktrackingTM.getSchema().read(f)
    tm3 = BacktrackingTM.read(tmProto3)

    savePath2 = os.path.join(self._tmpDir, 'tm2.bin')
    tmProto2 = BacktrackingTM.getSchema().new_message()
    tm2.write(tmProto2)
    with open(savePath2, "wb") as f:
      tmProto2.write(f)
    with open(savePath2, "rb") as f:
      tmProto4 = BacktrackingTM.getSchema().read(f)
    tm4 = BacktrackingTM.read(tmProto4)

    self.assertTMsEqual(tm1, tm3)
    self.assertTMsEqual(tm2, tm4)

    for r in records[250:]:
      print i
      i += 1
      out1 = tm1.compute(r, True, True)
      out2 = tm2.compute(r, True, True)
      out3 = tm3.compute(r, True, True)
      out4 = tm4.compute(r, True, True)

      self.assertTrue(numpy.array_equal(out1, out2))
      self.assertTrue(numpy.array_equal(out1, out3))
      self.assertTrue(numpy.array_equal(out1, out4))

    self.assertTMsEqual(tm1, tm2)
    self.assertTMsEqual(tm1, tm3)
    self.assertTMsEqual(tm2, tm4)


  def testCheckpointLearned(self):
    # Create a model and give it some inputs to learn.
    tm1 = BacktrackingTM(numberOfCols=100, cellsPerColumn=12,
                         verbosity=VERBOSITY)
    sequences = [self.generateSequence() for _ in xrange(5)]
    train = list(itertools.chain.from_iterable(sequences[:3]))
    for bottomUpInput in train:
      if bottomUpInput is None:
        tm1.reset()
      else:
        tm1.compute(bottomUpInput, True, True)

    # Serialize and deserialized the TM.
    checkpointPath = os.path.join(self._tmpDir, 'a')
    tm1.saveToFile(checkpointPath)
    tm2 = pickle.loads(pickle.dumps(tm1))
    tm2.loadFromFile(checkpointPath)

    # Check that the TMs are the same.
    self.assertTMsEqual(tm1, tm2)

    # Feed some data into the models.
    test = list(itertools.chain.from_iterable(sequences[3:]))
    for bottomUpInput in test:
      if bottomUpInput is None:
        tm1.reset()
        tm2.reset()
      else:
        result1 = tm1.compute(bottomUpInput, True, True)
        result2 = tm2.compute(bottomUpInput, True, True)

        self.assertTMsEqual(tm1, tm2)
        self.assertTrue(numpy.array_equal(result1, result2))


  def testCheckpointMiddleOfSequence(self):
    # Create a model and give it some inputs to learn.
    tm1 = BacktrackingTM(numberOfCols=100, cellsPerColumn=12,
                         verbosity=VERBOSITY)
    sequences = [self.generateSequence() for _ in xrange(5)]
    train = list(itertools.chain.from_iterable(sequences[:3] +
                                               [sequences[3][:5]]))
    for bottomUpInput in train:
      if bottomUpInput is None:
        tm1.reset()
      else:
        tm1.compute(bottomUpInput, True, True)

    # Serialize and deserialized the TM.
    checkpointPath = os.path.join(self._tmpDir, 'a')
    tm1.saveToFile(checkpointPath)
    tm2 = pickle.loads(pickle.dumps(tm1))
    tm2.loadFromFile(checkpointPath)

    # Check that the TMs are the same.
    self.assertTMsEqual(tm1, tm2)

    # Feed some data into the models.
    test = list(itertools.chain.from_iterable([sequences[3][5:]] +
                                              sequences[3:]))
    for bottomUpInput in test:
      if bottomUpInput is None:
        tm1.reset()
        tm2.reset()
      else:
        result1 = tm1.compute(bottomUpInput, True, True)
        result2 = tm2.compute(bottomUpInput, True, True)

        self.assertTMsEqual(tm1, tm2)
        self.assertTrue(numpy.array_equal(result1, result2))


  def testCheckpointMiddleOfSequence2(self):
    """More complex test of checkpointing in the middle of a sequence."""
    tm1 = BacktrackingTM(2048, 32, 0.21, 0.5, 11, 20, 0.1, 0.1, 1.0, 0.0, 14,
                         False, 5, 2, False, 1960, 0, False, 3, 10, 5, 0, 32,
                         128, 32, 'normal')
    tm2 = BacktrackingTM(2048, 32, 0.21, 0.5, 11, 20, 0.1, 0.1, 1.0, 0.0, 14,
                         False, 5, 2, False, 1960, 0, False, 3, 10, 5, 0, 32,
                         128, 32, 'normal')

    with open(resource_filename(__name__, 'data/tm_input.csv'), 'r') as fin:
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
      output1 = tm1.compute(r, True, True)
      output2 = tm2.compute(r, True, True)
      self.assertTrue(numpy.array_equal(output1, output2))

    print 'Serializing and deserializing models.'

    savePath1 = os.path.join(self._tmpDir, 'tm1.bin')
    tm1.saveToFile(savePath1)
    tm3 = pickle.loads(pickle.dumps(tm1))
    tm3.loadFromFile(savePath1)

    savePath2 = os.path.join(self._tmpDir, 'tm2.bin')
    tm2.saveToFile(savePath2)
    tm4 = pickle.loads(pickle.dumps(tm2))
    tm4.loadFromFile(savePath2)

    self.assertTMsEqual(tm1, tm3)
    self.assertTMsEqual(tm2, tm4)

    for r in records[250:]:
      print i
      i += 1
      out1 = tm1.compute(r, True, True)
      out2 = tm2.compute(r, True, True)
      out3 = tm3.compute(r, True, True)
      out4 = tm4.compute(r, True, True)

      self.assertTrue(numpy.array_equal(out1, out2))
      self.assertTrue(numpy.array_equal(out1, out3))
      self.assertTrue(numpy.array_equal(out1, out4))

    self.assertTMsEqual(tm1, tm2)
    self.assertTMsEqual(tm1, tm3)
    self.assertTMsEqual(tm2, tm4)


  def assertTMsEqual(self, tm1, tm2):
    """Asserts that two TM instances are the same.

    This is temporarily disabled since it does not work with the C++
    implementation of the TM.
    """
    self.assertEqual(tm1, tm2, tm1.diff(tm2))
    self.assertTrue(fdrutilities.tmDiff2(tm1, tm2, 1, False))


  @staticmethod
  def generateSequence(n=10, numCols=100, minOnes=21, maxOnes=25):
    """Generates a sequence of n patterns."""
    return [None] + [BacktrackingTMTest.generatePattern(numCols, minOnes,
                                                        maxOnes)
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
