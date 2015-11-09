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

"""
CSV file based implementation of a record stream

FileRecordStream is class that can read and write .csv files that contain
records. The file has 3 header lines that contain, for each field, the name
(line 1), type (line 2), and a special indicator (line 3). The special indicator
can indicate that the field specifies a reset, is a sequence ID, or is a
timestamp for the record.

The header lines look like:

f1,f2,f3,....fN
int,string,datetime,bool,...
R,S,T,,,,....

The data lines are just comma separated values that match the types in the
second header line. The supported types are: int, float, string, bool, datetime

The format for datetime fields is yyyy-mm-dd hh:mm:ss.us
The 'us' component is microseconds.

When reading a file the FileRecordStream will automatically read the header line
and will figure out the type of each field and what are the timestamp, reset
and sequenceId fields (if any).

The FileRecordStream class supports the context manager ('with' statement )
protocol. That means you con do:

with FileRecordStream(filename) as f:
  ...
  ...

When the control exits the 'with' block the file will be closed automatically.
You may still call the .close() method at any point (even multiple times).

The FileRecordStream also supports the iteration protocol so you may read its
contents using a for loop:

  for r in f:
    print r
"""

import os
import csv
import copy
import json

from nupic.data.fieldmeta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.record_stream import RecordStreamIface
from nupic.data.utils import (intOrNone, floatOrNone, parseBool, parseTimestamp,
    serializeTimestamp, serializeTimestampNoMS, escape, unescape, parseSdr,
    serializeSdr, parseStringList, stripList)



class FileRecordStream(RecordStreamIface):
  """ CSV file based RecordStream implementation
  """

  # Private: number of header rows (field names, types, special)
  _NUM_HEADER_ROWS = 3

  # Private: file mode for opening file for writing
  _FILE_WRITE_MODE = 'w'

  # Private: file mode for opening file for reading
  _FILE_READ_MODE = 'r'


  def __init__(self, streamID, write=False, fields=None, missingValues=None,
               bookmark=None, includeMS=True, firstRecord=None):
    """
    streamID:
        CSV file name, input or output
    write:
        True or False, open for writing if True
    fields:
        a list of nupic.data.fieldmeta.FieldMetaInfo field descriptors, only
        applicable when write==True
    missingValues:
        what missing values should be replaced with?
    bookmark:
        a reference to the previous reader, if passed in, the records will be
        returned starting from the point where bookmark was requested. Either
        bookmark or firstRecord can be specified, not both. If bookmark is used,
        then firstRecord MUST be None.
    includeMS:
        If false, the microseconds portion is not included in the
        generated output file timestamp fields. This makes it compatible
        with reading in from Excel.
    firstRecord:
        0-based index of the first record to start reading from. Either bookmark
        or firstRecord can be specified, not both. If bookmark is used, then
        firstRecord MUST be None.

    Each field is a 3-tuple (name, type, special or FieldMetaSpecial.none)

    The name is the name of the field. The type is one of the constants in
    `FieldMetaType`. The special is one of the `FieldMetaSpecial` values
    that designate their field as the sequenceId, reset, timestamp, or category.
    With exception of multiple categories, there can be at most one of each.
    There may be multiple fields of type datetime, but no more than one of them
    may be the timestamp field (FieldMetaSpecial.timestamp). The sequence id
    field must be either a string or an int. The reset field must be an int (and
    must contain 0 or 1).

    The category field must be an int or space-separated list of ints, where
    the former represents single-label classification and the latter is for
    multi-label classification (e.g. "1 3 4" designates a record for labels 1,
    3, and 4). The number of categories is allowed to vary record to record;
    sensor regions represent non-categories with -1, thus the category values
    must be >= 0.

    The FileRecordStream iterates over the field names, types and specials and
    stores the information.
    """
    super(FileRecordStream, self).__init__()

    # Only bookmark or firstRow can be specified, not both
    if bookmark is not None and firstRecord is not None:
      raise RuntimeError(
          "Only bookmark or firstRecord can be specified, not both")

    if fields is None:
      fields = []
    if missingValues is None:
      missingValues = ['']

    # We'll be operating on csvs with arbitrarily long fields
    size = 2**27
    csv.field_size_limit(size)

    self._filename = streamID
    # We can't guarantee what system files are coming from, use universal
    # newlines
    self._write = write
    self._mode = self._FILE_WRITE_MODE if write else self._FILE_READ_MODE
    self._file = open(self._filename, self._mode)
    self._sequences = set()
    self.rewindAtEOF = False

    if write:
      assert fields is not None
      assert isinstance(fields, (tuple, list))
      # Verify all fields are 3-tuple
      assert all(isinstance(f, (tuple, FieldMetaInfo)) and len(f) == 3
                 for f in fields)
      names, types, specials = zip(*fields)
      self._writer = csv.writer(self._file)
    else:
      # Read header lines
      self._reader = csv.reader(self._file, dialect="excel")
      try:
        names = [n.strip() for n in self._reader.next()]
      except:
        raise Exception('The header line of the file %s contained a NULL byte' \
                        % self._filename)
      types = [t.strip() for t in self._reader.next()]
      specials = [s.strip() for s in self._reader.next()]

      # If there are no specials, this means there was a blank line
      if len(specials) == 0:
        specials=[""]

    if not len(names) == len(types) == len(specials):
      raise Exception('Invalid file format: different number of fields '
                      'in the header rows of file %s (%d, %d, %d)' %
                      (streamID, len(names), len(types), len(specials)))

    # Verify standard file format
    for t in types:
      if not FieldMetaType.isValid(t):
        raise Exception('Invalid file format for "%s" - field type "%s" '
                        'not a valid FieldMetaType' % (self._filename, t,))

    for s in specials:
      if not FieldMetaSpecial.isValid(s):
        raise Exception('Invalid file format. \'%s\' is not a valid special '
                        'flag' % s)

    self._fields = [FieldMetaInfo(*attrs)
                    for attrs in zip(names, types, specials)]
    self._fieldCount = len(self._fields)

    # Keep track on how many records have been read/written
    self._recordCount = 0

    self._timeStampIdx = (specials.index(FieldMetaSpecial.timestamp)
                          if FieldMetaSpecial.timestamp in specials else None)
    self._resetIdx = (specials.index(FieldMetaSpecial.reset)
                      if FieldMetaSpecial.reset in specials else None)
    self._sequenceIdIdx = (specials.index(FieldMetaSpecial.sequence)
                           if FieldMetaSpecial.sequence in specials else None)
    self._categoryIdx = (specials.index(FieldMetaSpecial.category)
                         if FieldMetaSpecial.category in specials else None)
    self._learningIdx = (specials.index(FieldMetaSpecial.learning)
                         if FieldMetaSpecial.learning in specials else None)

    # keep track of the current sequence
    self._currSequence = None
    self._currTime = None

    if self._timeStampIdx:
      assert types[self._timeStampIdx] == FieldMetaType.datetime
    if self._sequenceIdIdx:
      assert types[self._sequenceIdIdx] in (FieldMetaType.string,
                                            FieldMetaType.integer)
    if self._resetIdx:
      assert types[self._resetIdx] == FieldMetaType.integer
    if self._categoryIdx:
      assert types[self._categoryIdx] in (FieldMetaType.list,
                                          FieldMetaType.integer)
    if self._learningIdx:
      assert types[self._learningIdx] == FieldMetaType.integer

    # Convert the types to the actual types in order to convert the strings
    if self._mode == self._FILE_READ_MODE:
      m = {FieldMetaType.integer: intOrNone,
           FieldMetaType.float: floatOrNone,
           FieldMetaType.boolean: parseBool,
           FieldMetaType.string: unescape,
           FieldMetaType.datetime: parseTimestamp,
           FieldMetaType.sdr: parseSdr,
           FieldMetaType.list: parseStringList}
    else:
      if includeMS:
        datetimeFunc = serializeTimestamp
      else:
        datetimeFunc = serializeTimestampNoMS
      m = {FieldMetaType.integer: str,
           FieldMetaType.float: str,
           FieldMetaType.string: escape,
           FieldMetaType.boolean: str,
           FieldMetaType.datetime: datetimeFunc,
           FieldMetaType.sdr: serializeSdr,
           FieldMetaType.list: stripList}

    self._adapters = [m[t] for t in types]

    self._missingValues = missingValues

    #
    # If the bookmark is set, we need to skip over first N records
    #
    if bookmark is not None:
      rowsToSkip = self._getStartRow(bookmark)
    elif firstRecord is not None:
      rowsToSkip = firstRecord
    else:
      rowsToSkip = 0

    while rowsToSkip > 0:
      self.next()
      rowsToSkip -= 1


    # Dictionary to store record statistics (min and max of scalars for now)
    self._stats = None


  def __getstate__(self):
    d = dict()
    d.update(self.__dict__)
    del d['_reader']
    del d['_file']
    return d


  def __setstate__(self, state):
    self.__dict__ = state
    self._file = None
    self._reader = None
    self.rewind()


  def close(self):
    if self._file is not None:
      self._file.close()
      self._file = None


  def rewind(self):
    """Put us back at the beginning of the file again)
    """

    # Superclass rewind
    super(FileRecordStream, self).rewind()

    self.close()
    self._file = open(self._filename, self._mode)
    self._reader = csv.reader(self._file, dialect="excel")

    # Skip header rows
    self._reader.next()
    self._reader.next()
    self._reader.next()

    # Reset record count, etc.
    self._recordCount = 0


  def getNextRecord(self, useCache=True):
    """ Returns next available data record from the file.

    retval: a data row (a list or tuple) if available; None, if no more records
             in the table (End of Stream - EOS); empty sequence (list or tuple)
             when timing out while waiting for the next record.
    """
    assert self._file is not None
    assert self._mode == self._FILE_READ_MODE

    # Read the line
    try:
      line = self._reader.next()

    except StopIteration:
      if self.rewindAtEOF:
        if self._recordCount == 0:
          raise Exception("The source configured to reset at EOF but "
                          "'%s' appears to be empty" % self._filename)
        self.rewind()
        line = self._reader.next()

      else:
        return None

    # Keep score of how many records were read
    self._recordCount += 1

    # Split the line to text fields and convert each text field to a Python
    # object if value is missing (empty string) encode appropriately for
    # upstream consumers in the case of numeric types, this means replacing
    # missing data with a sentinel value for string type, we can leave the empty
    # string in place
    record = []
    for i, f in enumerate(line):
      #print "DEBUG: Evaluating field @ index %s: %r" % (i, f)
      #sys.stdout.flush()
      if f in self._missingValues:
        record.append(SENTINEL_VALUE_FOR_MISSING_DATA)
      else:
        # either there is valid data, or the field is string type,
        # in which case the adapter does the right thing by default
        record.append(self._adapters[i](f))

    return record


  def getRecordsRange(self, bookmark=None, range=None):
    """ Returns a range of records, starting from the bookmark. If 'bookmark'
    is None, then records read from the first available. If 'range' is
    None, all available records will be returned (caution: this could be
    a lot of records and require a lot of memory).
    """

    raise Exception('getRecordsRange() is not supported for the file storage')


  def getLastRecords(self, numRecords):
    """ Returns a tuple (successCode, recordsArray), where
        successCode - if the stream had enough records to return, True/False
        recordsArray - an array of last numRecords records available when
                       the call was made. Records appended while in the
                       getLastRecords will be not returned until the next
                       call to either getNextRecord() or getLastRecords()
    """

    raise Exception('getLastRecords() is not supported for the file storage')


  def removeOldData(self):
    raise Exception('removeOldData is not supported in this class.')


  def appendRecord(self, record, inputBookmark=None):
    """ Saves the record in the underlying csv file.

        record: a list of Python objects that will be string-ified

        Returns: nothing
    """

    # input bookmark is not applicable in case of a file storage
    inputBookmark = inputBookmark

    assert self._file is not None
    assert self._mode == self._FILE_WRITE_MODE
    assert isinstance(record, (list, tuple)), \
      "unexpected record type: " + repr(type(record))

    assert len(record) == self._fieldCount, \
      "len(record): %s, fieldCount: %s" % (len(record), self._fieldCount)

    # Write header if needed
    if self._recordCount == 0:
      # Write the header
      names, types, specials = zip(*self.getFields())
      for line in names, types, specials:
        self._writer.writerow(line)

    # Keep track of sequences, make sure time flows forward
    self._updateSequenceInfo(record)

    line = [self._adapters[i](f) for i, f in enumerate(record)]

    self._writer.writerow(line)
    self._recordCount += 1


  def appendRecords(self, records, inputRef=None, progressCB=None):
    """ Saves multiple records in the underlying storage.

        Params: records - array of records as in 'appendRecord'
                inputRef - reference to the corresponding input (not applicable
                  in case of a file storage)
                progressCB - callback to report progress

        Returns: nothing

    """

    # input ref is not applicable in case of a file storage
    inputRef = inputRef

    for record in records:
      self.appendRecord(record, None)
      if progressCB is not None:
        progressCB()


  def getBookmark(self):
    """ Returns an anchor to the current position in the data. Passing this
    anchor to a constructor makes the current position to be the first
    returned record.
    """

    if self._write and self._recordCount==0:
      return None

    rowDict = dict(filepath=os.path.realpath(self._filename),
                   currentRow=self._recordCount)
    return json.dumps(rowDict)


  def recordsExistAfter(self, bookmark):
    """Returns True iff there are records left after the  bookmark."""
    return (self.getDataRowCount() - self.getNextRecordIdx()) > 0


  def seekFromEnd(self, numRecords):
    """Seeks to numRecords from the end and returns a bookmark to the new
    position.
    """
    self._file.seek(self._getTotalLineCount() - numRecords)
    return self.getBookmark()


  def setAutoRewind(self, autoRewind):
    """
    Controls whether getNext() should automatically rewind the source when EOF
    is reached.

    autoRewind: True = getNext() will automatically rewind the source on EOF;
                False = getNext() will not automatically rewind the source
                on EOF
    """
    self.rewindAtEOF = autoRewind


  def getStats(self):
    """ Parse the file using dedicated reader and collect fields stats. Never
    called if user of FileRecordStream does not invoke getStats method.

    Returns: a dictionary of stats. In the current implementation, min and max
             fields are supported. Example of the return dictionary is:

             {
               'min' : [f1_min, f2_min, None, None, fn_min],
               'max' : [f1_max, f2_max, None, None, fn_max]
             }

             (where fx_min/fx_max are set for scalar fields, or None if not)

    """

    # Collect stats only once per File object, use fresh csv iterator
    # to keep the next() method returning sequential records no matter when
    # caller asks for stats
    if self._stats == None:
      # Stats are only available when reading csv file
      assert self._mode == self._FILE_READ_MODE

      inFile = open(self._filename, self._FILE_READ_MODE)

      # Create a new reader; read names, types, specials
      reader = csv.reader(inFile, dialect="excel")
      names = [n.strip() for n in reader.next()]
      types = [t.strip() for t in reader.next()]
      # Skip over specials
      reader.next()

      # Initialize stats to all None
      self._stats = dict()
      self._stats['min'] = []
      self._stats['max'] = []

      for i in xrange(len(names)):
        self._stats['min'].append(None)
        self._stats['max'].append(None)

      # Read the file, collect stats
      while True:
        try:
          line = reader.next()
          for i, f in enumerate(line):
            if (len(types) > i and
                types[i] in [FieldMetaType.integer, FieldMetaType.float] and
                f not in self._missingValues):
              value = self._adapters[i](f)
              if self._stats['max'][i] == None or \
                 self._stats['max'][i] < value:
                self._stats['max'][i] = value
              if self._stats['min'][i] == None or \
                 self._stats['min'][i] > value:
                self._stats['min'][i] = value

        except StopIteration:
          break

    return self._stats


  def clearStats(self):
    """ Resets stats collected so far.
    """
    self._stats = None


  def getError(self):
    """ Returns errors saved in the stream.
    """
    # CSV file version does not provide storage for the error information
    return None


  def setError(self, error):
    """ Saves specified error in the stream.
    """
    # CSV file version does not provide storage for the error information
    return


  def isCompleted(self):
    """ Returns True if all records are already in the stream or False
    if more records is expected.
    """
    # CSV file is always considered completed
    return True


  def setCompleted(self, completed=True):
    """ Marks the stream completed (True or False)
    """
    # CSV file is always considered completed, nothing to do
    return


  def getFieldNames(self):
    """ Returns an array of field names associated with the data.
    """
    return [f.name for f in self._fields]


  def getFields(self):
    """ Returns a sequence of nupic.data.fieldmeta.FieldMetaInfo
    name/type/special tuples for each field in the stream.
    """
    if self._fields is None:
      return None
    else:
      return copy.copy(self._fields)


  def _updateSequenceInfo(self, r):
    """Keep track of sequence and make sure time goes forward

    Check if the current record is the beginning of a new sequence
    A new sequence starts in 2 cases:

    1. The sequence id changed (if there is a sequence id field)
    2. The reset field is 1 (if there is a reset field)

    Note that if there is no sequenceId field or resetId field then the entire
    dataset is technically one big sequence. The function will not return True
    for the first record in this case. This is Ok because it is important to
    detect new sequences only when there are multiple sequences in the file.
    """

    # Get current sequence id (if any)
    newSequence = False
    sequenceId = (r[self._sequenceIdIdx]
                  if self._sequenceIdIdx is not None else None)
    if sequenceId != self._currSequence:
      # verify that the new sequence didn't show up before
      if sequenceId in self._sequences:
        raise Exception('Broken sequence: %s, record: %s' % \
                        (sequenceId, r))

      # add the finished sequence to the set of sequence
      self._sequences.add(self._currSequence)
      self._currSequence = sequenceId

      # Verify that the reset is consistent (if there is one)
      if self._resetIdx:
        assert r[self._resetIdx] == 1
      newSequence = True

    else:
      # Check the reset
      reset = False
      if self._resetIdx:
        reset = r[self._resetIdx]
        if reset == 1:
          newSequence = True

    # If it's still the same old sequence make sure the time flows forward
    if not newSequence:
      if self._timeStampIdx and self._currTime is not None:
        t = r[self._timeStampIdx]
        if t < self._currTime:
          raise Exception('No time travel. Early timestamp for record: %s' % r)

    if self._timeStampIdx:
      self._currTime = r[self._timeStampIdx]


  def _getStartRow(self, bookmark):
    """ Extracts start row from the bookmark information
    """
    bookMarkDict = json.loads(bookmark)

    realpath = os.path.realpath(self._filename)

    bookMarkFile = bookMarkDict.get('filepath', None)

    if bookMarkFile != realpath:
      print ("Ignoring bookmark due to mismatch between File's "
             "filename realpath vs. bookmark; realpath: %r; bookmark: %r") % (
        realpath, bookMarkDict)
      return 0
    else:
      return bookMarkDict['currentRow']


  def _getTotalLineCount(self):
    """ Returns:  count of ALL lines in dataset, including header lines
    """
    # Flush the file before we open it again to count lines
    if self._mode == self._FILE_WRITE_MODE:
      self._file.flush()
    return sum(1 for line in open(self._filename, self._FILE_READ_MODE))


  def getNextRecordIdx(self):
    """Returns the index of the record that will be read next from
    getNextRecord()
    """
    return self._recordCount


  def getDataRowCount(self):
    """
    Returns:  count of data rows in dataset (excluding header lines)
    """
    numLines = self._getTotalLineCount()

    if numLines == 0:
      # this may be the case in a file opened for write before the
      # header rows are written out
      assert self._mode == self._FILE_WRITE_MODE and self._recordCount == 0
      numDataRows = 0
    else:
      numDataRows = numLines - self._NUM_HEADER_ROWS

    assert numDataRows >= 0

    return numDataRows


  def setTimeout(self, timeout):
    """ Set the read timeout """
    pass


  def flush(self):
    if self._file is not None:
      self._file.flush()


  def __enter__(self):
    """Context guard - enter

    Just return the object
    """
    return self


  def __exit__(self, yupe, value, traceback):
    """Context guard - exit

    Ensures that the file is always closed at the end of the 'with' block.
    Lets exceptions propagate.
    """
    self.close()


  def __iter__(self):
    """Support for the iterator protocol. Return itself"""
    return self


  def next(self):
    """Implement the iterator protocol """
    record = self.getNextRecord()
    if record is None:
      raise StopIteration

    return record

