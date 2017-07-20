# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2014, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for utils module."""

import pickle
import tempfile
import unittest

from nupic.utils import MovingAverage

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.movingaverage_capnp import MovingAverageProto



class UtilsTest(unittest.TestCase):
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
    self.assertListEqual(historicalValues, [3.0, 4.0])
    self.assertEqual(total, 7.0)

    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, 5.0, windowSize)
    )
    self.assertEqual(newAverage, 4.0)
    self.assertListEqual(historicalValues, [3.0, 4.0, 5.0])
    self.assertEqual(total, 12.0)

    # Ensure the first value gets popped
    newAverage, historicalValues, total = (
      MovingAverage.compute(historicalValues, total, 6.0, windowSize)
    )
    self.assertEqual(newAverage, 5.0)
    self.assertListEqual(historicalValues, [4.0, 5.0, 6.0])
    self.assertEqual(total, 15.0)


  def testMovingAverageInstance(self):
    """
    Test that the (internal) moving average maintains the averages correctly,
    even for null initial condition and when the number of values goes over
    windowSize.  Pass in integers and floats.
    this is for the instantce method next()
    """
    ma = MovingAverage(windowSize=3)

    newAverage = ma.next(3)
    self.assertEqual(newAverage, 3.0)
    self.assertListEqual(ma.getSlidingWindow(), [3.0])
    self.assertEqual(ma.total, 3.0)

    newAverage = ma.next(4)
    self.assertEqual(newAverage, 3.5)
    self.assertListEqual(ma.getSlidingWindow(), [3.0, 4.0])
    self.assertEqual(ma.total, 7.0)

    newAverage = ma.next(5)
    self.assertEqual(newAverage, 4.0)
    self.assertListEqual(ma.getSlidingWindow(), [3.0, 4.0, 5.0])
    self.assertEqual(ma.total, 12.0)

    # Ensure the first value gets popped
    newAverage = ma.next(6)
    self.assertEqual(newAverage, 5.0)
    self.assertListEqual(ma.getSlidingWindow(), [4.0, 5.0, 6.0])
    self.assertEqual(ma.total, 15.0)


  def testMovingAverageSlidingWindowInit(self):
    """
    Test the slidingWindow value is correctly assigned when initializing a
    new MovingAverage object.
    """
    # With exisiting historical values; same values as tested in testMovingAverage()
    ma = MovingAverage(windowSize=3, existingHistoricalValues=[3.0, 4.0, 5.0])
    self.assertListEqual(ma.getSlidingWindow(), [3.0, 4.0, 5.0])

    # Withoout exisiting historical values
    ma = MovingAverage(windowSize=3)
    self.assertListEqual(ma.getSlidingWindow(), [])


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testMovingAverageReadWrite(self):
    ma = MovingAverage(windowSize=3)

    ma.next(3)
    ma.next(4.5)
    ma.next(5)

    proto1 = MovingAverageProto.new_message()
    ma.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = MovingAverageProto.read(f)

    resurrectedMa = MovingAverage.read(proto2)

    newAverage = ma.next(6)
    self.assertEqual(newAverage, resurrectedMa.next(6))
    self.assertListEqual(ma.getSlidingWindow(),
                         resurrectedMa.getSlidingWindow())
    self.assertEqual(ma.total, resurrectedMa.total)
    self.assertTrue(ma, resurrectedMa) #using the __eq__ method


  def testSerialization(self):
    """serialization using pickle"""
    ma = MovingAverage(windowSize=3)

    ma.next(3)
    ma.next(4.5)
    ma.next(5)

    stored = pickle.dumps(ma)
    restored = pickle.loads(stored)
    self.assertEqual(restored, ma) 
    self.assertEqual(ma.next(6), restored.next(6))


  def testEquals(self):
    ma = MovingAverage(windowSize=3)
    maP = MovingAverage(windowSize=3)
    self.assertEqual(ma, maP)
    
    maN = MovingAverage(windowSize=10)
    self.assertNotEqual(ma, maN)

    ma = MovingAverage(windowSize=2, existingHistoricalValues=[3.0, 4.0, 5.0])
    maP = MovingAverage(windowSize=2, existingHistoricalValues=[3.0, 4.0, 5.0])
    self.assertEqual(ma, maP)
    maP.next(6)
    self.assertNotEqual(ma, maP)
    ma.next(6)
    self.assertEqual(ma, maP)
    



if __name__ == "__main__":
  unittest.main()
