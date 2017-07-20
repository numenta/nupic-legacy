# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-15, Numenta, Inc.  Unless you have an agreement
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

import tempfile
import unittest

from datetime import datetime
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.field_meta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial
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
    fields = [FieldMetaInfo('name', FieldMetaType.string,
                            FieldMetaSpecial.none),
              FieldMetaInfo('timestamp', FieldMetaType.datetime,
                            FieldMetaSpecial.timestamp),
              FieldMetaInfo('integer', FieldMetaType.integer,
                            FieldMetaSpecial.none),
              FieldMetaInfo('real', FieldMetaType.float,
                            FieldMetaSpecial.none),
              FieldMetaInfo('reset', FieldMetaType.integer,
                            FieldMetaSpecial.reset),
              FieldMetaInfo('sid', FieldMetaType.string,
                            FieldMetaSpecial.sequence),
              FieldMetaInfo('categoryField', FieldMetaType.integer,
                            FieldMetaSpecial.category),]
    fieldNames = ['name', 'timestamp', 'integer', 'real', 'reset', 'sid',
                  'categoryField']

    print 'Creating temp file:', filename

    with FileRecordStream(streamID=filename, write=True, fields=fields) as s:

      self.assertEqual(0, s.getDataRowCount())

      # Records
      records = (
        ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1, 'seq-1', 10],
        ['rec_2', datetime(day=2, month=3, year=2010), 8, 7.5, 0, 'seq-1', 11],
        ['rec_3', datetime(day=3, month=3, year=2010), 12, 8.5, 0, 'seq-1', 12])

      self.assertEqual(fields, s.getFields())
      self.assertEqual(0, s.getNextRecordIdx())

      print 'Writing records ...'
      for r in records:
        print list(r)
        s.appendRecord(list(r))

      self.assertEqual(3, s.getDataRowCount())

      recordsBatch = (
        ['rec_4', datetime(day=4, month=3, year=2010), 2, 9.5, 1, 'seq-1', 13],
        ['rec_5', datetime(day=5, month=3, year=2010), 6, 10.5, 0, 'seq-1', 14],
        ['rec_6', datetime(day=6, month=3, year=2010), 11, 11.5, 0, 'seq-1', 15]
      )

      print 'Adding batch of records...'
      for rec in recordsBatch:
        print rec
      s.appendRecords(recordsBatch)
      self.assertEqual(6, s.getDataRowCount())

    with FileRecordStream(filename) as s:

      # Read the standard file
      self.assertEqual(6, s.getDataRowCount())
      self.assertEqual(fieldNames, s.getFieldNames())

      # Note! this is the number of records read so far
      self.assertEqual(0, s.getNextRecordIdx())

      readStats = s.getStats()
      print 'Got stats:', readStats
      expectedStats = {
                       'max': [None, None, 12, 11.5, 1, None, 15],
                       'min': [None, None, 2, 6.5, 0, None, 10]
                      }
      self.assertEqual(expectedStats, readStats)

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
        self.assertEqual(r1, r2)


  def testMultipleClasses(self):
    """Runs FileRecordStream tests with multiple category fields."""
    filename = _getTempFileName()

    # Write a standard file
    fields = [
      FieldMetaInfo('name', FieldMetaType.string,
                    FieldMetaSpecial.none),
      FieldMetaInfo('timestamp', FieldMetaType.datetime,
                    FieldMetaSpecial.timestamp),
      FieldMetaInfo('integer', FieldMetaType.integer,
                    FieldMetaSpecial.none),
      FieldMetaInfo('real', FieldMetaType.float,
                    FieldMetaSpecial.none),
      FieldMetaInfo('reset', FieldMetaType.integer,
                    FieldMetaSpecial.reset),
      FieldMetaInfo('sid', FieldMetaType.string,
                    FieldMetaSpecial.sequence),
      FieldMetaInfo('categories', FieldMetaType.list,
                    FieldMetaSpecial.category)]
    fieldNames = ['name', 'timestamp', 'integer', 'real', 'reset', 'sid',
                  'categories']

    print 'Creating temp file:', filename

    with FileRecordStream(streamID=filename, write=True, fields=fields) as s:

      self.assertEqual(0, s.getDataRowCount())

      # Records
      records = (
        ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1, 'seq-1',
         [0, 1, 2]],
        ['rec_2', datetime(day=2, month=3, year=2010), 8, 7.5, 0, 'seq-1',
         [3, 4, 5,]],
        ['rec_3', datetime(day=3, month=3, year=2010), 2, 8.5, 0, 'seq-1',
         [6, 7, 8,]])

      self.assertEqual(fields, s.getFields())
      self.assertEqual(0, s.getNextRecordIdx())

      print 'Writing records ...'
      for r in records:
        print r
        s.appendRecord(r)

      self.assertEqual(3, s.getDataRowCount())

      recordsBatch = (
        ['rec_4', datetime(day=4, month=3, year=2010), 2, 9.5, 1, 'seq-1',
         [2, 3, 4]],
        ['rec_5', datetime(day=5, month=3, year=2010), 6, 10.5, 0, 'seq-1',
         [3, 4, 5]],
        ['rec_6', datetime(day=6, month=3, year=2010), 11, 11.5, 0, 'seq-1',
         [4, 5, 6]])

      print 'Adding batch of records...'
      for rec in recordsBatch:
        print rec
      s.appendRecords(recordsBatch)
      self.assertEqual(6, s.getDataRowCount())

    with FileRecordStream(filename) as s:

      # Read the standard file
      self.assertEqual(6, s.getDataRowCount())
      self.assertEqual(fieldNames, s.getFieldNames())

      # Note! this is the number of records read so far
      self.assertEqual(0, s.getNextRecordIdx())

      readStats = s.getStats()
      print 'Got stats:', readStats
      expectedStats = {
                       'max': [None, None, 11, 11.5, 1, None, None],
                       'min': [None, None, 2, 6.5, 0, None, None]
                      }
      self.assertEqual(expectedStats, readStats)

      readRecords = []
      print 'Reading records ...'
      while True:
        r = s.getNextRecord()
        print r
        if r is None:
          break

        readRecords.append(r)

      expectedRecords = (
        ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1, 'seq-1',
         [0, 1, 2]],
        ['rec_2', datetime(day=2, month=3, year=2010), 8, 7.5, 0, 'seq-1',
         [3, 4, 5]],
        ['rec_3', datetime(day=3, month=3, year=2010), 2, 8.5, 0, 'seq-1',
         [6, 7, 8]],
        ['rec_4', datetime(day=4, month=3, year=2010), 2, 9.5, 1, 'seq-1',
         [2, 3, 4]],
        ['rec_5', datetime(day=5, month=3, year=2010), 6, 10.5, 0, 'seq-1',
         [3, 4, 5]],
        ['rec_6', datetime(day=6, month=3, year=2010), 11, 11.5, 0, 'seq-1',
         [4, 5, 6]])

      for r1, r2 in zip(expectedRecords, readRecords):
        self.assertEqual(r1, r2)


  def testEscapeUnescape(self):
    s = '1,2\n4,5'

    e = escape(s)
    u = unescape(e)

    self.assertEqual(u, s)


  def testParseSerializeTimestamp(self):
    t = datetime.now()
    s = serializeTimestamp(t)
    self.assertEqual(t, parseTimestamp(s))


  def testBadDataset(self):

    filename = _getTempFileName()

    print 'Creating tempfile:', filename

    # Write bad dataset with records going backwards in time
    fields = [FieldMetaInfo('timestamp', FieldMetaType.datetime,
                            FieldMetaSpecial.timestamp)]
    o = FileRecordStream(streamID=filename, write=True, fields=fields)
    # Records
    records = (
      [datetime(day=3, month=3, year=2010)],
      [datetime(day=2, month=3, year=2010)])

    o.appendRecord(records[0])
    o.appendRecord(records[1])
    o.close()

    # Write bad dataset with broken sequences
    fields = [FieldMetaInfo('sid', FieldMetaType.integer,
                            FieldMetaSpecial.sequence)]
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
    fields = [FieldMetaInfo('timestamp', FieldMetaType.datetime,
                            FieldMetaSpecial.timestamp),
              FieldMetaInfo('name', FieldMetaType.string,
                            FieldMetaSpecial.none),
              FieldMetaInfo('integer', FieldMetaType.integer,
                            FieldMetaSpecial.none),
              FieldMetaInfo('real', FieldMetaType.float,
                            FieldMetaSpecial.none)]
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
    self.assertEqual(fields, fieldsRead)

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
    self.assertEqual(SENTINEL_VALUE_FOR_MISSING_DATA, recordsRead[1][1])

    # missing int
    self.assertEqual(SENTINEL_VALUE_FOR_MISSING_DATA, recordsRead[2][2])

    # missing float
    self.assertEqual(SENTINEL_VALUE_FOR_MISSING_DATA, recordsRead[3][3])

    # sentinel value in input handled correctly for int field
    self.assertNotEqual(SENTINEL_VALUE_FOR_MISSING_DATA, recordsRead[4][2])

    # sentinel value in input handled correctly for float field
    self.assertNotEqual(SENTINEL_VALUE_FOR_MISSING_DATA, recordsRead[5][3])

    # sentinel value in input handled correctly for string field
    # this should leave the string as-is, since a missing string
    # is encoded not with a sentinel value but with an empty string
    self.assertNotEqual(SENTINEL_VALUE_FOR_MISSING_DATA, recordsRead[6][1])



if __name__ == '__main__':
  unittest.main()
