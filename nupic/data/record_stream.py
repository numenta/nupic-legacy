# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
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

"""Interface for different types of storages (file, hbase, rio, etc)."""

from abc import ABCMeta, abstractmethod
import datetime


from nupic.data.fieldmeta import FieldMetaSpecial



def _getFieldIndexBySpecial(fields, special):
  """ Return index of the field matching the field meta special value.
  :param fields: sequence of nupic.data.fieldmeta.FieldMetaInfo objects
    representing the fields of a stream
  :param special: one of the special field attribute values from
    nupic.data.fieldmeta.FieldMetaSpecial
  :returns: first zero-based index of the field tagged with the target field
    meta special attribute; None if no such field
  """
  for i, field in enumerate(fields):
    if field.special == special:
      return i
  return None



class ModelRecordEncoder(object):
  """Encodes metric data input rows  for consumption by OPF models. See
  the `ModelRecordEncoder.encode` method for more details.
  """


  def __init__(self, fields, aggregationPeriod=None):
    """
    :param fields: non-empty sequence of nupic.data.fieldmeta.FieldMetaInfo
      objects corresponding to fields in input rows.
    :param dict aggregationPeriod: aggregation period of the record stream as a
      dict containing 'months' and 'seconds'. The months is always an integer
      and seconds is a floating point. Only one is allowed to be non-zero at a
      time. If there is no aggregation associated with the stream, pass None.
      Typically, a raw file or hbase stream will NOT have any aggregation info,
      but subclasses of RecordStreamIface, like StreamReader, will and will
      provide the aggregation period. This is used by the encode method to
      assign a record number to a record given its timestamp and the aggregation
      interval.
    """
    if not fields:
      raise ValueError('fields arg must be non-empty, but got %r' % (fields,))

    self._fields = fields
    self._aggregationPeriod = aggregationPeriod

    self._sequenceId = -1

    self._fieldNames = tuple(f.name for f in fields)

    self._categoryFieldIndex = _getFieldIndexBySpecial(
      fields,
      FieldMetaSpecial.category)

    self._resetFieldIndex = _getFieldIndexBySpecial(
      fields,
      FieldMetaSpecial.reset)

    self._sequenceFieldIndex = _getFieldIndexBySpecial(
      fields,
      FieldMetaSpecial.sequence)

    self._timestampFieldIndex = _getFieldIndexBySpecial(
      fields,
      FieldMetaSpecial.timestamp)

    self._learningFieldIndex = _getFieldIndexBySpecial(
      fields,
      FieldMetaSpecial.learning)


  def rewind(self):
    """Put us back at the beginning of the file again """
    self._sequenceId = -1


  def encode(self, inputRow):
    """Encodes the given input row as a dict, with the
    keys being the field names. This also adds in some meta fields:
      '_category': The value from the category field (if any)
      '_reset': True if the reset field was True (if any)
      '_sequenceId': the value from the sequenceId field (if any)

    :param inputRow: sequence of values corresponding to a single input metric
      data row
    :rtype: dict
    """

    # Create the return dict
    result = dict(zip(self._fieldNames, inputRow))

    # Add in the special fields
    if self._categoryFieldIndex is not None:
      # category value can be an int or a list
      if isinstance(inputRow[self._categoryFieldIndex], int):
        result['_category'] = [inputRow[self._categoryFieldIndex]]
      else:
        result['_category'] = (inputRow[self._categoryFieldIndex]
                               if inputRow[self._categoryFieldIndex]
                               else [None])
    else:
      result['_category'] = [None]

    if self._resetFieldIndex is not None:
      result['_reset'] = int(bool(inputRow[self._resetFieldIndex]))
    else:
      result['_reset'] = 0

    if self._learningFieldIndex is not None:
      result['_learning'] = int(bool(inputRow[self._learningFieldIndex]))

    result['_timestampRecordIdx'] = None
    if self._timestampFieldIndex is not None:
      result['_timestamp'] = inputRow[self._timestampFieldIndex]
      # Compute the record index based on timestamp
      result['_timestampRecordIdx'] = self._computeTimestampRecordIdx(
        inputRow[self._timestampFieldIndex])
    else:
      result['_timestamp'] = None

    # -----------------------------------------------------------------------
    # Figure out the sequence ID
    hasReset = self._resetFieldIndex is not None
    hasSequenceId = self._sequenceFieldIndex is not None
    if hasReset and not hasSequenceId:
      # Reset only
      if result['_reset']:
        self._sequenceId += 1
      sequenceId = self._sequenceId

    elif not hasReset and hasSequenceId:
      sequenceId = inputRow[self._sequenceFieldIndex]
      result['_reset'] = int(sequenceId != self._sequenceId)
      self._sequenceId = sequenceId

    elif hasReset and hasSequenceId:
      sequenceId = inputRow[self._sequenceFieldIndex]

    else:
      sequenceId = 0

    if sequenceId is not None:
      result['_sequenceId'] = hash(sequenceId)
    else:
      result['_sequenceId'] = None

    return result


  def _computeTimestampRecordIdx(self, recordTS):
    """ Give the timestamp of a record (a datetime object), compute the record's
    timestamp index - this is the timestamp divided by the aggregation period.


    Parameters:
    ------------------------------------------------------------------------
    recordTS:  datetime instance
    retval:    record timestamp index, or None if no aggregation period
    """

    if self._aggregationPeriod is None:
      return None

    # Base record index on number of elapsed months if aggregation is in
    #  months
    if self._aggregationPeriod['months'] > 0:
      assert self._aggregationPeriod['seconds'] == 0
      result = int(
        (recordTS.year * 12 + (recordTS.month-1)) /
        self._aggregationPeriod['months'])

    # Base record index on elapsed seconds
    elif self._aggregationPeriod['seconds'] > 0:
      delta = recordTS - datetime.datetime(year=1, month=1, day=1)
      deltaSecs = delta.days * 24 * 60 * 60   \
                + delta.seconds               \
                + delta.microseconds / 1000000.0
      result = int(deltaSecs / self._aggregationPeriod['seconds'])

    else:
      result = None

    return result



class RecordStreamIface(object):
  """This is the interface for the record input/output storage classes."""

  __metaclass__ = ABCMeta


  def __init__(self):
    # Will be initialized on-demand in getNextRecordDict with a
    # ModelRecordEncoder instance, once encoding metadata is available
    self._modelRecordEncoder = None


  @abstractmethod
  def close(self):
    """ Close the stream
    """


  def rewind(self):
    """Put us back at the beginning of the file again) """
    if self._modelRecordEncoder is not None:
      self._modelRecordEncoder.rewind()


  @abstractmethod
  def getNextRecord(self, useCache=True):
    """Returns next available data record from the storage. If useCache is
    False, then don't read ahead and don't cache any records.

    Raises nupic.support.exceptions.StreamDisappearedError if stream
    disappears (e.g., gets garbage-collected).

    retval: a data row (a list or tuple) if available; None, if no more records
             in the table (End of Stream - EOS); empty sequence (list or tuple)
             when timing out while waiting for the next record.
    """


  def getNextRecordDict(self):
    """Returns next available data record from the storage as a dict, with the
    keys being the field names. This also adds in some meta fields:
      '_category': The value from the category field (if any)
      '_reset': True if the reset field was True (if any)
      '_sequenceId': the value from the sequenceId field (if any)

    """

    values = self.getNextRecord()
    if values is None:
      return None

    if not values:
      return dict()

    if self._modelRecordEncoder is None:
      self._modelRecordEncoder = ModelRecordEncoder(
        fields=self.getFields(),
        aggregationPeriod=self.getAggregationMonthsAndSeconds())

    return self._modelRecordEncoder.encode(values)



  def getAggregationMonthsAndSeconds(self):
    """ Returns the aggregation period of the record stream as a dict
    containing 'months' and 'seconds'. The months is always an integer and
    seconds is a floating point. Only one is allowed to be non-zero.

    If there is no aggregation associated with the stream, returns None.

    Typically, a raw file or hbase stream will NOT have any aggregation info,
    but subclasses of RecordStreamIFace, like StreamReader, will and will
    return the aggregation period from this call. This call is used by the
    getNextRecordDict() method to assign a record number to a record given
    its timestamp and the aggregation interval

    Parameters:
    ------------------------------------------------------------------------
    retval: aggregationPeriod (as a dict) or None
              'months': number of months in aggregation period
              'seconds': number of seconds in aggregation period (as a float)
    """
    return None


  @abstractmethod
  def getRecordsRange(self, bookmark=None, range=None):
    """Returns a range of records, starting from the bookmark. If 'bookmark'
    is None, then records read from the first available. If 'range' is
    None, all available records will be returned (caution: this could be
    a lot of records and require a lot of memory).
    """


  @abstractmethod
  def getNextRecordIdx(self):
    """Returns the index of the record that will be read next from
    getNextRecord()
    """


  @abstractmethod
  def getLastRecords(self, numRecords):
    """Returns a tuple (successCode, recordsArray), where
    successCode - if the stream had enough records to return, True/False
    recordsArray - an array of last numRecords records available when
                   the call was made. Records appended while in the
                   getLastRecords will be not returned until the next
                   call to either getNextRecord() or getLastRecords()
    """


  @abstractmethod
  def removeOldData(self):
    """Deletes all rows from the table if any data was found."""


  @abstractmethod
  def appendRecord(self, record, inputRef=None):
    """Saves the record in the underlying storage."""


  @abstractmethod
  def appendRecords(self, records, inputRef=None, progressCB=None):
    """Saves multiple records in the underlying storage."""


  @abstractmethod
  def getBookmark(self):
    """Returns an anchor to the current position in the data. Passing this
    anchor to the constructor makes the current position to be the first
    returned record. If record is no longer in the storage, the first available
    after it will be returned.
    """


  @abstractmethod
  def recordsExistAfter(self, bookmark):
    """Returns True iff there are records left after the  bookmark."""


  @abstractmethod
  def seekFromEnd(self, numRecords):
    """Returns a bookmark numRecords from the end of the stream."""


  @abstractmethod
  def getStats(self):
    """Returns storage stats (like min and max values of the fields)."""


  def getFieldMin(self, fieldName):
    """ Returns current minimum value for the field 'fieldName'.

    If underlying implementation does not support min/max stats collection,
    or if a field type does not support min/max (non scalars), the return
    value will be None.
    """
    stats = self.getStats()
    if stats == None:
      return None
    minValues = stats.get('min', None)
    if minValues == None:
      return None
    index = self.getFieldNames().index(fieldName)
    return minValues[index]


  def getFieldMax(self, fieldName):
    """ Returns current maximum value for the field 'fieldName'.

    If underlying implementation does not support min/max stats collection,
    or if a field type does not support min/max (non scalars), the return
    value will be None.
    """
    stats = self.getStats()
    if stats == None:
      return None
    maxValues = stats.get('max', None)
    if maxValues == None:
      return None
    index = self.getFieldNames().index(fieldName)
    return maxValues[index]


  @abstractmethod
  def clearStats(self):
    """Resets stats collected so far."""


  @abstractmethod
  def getError(self):
    """Returns errors saved in the storage."""


  @abstractmethod
  def setError(self, error):
    """Saves specified error in the storage."""


  @abstractmethod
  def isCompleted(self):
    """Returns True if all records are already in the storage or False
    if more records is expected.
    """


  @abstractmethod
  def setCompleted(self, completed):
    """Marks the stream completed (True or False)."""


  @abstractmethod
  def getFieldNames(self):
    """Returns an array of field names associated with the data."""


  @abstractmethod
  def getFields(self):
    """Returns a sequence of nupic.data.fieldmeta.FieldMetaInfo
    name/type/special tuples for each field in the stream. Might be None, if
    that information is provided externally (thru stream def, for example).
    """


  def getResetFieldIdx(self):
    """
    :returns: index of the 'reset' field; None if no such field. """
    return _getFieldIndexBySpecial(self.getFields(), FieldMetaSpecial.reset)


  def getTimestampFieldIdx(self):
    """ Return index of the 'timestamp' field. """
    return _getFieldIndexBySpecial(self.getFields(), FieldMetaSpecial.timestamp)


  def getSequenceIdFieldIdx(self):
    """ Return index of the 'sequenceId' field. """
    return _getFieldIndexBySpecial(self.getFields(), FieldMetaSpecial.sequence)


  def getCategoryFieldIdx(self):
    """ Return index of the 'category' field. """
    return _getFieldIndexBySpecial(self.getFields(), FieldMetaSpecial.category)


  def getLearningFieldIdx(self):
    """ Return index of the 'learning' field. """
    return _getFieldIndexBySpecial(self.getFields(), FieldMetaSpecial.learning)


  @abstractmethod
  def setTimeout(self, timeout):
    """ Set the read timeout in seconds (int or floating point) """


  @abstractmethod
  def flush(self):
    """ Flush the file to disk """
