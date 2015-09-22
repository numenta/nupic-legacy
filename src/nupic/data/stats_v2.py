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

import itertools
import pprint
import operator
from collections import defaultdict

from pkg_resources import resource_filename

import numpy
from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import date as DateEncoder


VERBOSITY = 0

"""
We collect stats for each column in the datafile.

Supported stats fields are

int
float
string
datetime
bool

class ModelStatsCollector(object):
  def __init__(self, fieldname):
    pass

  def addValue(self, value):
    pass

  def getStats(self,):
    pass
"""

class BaseStatsCollector(object):

  def __init__(self, fieldname, fieldtype, fieldspecial):
    self.fieldname = fieldname
    self.fieldtype = fieldtype
    self.fieldspecial = fieldspecial
    # we can remove value list if it is a speed or memory bottleneck
    self.valueList = []
    self.valueSet = set()

  def addValue(self, value):
    self.valueList.append(value)
    self.valueSet.add(value)

  def getStats(self, stats):
    # Intialize a new dict for this field
    stats[self.fieldname] = dict()
    stats[self.fieldname]['name']    = self.fieldname
    stats[self.fieldname]['type']    = self.fieldtype
    stats[self.fieldname]['special'] = self.fieldspecial

    # Basic stats valid for all fields
    totalNumEntries = len(self.valueList)
    totalNumDistinctEntries = len(self.valueSet)
    stats[self.fieldname]['totalNumEntries'] = totalNumEntries
    stats[self.fieldname]['totalNumDistinctEntries'] = totalNumDistinctEntries

    if VERBOSITY > 1:
      print "-"*40
      print "Field '%s'" % self.fieldname
      print "--"
      print "Counts:"
      print "Total number of entries:%d" % totalNumEntries
      print "Total number of distinct entries:%d" % totalNumDistinctEntries

class StringStatsCollector(BaseStatsCollector):

  def getStats(self, stats):

    BaseStatsCollector.getStats(self, stats)

    if VERBOSITY > 2:

      valueCountDict = defaultdict(int)
      for value in self.valueList:
        valueCountDict[value] += 1

      print "--"
      # Print the top 5 frequent strings
      topN = 5
      print " Sorted list:"
      for key, value in sorted(valueCountDict.iteritems(),
                               key=operator.itemgetter(1),
                               reverse=True,)[:topN]:

        print "%s:%d" % (key, value)
      if len(valueCountDict) > topN:
        print "..."

class NumberStatsCollector(BaseStatsCollector):

  def getStats(self, stats):
    """ Override of getStats()  in BaseStatsCollector

        stats: A dictionary where all the stats are
        outputted

    """
    BaseStatsCollector.getStats(self, stats)

    sortedNumberList = sorted(self.valueList)
    listLength = len(sortedNumberList)
    min = sortedNumberList[0]
    max = sortedNumberList[-1]
    mean = numpy.mean(self.valueList)
    median = sortedNumberList[int(0.5*listLength)]
    percentile1st = sortedNumberList[int(0.01*listLength)]
    percentile99th = sortedNumberList[int(0.99*listLength)]

    differenceList = \
               [(cur - prev) for prev, cur in itertools.izip(list(self.valueSet)[:-1],
                                                             list(self.valueSet)[1:])]
    if min > max:
      print self.fieldname, min, max, '-----'
    meanResolution = numpy.mean(differenceList)


    stats[self.fieldname]['min'] = min
    stats[self.fieldname]['max'] = max
    stats[self.fieldname]['mean'] = mean
    stats[self.fieldname]['median'] = median
    stats[self.fieldname]['percentile1st'] = percentile1st
    stats[self.fieldname]['percentile99th'] = percentile99th
    stats[self.fieldname]['meanResolution'] = meanResolution

    # TODO: Right now, always pass the data along.
    # This is used for data-dependent encoders.
    passData = True
    if passData:
      stats[self.fieldname]['data'] = self.valueList

    if VERBOSITY > 2:
      print '--'
      print "Statistics:"
      print "min:", min
      print "max:", max
      print "mean:", mean
      print "median:", median
      print "1st percentile :", percentile1st
      print "99th percentile:", percentile99th

      print '--'
      print "Resolution:"
      print "Mean Resolution:", meanResolution

    if VERBOSITY > 3:
      print '--'
      print "Histogram:"
      counts, bins = numpy.histogram(self.valueList, new=True)
      print "Counts:", counts.tolist()
      print "Bins:", bins.tolist()


class IntStatsCollector(NumberStatsCollector):
  pass

class FloatStatsCollector(NumberStatsCollector):
  pass

class BoolStatsCollector(BaseStatsCollector):
  pass

class DateTimeStatsCollector(BaseStatsCollector):

  def getStats(self, stats):

    BaseStatsCollector.getStats(self, stats)

    # We include subencoders for datetime field if there is a variation in encodings
    # for that particular subencoding
    # gym_melbourne_wed_train.csv has data only on the wednesdays, it doesn't
    # make sense to include dayOfWeek in the permutations because it is constant
    # in the entire dataset

    # We check for variation in sub-encodings by passing the timestamp field
    # through the maximal sub-encoder and checking for variation in post-encoding
    # values

    # Setup a datetime encoder with maximal resolution for each subencoder
    encoder = DateEncoder.DateEncoder(season=(1,1), # width=366, resolution=1day
                                      dayOfWeek=(1,1), # width=7, resolution=1day
                                      timeOfDay=(1,1.0/60), # width=1440, resolution=1min
                                      weekend=1, # width=2, binary encoding
                                      holiday=1, # width=2, binary encoding
                                      )

    # Collect all encoder outputs
    totalOrEncoderOutput = numpy.zeros(encoder.getWidth(), dtype=numpy.uint8)
    for value in self.valueList:
      numpy.logical_or(totalOrEncoderOutput, encoder.encode(value),
                       totalOrEncoderOutput)

    encoderDescription = encoder.getDescription()
    numSubEncoders = len(encoderDescription)
    for i in range(numSubEncoders):
      subEncoderName,_ = encoderDescription[i]
      beginIdx = encoderDescription[i][1]
      if i == (numSubEncoders - 1):
        endIdx = encoder.getWidth()
      else:
        endIdx = encoderDescription[i+1][1]
      stats[self.fieldname][subEncoderName] = \
                                 (totalOrEncoderOutput[beginIdx:endIdx].sum()>1)

    decodedInput = encoder.decode(totalOrEncoderOutput)[0]

    if VERBOSITY > 2:
      print "--"
      print "Sub-encoders:"
      for subEncoderName,_ in encoderDescription:
        print "%s:%s" % (subEncoderName, stats[self.fieldname][subEncoderName])

def generateStats(filename, maxSamples = None,):
  """
  Collect statistics for each of the fields in the user input data file and
  return a stats dict object.

  Parameters:
  ------------------------------------------------------------------------------
  filename:             The path and name of the data file.
  maxSamples:           Upper bound on the number of rows to be processed
  retval:               A dictionary of dictionaries. The top level keys are the
                        field names and the corresponding values are the statistics
                        collected for the individual file.
                        Example:
                        {
                          'consumption':{'min':0,'max':90,'mean':50,...},
                          'gym':{'numDistinctCategories':10,...},
                          ...
                         }


  """
  # Mapping from field type to stats collector object
  statsCollectorMapping = {'float':    FloatStatsCollector,
                           'int':      IntStatsCollector,
                           'string':   StringStatsCollector,
                           'datetime': DateTimeStatsCollector,
                           'bool':     BoolStatsCollector,
                           }

  filename = resource_filename("nupic.datafiles", filename)
  print "*"*40
  print "Collecting statistics for file:'%s'" % (filename,)
  dataFile = FileRecordStream(filename)

  # Initialize collector objects
  # statsCollectors list holds statsCollector objects for each field
  statsCollectors = []
  for fieldName, fieldType, fieldSpecial in dataFile.getFields():
    # Find the corresponding stats collector for each field based on field type
    # and intialize an instance
    statsCollector = \
            statsCollectorMapping[fieldType](fieldName, fieldType, fieldSpecial)
    statsCollectors.append(statsCollector)

  # Now collect the stats
  if maxSamples is None:
    maxSamples = 500000
  for i in xrange(maxSamples):
    record = dataFile.getNextRecord()
    if record is None:
      break
    for i, value in enumerate(record):
      statsCollectors[i].addValue(value)

  # stats dict holds the statistics for each field
  stats = {}
  for statsCollector in statsCollectors:
    statsCollector.getStats(stats)

  # We don't want to include reset field in permutations
  # TODO: handle reset field in a clean way
  if dataFile.getResetFieldIdx() is not None:
    resetFieldName,_,_ = dataFile.getFields()[dataFile.reset]
    stats.pop(resetFieldName)

  if VERBOSITY > 0:
    pprint.pprint(stats)

  return stats

def testGym1():
  generateStats("extra/gym/gym_melbourne_wed_train.csv")

def testGym2():
  generateStats("extra/gym/gym_melbourne_train.csv")

def testGym3():
  generateStats("extra/gym/gym_train.csv")

def testIris():
  generateStats("extra/iris/iris_train.csv")

def testMovieLens():
  generateStats("extra/movielens100k/movie_train.csv")

if __name__=="__main__":
  testIris()
  testGym1()
  testGym2()
  testGym3()
  testMovieLens()
