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

import datetime
import os
import tempfile

from pkg_resources import resource_filename

from nupic.data.file_record_stream import FileRecordStream

from nupic.data.aggregator import Aggregator, generateDataset

from nupic import support as nupic_support
from nupic.support.unittesthelpers.testcasebase import (unittest,
  TestCaseBase as HelperTestCaseBase)



def _aggregate(input, options, output, timeFieldName):
  """ Aggregate the input stream and write aggregated records to the output
  stream
  """
  
  aggregator = Aggregator(aggregationInfo=options, 
                          inputFields=input.getFields(),
                          timeFieldName=timeFieldName)
  
  while True:
    inRecord = input.getNextRecord()
    
    print "Feeding in: ", inRecord

    (outRecord, aggBookmark) = aggregator.next(record = inRecord, 
                                            curInputBookmark = None)
    print "Record out: ", outRecord
    
    if outRecord is not None:
      output.appendRecord(outRecord, None)
      
    if inRecord is None and outRecord is None:
      break
      

class DataInputList(object):
  """
  Wrapper for list as input
  """

  _list = None


  def __init__(self, list, fields):
    self._list = list
    self._fields = fields
    self._recNo = 0


  def getNextRecord(self):
    try:
      if self._recNo >= len(self._list):
        return None
      ret = self._list[self._recNo]
      self._recNo += 1
    except:
      ret = None

    return ret


  def getCurPos(self):
    return 0
  
  def getFields(self):
    return self._fields


class DataOutputList(object):
  """
  List wrapper for output
  """

  metaProvider = None


  def __init__(self, file):
    self._store = []
    pass


  def appendRecord(self, record, inputRef=None):
    self._store.append(record)

  def close(self):
    pass

class DataOutputMyFile(object):
  """
  File wrapper for output
  """
  _file = None

  metaProvider = None


  def __init__(self, file):
    self._file = file


  def appendRecord(self, record, inputRef):
    if self._file == None:
      print 'No File'
    self._file.appendRecord(record)

  def close(self):
    self._file.close()



#def makeDataset(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0,
#                irregular=False, gaps=False, reset=False, sequenceId=False):
#  """Make dataset with certain characteristics
#
#  - years, months, days, hours. minutes, seconds : the time interval between
#     consecutive records
#  - irregular: if True introduce irregular intervals between records
#  - gaps: if True introduce gaps (missing records)
#  - reset: if reset is True, will generate a reset signal=1 in the 1st and 9th
#      records (meaning a second sequence started in the 9th). Otherwise only the
#      the 1st record will have a reset=1 meaning all the records belong to the
#      same sequence
#  - sequenceId: if sequenceId=True, will generate a sequenceId=1 for all the
#      records until the 8th record. All the records starting with the 9th will
#      have sequenceId=2 (meaning a second sequence started in the 9th).
#  Always generates 16 records to a file named test.csv
#  If irregular the 6rd and 7th records will be in the same period
#  If gaps there will be a gap of 3 periods between the 12th and 13th records
#  """
#  d = datetime.datetime(1,1,1)
#
#  period = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
#
#  # Verify that all variables are either 0 or 1
#  assert all(x in (0, 1) for x in (years, months,days, hours, minutes, seconds))
#  # Verify that only one time unit is periodized (easier to manage)
#  assert sum((years, months,days, hours, minutes, seconds)) == 1
#
#
#  fields =  [('reset', 'int', 'R'),
#             ('sequenceId', 'int', 'S'),
#             ('timestamp', 'datetime', 'T'),
#              ('a', 'int', ''),
#              ('b', 'int', ''),
#              ('c', 'int', ''),
#              ('d', 'int', '')]
#
#  with File('test.csv', fields) as f:
#    for i in range(4):
#      for j in range(4):
#        index = 4 * i + j
#        if irregular and index == 5:
#          y = 0
#          m = 0
#          p = None
#        elif gaps and index == 11:
#            y = years * 3
#            m = months * 3
#            y += m / 12
#            m = m % 12
#            p = period * 3
#        else:
#          y = years
#          m = months
#          p = period
#
#        if y > 0 or m > 0:
#          year = d.year + y + (d.month - 1 + m) / 12
#          month = (d.month - 1 + m) % 12 + 1
#          d = d.replace(year=year, month=month)
#        if p is not None:
#          d += p
#
#        if index == 0 or (index == 8 and reset):
#          resetSignal = 1
#        else:
#          resetSignal = 0
#
#        if index < 8:
#          seqId = 1
#        elif sequenceId:
#          seqId = 2
#
#
#        #line = '%d,%d,%s,%d,%d,%d\n' % (resetSignal, seqId, str(d), i, j, i * 100)
#        #print line
#        record = [resetSignal, seqId, d, i, j, i * 100]
#        f.write(record)
#
#  return


#def test():
#  average = lambda x: sum(x) / float(len(x))
#
#  #class TestParser(BaseParser):
#  #  def __init__(self):
#  #    def parseTimestamp(s):
#  #      d,t = s.split()
#  #      year, month, day = [int(x) for x in d.split('-')]
#  #      hour, minute, second = [int(x) for x in t.split(':')]
#  #      return datetime.datetime(year, month, day, hour, minute, second)
#  #
#  #    BaseParser.__init__(self,
#  #
#  #                        [('reset', int),
#  #                         ('sequenceId', int),
#  #                         ('timestamp', parseTimestamp),
#  #                         ('a', int),
#  #                         ('b', int),
#  #                         ('c', int),
#  #                         ('d', int)],
#  #                        delimiter=',')
#  #  def parse(self, line):
#  #    values = BaseParser.parse(self, line)
#  #    return values
#
#  from nupic.support import title
#
#
#  fields = [('timestamp', 'datetime', ''), ('b', 'float', ''), ('c', 'int', '')]
#
#  #-------------------------------
#  #
#  #  Regular intervals every minute
#  #
#  #-------------------------------
#  makeDataset(minutes=1)
#
#  title('Write entire file to standard output (16 records)')
#  with open('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 19
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate every 4 minutes (expecting 4 records)')
#
#
#  options = dict(
#  timeField=File('test.csv').fieldNames.index('timestamp'),
#  fields=[
#    # custom aggregate function
#    ('b', lambda seq: sum(seq) / float(len(seq))),
#    # built-in aggregate function
#    ('c',sum)],
#  minutes=4)
#
#
#  with File('test.csv') as f:
#
#
#
#    with File('test.bin', fields) as out:
#      # writing the file with fields b, c
#      _aggregate(f, options, out)
#
#
#  for i, r in enumerate(File('test.bin')):
#    timestamp, b, c = r
#    print "timestamp = %s" % timestamp
#    assert b == 1.5 # average
#    assert c == 400 * i
#
#  title('Aggregate every 2 minutes (expecting 8 records)')
#  options['minutes'] = 2
#
#  with File('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      assert b == 0.5 if (i % 2 == 0) else 2.5 # average
#      assert c == 200 * (i / 2)
#
#  #-------------------------------
#  #
#  #  Regular intervals every month
#  #
#  #-------------------------------
#  makeDataset(months=1)
#  title('Write entire file to standard output (16 records)')
#  with File('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 16
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate every 3 months (expecting 5 records)')
#
#  options['months'] = 3
#  options['minutes'] = 0
#
#  with File('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[0] == (1.0, 0)
#    assert values[3] == (2.0, 600)
#    assert values[4] == (1.0, 900)
#    assert values[5] == (3.0, 300) # aggregation of last record only
#
#  #-------------------------------
#  #
#  #  Irregular intervals every second
#  #
#  #-------------------------------
#  makeDataset(seconds=1, irregular=True)
#  title('Write entire file to standard output (16 records)')
#  with File('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 16
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate every second (expecting 15 records)')
#
#
#  options['months'] = 0
#  options['seconds'] = 1
#
#  with File('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[0] == (0.0, 0)
#    assert values[4] == (0.5, 200) # aggregate of two records
#    assert values[5] == (2.0, 100)
#    assert values[14] == (3.0, 300)
#
#
#  title('Aggregate every 8 seconds (expecting 2 records)')
#  options['seconds'] = 8
#
#  with File('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[0][1] == 600
#    assert values[1][1] == 1800
#
#
#  #-------------------------------
#  #
#  #  Annual intervals with a gap
#  #
#  #-------------------------------
#  makeDataset(years=1, gaps=1)
#  title('Write entire file to standard output (16 records)')
#  with File('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 16
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate two years (expecting 9 records)')
#
#  options['years'] = 2
#  options['seconds'] = 0
#
#  with File('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[5] == (2.0, 200) # aggregated just a single record due to the gap
#    assert values[6] == (3.0, 200) # aggregated just a single record due to the gap
#    assert values[7] == (0.5, 600)
#
#
#  #------------------------------------
#  #
#  #  Daily intervals with reset signal
#  #
#  #-----------------------------------
#  makeDataset(days=1, reset=True)
#  title('Write entire file to standard output (16 records)')
#  with File('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 16
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate 6 days (expecting 4 records)')
#  #
#  options['years'] = 0
#  options['resetField'] = 'reset'
#  options['days'] = 6
#
#  with File('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[0][1] == 200     # records 0 through 5
#    assert values[1] == (2.5, 200) # records 6 & 7
#    assert values[2][1] == 1400    # records 8 through 13
#    assert values[3] == (2.5, 600) # records 14 & 15
#
#  #------------------------------------
#  #
#  #  Daily intervals with sequence id
#  #
#  #-----------------------------------
#  makeDataset(days=1, sequenceId=True)
#  title('Write entire file to standard output (16 records)')
#  with open('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 16
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate 6 days (expecting 4 records)')
#  #
#  options['years'] = 0
#  options['resetField'] = None
#  options['sequenceIdField'] = 'sequenceId'
#  options['days'] = 6
#
#  with open('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[0][1] == 200     # records 0 through 5
#    assert values[1] == (2.5, 200) # records 6 & 7
#    assert values[2][1] == 1400    # records 8 through 13
#    assert values[3] == (2.5, 600) # records 14 & 15
#
#
#  #-------------------------------
#  #
#  #  Hourly intervals with a gap
#  #
#  #-------------------------------
#  makeDataset(hours=1, gaps=1)
#  title('Write entire file to standard output (16 records)')
#  with open('test.csv') as f:
#    lines = f.readlines()
#    assert len(lines) == 16
#    for line in lines:
#      print line[:-1]
#
#  title('Aggregate tow hours (expecting 9 records)')
#
#  options['hours'] = 2
#  options['days'] = 0
#
#  with open('test.csv') as f:
#    with File('test.bin', fields) as out:
#      _aggregate(f, options, out)
#
#    values = []
#    for i, r in enumerate(File('test.bin')):
#      print line
#      timestamp, b, c = r
#      values.append((b, c))
#
#    assert values[5] == (2.0, 200) # aggregated just a single record due to the gap
#    assert values[6] == (3.0, 200) # aggregated just a single record due to the gap
#    assert values[7] == (0.5, 600)



class AggregationTests(HelperTestCaseBase):

  def setUp(self):
    """ Method called to prepare the test fixture. This is called immediately
    before calling the test method; any exception raised by this method will be
    considered an error rather than a test failure. The default implementation
    does nothing.

    NOTE: this is called once for every sub-test and a new AggregationTests
      instance is constructed for every sub-test.
    """
    # Insert newline before each sub-test's output
    print
    return


  def test_GymAggregateWithOldData(self):
    filename = resource_filename(
      "nupic.datafiles", "extra/gym/gym.csv"
    )

    input = []

    gymFields = None

    with FileRecordStream(filename) as f:
      gymFields = f.getFields()
      for i in range(10):
        input.append(f.getNextRecord())

    #Append the records from the beginning to the end of the dataset
    input.extend(input[0:3])
    for h in (1,3):
      aggregationOptions = dict(
        fields=[
          ('timestamp', lambda x: x[0],),
          ('attendeeCount', sum),
          ('consumption', sum)],
        hours=h
      )


      handle = \
        tempfile.NamedTemporaryFile(prefix='test', 
          suffix='.bin')
      outputFile = handle.name
      handle.close()
      
      dataInput = DataInputList(input, gymFields)
      dataOutput = DataOutputList(None)

      _aggregate(input=dataInput, options=aggregationOptions, 
                 timeFieldName='timestamp', output=dataOutput)
      dataOutput.close()

      outputRecords = dataOutput._store
      
      timeFieldIdx = [f[0] for f in gymFields].index('timestamp')
      diffs = []
      for i in range(1,len(outputRecords)):
        diffs.append(outputRecords[i][timeFieldIdx] - \
                     outputRecords[i-1][timeFieldIdx])
      positiveTimeFlow = map((lambda x: x < datetime.timedelta(seconds=0)), 
                            diffs)
      #Make sure that old records are in the aggregated output and at the same
      #time make sure that they are in consecutive order after being inserted
      self.assertEquals(sum(positiveTimeFlow), 1)
        
    return

  def test_GymAggregate(self):
    filename = resource_filename(
      "nupic.datafiles", "extra/gym/gym.csv"
    )

    input = []

    gymFields = None

    with FileRecordStream(filename) as f:
      gymFields = f.getFields()
      for i in range(10):
        input.append(f.getNextRecord())

    for h in (1,3):
      aggregationOptions = dict(
        fields=[
          ('timestamp', lambda x: x[0],),
          ('attendeeCount', sum),
          ('consumption', sum)],
        hours=h
      )


      handle = \
        tempfile.NamedTemporaryFile(prefix='test', 
          suffix='.bin')
      outputFile = handle.name
      handle.close()
      
      dataInput = DataInputList(input, gymFields)
      dataOutput = DataOutputMyFile(FileRecordStream(outputFile, write=True,
                                                     fields=gymFields))

      _aggregate(input=dataInput, options=aggregationOptions, 
                 timeFieldName='timestamp', output=dataOutput)

      dataOutput.close()

      for r in FileRecordStream(outputFile):
        print r
      print '-' * 30

    return


  def test_GenerateDataset(self):
    dataset = 'extra/gym/gym.csv'

    print "Using input dataset: ", dataset

    filename = resource_filename("nupic.datafiles", dataset)

    with FileRecordStream(filename) as f:
      gymFields = f.getFieldNames()

    aggregationOptions = dict(
      timeField=gymFields.index('timestamp'),
      fields=[('attendeeCount', sum),
              ('consumption', sum),
              ('timestamp', lambda x: x[0])],

      hours=5
      )
    
    handle = \
      tempfile.NamedTemporaryFile(prefix='agg_gym_hours_5', 
        suffix='.csv', 
        dir=os.path.dirname(
          resource_filename("nupic.datafiles", dataset)
        )
      )
    outputFile = handle.name
    handle.close()

    print "Expected outputFile path: ", outputFile

    print "Files in the destination folder before the test:"
    print os.listdir(os.path.abspath(os.path.dirname(
      resource_filename("nupic.datafiles", dataset)))
    )

    if os.path.isfile(outputFile):
      print "Removing existing outputFile: ", outputFile
      os.remove(outputFile)

    self.assertFalse(os.path.exists(outputFile),
                     msg="Shouldn't exist, but does: " + str(outputFile))

    result = generateDataset(aggregationOptions, dataset, outputFile)
    print "generateDataset() returned: ", result

    f1 = os.path.abspath(os.path.normpath(result))
    print "normalized generateDataset() result path: ", f1
    f2 = os.path.normpath(outputFile)
    print "normalized outputFile path: ", f2
    self.assertEqual(f1, f2)

    print "Checking for presence of outputFile: ", outputFile
    self.assertTrue(
      os.path.isfile(outputFile),
      msg="Missing outputFile: %r; normalized generateDataset() result: %r" % (
        outputFile, f1))

    print "Files in the destination folder after the test:"
    print os.listdir(os.path.abspath(os.path.dirname(
      resource_filename("nupic.datafiles", dataset)
    )))

    print result
    print '-' * 30

    return


  def test_GapsInIrregularData(self):
    # Cleanup previous files if exist
    import glob
    for f in glob.glob('gap.*'):
      print 'Removing', f
      os.remove(f)

    #class TestParser(BaseParser):
    #  def __init__(self):
    #    def parseTimestamp(s):
    #      d,t = s.split()
    #      year, month, day = [int(x) for x in d.split('-')]
    #      hour, minute, second = [int(x) for x in t.split(':')]
    #      return datetime.datetime(year, month, day, hour, minute, second)
    #
    #    BaseParser.__init__(self,
    #                        [('dateTime', parseTimestamp),
    #                         ('sequenceId', int),
    #                         ('cardtype', int),
    #                         ('fraud', bool),
    #                         ('amount', float)],
    #                        delimiter=',')
    #  def parse(self, line):
    #    values = BaseParser.parse(self, line)
    #    return values

  #dateTime,cardnum,cardtype,fraud,amount
    data = """\
2009-04-03 19:05:06,129.3
2009-04-04 15:19:12,46.6
2009-04-07 02:54:04,30.32
2009-04-07 06:27:12,84.52
2009-04-07 06:42:21,21.1
2009-04-09 01:01:14,29.24
2009-04-09 06:47:42,99.76
2009-04-11 18:06:11,29.66
2009-04-11 18:12:53,148.32
2009-04-11 19:15:08,61.03
2009-04-15 19:25:40,53.14
2009-05-04 21:07:02,816.75
2009-05-04 21:08:27,686.07
2009-05-06 20:40:04,489.08
2009-05-06 20:40:42,586.9
2009-05-06 20:41:15,554.3
2009-05-06 20:41:51,652.11"""
    fields = [('timestamp', 'datetime', 'T'), ('amount', 'float', '')]
    with FileRecordStream(resource_filename('nupic.datafiles', 'gap.csv'), write=True, fields=fields) as f:
      lines = data.split('\n')
      for line in lines:
        t, a = line.split(',')

        components = t.split()

        yyyy, mm, dd = [int(x) for x in components[0].split('-')]
        h, m, s = [int(x) for x in components[1].split(':')]

        t = datetime.datetime(yyyy, mm, dd, h, m, s)
        a = float(a)
        f.appendRecord([t, a])

    aggregationOptions = dict(
      timeField='timestamp',
      fields=[('timestamp', lambda x: x[0]),
              ('amount', sum)],
      hours=24
      )


    handle = \
      tempfile.NamedTemporaryFile(prefix='agg_gap_hours_24', 
        suffix='.csv', 
        dir='.')
    outputFile = handle.name
    handle.close()
    
    if os.path.isfile(outputFile):
      os.remove(outputFile)
    self.assertFalse(os.path.exists(outputFile),
                     msg="shouldn't exist, but does: " + str(outputFile))

    result = generateDataset(aggregationOptions, 'gap.csv', outputFile)
    self.assertEqual(
      os.path.normpath(os.path.abspath(outputFile)), os.path.normpath(result),
      msg="result = '%s'; outputFile = '%s'" % (result, outputFile))
    self.assertTrue(os.path.isfile(outputFile),
                    msg="outputFile missing or is not file: %r" % (outputFile))
    print outputFile
    print '-' * 30

    s = ''
    for r in FileRecordStream(outputFile):
      s += ', '.join([str(x) for x in r]) + '\n'

    expected = """\
2009-04-03 19:05:06, 175.9
2009-04-06 19:05:06, 135.94
2009-04-08 19:05:06, 129.0
2009-04-10 19:05:06, 177.98
2009-04-11 19:05:06, 61.03
2009-04-15 19:05:06, 53.14
2009-05-04 19:05:06, 1502.82
2009-05-06 19:05:06, 2282.39
"""

    self.assertEqual(s, expected)

    return


  def test_AutoSpecialFields(self):
    # Cleanup old files
    #for f in glob.glob('*.*'):
    #  if 'auto_specials' in f:
    #    os.remove(f)


    fields = [('dummy', 'string', ''),
              ('timestamp', 'datetime', 'T'),
              ('reset', 'int', 'R'),
              ('sid', 'int', 'S'),
              ]

    records = (
      ['dummy-1', datetime.datetime(2000, 3, 1), 1, 1],
      ['dummy-2', datetime.datetime(2000, 3, 2), 0, 1],
      ['dummy-3', datetime.datetime(2000, 3, 3), 0, 1],
      ['dummy-4', datetime.datetime(2000, 3, 4), 1, 2],
      ['dummy-5', datetime.datetime(2000, 3, 5), 0, 2],
    )

    with FileRecordStream(resource_filename('nupic.datafiles', 'auto_specials.csv'), write=True, fields=fields) \
           as o:
      for r in records:
        o.appendRecord(r)

    # Aggregate just the dummy field, all the specials should be added
    ai = dict(
      fields=[('dummy', lambda x: x[0])],
      weeks=3
      )
    
    handle = \
      tempfile.NamedTemporaryFile(prefix='auto_specials', 
        suffix='.csv',
        dir='.')
    tempFile = handle.name
    handle.close()    

    outputFile = generateDataset(ai, 'auto_specials.csv', tempFile)

    result = []
    with FileRecordStream(outputFile) as f:
      print f.getFields()
      for r in f:
        result.append(r)

    self.assertEqual(result[0][2], 1) # reset
    self.assertEqual(result[0][3], 1) # seq id
    self.assertEqual(result[0][0], 'dummy-1')
    self.assertEqual(result[1][2], 1) # reset
    self.assertEqual(result[1][3], 2) # seq id
    self.assertEqual(result[1][0], 'dummy-4')

    return


  def test_WeightedMean(self):
    # Cleanup old files
    #for f in glob.glob('*.*'):
    #  if 'auto_specials' in f:
    #    os.remove(f)


    fields = [('dummy1', 'int', ''),
              ('dummy2', 'int', ''),
              ('timestamp', 'datetime', 'T'),
              ]

    records = (
      [10, 1, datetime.datetime(2000, 3, 1)],
      [5, 2, datetime.datetime(2000, 3, 2)],
      [1, 100, datetime.datetime(2000, 3, 3)],
      [2, 4, datetime.datetime(2000, 3, 4)],
      [4, 1, datetime.datetime(2000, 3, 5)],
      [4, 0, datetime.datetime(2000, 3, 6)],
      [5, 0, datetime.datetime(2000, 3, 7)],
      [6, 0, datetime.datetime(2000, 3, 8)],
    )

    with FileRecordStream(resource_filename('nupic.datafiles', 'weighted_mean.csv'), write=True, fields=fields) \
          as o:
      for r in records:
        o.appendRecord(r)

    # Aggregate just the dummy field, all the specials should be added
    ai = dict(
      fields=[('dummy1', 'wmean:dummy2', None),
              ('dummy2', 'mean', None)],
      days=2
      )
    
    handle = \
      tempfile.NamedTemporaryFile(prefix='weighted_mean', 
        suffix='.csv',
        dir='.')
    tempFile = handle.name
    handle.close()    

    outputFile = generateDataset(ai, 'weighted_mean.csv', tempFile)

    result = []
    with FileRecordStream(outputFile) as f:
      print f.getFields()
      for r in f:
        result.append(r)

    self.assertEqual(result[0][0], 6.0)
    self.assertEqual(result[0][1], 1.0)
    self.assertEqual(result[1][0], 1.0)
    self.assertEqual(result[1][1], 52.0)
    self.assertEqual(result[2][0], 4.0)
    self.assertEqual(result[2][1], 0.0)
    self.assertEqual(result[3][0], None)
    self.assertEqual(result[3][1], 0.0)
    return


if __name__=='__main__':
  nupic_support.initLogging()

  # Add verbosity to unittest output (so it prints a header for each test)
  #sys.argv.append("--verbose")

  # Run the test
  unittest.TestProgram()
