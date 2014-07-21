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

"""Interface for different types of storages (file, hbase, rio, etc)."""

from abc import ABCMeta, abstractmethod
import datetime


##############################################################################
##############################################################################
class RecordStreamIface(object):
  """This is the interface for the record input/output storage classes."""

  __metaclass__ = ABCMeta


  ##############################################################################
  def __init__(self):
    self._sequenceId = -1
  
  ##############################################################################
  @abstractmethod
  def close(self):
    """ Close the stream
    """

  ##############################################################################
  def rewind(self):
    """Put us back at the beginning of the file again) """
    self._sequenceId = -1

  ##############################################################################
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

  ##############################################################################
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
    
    # Create the return dict
    result = dict(zip(self.getFieldNames(), values))
    
    # Add in the special fields
    catIdx = self.getCategoryFieldIdx()
    resetIdx = self.getResetFieldIdx()
    sequenceIdx = self.getSequenceIdFieldIdx()
    timeIdx = self.getTimestampFieldIdx()
    learningIdx = self.getLearningFieldIdx()

    if catIdx is not None:
      result['_category'] = values[catIdx]
    else:
      result['_category'] = None

    if resetIdx is not None:
      result['_reset'] = int(bool(values[resetIdx]))
    else:
      result['_reset'] = 0
      
    if learningIdx is not None:
      result['_learning'] = int(bool(values[learningIdx]))
      
    result['_timestampRecordIdx'] = None
    if timeIdx is not None:
      result['_timestamp'] = values[timeIdx]      
      # Compute the record index based on timestamp
      result['_timestampRecordIdx'] = self._computeTimestampRecordIdx(
                                                        values[timeIdx])
    else:
      result['_timestamp'] = None
    
    # -----------------------------------------------------------------------
    # Figure out the sequence ID
    hasReset = resetIdx is not None
    hasSequenceId = sequenceIdx is not None
    if hasReset and not hasSequenceId:
      # Reset only
      if result['_reset']:
        try:
          self._sequenceId += 1
        except:
          import pdb; pdb.set_trace() 
      sequenceId = self._sequenceId
      
    elif not hasReset and hasSequenceId:
      sequenceId = values[sequenceIdx]
      result['_reset'] = int(sequenceId != self._sequenceId)
      self._sequenceId = sequenceId
      
    elif hasReset and hasSequenceId:
      sequenceId = values[sequenceIdx]
      
    else:
      sequenceId = 0
      
    if sequenceId is not None:
      result['_sequenceId'] = hash(sequenceId)
    else:
      result['_sequenceId'] = None
    
    return result


  ##############################################################################
  def _computeTimestampRecordIdx(self, recordTS):
    """ Give the timestamp of a record (a datetime object), compute the record's
    timestamp index - this is the timestamp divided by the aggregation period. 
    
    
    Parameters:
    ------------------------------------------------------------------------
    recordTS:  datetime instance
    retval:    record timestamp index, or None if no aggregation period 
    """
    
    aggPeriod = self.getAggregationMonthsAndSeconds()
    if aggPeriod is None:
      return None
    
    # Base record index on number of elapsed months if aggregation is in 
    #  months
    if aggPeriod['months'] > 0:
      assert aggPeriod['seconds'] == 0
      result = \
        int((recordTS.year * 12 + (recordTS.month-1)) / aggPeriod['months'])
        
    # Base record index on elapsed seconds
    elif aggPeriod['seconds'] > 0:
      delta = recordTS - datetime.datetime(year=1, month=1, day=1)
      deltaSecs = delta.days * 24 * 60 * 60   \
                + delta.seconds               \
                + delta.microseconds / 1000000.0
      result = int(deltaSecs / aggPeriod['seconds'])
    
    else:
      result = None
      
    return result



  ##############################################################################
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

  ##############################################################################
  @abstractmethod
  def getRecordsRange(self, bookmark=None, range=None):
    """Returns a range of records, starting from the bookmark. If 'bookmark'
    is None, then records read from the first available. If 'range' is
    None, all available records will be returned (caution: this could be
    a lot of records and require a lot of memory).
    """

  ##############################################################################
  @abstractmethod
  def getNextRecordIdx(self):
    """Returns the index of the record that will be read next from getNextRecord()
    """

  ##############################################################################
  @abstractmethod
  def getLastRecords(self, numRecords):
    """Returns a tuple (successCode, recordsArray), where
    successCode - if the stream had enough records to return, True/False
    recordsArray - an array of last numRecords records available when
                   the call was made. Records appended while in the
                   getLastRecords will be not returned until the next
                   call to either getNextRecord() or getLastRecords()
    """

  ##############################################################################
  @abstractmethod
  def removeOldData(self):
    """Deletes all rows from the table if any data was found."""

  ##############################################################################
  @abstractmethod
  def appendRecord(self, record, inputRef=None):
    """Saves the record in the underlying storage."""

  ##############################################################################
  @abstractmethod
  def appendRecords(self, records, inputRef=None, progressCB=None):
    """Saves multiple records in the underlying storage."""

  ##############################################################################
  @abstractmethod
  def getBookmark(self):
    """Returns an anchor to the current position in the data. Passing this
    anchor to the constructor makes the current position to be the first
    returned record. If record is no longer in the storage, the first available
    after it will be returned.
    """

  ##############################################################################
  @abstractmethod
  def recordsExistAfter(self, bookmark):
    """Returns True iff there are records left after the  bookmark."""

  ##############################################################################
  @abstractmethod
  def seekFromEnd(self, numRecords):
    """Returns a bookmark numRecords from the end of the stream."""

  ##############################################################################
  @abstractmethod
  def getStats(self):
    """Returns storage stats (like min and max values of the fields)."""

  ##############################################################################
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


  ##############################################################################
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


  ##############################################################################
  @abstractmethod
  def clearStats(self):
    """Resets stats collected so far."""

  ##############################################################################
  @abstractmethod
  def getError(self):
    """Returns errors saved in the storage."""

  ##############################################################################
  @abstractmethod
  def setError(self, error):
    """Saves specified error in the storage."""

  ##############################################################################
  @abstractmethod
  def isCompleted(self):
    """Returns True if all records are already in the storage or False
    if more records is expected.
    """

  ##############################################################################
  @abstractmethod
  def setCompleted(self, completed):
    """Marks the stream completed (True or False)."""

  ##############################################################################
  @abstractmethod
  def getFieldNames(self):
    """Returns an array of field names associated with the data."""

  ##############################################################################
  @abstractmethod
  def getFields(self):
    """Returns a sequence of nupic.data.fieldmeta.FieldMetaInfo
    name/type/special tuples for each field in the stream. Might be None, if
    that information is provided externally (thru stream def, for example).
    """

  #############################################################################
  def getResetFieldIdx(self):
    """ Index of the 'reset' field. """
    for i, field in enumerate(self.getFields()):
      if field[2] == 'R' or field[2] == 'r':
        return i
    return None


  #############################################################################
  def getTimestampFieldIdx(self):
    """ Index of the 'timestamp' field. """
    for i, field in enumerate(self.getFields()):
      if field[2] == 'T' or field[2] == 't':
        return i
    return None


  #############################################################################
  def getSequenceIdFieldIdx(self):
    """ Index of the 'sequenceId' field. """
    for i, field in enumerate(self.getFields()):
      if field[2] == 'S' or field[2] == 's':
        return i
    return None
      
      
  #############################################################################
  def getCategoryFieldIdx(self):
    """ Index of the 'category' field. """
    for i, field in enumerate(self.getFields()):
      if field[2] == 'C' or field[2] == 'c':
        return i
    return None
  
  #############################################################################
  def getLearningFieldIdx(self):
    """ Index of the 'learning' field. """
    for i, field in enumerate(self.getFields()):
      if field[2] == 'L' or field[2] == 'l':
        return i
    return None


  ##############################################################################
  @abstractmethod
  def setTimeout(self, timeout):
    """ Set the read timeout in seconds (int or floating point) """

  #############################################################################
  @abstractmethod
  def flush(self):
    """ Flush the file to disk """
