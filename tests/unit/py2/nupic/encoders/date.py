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

"""Unit tests for date encoder"""

from base import *
import datetime
import numpy
import unittest2 as unittest

from nupic.encoders.date import DateEncoder


#########################################################################
class DateEncoderTest(unittest.TestCase):
  '''Unit tests for DateEncoder class'''
  
  def testDateEncoder(self):
    '''creating date encoder instance'''

    # 3 bits for season, 1 bit for day of week, 2 for weekend, 5 for time of day
    e = DateEncoder(season=3, dayOfWeek=1, weekend=3, timeOfDay=5)
    assert e.getDescription() == [("season", 0), ("day of week", 12),
                                ("weekend", 19), ("time of day", 25)]

    # in the middle of fall, thursday, not a weekend, afternoon
    d = datetime.datetime(2010, 11, 4, 14, 55)
    bits = e.encode(d)

    # season is aaabbbcccddd (1 bit/month)
    seasonExpected = [0,0,0,0,0,0,0,0,0,1,1,1]

    # should be 000000000111 (centered on month 11)
    # week is MTFTFSS
    # contrary to localtime documentation, Monaday = 0 (for python
    #  datetime.datetime.timetuple()
    dayOfWeekExpected = [0,0,0,1,0,0,0]

    # not a weekend, so it should be "False"
    weekendExpected = [1,1,1,0,0,0]

    # time of day has radius of 4 hours and w of 5 so each bit = 240/5 min = 48min
    # 14:55 is minute 14*60 + 55 = 895; 895/48 = bit 18.6
    # should be 30 bits total (30 * 48 minutes = 24 hours)
    timeOfDayExpected = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0]
    expected = numpy.array(seasonExpected + dayOfWeekExpected + weekendExpected \
                          + timeOfDayExpected, dtype=defaultDtype)
    self.assertEqual(expected,bits).all()

    print
    e.pprintHeader()
    e.pprint(bits)
    print

  def testMissingValues(self, e):
    '''missing values'''
    mvOutput = e.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
    self.assertEqual(sum(mvOutput), 0)

  def testDecoding(self, e):
    '''decoding date'''
    decoded = e.decode(bits)

    (fieldsDict, fieldNames) = decoded
    self.assertEqual(len(fieldsDict), 4)

    (ranges, desc) = fieldsDict['season']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [305, 305])
    
    (ranges, desc) = fieldsDict['time of day']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [14.4, 14.4])
    
    (ranges, desc) = fieldsDict['day of week']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [3, 3])
    
    (ranges, desc) = fieldsDict['weekend']
    self.assertEqual(len(ranges), 1)
    self.assertSequenceEqual(ranges[0], [0, 0])
    
    print decoded
    print "decodedToStr=>", e.decodedToStr(decoded)

  def testTopDownCompute(self, e):
    '''Check topDownCompute'''
    topDown = e.topDownCompute(bits)
    topDownValues = numpy.array([elem.value for elem in topDown])
    errs = topDownValues - numpy.array([320.25, 3.5, .167, 14.8])
    self.assertAlmostEqual(errs.max(), 0, 4)

  def testBucketIndexSupport(self, e):
    '''Check bucket index support'''
    bucketIndices = e.getBucketIndices(d)
    print "bucket indices:", bucketIndices
    topDown = e.getBucketInfo(bucketIndices)
    topDownValues = numpy.array([elem.value for elem in topDown])
    errs = topDownValues - numpy.array([320.25, 3.5, .167, 14.8])
    self.assertAlmostEqual(errs.max(), 0, 4)

    encodings = []
    for x in topDown:
      encodings.extend(x.encoding)
    self.assertSequenceEqual(encodings, expected)

  def testHoliday(self, e):
    '''look at holiday more carefully because of the smooth transition'''
    e = DateEncoder(holiday=5)
    holiday = numpy.array([0,0,0,0,0,1,1,1,1,1], dtype='uint8')
    notholiday = numpy.array([1,1,1,1,1,0,0,0,0,0], dtype='uint8')
    holiday2 = numpy.array([0,0,0,1,1,1,1,1,0,0], dtype='uint8')

    d = datetime.datetime(2010, 12, 25, 4, 55)
    self.assertSequenceEqual(e.encode(d), holiday)

    d = datetime.datetime(2008, 12, 27, 4, 55)
    self.assertSequenceEqual(e.encode(d), notholiday)

    d = datetime.datetime(1999, 12, 26, 8, 00)
    self.assertSequenceEqual(e.encode(d), holiday2)

    d = datetime.datetime(2011, 12, 24, 16, 00)
    self.assertSequenceEqual(e.encode(d), holiday2)

  def testWeekend(self, e):
    '''Test weekend encoder'''
    e = DateEncoder(customDays = (21,["sat","sun","fri"]))
    mon = DateEncoder(customDays = (21,"Monday"))

    e2 = DateEncoder(weekend=(21,1))
    d = datetime.datetime(1988,5,29,20,00)
    self.assertSequenceEqual(e.encode(d), e2.encode(d))
    for _ in range(300):
      d = d+datetime.timedelta(days=1)
      self.assertSequenceEqual(e.encode(d), e2.encode(d))
      print mon.decode(mon.encode(d))
      #Make sure
      if mon.decode(mon.encode(d))[0]["Monday"][0][0][0]==1.0:
        self.assertEqual(d.weekday(), 0)
      else:
        self.assertFalse(d.weekday()==0)

###########################################
if __name__ == '__main__':
  unittest.main()