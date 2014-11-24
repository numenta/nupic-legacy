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

from datetime import datetime
import tempfile

import unittest2 as unittest

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.file_record_stream import FileRecordStream
from nupic.data.utils import (
    parseTimestamp, serializeTimestamp, escape, unescape)



def _getTempFileName():
  """Creates unique file name that starts with 'test' and ends with '.txt'."""
  handle = tempfile.NamedTemporaryFile(prefix='test', suffix='.txt', dir='.')
  filename = handle.name
  handle.close()

  return filename



class TestFileRecordStream(unittest.TestCase):


  def testBasic(self):
    """Runs basic FileRecordStream tests."""
    filename = _getTempFileName()

    # Write a standard file
    fields = [('name', 'string', ''),
              ('timestamp', 'datetime', 'T'),
              ('integer', 'int', ''),
              ('real', 'float', ''),
              ('reset', 'int', 'R'),
              ('sid', 'string', 'S'),
              ('categoryField', 'int', 'C'),]
    fieldNames = ['name', 'timestamp', 'integer', 'real', 'reset', 'sid',
                  'categoryField']

    print 'Creating temp file:', filename

    s = FileRecordStream(streamID=filename, write=True, fields=fields)

    self.assertTrue(s.getDataRowCount() == 0)

    # Records
    records = (
      ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1, 'seq-1', 10],
      ['rec_2', datetime(day=2, month=3, year=2010), 8, 7.5, 0, 'seq-1', 11],
      ['rec_3', datetime(day=3, month=3, year=2010), 12, 8.5, 0, 'seq-1', 12])

    self.assertTrue(s.getFields() == fields)
    self.assertTrue(s.getNextRecordIdx() == 0)

    print 'Writing records ...'
    for r in records:
      print list(r)
      s.appendRecord(list(r))

    self.assertTrue(s.getDataRowCount() == 3)

    recordsBatch = (
      ['rec_4', datetime(day=4, month=3, year=2010), 2, 9.5, 1, 'seq-1', 13],
      ['rec_5', datetime(day=5, month=3, year=2010), 6, 10.5, 0, 'seq-1', 14],
      ['rec_6', datetime(day=6, month=3, year=2010), 11, 11.5, 0, 'seq-1', 15])

    print 'Adding batch of records...'
    for rec in recordsBatch:
      print rec
    s.appendRecords(recordsBatch)
    self.assertTrue(s.getDataRowCount() == 6)

    s.close()

    # Read the standard file
    s = FileRecordStream(filename)
    self.assertTrue(s.getDataRowCount() == 6)
    self.assertTrue(s.getFieldNames() == fieldNames)

    # Note! this is the number of records read so far
    self.assertTrue(s.getNextRecordIdx() == 0)

    readStats = s.getStats()
    print 'Got stats:', readStats
    expectedStats = {
                     'max': [None, None, 12, 11.5, 1, None, 15],
                     'min': [None, None, 2, 6.5, 0, None, 10]
                    }
    self.assertTrue(readStats == expectedStats)

    readRecords = []
    print 'Reading records ...'
    while True:
      r = s.getNextRecord()
      print r
      if r is None:
        break

      readRecords.append(r)

    allRecords = records + recordsBatch
    for r1, r2 in zip(allRecords, readRecords):
      print 'Expected:', r1
      print 'Read    :', r2
      self.assertTrue(r1 == r2)

    s.close()


  def testEscapeUnescape(self):
    s = '1,2\n4,5'

    e =  escape(s)
    u = unescape(e)

    self.assertTrue(u == s)


  def testParseSerializeTimestamp(self):
    t = datetime.now()
    s = serializeTimestamp(t)
    self.assertTrue(parseTimestamp(s) == t)


  def testBadDataset(self):

    filename = _getTempFileName()

    print 'Creating tempfile:', filename

    # Write bad dataset with records going backwards in time
    fields = [('timestamp', 'datetime', 'T')]
    o = FileRecordStream(streamID=filename, write=True, fields=fields)
    # Records
    records = (
      [datetime(day=3, month=3, year=2010)],
      [datetime(day=2, month=3, year=2010)])

    o.appendRecord(records[0])
    o.appendRecord(records[1])
    o.close()

    # Write bad dataset with broken sequences
    fields = [('sid', 'int', 'S')]
    o = FileRecordStream(streamID=filename, write=True, fields=fields)
    # Records
    records = ([1], [2], [1])

    o.appendRecord(records[0])
    o.appendRecord(records[1])
    self.assertRaises(Exception, o.appendRecord, (records[2],))
    o.close()


  def testMissingValues(self):

    print "Beginning Missing Data test..."
    filename = _getTempFileName()

    # Some values missing of each type
    # read dataset from disk, retrieve values
    # string should return empty string, numeric types sentinelValue

    print 'Creating tempfile:', filename

    # write dataset to disk with float, int, and string fields
    fields = [('timestamp', 'datetime', 'T'),
              ('name', 'string', ''),
              ('integer', 'int', ''),
              ('real', 'float', '')]
    s = FileRecordStream(streamID=filename, write=True, fields=fields)

    # Records
    records = (
      [datetime(day=1, month=3, year=2010), 'rec_1', 5, 6.5],
      [datetime(day=2, month=3, year=2010), '', 8, 7.5],
      [datetime(day=3, month=3, year=2010), 'rec_3', '', 8.5],
      [datetime(day=4, month=3, year=2010), 'rec_4', 12, ''],
      [datetime(day=5, month=3, year=2010), 'rec_5', -87657496599, 6.5],
      [datetime(day=6, month=3, year=2010), 'rec_6', 12, -87657496599],
      [datetime(day=6, month=3, year=2010), str(-87657496599), 12, 6.5])

    for r in records:
      s.appendRecord(list(r))

    s.close()

    # Read the standard file
    s = FileRecordStream(streamID=filename, write=False)

    fieldsRead = s.getFields()
    self.assertTrue(fields == fieldsRead)

    recordsRead = []
    while True:
      r = s.getNextRecord()
      if r is None:
        break
      print 'Reading record ...'
      print r
      recordsRead.append(r)

    # sort the records by date, so we know for sure which is which
    sorted(recordsRead, key=lambda rec: rec[0])

    # empty string
    self.assertTrue(recordsRead[1][1] == SENTINEL_VALUE_FOR_MISSING_DATA)

    # missing int
    self.assertTrue(recordsRead[2][2] == SENTINEL_VALUE_FOR_MISSING_DATA)

    # missing float
    self.assertTrue(recordsRead[3][3] == SENTINEL_VALUE_FOR_MISSING_DATA)

    # sentinel value in input handled correctly for int field
    self.assertTrue(recordsRead[4][2] != SENTINEL_VALUE_FOR_MISSING_DATA)

    # sentinel value in input handled correctly for float field
    self.assertTrue(recordsRead[5][3] != SENTINEL_VALUE_FOR_MISSING_DATA)

    # sentinel value in input handled correctly for string field
    # this should leave the string as-is, since a missing string
    # is encoded not with a sentinel value but with an empty string
    self.assertTrue(recordsRead[6][1] != SENTINEL_VALUE_FOR_MISSING_DATA)



if __name__ == '__main__':
  unittest.main()
