# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

"""
  Test for get/setParameter in python -- these methods are syntactic sugar
  that allow you to access parameters without knowing their types,
  at a moderate performance penalty.
"""

import unittest2 as unittest

# import for type comparison with Array.
# (Seems we should be able to use nupic.engine.Array directly.)
import nupic.bindings.engine_internal
from nupic.engine import Network



class NetworkUnifiedPyParameterTest(unittest.TestCase):


  def testScalars(self):
    scalars = [
      ("int32Param", 32, int, 35),
      ("uint32Param", 33, int, 36),
      ("int64Param", 64, long, 74),
      ("uint64Param", 65, long, 75),
      ("real32Param", 32.1, float, 33.1),
      ("real64Param", 64.1, float, 65.1),
      ("stringParam", "nodespec value", str, "new value")]

    n = Network()
    l1= n.addRegion("l1", "TestNode", "")
    x = l1.getParameter("uint32Param")

    for paramName, initval, paramtype, newval in scalars:
      # Check the initial value for each parameter.
      x = l1.getParameter(paramName)
      self.assertEqual(type(x), paramtype)
      if initval is None:
        continue
      if type(x) == float:
        self.assertTrue(abs(x  - initval) < 0.00001)
      else:
        self.assertEqual(x, initval)

      # Now set the value, and check to make sure the value is updated
      l1.setParameter(paramName, newval)
      x = l1.getParameter(paramName)
      self.assertEqual(type(x), paramtype)
      if type(x) == float:
        self.assertTrue(abs(x  - newval) < 0.00001)
      else:
        self.assertEqual(x, newval)


  def testArrays(self):
    arrays = [
      ("real32ArrayParam",
        [0*32, 1*32, 2*32, 3*32, 4*32, 5*32, 6*32, 7*32],
       "Real32"),
      ("int64ArrayParam",
        [0*64, 1*64, 2*64, 3*64],
        "Int64")
    ]

    n = Network()
    l1= n.addRegion("l1", "TestNode", "")

    for paramName, initval, paramtype in arrays:
      x = l1.getParameter(paramName)
      self.assertTrue(isinstance(x, nupic.bindings.engine_internal.Array))
      self.assertEqual(x.getType(), paramtype)
      self.assertEqual(len(x), len(initval))
      for i in xrange(len(x)):
        self.assertEqual(x[i], initval[i])

      for i in xrange(len(x)):
        x[i] = x[i] * 2
      l1.setParameter(paramName, x)

      x = l1.getParameter(paramName)
      self.assertTrue(isinstance(x, nupic.bindings.engine_internal.Array))
      self.assertEqual(x.getType(), paramtype)
      self.assertEqual(len(x), len(initval))
      for i in xrange(len(x)):
        self.assertEqual(x[i], 2 * initval[i])



if __name__ == "__main__":
  unittest.main()
