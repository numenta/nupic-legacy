# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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

"""Unit tests for nupic.data.record_stream."""

from datetime import datetime
import unittest

import mock


from nupic.data.fieldmeta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial
from nupic.data.record_stream import ModelRecordEncoder, RecordStreamIface



class ModelRecordEncoderTest(unittest.TestCase):


  def testEmptyFieldsArgRaisesValueErrorInConstructor(self):
    with self.assertRaises(ValueError):
      ModelRecordEncoder(fields=[])


  def testEncoderWithSequenceAndResetFields(self):
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
                    FieldMetaSpecial.category)
    ]


    encoder = ModelRecordEncoder(fields=fields)

    result = encoder.encode(
      ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1, 99,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_1',
        'timestamp': datetime(2010, 3, 1, 0, 0),
        'integer': 5,
        'real': 6.5,
        'reset': 1,
        'sid': 99,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 1,
        '_sequenceId': 99,
        '_timestamp': datetime(2010, 3, 1, 0, 0),
        '_timestampRecordIdx': None })


  def testEncoderWithResetFieldWithoutSequenceField(self):
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
      FieldMetaInfo('categories', FieldMetaType.list,
                    FieldMetaSpecial.category)
    ]


    encoder = ModelRecordEncoder(fields=fields)

    result = encoder.encode(
      ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_1',
        'timestamp': datetime(2010, 3, 1, 0, 0),
        'integer': 5,
        'real': 6.5,
        'reset': 1,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 1,
        '_sequenceId': 0,
        '_timestamp': datetime(2010, 3, 1, 0, 0),
        '_timestampRecordIdx': None })

    # One more time to verify incremeting sequence id
    result = encoder.encode(
      ['rec_2', datetime(day=2, month=3, year=2010), 5, 6.5, 1,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_2',
        'timestamp': datetime(2010, 3, 2, 0, 0),
        'integer': 5,
        'real': 6.5,
        'reset': 1,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 1,
        '_sequenceId': 1,
        '_timestamp': datetime(2010, 3, 2, 0, 0),
        '_timestampRecordIdx': None })

    # Now with reset turned off, expecting no change to sequence id
    result = encoder.encode(
      ['rec_3', datetime(day=3, month=3, year=2010), 5, 6.5, 0,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_3',
        'timestamp': datetime(2010, 3, 3, 0, 0),
        'integer': 5,
        'real': 6.5,
        'reset': 0,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 0,
        '_sequenceId': 1,
        '_timestamp': datetime(2010, 3, 3, 0, 0),
        '_timestampRecordIdx': None })

    # Now check that rewind resets sequence id
    encoder.rewind()
    result = encoder.encode(
      ['rec_4', datetime(day=4, month=3, year=2010), 5, 6.5, 1,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_4',
        'timestamp': datetime(2010, 3, 4, 0, 0),
        'integer': 5,
        'real': 6.5,
        'reset': 1,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 1,
        '_sequenceId': 0,
        '_timestamp': datetime(2010, 3, 4, 0, 0),
        '_timestampRecordIdx': None })


  def testEncoderWithSequenceFieldWithoutResetField(self):
    fields = [
      FieldMetaInfo('name', FieldMetaType.string,
                    FieldMetaSpecial.none),
      FieldMetaInfo('timestamp', FieldMetaType.datetime,
                    FieldMetaSpecial.timestamp),
      FieldMetaInfo('integer', FieldMetaType.integer,
                    FieldMetaSpecial.none),
      FieldMetaInfo('real', FieldMetaType.float,
                    FieldMetaSpecial.none),
      FieldMetaInfo('sid', FieldMetaType.string,
                    FieldMetaSpecial.sequence),
      FieldMetaInfo('categories', FieldMetaType.list,
                    FieldMetaSpecial.category)
    ]


    encoder = ModelRecordEncoder(fields=fields)

    # _reset should be 1 the first time
    result = encoder.encode(
      ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 99,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_1',
        'timestamp': datetime(2010, 3, 1, 0, 0),
        'integer': 5,
        'real': 6.5,
        'sid': 99,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 1,
        '_sequenceId': 99,
        '_timestamp': datetime(2010, 3, 1, 0, 0),
        '_timestampRecordIdx': None })

    # _reset should be 0 when same sequence id is repeated
    result = encoder.encode(
      ['rec_2', datetime(day=2, month=3, year=2010), 5, 6.5, 99,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_2',
        'timestamp': datetime(2010, 3, 2, 0, 0),
        'integer': 5,
        'real': 6.5,
        'sid': 99,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 0,
        '_sequenceId': 99,
        '_timestamp': datetime(2010, 3, 2, 0, 0),
        '_timestampRecordIdx': None })

    # _reset should be 1 when sequence id changes
    result = encoder.encode(
      ['rec_3', datetime(day=2, month=3, year=2010), 5, 6.5, 100,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_3',
        'timestamp': datetime(2010, 3, 2, 0, 0),
        'integer': 5,
        'real': 6.5,
        'sid': 100,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 1,
        '_sequenceId': 100,
        '_timestamp': datetime(2010, 3, 2, 0, 0),
        '_timestampRecordIdx': None })



  def testEncoderWithoutResetAndSequenceFields(self):
    fields = [
      FieldMetaInfo('name', FieldMetaType.string,
                    FieldMetaSpecial.none),
      FieldMetaInfo('timestamp', FieldMetaType.datetime,
                    FieldMetaSpecial.timestamp),
      FieldMetaInfo('integer', FieldMetaType.integer,
                    FieldMetaSpecial.none),
      FieldMetaInfo('real', FieldMetaType.float,
                    FieldMetaSpecial.none),
      FieldMetaInfo('categories', FieldMetaType.list,
                    FieldMetaSpecial.category)
    ]


    encoder = ModelRecordEncoder(fields=fields)

    result = encoder.encode(
      ['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_1',
        'timestamp': datetime(2010, 3, 1, 0, 0),
        'integer': 5,
        'real': 6.5,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 0,
        '_sequenceId': 0,
        '_timestamp': datetime(2010, 3, 1, 0, 0),
        '_timestampRecordIdx': None })

    # One more time to verify that sequence id is still 0
    result = encoder.encode(
      ['rec_2', datetime(day=2, month=3, year=2010), 5, 6.5,
       [0, 1, 2]])

    self.assertEqual(
      result,
      {
        'name': 'rec_2',
        'timestamp': datetime(2010, 3, 2, 0, 0),
        'integer': 5,
        'real': 6.5,
        'categories': [0, 1, 2],
        '_category': [0, 1, 2],
        '_reset': 0,
        '_sequenceId': 0,
        '_timestamp': datetime(2010, 3, 2, 0, 0),
        '_timestampRecordIdx': None })



class RecordStreamIfaceTest(unittest.TestCase):


  class MyRecordStream(RecordStreamIface):
    """Record stream class for testing functionality of the RecordStreamIface
    abstract base class
    """

    def __init__(self, fieldsMeta):
      super(RecordStreamIfaceTest.MyRecordStream, self).__init__()
      self._fieldsMeta = fieldsMeta
      self._fieldNames = tuple(f.name for f in fieldsMeta)


    def getNextRecord(self, useCache=True):
      """[ABC method implementation]

      retval: a data row (a list or tuple) if available; None, if no more records
               in the table (End of Stream - EOS); empty sequence (list or tuple)
               when timing out while waiting for the next record.
      """
      # The tests will patch this method to feed data
      pass


    def getFieldNames(self):
      """[ABC method implementation]"""
      return self._fieldNames


    def getFields(self):
      """[ABC method implementation]"""
      return self._fieldsMeta


    # Satisfy Abstract Base Class requirements for the ABC RecordStreamIface
    # methods that are no-ops for the currently-implemented tests.
    close = None
    getRecordsRange = None
    getNextRecordIdx = None
    getLastRecords = None
    removeOldData = None
    appendRecord=None
    appendRecords = None
    getBookmark = None
    recordsExistAfter = None
    seekFromEnd = None
    getStats = None
    clearStats = None
    getError = None
    setError = None
    isCompleted = None
    setCompleted = None
    setTimeout = None
    flush = None


  def testRewindBeforeModelRecordEncoderIsCreated(self):
    fields = [
      FieldMetaInfo('name', FieldMetaType.string,
                    FieldMetaSpecial.none),
    ]

    stream = self.MyRecordStream(fields)

    # Check that it doesn't crash by trying to operate on an absent encoder
    self.assertIsNone(stream._modelRecordEncoder)
    stream.rewind()


  def testGetNextRecordDictWithResetFieldWithoutSequenceField(self):
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
      FieldMetaInfo('categories', FieldMetaType.list,
                    FieldMetaSpecial.category)
    ]


    stream = self.MyRecordStream(fields)


    with mock.patch.object(
        stream, 'getNextRecord', autospec=True,
        return_value=['rec_1', datetime(day=1, month=3, year=2010), 5, 6.5, 1,
                      [0, 1, 2]]):

      result = stream.getNextRecordDict()

      self.assertEqual(
        result,
        {
          'name': 'rec_1',
          'timestamp': datetime(2010, 3, 1, 0, 0),
          'integer': 5,
          'real': 6.5,
          'reset': 1,
          'categories': [0, 1, 2],
          '_category': [0, 1, 2],
          '_reset': 1,
          '_sequenceId': 0,
          '_timestamp': datetime(2010, 3, 1, 0, 0),
          '_timestampRecordIdx': None })

    # One more time to verify incremeting sequence id
    with mock.patch.object(
        stream, 'getNextRecord', autospec=True,
        return_value=['rec_2', datetime(day=2, month=3, year=2010), 5, 6.5, 1,
                      [0, 1, 2]]):

      result = stream.getNextRecordDict()

      self.assertEqual(
        result,
        {
          'name': 'rec_2',
          'timestamp': datetime(2010, 3, 2, 0, 0),
          'integer': 5,
          'real': 6.5,
          'reset': 1,
          'categories': [0, 1, 2],
          '_category': [0, 1, 2],
          '_reset': 1,
          '_sequenceId': 1,
          '_timestamp': datetime(2010, 3, 2, 0, 0),
          '_timestampRecordIdx': None })

    # Now with reset turned off, expecting no change to sequence id
    with mock.patch.object(
        stream, 'getNextRecord', autospec=True,
        return_value=['rec_3', datetime(day=3, month=3, year=2010), 5, 6.5, 0,
                      [0, 1, 2]]):

      result = stream.getNextRecordDict()

      self.assertEqual(
        result,
        {
          'name': 'rec_3',
          'timestamp': datetime(2010, 3, 3, 0, 0),
          'integer': 5,
          'real': 6.5,
          'reset': 0,
          'categories': [0, 1, 2],
          '_category': [0, 1, 2],
          '_reset': 0,
          '_sequenceId': 1,
          '_timestamp': datetime(2010, 3, 3, 0, 0),
          '_timestampRecordIdx': None })

    # Now check that rewind resets sequence id
    with mock.patch.object(
        stream, 'getNextRecord', autospec=True,
        return_value=['rec_4', datetime(day=4, month=3, year=2010), 5, 6.5, 1,
                      [0, 1, 2]]):
      stream.rewind()
      result = stream.getNextRecordDict()

      self.assertEqual(
        result,
        {
          'name': 'rec_4',
          'timestamp': datetime(2010, 3, 4, 0, 0),
          'integer': 5,
          'real': 6.5,
          'reset': 1,
          'categories': [0, 1, 2],
          '_category': [0, 1, 2],
          '_reset': 1,
          '_sequenceId': 0,
          '_timestamp': datetime(2010, 3, 4, 0, 0),
          '_timestampRecordIdx': None })



if __name__ == "__main__":
  unittest.main()
