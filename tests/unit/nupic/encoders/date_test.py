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

"""Unit tests for date encoder"""

import datetime
import numpy
import tempfile
from nupic.encoders.base import defaultDtype
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import unittest2 as unittest

from nupic.encoders.date import DateEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.date_capnp import DateEncoderProto



class DateEncoderTest(unittest.TestCase):
  """Unit tests for DateEncoder class"""


  def setUp(self):
    # 3 bits for season, 1 bit for day of week, 1 for weekend, 5 for time of
    # day
    # use of forced is not recommended, used here for readibility, see scalar.py
    self._e = DateEncoder(season=3, dayOfWeek=1, weekend=1, timeOfDay=5)
    # in the middle of fall, Thursday, not a weekend, afternoon - 4th Nov,
    # 2010, 14:55
    self._d = datetime.datetime(2010, 11, 4, 14, 55)
    self._bits = self._e.encode(self._d)
    # season is aaabbbcccddd (1 bit/month) # TODO should be <<3?
    # should be 000000000111 (centered on month 11 - Nov)
    seasonExpected = [0,0,0,0,0,0,0,0,0,1,1,1]

    # week is MTWTFSS
    # contrary to localtime documentation, Monday = 0 (for python
    #  datetime.datetime.timetuple()
    dayOfWeekExpected = [0,0,0,1,0,0,0]

    # not a weekend, so it should be "False"
    weekendExpected = [1, 0]

    # time of day has radius of 4 hours and w of 5 so each bit = 240/5
    # min = 48min 14:55 is minute 14*60 + 55 = 895; 895/48 = bit 18.6
    # should be 30 bits total (30 * 48 minutes = 24 hours)
    timeOfDayExpected = (
      [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0])
    self._expected = numpy.array(seasonExpected +
                                 dayOfWeekExpected +
                                 weekendExpected +
                                 timeOfDayExpected, dtype=defaultDtype)

  def testDateEncoder(self):
    """creating date encoder instance"""
    self.assertSequenceEqual(
      self._e.getDescription(),
      [("season", 0),
       ("day of week", 12),
       ("weekend", 19), ("time of day", 21)])
    self.assertTrue(numpy.array_equal(self._expected, self._bits))


  def testMissingValues(self):
    """missing values"""
    mvOutput = self._e.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(sum(mvOutput), 0)


  def testDecoding(self):
    """decoding date"""
    decoded = self._e.decode(self._bits)

    (fieldsDict, _) = decoded
    self.assertEqual(len(fieldsDict), 4)

    (ranges, _) = fieldsDict['season']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [305, 305])

    (ranges, _) = fieldsDict['time of day']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [14.4, 14.4])

    (ranges, _) = fieldsDict['day of week']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [3, 3])

    (ranges, _) = fieldsDict['weekend']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [0, 0])


  def testTopDownCompute(self):
    """Check topDownCompute"""
    topDown = self._e.topDownCompute(self._bits)
    topDownValues = numpy.array([elem.value for elem in topDown])
    errs = topDownValues - numpy.array([320.25, 3.5, .167, 14.8])
    self.assertAlmostEqual(errs.max(), 0, 4)


  def testBucketIndexSupport(self):
    """Check bucket index support"""
    bucketIndices = self._e.getBucketIndices(self._d)
    topDown = self._e.getBucketInfo(bucketIndices)
    topDownValues = numpy.array([elem.value for elem in topDown])
    errs = topDownValues - numpy.array([320.25, 3.5, .167, 14.8])
    self.assertAlmostEqual(errs.max(), 0, 4)

    encodings = []
    for x in topDown:
      encodings.extend(x.encoding)
    self.assertTrue(numpy.array_equal(encodings, self._expected))


  def testHoliday(self):
    """look at holiday more carefully because of the smooth transition"""
    # use of forced is not recommended, used here for readibility, see
    # scalar.py
    e = DateEncoder(holiday=5, forced=True)
    holiday = numpy.array([0,0,0,0,0,1,1,1,1,1], dtype="uint8")
    notholiday = numpy.array([1,1,1,1,1,0,0,0,0,0], dtype="uint8")
    holiday2 = numpy.array([0,0,0,1,1,1,1,1,0,0], dtype="uint8")

    d = datetime.datetime(2010, 12, 25, 4, 55)
    self.assertTrue(numpy.array_equal(e.encode(d), holiday))

    d = datetime.datetime(2008, 12, 27, 4, 55)
    self.assertTrue(numpy.array_equal(e.encode(d), notholiday))

    d = datetime.datetime(1999, 12, 26, 8, 00)
    self.assertTrue(numpy.array_equal(e.encode(d), holiday2))

    d = datetime.datetime(2011, 12, 24, 16, 00)
    self.assertTrue(numpy.array_equal(e.encode(d), holiday2))


  def testWeekend(self):
    """Test weekend encoder"""
    # use of forced is not recommended, used here for readibility, see scalar.py
    e = DateEncoder(customDays=(21, ["sat", "sun", "fri"]), forced=True)
    mon = DateEncoder(customDays=(21, "Monday"), forced=True)

    e2 = DateEncoder(weekend=(21, 1), forced=True)
    d = datetime.datetime(1988, 5, 29, 20, 00)
    self.assertTrue(numpy.array_equal(e.encode(d), e2.encode(d)))
    for _ in range(300):
      d = d+datetime.timedelta(days=1)
      self.assertTrue(numpy.array_equal(e.encode(d), e2.encode(d)))

      #Make sure
      if mon.decode(mon.encode(d))[0]["Monday"][0][0][0] == 1.0:
        self.assertEqual(d.weekday(), 0)
      else:
        self.assertNotEqual(d.weekday(), 0)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    originalTS = datetime.datetime(1997, 8, 29, 2, 14)
    originalValue = self._e.encode(originalTS)

    proto1 = DateEncoderProto.new_message()
    self._e.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = DateEncoderProto.read(f)

    encoder = DateEncoder.read(proto2)

    self.assertIsInstance(encoder, DateEncoder)
    self.assertEqual(encoder.width, self._e.width)
    self.assertEqual(encoder.weekendOffset, self._e.weekendOffset)
    self.assertEqual(encoder.timeOfDayOffset, self._e.timeOfDayOffset)
    self.assertEqual(encoder.seasonOffset, self._e.seasonOffset)
    self.assertEqual(encoder.dayOfWeekOffset, self._e.dayOfWeekOffset)
    self.assertIsInstance(encoder.customDaysEncoder,
                          self._e.customDaysEncoder.__class__)
    self.assertIsInstance(encoder.dayOfWeekEncoder,
                          self._e.dayOfWeekEncoder.__class__)
    self.assertIsInstance(encoder.seasonEncoder,
                          self._e.seasonEncoder.__class__)
    self.assertIsInstance(encoder.timeOfDayEncoder,
                          self._e.timeOfDayEncoder.__class__)
    self.assertIsInstance(encoder.weekendEncoder,
                          self._e.weekendEncoder.__class__)
    self.assertTrue(numpy.array_equal(self._bits, encoder.encode(self._d)))
    self.assertTrue(numpy.array_equal(encoder.encode(originalTS),
                                      originalValue))
    self.assertEqual(self._e.decode(encoder.encode(self._d)),
                     encoder.decode(self._e.encode(self._d)))



if __name__ == "__main__":
  unittest.main()
