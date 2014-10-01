#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

"""NuPIC random module tests."""

import cPickle as pickle
import unittest

import numpy

from nupic.bindings.math import Random, StdRandom



class TestNupicRandom(unittest.TestCase):


  def testNupicRandomPickling(self):
    """Test pickling / unpickling of NuPIC randomness."""

    # Simple test: make sure that dumping / loading works...
    r = Random(42)
    pickledR = pickle.dumps(r)

    test1 = [r.getUInt32() for _ in xrange(10)]
    r = pickle.loads(pickledR)
    test2 = [r.getUInt32() for _ in xrange(10)]

    self.assertEqual(test1, test2,
                     "Simple NuPIC random pickle/unpickle failed.")

    # A little tricker: dump / load _after_ some numbers have been generated
    # (in the first test).  Things should still work...
    # ...the idea of this test is to make sure that the pickle code isn't just
    # saving the initial seed...
    pickledR = pickle.dumps(r)

    test3 = [r.getUInt32() for _ in xrange(10)]
    r = pickle.loads(pickledR)
    test4 = [r.getUInt32() for _ in xrange(10)]

    self.assertEqual(
        test3, test4,
        "NuPIC random pickle/unpickle didn't work for saving later state.")

    self.assertNotEqual(test1, test3,
                        "NuPIC random gave the same result twice?!?")


  def testStdRandomStateFunctions(self):
    """Test the NuPIC StdRandom to make sure getstate / setstate works."""
    sr = StdRandom(43)

    srState = sr.getstate()
    r1 = sr.random()
    r2 = sr.random()
    sr.setstate(srState)

    self.assertEqual(sr.random(), r1)
    self.assertEqual(sr.random(), r2)

    srState = sr.getstate()
    r1 = sr.random()
    r2 = sr.random()
    sr.setstate(srState)

    self.assertEqual(sr.random(), r1)
    self.assertEqual(sr.random(), r2)


  def testSample(self):
    r = Random(42)
    population = numpy.array([1, 2, 3, 4], dtype="uint32")
    sample = numpy.zeros([2], dtype="uint32")

    r.sample(population, sample)

    self.assertEqual(sample[0], 2)
    self.assertEqual(sample[1], 4)


  def testSampleNone(self):
    r = Random(42)
    population = numpy.array([1, 2, 3, 4], dtype="uint32")
    sample = numpy.zeros([0], dtype="uint32")

    # Just make sure there is no exception thrown.
    r.sample(population, sample)

    self.assertEqual(sample.size, 0)


  def testSampleAll(self):
    r = Random(42)
    population = numpy.array([1, 2, 3, 4], dtype="uint32")
    sample = numpy.zeros([4], dtype="uint32")

    r.sample(population, sample)

    self.assertEqual(sample[0], 1)
    self.assertEqual(sample[1], 2)
    self.assertEqual(sample[2], 3)
    self.assertEqual(sample[3], 4)


  def testSampleSequence(self):
    r = Random(42)
    population = [1, 2, 3, 4]
    sample = [0, 0]

    with self.assertRaises(TypeError):
      r.sample(population, sample)


  def testSampleBadDtype(self):
    r = Random(42)
    population = numpy.array([1, 2, 3, 4], dtype="int64")
    sample = numpy.zeros([2], dtype="int64")

    with self.assertRaises(TypeError):
      r.sample(population, sample)


  def testSamplePopulationTooSmall(self):
    r = Random(42)
    population = numpy.array([1, 2, 3, 4], dtype="uint32")
    sample = numpy.zeros([5], dtype="uint32")

    with self.assertRaises(ValueError) as exc:
      r.sample(population, sample)

    self.assertEqual(exc.exception.message,
                     "population size must be greater than number of choices")


  def testShuffle(self):
    r = Random(42)
    arr = numpy.array([1, 2, 3, 4], dtype="uint32")

    r.shuffle(arr)

    self.assertSequenceEqual(list(arr), (3, 4, 2, 1))


  def testShuffleEmpty(self):
    r = Random(42)
    arr = numpy.zeros([0], dtype="uint32")

    r.shuffle(arr)

    self.assertEqual(arr.size, 0)


  def testShuffleBadDtype(self):
    r = Random(42)
    arr = numpy.array([1, 2, 3, 4], dtype="int64")

    with self.assertRaises(TypeError):
      r.shuffle(arr)



if __name__ == "__main__":
  unittest.main()
