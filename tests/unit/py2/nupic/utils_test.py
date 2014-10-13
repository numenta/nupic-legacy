#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2014, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for utils module."""

import unittest2 as unittest

from nupic.utils import MovingAverage
from nupic.support.unittesthelpers.testcasebase import TestCaseBase



class UtilsTest(TestCaseBase):
  """testing common.utils"""


  def testMovingAverage(self):
    """
    Test that the (internal) moving average maintains the averages correctly,
    even for null initial condition and when the number of values goes over
    windowSize.  Pass in integers and floats.
    """
    historicalValues = []
    total = 0
    windowSize = 3
    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, 3, windowSize)
    )
    self.assertEqual(newAverage, 3.0)
    self.assertEqual(historicalValues, [3.0])
    self.assertEqual(total, 3.0)

    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, 4, windowSize)
    )
    self.assertEqual(newAverage, 3.5)
    self.assertEqual(historicalValues, [3.0, 4.0])
    self.assertEqual(total, 7.0)

    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, 5.0, windowSize)
    )
    self.assertEqual(newAverage, 4.0)
    self.assertEqual(historicalValues, [3.0, 4.0, 5.0])
    self.assertEqual(total, 12.0)

    # Ensure the first value gets popped
    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, 6.0, windowSize)
    )
    self.assertEqual(newAverage, 5.0)
    self.assertEqual(historicalValues, [4.0, 5.0, 6.0])
    self.assertEqual(total, 15.0)


  def testMovingAverageInstance(self):
    """
    Test that the (internal) moving average maintains the averages correctly,
    even for null initial condition and when the number of values goes over
    windowSize.  Pass in integers and floats.
    this is for the instantce method next()
    """
    ma = MovingAverage(windowSize=3)

    newAverage, historicalValues, total = (ma.next(3))
    self.assertEqual(newAverage, 3.0)
    self.assertEqual(historicalValues, [3.0])
    self.assertEqual(total, 3.0)

    newAverage, historicalValues, total = (ma.next(4))
    self.assertEqual(newAverage, 3.5)
    self.assertEqual(historicalValues, [3.0, 4.0])
    self.assertEqual(total, 7.0)

    newAverage, historicalValues, total = (ma.next(5))
    self.assertEqual(newAverage, 4.0)
    self.assertEqual(historicalValues, [3.0, 4.0, 5.0])
    self.assertEqual(total, 12.0)

    # Ensure the first value gets popped
    newAverage, historicalValues, total = (ma.next(6))
    self.assertEqual(newAverage, 5.0)
    self.assertEqual(historicalValues, [4.0, 5.0, 6.0])
    self.assertEqual(total, 15.0)


if __name__ == "__main__":
  unittest.main()
