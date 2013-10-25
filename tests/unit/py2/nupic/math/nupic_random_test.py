#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
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

"""NuPIC random module tests."""

import cPickle as pickle

import unittest2 as unittest

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



if __name__ == "__main__":
  unittest.main()
