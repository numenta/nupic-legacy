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

from collections import defaultdict
import datetime
import os
from pkg_resources import resource_filename
import time

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.field_meta import FieldMetaSpecial
from nupic.data.file_record_stream import FileRecordStream


"""The aggregator aggregates PF datasets

It supports aggregation of multiple records based on time.

Common use cases:

- Aggregate records by month
- Aggregate records every 3 months starting April 15th
- Aggregate records in 2.5 seconds intervals

Assumption: aggregated slices fit in memory. All the records that are aggregated
per period are stored in memory until the next slice starts and are only
aggregated then. If this assumption is too strong the script will need to write
slices to a temp storage or use incremental aggregation techniques.
"""



def initFilter(input, filterInfo = None):
  """ Initializes internal filter variables for further processing.
  Returns a tuple (function to call,parameters for the filter call)

  The filterInfo is a dict. Here is an example structure:
    {fieldName: {'min': x,
                 'max': y,
                 'type': 'category', # or 'number'
                 'acceptValues': ['foo', 'bar'],
                 }
    }

  This returns the following:
    (filterFunc, ((fieldIdx, fieldFilterFunc, filterDict),
                  ...)

  Where fieldIdx is the index of the field within each record
        fieldFilterFunc returns True if the value is "OK" (within min, max or
           part of acceptValues)
        fieldDict is a dict containing 'type', 'min', max', 'acceptValues'
  """

  if filterInfo is None:
    return None

  # Build an array of index/func to call on record[index]
  filterList = []
  for i, fieldName in enumerate(input.getFieldNames()):
    fieldFilter = filterInfo.get(fieldName, None)
    if fieldFilter == None:
      continue

    var = dict()
    var['acceptValues'] = None
    min = fieldFilter.get('min', None)
    max = fieldFilter.get('max', None)
    var['min'] = min
    var['max'] = max


    if fieldFilter['type'] == 'category':
      var['acceptValues'] = fieldFilter['acceptValues']
      fp = lambda x: (x['value'] != SENTINEL_VALUE_FOR_MISSING_DATA and \
                      x['value'] in x['acceptValues'])

    elif fieldFilter['type'] == 'number':

      if min != None and max != None:
        fp = lambda x: (x['value'] != SENTINEL_VALUE_FOR_MISSING_DATA and \
                        x['value'] >= x['min'] and x['value'] <= x['max'])
      elif min != None:
        fp = lambda x: (x['value'] != SENTINEL_VALUE_FOR_MISSING_DATA and \
                        x['value'] >= x['min'])
      else:
        fp = lambda x: (x['value'] != SENTINEL_VALUE_FOR_MISSING_DATA and \
                        x['value'] <= x['max'])

    filterList.append((i, fp, var))

  return (_filterRecord, filterList)



def _filterRecord(filterList, record):
  """ Takes a record and returns true if record meets filter criteria,
  false otherwise
  """

  for (fieldIdx, fp, params) in filterList:
    x = dict()
    x['value'] = record[fieldIdx]
    x['acceptValues'] = params['acceptValues']
    x['min'] = params['min']
    x['max'] = params['max']
    if not fp(x):
      return False

  # None of the field filters triggered, accept the record as a good one
  return True



def _aggr_first(inList):
  """ Returns first non-None element in the list, or None if all are None
  """
  for elem in inList:
    if elem != SENTINEL_VALUE_FOR_MISSING_DATA:
      return elem
  return None



def _aggr_last(inList):
  """ Returns last non-None element in the list, or None if all are None
  """
  for elem in reversed(inList):
    if elem != SENTINEL_VALUE_FOR_MISSING_DATA:
      return elem
  return None



def _aggr_sum(inList):
  """ Returns sum of the elements in the list. Missing items are replaced with
  the mean value
  """
  aggrMean = _aggr_mean(inList)
  if aggrMean == None:
    return None

  aggrSum = 0
  for elem in inList:
    if elem != SENTINEL_VALUE_FOR_MISSING_DATA:
      aggrSum += elem
    else:
      aggrSum += aggrMean

  return aggrSum



def _aggr_mean(inList):
  """ Returns mean of non-None elements of the list
  """
  aggrSum = 0
  nonNone = 0
  for elem in inList:
    if elem != SENTINEL_VALUE_FOR_MISSING_DATA:
      aggrSum += elem
      nonNone += 1
  if nonNone != 0:
    return aggrSum / nonNone
  else:
    return None



def _aggr_mode(inList):
  """ Returns most common value seen in the non-None elements of the list
  """

  valueCounts = dict()
  nonNone = 0

  for elem in inList:
    if elem == SENTINEL_VALUE_FOR_MISSING_DATA:
      continue

    nonNone += 1
    if elem in valueCounts:
      valueCounts[elem] += 1
    else:
      valueCounts[elem] = 1

  # Get the most common one
  if nonNone == 0:
    return None

  # Sort by counts
  sortedCounts = valueCounts.items()
  sortedCounts.sort(cmp=lambda x,y: x[1] - y[1], reverse=True)
  return sortedCounts[0][0]



def _aggr_weighted_mean(inList, params):
  """ Weighted mean uses params (must be the same size as inList) and
  makes weighed mean of inList"""
  assert(len(inList) == len(params))

  # If all weights are 0, then the value is not defined, return None (missing)
  weightsSum = sum(params)
  if weightsSum == 0:
    return None

  weightedMean = 0
  for i, elem in enumerate(inList):
    weightedMean += elem * params[i]

  return weightedMean / weightsSum



class Aggregator(object):
  """
  This class provides context and methods for aggregating records. The caller
  should construct an instance of Aggregator and then call the next() method
  repeatedly to get each aggregated record.

  This is an example aggregationInfo dict:
    {
      'hours': 1,
      'minutes': 15,
      'fields': [
          ('timestamp', 'first'),
          ('gym', 'first'),
          ('consumption', 'sum')
      ],
   }

  """


  def __init__(self, aggregationInfo, inputFields, timeFieldName=None,
               sequenceIdFieldName=None, resetFieldName=None, filterInfo=None):
    """ Construct an aggregator instance

    Params:

    - aggregationInfo: a dictionary that contains the following entries
      - fields: a list of pairs. Each pair is a field name and an
        aggregation function (e.g. sum). The function will be used to aggregate
        multiple values during the aggregation period.

      - aggregation period: 0 or more of unit=value fields; allowed units are:
          [years months] | [weeks days hours minutes seconds milliseconds
          microseconds]
          NOTE: years and months are mutually-exclusive with the other units.  See
                getEndTime() and _aggregate() for more details.
          Example1: years=1, months=6,
          Example2: hours=1, minutes=30,
          If none of the period fields are specified or if all that are specified
          have values of 0, then aggregation will be suppressed, and the given
          inputFile parameter value will be returned.

    - inputFields: The fields from the data source. This is a sequence of
      `nupic.data.fieldmeta.FieldMetaInfo` instances.

    - timeFieldName: name of the field to use as the time field. If None,
          then the time field will be queried from the reader.

    - sequenceIdFieldName: name of the field to use as the sequenecId. If None,
          then the time field will be queried from the reader.

    - resetFieldName: name of the field to use as the reset field. If None,
          then the time field will be queried from the reader.

    - filterInfo: a structure with rules for filtering records out


    If the input file contains a time field, sequence id field or reset field
    that were not specified in aggregationInfo fields, those fields will be
    added automatically with the following rules:

    1. The order will be R, S, T, rest of the fields
    2. The aggregation function for these will be to pick the first:
       lambda x: x[0]

    """

    # -----------------------------------------------------------------------
    # Save member variables.

    # The same aggregationInfo dict may be used by the caller for generating
    # more datasets (with slight changes), so it is safer to copy it here and
    # all changes made here will not affect the input aggregationInfo
    self._filterInfo = filterInfo
    self._nullAggregation = False
    self._inputFields = inputFields


    # See if this is a null aggregation
    self._nullAggregation = False
    if aggregationInfo is None:
      self._nullAggregation = True
    else:
      aggDef = defaultdict(lambda: 0, aggregationInfo)
      if (aggDef['years'] == aggDef['months'] == aggDef['weeks'] ==
          aggDef['days'] == aggDef['hours'] == aggDef['minutes'] ==
          aggDef['seconds'] == aggDef['milliseconds'] ==
          aggDef['microseconds'] == 0):
        self._nullAggregation = True


    # Prepare the field filtering info. The filter allows us to ignore records
    #  based on specified min or max values for each field.
    self._filter = initFilter(self._inputFields, self._filterInfo)

    # ----------------------------------------------------------------------
    # Fill in defaults
    self._fields = None
    self._resetFieldIdx = None
    self._timeFieldIdx = None
    self._sequenceIdFieldIdx = None
    self._aggTimeDelta = datetime.timedelta()
    self._aggYears = 0
    self._aggMonths = 0

    # Init state variables used within next()
    self._aggrInputBookmark = None
    self._startTime = None
    self._endTime = None
    self._sequenceId = None
    self._firstSequenceStartTime = None
    self._inIdx = -1
    self._slice = defaultdict(list)


    # ========================================================================
    # Get aggregation params
    # self._fields will be a list of tuples: (fieldIdx, funcPtr, funcParam)
    if not self._nullAggregation:

      # ---------------------------------------------------------------------
      # Verify that all aggregation field names exist in the input
      fieldNames = [f[0] for f in aggregationInfo['fields']]
      readerFieldNames = [f[0] for f in self._inputFields]
      for name in fieldNames:
        if not name in readerFieldNames:
          raise Exception('No such input field: %s' % (name))


      # ---------------------------------------------------------------------
      # Get the indices of the special fields, if given to our constructor
      if timeFieldName is not None:
        self._timeFieldIdx = readerFieldNames.index(timeFieldName)
      if resetFieldName is not None:
        self._resetFieldIdx = readerFieldNames.index(resetFieldName)
      if sequenceIdFieldName is not None:
        self._sequenceIdFieldIdx = readerFieldNames.index(sequenceIdFieldName)


      # ---------------------------------------------------------------------
      # Re-order the fields to match the order in the reader and add in any
      #  fields from the reader that were not already in the aggregationInfo
      #  fields list.
      self._fields = []
      fieldIdx = -1
      for (name, type, special) in self._inputFields:

        fieldIdx += 1

        # See if it exists in the aggregationInfo
        found = False
        for field in aggregationInfo['fields']:
          if field[0] == name:
            aggFunctionName = field[1]
            found = True
            break
        if not found:
          aggFunctionName = 'first'

        # Convert to a function pointer and optional params
        (funcPtr, params) = self._getFuncPtrAndParams(aggFunctionName)

        # Add it
        self._fields.append((fieldIdx, funcPtr, params))

        # Is it a special field that we are still looking for?
        if special == FieldMetaSpecial.reset and self._resetFieldIdx is None:
          self._resetFieldIdx = fieldIdx
        if special == FieldMetaSpecial.timestamp and self._timeFieldIdx is None:
          self._timeFieldIdx = fieldIdx
        if (special == FieldMetaSpecial.sequence and
            self._sequenceIdFieldIdx is None):
          self._sequenceIdFieldIdx = fieldIdx


      assert self._timeFieldIdx is not None, "No time field was found"

      # Create an instance of _AggregationPeriod with the aggregation period
      self._aggTimeDelta = datetime.timedelta(days=aggDef['days'],
                                     hours=aggDef['hours'],
                                     minutes=aggDef['minutes'],
                                     seconds=aggDef['seconds'],
                                     milliseconds=aggDef['milliseconds'],
                                     microseconds=aggDef['microseconds'],
                                     weeks=aggDef['weeks'])
      self._aggYears = aggDef['years']
      self._aggMonths = aggDef['months']
      if self._aggTimeDelta:
        assert self._aggYears == 0
        assert self._aggMonths == 0


  def _getEndTime(self, t):
    """Add the aggregation period to the input time t and return a datetime object

    Years and months are handled as aspecial case due to leap years
    and months with different number of dates. They can't be converted
    to a strict timedelta because a period of 3 months will have different
    durations actually. The solution is to just add the years and months
    fields directly to the current time.

    Other periods are converted to timedelta and just added to current time.
    """

    assert isinstance(t, datetime.datetime)
    if self._aggTimeDelta:
      return t + self._aggTimeDelta
    else:
      year = t.year + self._aggYears + (t.month - 1 + self._aggMonths) / 12
      month = (t.month - 1 + self._aggMonths) % 12 + 1
      return t.replace(year=year, month=month)


  def _getFuncPtrAndParams(self, funcName):
    """ Given the name of an aggregation function, returns the function pointer
    and param.

    Parameters:
    ------------------------------------------------------------------------
    funcName:  a string (name of function) or funcPtr
    retval:   (funcPtr, param)
    """

    params = None
    if isinstance(funcName, basestring):
      if funcName == 'sum':
        fp = _aggr_sum
      elif funcName == 'first':
        fp = _aggr_first
      elif funcName == 'last':
        fp = _aggr_last
      elif funcName == 'mean':
        fp = _aggr_mean
      elif funcName == 'max':
        fp = max
      elif funcName == 'min':
        fp = min
      elif funcName == 'mode':
        fp = _aggr_mode
      elif funcName.startswith('wmean:'):
        fp = _aggr_weighted_mean
        paramsName = funcName[6:]
        params = [f[0] for f in self._inputFields].index(paramsName)
    else:
      fp = funcName

    return (fp, params)


  def _createAggregateRecord(self):
    """ Generate the aggregated output record

    Parameters:
    ------------------------------------------------------------------------
    retval: outputRecord

    """

    record = []

    for i, (fieldIdx, aggFP, paramIdx) in enumerate(self._fields):
      if aggFP is None: # this field is not supposed to be aggregated.
        continue

      values = self._slice[i]
      refIndex = None
      if paramIdx is not None:
        record.append(aggFP(values, self._slice[paramIdx]))
      else:
        record.append(aggFP(values))

    return record


  def isNullAggregation(self):
    """ Return True if no aggregation will be performed, either because the
    aggregationInfo was None or all aggregation params within it were 0.
    """
    return self._nullAggregation


  def next(self, record, curInputBookmark):
    """ Return the next aggregated record, if any

    Parameters:
    ------------------------------------------------------------------------
    record:         The input record (values only) from the input source, or
                    None if the input has reached EOF (this will cause this
                    method to force completion of and return any partially
                    aggregated time period)
    curInputBookmark: The bookmark to the next input record
    retval:
      (outputRecord, inputBookmark)

      outputRecord: the aggregated record
      inputBookmark: a bookmark to the last position from the input that
                      contributed to this aggregated record.

      If we don't have any aggregated records yet, returns (None, None)


    The caller should generally do a loop like this:
      while True:
        inRecord = reader.getNextRecord()
        bookmark = reader.getBookmark()

        (aggRecord, aggBookmark) = aggregator.next(inRecord, bookmark)

        # reached EOF?
        if inRecord is None and aggRecord is None:
          break

        if aggRecord is not None:
          proessRecord(aggRecord, aggBookmark)


    This method makes use of the self._slice member variable to build up
    the values we need to aggregate. This is a dict of lists. The keys are
    the field indices and the elements of each list are the values for that
    field. For example:

      self._siice = { 0: [42, 53], 1: [4.0, 5.1] }

    """

    # This will hold the aggregated record we return
    outRecord = None

    # This will hold the bookmark of the last input used within the
    #  aggregated record we return.
    retInputBookmark = None

    if record is not None:

      # Increment input count
      self._inIdx += 1

      #print self._inIdx, record

      # Apply the filter, ignore the record if any field is unacceptable
      if self._filter != None and not self._filter[0](self._filter[1], record):
        return (None, None)

      # If no aggregation info just return as-is
      if self._nullAggregation:
        return (record, curInputBookmark)


      # ----------------------------------------------------------------------
      # Do aggregation

      #
      # Remember the very first record time stamp - it will be used as
      # the timestamp for all first records in all sequences to align
      # times for the aggregation/join of sequences.
      #
      # For a set of aggregated records, it will use the beginning of the time
      # window as a timestamp for the set
      #
      t = record[self._timeFieldIdx]

      if self._firstSequenceStartTime == None:
        self._firstSequenceStartTime = t

      # Create initial startTime and endTime if needed
      if self._startTime is None:
        self._startTime = t
      if self._endTime is None:
        self._endTime = self._getEndTime(t)
        assert self._endTime > t

      #print 'Processing line:', i, t, endTime
      #from dbgp.client import brk; brk(port=9011)


      # ----------------------------------------------------------------------
      # Does this record have a reset signal or sequence Id associated with it?
      # If so, see if we've reached a sequence boundary
      if self._resetFieldIdx is not None:
        resetSignal = record[self._resetFieldIdx]
      else:
        resetSignal = None

      if self._sequenceIdFieldIdx is not None:
        currSequenceId = record[self._sequenceIdFieldIdx]
      else:
        currSequenceId = None

      newSequence = (resetSignal == 1 and self._inIdx > 0) \
                      or self._sequenceId != currSequenceId \
                      or self._inIdx == 0

      if newSequence:
        self._sequenceId = currSequenceId


      # --------------------------------------------------------------------
      # We end the aggregation chunk if we go past the end time
      # -OR- we get an out of order record (t < startTime)
      sliceEnded = (t >= self._endTime or t < self._startTime)


      # -------------------------------------------------------------------
      # Time to generate a new output record?
      if (newSequence or sliceEnded) and len(self._slice) > 0:
        # Create aggregated record
        # print 'Creating aggregate record...'

        # Make first record timestamp as the beginning of the time period,
        # in case the first record wasn't falling on the beginning of the period
        for j, f in enumerate(self._fields):
          index = f[0]
          if index == self._timeFieldIdx:
            self._slice[j][0] = self._startTime
            break

        # Generate the aggregated record
        outRecord = self._createAggregateRecord()
        retInputBookmark = self._aggrInputBookmark

        # Reset the slice
        self._slice = defaultdict(list)


      # --------------------------------------------------------------------
      # Add current record to slice (Note keeping slices in memory). Each
      # field in the slice is a list of field values from all the sliced
      # records
      for j, f in enumerate(self._fields):
        index = f[0]
        # append the parsed field value to the proper aggregated slice field.
        self._slice[j].append(record[index])
        self._aggrInputBookmark = curInputBookmark


      # --------------------------------------------------------------------
      # If we've encountered a new sequence, start aggregation over again
      if newSequence:
        # TODO: May use self._firstSequenceStartTime as a start for the new
        # sequence (to align all sequences)
        self._startTime = t
        self._endTime = self._getEndTime(t)


      # --------------------------------------------------------------------
      # If a slice just ended, re-compute the start and end time for the
      #  next aggregated record
      if sliceEnded:
        # Did we receive an out of order record? If so, go back and iterate
        #   till we get to the next end time boundary.
        if t < self._startTime:
          self._endTime = self._firstSequenceStartTime
        while t >= self._endTime:
          self._startTime = self._endTime
          self._endTime = self._getEndTime(self._endTime)


      # If we have a record to return, do it now
      if outRecord is not None:
        return (outRecord, retInputBookmark)


    # ---------------------------------------------------------------------
    # Input reached EOF
    # Aggregate one last time in the end if necessary
    elif self._slice:

      # Make first record timestamp as the beginning of the time period,
      # in case the first record wasn't falling on the beginning of the period
      for j, f in enumerate(self._fields):
        index = f[0]
        if index == self._timeFieldIdx:
          self._slice[j][0] = self._startTime
          break

      outRecord = self._createAggregateRecord()
      retInputBookmark = self._aggrInputBookmark

      self._slice = defaultdict(list)


    # Return aggregated record
    return (outRecord, retInputBookmark)



def generateDataset(aggregationInfo, inputFilename, outputFilename=None):
  """Generate a dataset of aggregated values

  Parameters:
  ----------------------------------------------------------------------------
  aggregationInfo: a dictionary that contains the following entries
    - fields: a list of pairs. Each pair is a field name and an
      aggregation function (e.g. sum). The function will be used to aggregate
      multiple values during the aggregation period.

  aggregation period: 0 or more of unit=value fields; allowed units are:
        [years months] |
        [weeks days hours minutes seconds milliseconds microseconds]
        NOTE: years and months are mutually-exclusive with the other units.
              See getEndTime() and _aggregate() for more details.
        Example1: years=1, months=6,
        Example2: hours=1, minutes=30,
        If none of the period fields are specified or if all that are specified
        have values of 0, then aggregation will be suppressed, and the given
        inputFile parameter value will be returned.

  inputFilename: filename of the input dataset within examples/prediction/data

  outputFilename: name for the output file. If not given, a name will be
        generated based on the input filename and the aggregation params

  retval: Name of the generated output file. This will be the same as the input
      file name if no aggregation needed to be performed



  If the input file contained a time field, sequence id field or reset field
  that were not specified in aggregationInfo fields, those fields will be
  added automatically with the following rules:

  1. The order will be R, S, T, rest of the fields
  2. The aggregation function for all will be to pick the first: lambda x: x[0]

    Returns: the path of the aggregated data file if aggregation was performed
      (in the same directory as the given input file); if aggregation did not
      need to be performed, then the given inputFile argument value is returned.
  """



  # Create the input stream
  inputFullPath = resource_filename("nupic.datafiles", inputFilename)
  inputObj = FileRecordStream(inputFullPath)


  # Instantiate the aggregator
  aggregator = Aggregator(aggregationInfo=aggregationInfo,
                          inputFields=inputObj.getFields())


  # Is it a null aggregation? If so, just return the input file unmodified
  if aggregator.isNullAggregation():
    return inputFullPath


  # ------------------------------------------------------------------------
  # If we were not given an output filename, create one based on the
  #  aggregation settings
  if outputFilename is None:
    outputFilename = 'agg_%s' % \
                        os.path.splitext(os.path.basename(inputFullPath))[0]
    timePeriods = 'years months weeks days '\
                  'hours minutes seconds milliseconds microseconds'
    for k in timePeriods.split():
      if aggregationInfo.get(k, 0) > 0:
        outputFilename += '_%s_%d' % (k, aggregationInfo[k])

    outputFilename += '.csv'
    outputFilename = os.path.join(os.path.dirname(inputFullPath), outputFilename)



  # ------------------------------------------------------------------------
  # If some other process already started creating this file, simply
  #   wait for it to finish and return without doing anything
  lockFilePath = outputFilename + '.please_wait'
  if os.path.isfile(outputFilename) or \
     os.path.isfile(lockFilePath):
    while os.path.isfile(lockFilePath):
      print 'Waiting for %s to be fully written by another process' % \
            lockFilePath
      time.sleep(1)
    return outputFilename


  # Create the lock file
  lockFD = open(lockFilePath, 'w')



  # -------------------------------------------------------------------------
  # Create the output stream
  outputObj = FileRecordStream(streamID=outputFilename, write=True,
                               fields=inputObj.getFields())


  # -------------------------------------------------------------------------
  # Write all aggregated records to the output
  while True:
    inRecord = inputObj.getNextRecord()

    (aggRecord, aggBookmark) = aggregator.next(inRecord, None)

    if aggRecord is None and inRecord is None:
      break

    if aggRecord is not None:
      outputObj.appendRecord(aggRecord)

  return outputFilename



def getFilename(aggregationInfo, inputFile):
  """Generate the filename for aggregated dataset

  The filename is based on the input filename and the
  aggregation period.

  Returns the inputFile if no aggregation required (aggregation
  info has all 0's)
  """

  # Find the actual file, with an absolute path
  inputFile = resource_filename("nupic.datafiles", inputFile)

  a = defaultdict(lambda: 0, aggregationInfo)
  outputDir = os.path.dirname(inputFile)
  outputFile = 'agg_%s' % os.path.splitext(os.path.basename(inputFile))[0]
  noAggregation = True
  timePeriods = 'years months weeks days '\
                'hours minutes seconds milliseconds microseconds'
  for k in timePeriods.split():
    if a[k] > 0:
      noAggregation = False
      outputFile += '_%s_%d' % (k, a[k])

  if noAggregation:
    return inputFile
  outputFile += '.csv'
  outputFile = os.path.join(outputDir, outputFile)

  return outputFile
