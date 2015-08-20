#!/usr/bin/env python
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

import os
import logging
import tempfile

import pkg_resources

from nupic.data.aggregator import Aggregator
from nupic.data.fieldmeta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial
from nupic.data.file_record_stream import FileRecordStream
from nupic.data import jsonhelpers
from nupic.data.record_stream import RecordStreamIface
from nupic.frameworks.opf import jsonschema
import nupic.support

FILE_PREF = 'file://'

# If timeout is not set in the configuration file, default is 6 hours
READ_TIMEOUT = 6*60*60



class StreamTimeoutException(Exception):
  """ Defines the exception thrown when the input stream times out receiving
  new records."""
  pass



class StreamReader(RecordStreamIface):
  """
  Implements a stream reader. This is a high level class that owns one or more
  underlying implementations of a RecordStreamIFace. Each RecordStreamIFace
  implements the raw reading of records from the record store (which could be a
  file, hbase table or something else).

  In the future, we will support joining of two or more RecordStreamIface's (
  which is why the streamDef accepts a list of 'stream' elements), but for now
  only 1 source is supported.

  The class also implements aggregation of the (in the future) joined records
  from the sources.

  This module parses the stream definition (as defined in
  /nupic/frameworks/opf/jsonschema/stream_def.json), creates the
  RecordStreamIFace for each source ('stream's element) defined in the stream
  def, performs aggregation, and returns each record in the correct format
  according to the desired column names specified in the streamDef.

  This class implements the RecordStreamIFace interface and thus can be used
  in place of a raw record stream.

  This is an example streamDef:
    {
      'version': 1
      'info': 'test_hotgym',

      'streams': [
          {'columns': [u'*'],
           'info': u'hotGym.csv',
           'last_record': 4000,
           'source': u'file://extra/hotgym/hotgym.csv'}.
      ],

      'timeField': 'timestamp',

      'aggregation': {
        'hours': 1,
        'fields': [
            ('timestamp', 'first'),
            ('gym', 'first'),
            ('consumption', 'sum')
        ],
      }

    }

  """


  def __init__(self, streamDef, bookmark=None, saveOutput=False,
               isBlocking=True, maxTimeout=0, eofOnTimeout=False):
    """ Base class constructor, performs common initialization

    Parameters:
    ----------------------------------------------------------------
    streamDef:  The stream definition, potentially containing multiple sources
                (not supported yet). See
                /nupic/frameworks/opf/jsonschema/stream_def.json for the format
                of this dict

    bookmark: Bookmark to start reading from. This overrides the first_record
                field of the streamDef if provided.

    saveOutput: If true, save the output to a csv file in a temp directory.
                The path to the generated file can be found in the log
                output.

    isBlocking: should read operation block *forever* if the next row of data
                is not available, but the stream is not marked as 'completed'
                yet?

    maxTimeout: if isBlocking is False, max seconds to wait for more data before
                timing out; ignored when isBlocking is True.

    eofOnTimeout: If True and we get a read timeout (isBlocking must be False
                to get read timeouts), assume we've reached the end of the
                input and produce the last aggregated record, if one can be
                completed.

    """

    # Call superclass constructor
    super(StreamReader, self).__init__()

    loggerPrefix = 'com.numenta.nupic.data.StreamReader'
    self._logger = logging.getLogger(loggerPrefix)
    jsonhelpers.validate(streamDef,
                         schemaPath=pkg_resources.resource_filename(
                             jsonschema.__name__, "stream_def.json"))
    assert len(streamDef['streams']) == 1, "Only 1 source stream is supported"

    # Save constructor args
    sourceDict = streamDef['streams'][0]
    self._recordCount = 0
    self._eofOnTimeout = eofOnTimeout
    self._logger.debug('Reading stream with the def: %s', sourceDict)

    # Dictionary to store record statistics (min and max of scalars for now)
    self._stats = None

    # ---------------------------------------------------------------------
    # Get the stream definition params

    # Limiting window of the stream. It would not return any records until
    # 'first_record' ID is read (or very first with the ID above that). The
    # stream will return EOS once it reads record with ID 'last_record' or
    # above (NOTE: the name 'lastRecord' is misleading because it is NOT
    #  inclusive).
    firstRecordIdx = sourceDict.get('first_record', None)
    self._sourceLastRecordIdx = sourceDict.get('last_record', None)

    # If a bookmark was given, then override first_record from the stream
    #  definition.
    if bookmark is not None:
      firstRecordIdx = None


    # Column names must be provided in the streamdef json
    # Special case is ['*'], meaning all available names from the record stream
    self._streamFieldNames = sourceDict.get('columns', None)
    if self._streamFieldNames != None and self._streamFieldNames[0] == '*':
      self._needFieldsFiltering = False
    else:
      self._needFieldsFiltering = True

    # Types must be specified in streamdef json, or in case of the
    #  file_recod_stream types could be implicit from the file
    streamFieldTypes = sourceDict.get('types', None)
    self._logger.debug('Types from the def: %s', streamFieldTypes)
    # Validate that all types are valid
    if streamFieldTypes is not None:
      for dataType in streamFieldTypes:
        assert FieldMetaType.isValid(dataType)

    # Reset, sequence and time fields might be provided by streamdef json
    streamResetFieldName = streamDef.get('resetField', None)
    streamTimeFieldName = streamDef.get('timeField', None)
    streamSequenceFieldName = streamDef.get('sequenceIdField', None)
    self._logger.debug('r, t, s fields: %s, %s, %s', streamResetFieldName,
                                                      streamTimeFieldName,
                                                      streamSequenceFieldName)


    # =======================================================================
    # Open up the underlying record store
    dataUrl = sourceDict.get('source', None)
    assert dataUrl is not None
    self._recordStore = self._openStream(dataUrl, isBlocking, maxTimeout,
                                         bookmark, firstRecordIdx)
    assert self._recordStore is not None


    # =======================================================================
    # Prepare the data structures we need for returning just the fields
    #  the caller wants from each record
    recordStoreFields = self._recordStore.getFields()
    self._recordStoreFieldNames = self._recordStore.getFieldNames()

    if not self._needFieldsFiltering:
      self._streamFieldNames = self._recordStoreFieldNames

    # Build up the field definitions for each field. This is a list of tuples
    #  of (name, type, special)
    self._streamFields = []
    for dstIdx, name in enumerate(self._streamFieldNames):
      if name not in self._recordStoreFieldNames:
        raise RuntimeError("The column '%s' from the stream definition "
          "is not present in the underlying stream which has the following "
          "columns: %s" % (name, self._recordStoreFieldNames))

      fieldIdx = self._recordStoreFieldNames.index(name)
      fieldType = recordStoreFields[fieldIdx].type
      fieldSpecial = recordStoreFields[fieldIdx].special

      # If the types or specials were defined in the stream definition,
      #   then override what was found in the record store
      if streamFieldTypes is not None:
        fieldType = streamFieldTypes[dstIdx]

      if streamResetFieldName is not None and streamResetFieldName == name:
        fieldSpecial = FieldMetaSpecial.reset
      if streamTimeFieldName is not None and streamTimeFieldName == name:
        fieldSpecial = FieldMetaSpecial.timestamp
      if (streamSequenceFieldName is not None and
          streamSequenceFieldName == name):
        fieldSpecial = FieldMetaSpecial.sequence

      self._streamFields.append(FieldMetaInfo(name, fieldType, fieldSpecial))


    # ========================================================================
    # Create the aggregator which will handle aggregation of records before
    #  returning them.
    self._aggregator = Aggregator(
            aggregationInfo=streamDef.get('aggregation', None),
            inputFields=recordStoreFields,
            timeFieldName=streamDef.get('timeField', None),
            sequenceIdFieldName=streamDef.get('sequenceIdField', None),
            resetFieldName=streamDef.get('resetField', None))

    # We rely on the aggregator to tell us the bookmark of the last raw input
    #  that contributed to the aggregated record
    self._aggBookmark = None

    # Compute the aggregation period in terms of months and seconds
    if 'aggregation' in streamDef:
      self._aggMonthsAndSeconds = nupic.support.aggregationToMonthsSeconds(
                streamDef.get('aggregation'))
    else:
      self._aggMonthsAndSeconds = None


    # ========================================================================
    # Are we saving the generated output to a csv?
    if saveOutput:
      tmpDir = tempfile.mkdtemp()
      outFilename = os.path.join(tmpDir, "generated_output.csv")
      self._logger.info("StreamReader: Saving generated records to: '%s'" %
                        outFilename)
      self._writer = FileRecordStream(streamID=outFilename,
                                      write=True,
                                      fields=self._streamFields)
    else:
      self._writer = None


  @staticmethod
  def _openStream(dataUrl,
                  isBlocking,  # pylint: disable=W0613
                  maxTimeout,  # pylint: disable=W0613
                  bookmark,
                  firstRecordIdx):
    """Open the underlying file stream
    This only supports 'file://' prefixed paths.

    :returns: record stream instance
    :rtype: FileRecordStream
    """
    filePath = dataUrl[len(FILE_PREF):]
    if not os.path.isabs(filePath):
      filePath = os.path.join(os.getcwd(), filePath)
    return FileRecordStream(streamID=filePath,
                            write=False,
                            bookmark=bookmark,
                            firstRecord=firstRecordIdx)


  def close(self):
    """ Close the stream
    """
    return self._recordStore.close()


  def getNextRecord(self):
    """ Returns combined data from all sources (values only).
    Returns None on EOF; empty sequence on timeout.
    """


    # Keep reading from the raw input till we get enough for an aggregated
    #  record
    while True:

      # Reached EOF due to lastRow constraint?
      if self._sourceLastRecordIdx is not None  and \
          self._recordStore.getNextRecordIdx() >= self._sourceLastRecordIdx:
        preAggValues = None                             # indicates EOF
        bookmark = self._recordStore.getBookmark()

      else:
        # Get the raw record and bookmark
        preAggValues = self._recordStore.getNextRecord()
        bookmark = self._recordStore.getBookmark()

      if preAggValues == ():  # means timeout error occurred
        if self._eofOnTimeout:
          preAggValues = None  # act as if we got EOF
        else:
          return preAggValues  # Timeout indicator

      self._logger.debug('Read source record #%d: %r',
                        self._recordStore.getNextRecordIdx()-1, preAggValues)

      # Perform aggregation
      (fieldValues, aggBookmark) = self._aggregator.next(preAggValues, bookmark)

      # Update the aggregated record bookmark if we got a real record back
      if fieldValues is not None:
        self._aggBookmark = aggBookmark

      # Reached EOF?
      if preAggValues is None and fieldValues is None:
        return None

      # Return it if we have a record
      if fieldValues is not None:
        break


    # Do we need to re-order the fields in the record?
    if self._needFieldsFiltering:
      values = []
      srcDict = dict(zip(self._recordStoreFieldNames, fieldValues))
      for name in self._streamFieldNames:
        values.append(srcDict[name])
      fieldValues = values


    # Write to debug output?
    if self._writer is not None:
      self._writer.appendRecord(fieldValues)

    self._recordCount += 1

    self._logger.debug('Returning aggregated record #%d from getNextRecord(): '
                      '%r. Bookmark: %r',
                      self._recordCount-1, fieldValues, self._aggBookmark)
    return fieldValues


  def getDataRowCount(self):
    """Iterates through stream to calculate total records after aggregation.
    This will alter the bookmark state.
    """
    inputRowCountAfterAggregation = 0
    while True:
      record = self.getNextRecord()
      if record is None:
        return inputRowCountAfterAggregation
      inputRowCountAfterAggregation += 1

      if inputRowCountAfterAggregation > 10000:
        raise RuntimeError('No end of datastream found.')


  def getLastRecords(self, numRecords):
    """Saves the record in the underlying storage."""
    raise RuntimeError("Not implemented in StreamReader")


  def getRecordsRange(self, bookmark=None, range=None):
    """ Returns a range of records, starting from the bookmark. If 'bookmark'
    is None, then records read from the first available. If 'range' is
    None, all available records will be returned (caution: this could be
    a lot of records and require a lot of memory).
    """
    raise RuntimeError("Not implemented in StreamReader")


  def getNextRecordIdx(self):
    """Returns the index of the record that will be read next from
    getNextRecord()
    """
    return self._recordCount


  def recordsExistAfter(self, bookmark):
    """Returns True iff there are records left after the  bookmark."""
    return self._recordStore.recordsExistAfter(bookmark)


  def getAggregationMonthsAndSeconds(self):
    """ Returns the aggregation period of the record stream as a dict
    containing 'months' and 'seconds'. The months is always an integer and
    seconds is a floating point. Only one is allowed to be non-zero at a
    time.

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
    return self._aggMonthsAndSeconds


  def appendRecord(self, record, inputRef=None):
    """Saves the record in the underlying storage."""
    raise RuntimeError("Not implemented in StreamReader")


  def appendRecords(self, records, inputRef=None, progressCB=None):
    """Saves multiple records in the underlying storage."""
    raise RuntimeError("Not implemented in StreamReader")


  def removeOldData(self):
    raise RuntimeError("Not implemented in StreamReader")


  def seekFromEnd(self, numRecords):
    """Seeks to numRecords from the end and returns a bookmark to the new
    position.
    """
    raise RuntimeError("Not implemented in StreamReader")


  def getFieldNames(self):
    """ Returns all fields in all inputs (list of plain names).
    NOTE: currently, only one input is supported
    """
    return [f.name for f in self._streamFields]


  def getFields(self):
    """ Returns a sequence of nupic.data.fieldmeta.FieldMetaInfo
    name/type/special tuples for each field in the stream.
    """
    return self._streamFields


  def getBookmark(self):
    """ Returns a bookmark to the current position
    """
    return self._aggBookmark


  def clearStats(self):
    """ Resets stats collected so far.
    """
    self._recordStore.clearStats()


  def getStats(self):
    """ Returns stats (like min and max values of the fields).

    TODO: This method needs to be enhanced to get the stats on the *aggregated*
    records.
    """

    # The record store returns a dict of stats, each value in this dict is
    #  a list with one item per field of the record store
    #         {
    #           'min' : [f1_min, f2_min, f3_min],
    #           'max' : [f1_max, f2_max, f3_max]
    #         }
    recordStoreStats = self._recordStore.getStats()

    # We need to convert each item to represent the fields of the *stream*
    streamStats = dict()
    for (key, values) in recordStoreStats.items():
      fieldStats = dict(zip(self._recordStoreFieldNames, values))
      streamValues = []
      for name in self._streamFieldNames:
        streamValues.append(fieldStats[name])
      streamStats[key] = streamValues

    return streamStats


  def getError(self):
    """ Returns errors saved in the stream.
    """
    return self._recordStore.getError()


  def setError(self, error):
    """ Saves specified error in the stream.
    """
    self._recordStore.setError(error)


  def isCompleted(self):
    """ Returns True if all records have been read.
    """
    return self._recordStore.isCompleted()


  def setCompleted(self, completed=True):
    """ Marks the stream completed (True or False)
    """
    # CSV file is always considered completed, nothing to do
    self._recordStore.setCompleted(completed)


  def setTimeout(self, timeout):
    """ Set the read timeout """
    self._recordStore.setTimeout(timeout)


  def flush(self):
    """ Flush the file to disk """
    raise RuntimeError("Not implemented in StreamReader")


