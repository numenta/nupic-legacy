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

import sys
import os
import numpy
import pprint
from copy import deepcopy
import math

import pylab

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA

#############################################################################
class IpsDetails(object):
  """ This class is a container for capturing and reporting input prediction
  score stats for a particular offset within each sequence. This class is
  used by both this module and the ngramstats module.
  """

  #######################################################################
  def __init__(self, netInfo, fieldName, offset, maxPathLen, clientName=''):
    """ Instantiate data structures for capturing IPS stats at this offset
    within each sequence.

    Parameters:
    -----------------------------------------------------------------
    netInfo:            Info about the trained network
    fieldName:          Which input field name to capture details for
    offset:             Which element offset to capture stats for, or None
                          if you want to capture for all elements
    maxPathLen:         Maximum path length to record. We categorize errors
                          by the path leading up to them.
    clientName:         Name of the caller, for print messages

    """

    # Save params
    self.clientName = clientName
    self.fieldName = fieldName
    self.targetOffset = offset
    self.maxPathLen = maxPathLen

    # Field offset
    sourceFieldNames = netInfo['encoder'].getScalarNames()
    self.fieldIdx = sourceFieldNames.index(fieldName)

    # Index within the current sequence
    self.idxWithinSequence = 0

    # Current path. This is the list of the last N scalar input values seen
    self.path = []

    # Number of samples for each path into this offset. The key is a string
    #  representing the path into this offset. Each value is
    #  [numSamples, numErrs]
    self.stats = dict()


  #######################################################################
  def compute(self, sampleIdx, resetOutput, sourceScalars,
                predictedSourceScalars):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:                The index assigned to this sample
    resetOutput:              The reset signal for this sample
    sourceScalars:            The actual source scalars for this sample
    predictedSourceScalars:   The predicted source scalars for this sample
    """

    # Which element within a sequence are we in?
    if resetOutput:
      self.idxWithinSequence = 0
    else:
      self.idxWithinSequence += 1

    # Get the scalar value coming into our target field
    scalarIn = sourceScalars[self.fieldIdx]
    predictedScalarIn = predictedSourceScalars[self.fieldIdx]

    # --------------------------------------------------------------
    # Update the path of the last N elements
    if self.idxWithinSequence == 0:
      self.path = [scalarIn]

    else:
      self.path.append(scalarIn)
      if len(self.path) > self.maxPathLen + 1:
        self.path.pop(0)

    # Should we accumulate stats at this element?
    if len(self.path) <= 1:
      return

    if self.targetOffset is not None \
            and self.idxWithinSequence != self.targetOffset:
      return

    # -----------------------------------------------------------------------
    # Accumulate stats
    else:
      pathStr = '_'.join([str(x) for x in self.path[0:-1]])

      #if pathStr == '80.0_68.0':
      #  print sampleIdx, self.path, self.clientName, "act:", scalarIn, "pred:", \
      #          predictedScalarIn
      #  #import pdb; pdb.set_trace()

      [numSamples, numErrs] = self.stats.get(pathStr, [0, 0])
      numSamples += 1
      if scalarIn != predictedScalarIn:
        numErrs += 1
      self.stats[pathStr] = [numSamples, numErrs]


  #########################################################################
  def printStats(self):
    """ Print out the detailed information we captured.


    """

    # --------------------------------------------------------------------
    # Compute an accuracy for each path and sort by frequency
    accuracies = []
    maxKeyLen = 0
    totalSamples = 0
    totalErrors = 0
    for (path, (numSamples, numErrs)) in self.stats.iteritems():
      maxKeyLen = max(maxKeyLen, len(path))
      accuracy = float(numSamples - numErrs) / numSamples
      accuracies.append((path, accuracy, numSamples))
      totalSamples += numSamples
      totalErrors += numErrs


    def compareFunc(x, y):
      # Put preference in the one with more samples
      if x[2] != y[2]:
        return int(y[2] - x[2])

      # If num samples are the same, sort by path
      if x[0] > y[0]:
        return 1
      elif x[0] < y[0]:
        return -1
      else:
        return 0

    accuracies.sort(cmp=compareFunc)


    # --------------------------------------------------------------------
    # Pretty print the results
    format = "%%-%ds" % (maxKeyLen)

    print
    if self.targetOffset is not None:
      print "\n%s prediction details for field '%s', offset %d within each " \
          "sequence:" % (self.clientName, self.fieldName, self.targetOffset)
    print "\n%s prediction details for field '%s', categorized by the last " \
          "%d elements leading into each element:" % (self.clientName,
          self.fieldName, self.maxPathLen)
    print format % ("path"), "  accuracy  numSamples numErrors"
    print "--------------------------------------------------------------"
    print format % ("overall"), "  %6.2f    %5d    %5d" % \
        (100.0*(totalSamples-totalErrors)/totalSamples, totalSamples, totalErrors)
    for (path, accuracy, numSamples) in accuracies:
      print format % (path), "  %6.2f    %5d    %5d" % (100.0*accuracy,
            numSamples, round(numSamples*(1.0-accuracy)))
    print

#############################################################################
class PredictionLogger(object):
  """
  This class logs the actual and predicted values to the disk.
  """
  #######################################################################
  def __init__(self, netInfo, options, label='unknown'):
    """ Instantiate the log file and write the header line with columns names

    Parameters:
    -----------------------------------------------------------------
    options:    object containing all "command-line" options for post-processsing
    """
    # --
    # Instatiate the log file
    # Split base filename
    root, ext = os.path.splitext(options['predictionLogFilename'])
    # Append label to distinguish between spatial and temporal predictions
    filename = '%s_%s.csv' % (root, label)
    # open in write mode for logging
    self.logFile = open(filename, "w")

    # --
    # Write the header line with columns names
    # Get field names
    sourceFieldNames = netInfo['encoder'].getScalarNames()
    # Collect the list of column names
    columnNames = []
    columnNames.append('reset')
    for fieldName in sourceFieldNames:
      columnNames.extend(['%s_actual' % fieldName,'%s_predicted' % fieldName])
    # Write the header line
    print >>self.logFile, ','.join(columnNames)

  #######################################################################
  def log(self, reset, actualScalarValues, predictedScalarValues):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    reset:                    The reset signal for this sample
    actualScalarValues:       The actual source scalars for this sample
    predictedScalarValues:    The predicted source scalars for this sample
    """

    dataRow = '%s,' % reset
    for actualScalarValue, predictedScalarValue in zip(actualScalarValues,
                                                       predictedScalarValues):
      dataRow += '%s,%s,' % (actualScalarValue, predictedScalarValue)

    print >>self.logFile, dataRow[:-1]



#############################################################################
class TemporalHistogram(object):
  """
  This class is a container for capturing and reporting prediction errors at all
  offsets within each sequence.
  The error histograms are saved as png files in the end.
  """

  #######################################################################
  def __init__(self, netInfo, maxOffset=24,
               temporalHistogramFilename='temporalHistogram.txt'):
    """ Instantiate data structures for capturing IPS stats at this offset
    within each sequence.

    Parameters:
    -----------------------------------------------------------------
    netInfo:                      Info about the trained network.
    maxOffset:                    Maximum offset for saving error info. Error
                                  stats from the first <maxOffset> timesteps after
                                  the reset are stored and processed.
    temporalHistogramFilename:    Filename for saving the plots.
    """
    # Save params
    self.netInfo                   = netInfo
    self.maxOffset                 = maxOffset
    self.temporalHistogramFilename = temporalHistogramFilename


    # Field Names
    self.sourceFieldNames = netInfo['encoder'].getScalarNames()

    # Index within the current sequence
    self.idxWithinSequence = 0

    # To collect error stats for each field at each offset.
    # The key is a tuple   (fieldName, offset)
    # The value is a tuple (numSamples, sumOfErrors,
    #                        sumOfScalars, sumOfPredictedScalars)
    self.stats = dict()
    pass


  #######################################################################
  def compute(self, sampleIdx, resetOutput, sourceScalars,
                predictedSourceScalars, absSourceCloseness):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:                The index assigned to this sample
    resetOutput:              The reset signal for this sample
    sourceScalars:            The actual source scalars for this sample
    predictedSourceScalars:   The predicted source scalars for this sample
    """

    # Which element within a sequence are we in?
    if resetOutput:
      self.idxWithinSequence = 0
    else:
      self.idxWithinSequence += 1


    # We keep error stastics only for the first <maxOffset> timesteps after reset
    if self.idxWithinSequence > self.maxOffset:
      return

    # Get the scalar value coming for the selected fields
    for fieldIdx, fieldName in enumerate(self.sourceFieldNames):

      sourceIn          = sourceScalars[fieldIdx]
      predictedIn = predictedSourceScalars[fieldIdx]
      sourceClosenessIn = absSourceCloseness[fieldIdx]

      isNumber = isinstance(sourceIn, (float, int))

      key = (fieldName, self.idxWithinSequence)
      (numSamples, sumOfErrors,
         sumOfScalars, sumOfPredictedScalars) = self.stats.get(key, (0, 0, 0, 0))

      numSamples            += 1
      sumOfErrors           += sourceClosenessIn
      if isNumber:
        sumOfScalars          += scalarIn
        sumOfPredictedScalars += predictedScalarIn
      else:
        sumOfScalars = None
        sumOfPredictedScalars = None

      self.stats[key]        = (numSamples, sumOfErrors,
                                sumOfScalars, sumOfPredictedScalars)



  #########################################################################
  def getStats(self, stats):
    """ Print out the detailed information we captured.
    """

    imageFiles = dict()
    # We print a seperate plot for each field
    for sourceFieldName in self.sourceFieldNames:

      # Filter the stats for this particular field - sourceFieldName
      fieldScores = dict()
      for key, value in self.stats.iteritems():
        fieldName, offset = key
        # Skip other fields
        if fieldName != sourceFieldName:
          continue
        newKey = offset
        fieldScores[newKey] = value

      # Get a sorted list of the stats sorted by the offset. Default sort of a
      # dict is by the key
      fieldScores = sorted(fieldScores.iteritems())

      # Helper Function
      def summarizeScore(score):
        """
        score is a tuple of the form
        (offset, (numSamples, sumOfErrors, sumOfScalars, sumOfPredictedScalars))
        """
        offset     = score[0]
        numSamples = max(1,score[1][0])
        error      = score[1][1]/numSamples
        if score[1][2] is not None:
          avgScalar  = score[1][2]/numSamples
        else:
          avgScalar = 0

        if score[1][3] is not None:
          predScalar = score[1][3]/numSamples
        else:
          predScalar = 0
        return (offset, error, avgScalar, predScalar)

      offsets, absErrors, \
        avgScalars, avgPredScalars = zip(*map(summarizeScore, fieldScores))

      fig = pylab.figure()

      axes = fig.add_subplot(2,1,1)
      axes.plot(offsets, absErrors)
      axes.set_xlabel('Offset')
      axes.set_ylabel('Error In Field Units')
      axes.set_title(sourceFieldName)

      axes = fig.add_subplot(2,1,2)
      axes.plot(offsets, avgScalars)
      axes.plot(offsets, avgPredScalars)
      axes.set_xlabel('Offset')
      axes.set_ylabel('Field Units')

      prefix = os.path.splitext(self.temporalHistogramFilename)[0]
      imageFilename = "%s_%s.png" % (prefix, sourceFieldName)
      fig.savefig(imageFilename)


#############################################################################
class InputPredictionStats(object):
  """ This class calculates various metrics related to predicting the
  next input using top-down computations.
  """

  #########################################################################
  @staticmethod
  def isSupported(netInfo, options, baseline, logNames):
    """ Return true if we support collecting stats in the passed in
    configuration.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    return  ('spTDOut' in logNames)

  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for calculating the SP stats on a given
    data set.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    # Get info about the network
    self.netInfo = netInfo
    self.options = options

    # Get the field names
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()
    self.numFields = len(self.sourceFieldNames)

    # Init previous values
    self.spTDOutputPrev = None
    self.sensorTDOutputPrev = numpy.zeros(self.numFields)
    self.sensorTDOutputValuePrev = [None] * self.numFields

    # Record the accuracy for each desired burn-in
    self.numSamples = dict()
    self.sourceClosenessSums = dict()
    self.absSourceClosenessSums = dict()
    self.rmseSourceClosenessSums = dict()
    for burnIn in self.options['burnIns']:
      self.numSamples[burnIn] = 0
      self.sourceClosenessSums[burnIn] = numpy.zeros(self.numFields)
      self.absSourceClosenessSums[burnIn] = numpy.zeros(self.numFields)
      self.rmseSourceClosenessSums[burnIn] = numpy.zeros(self.numFields)

    # Record the accuracy for each desired 'at' offset
    self.numSamplesAt = dict()
    self.sourceClosenessSumsAt = dict()
    self.absSourceClosenessSumsAt = dict()
    self.rmseSourceClosenessSumsAt = dict()
    for offset in self.options['ipsAt']:
      self.numSamplesAt[offset] = 0
      self.sourceClosenessSumsAt[offset] = numpy.zeros(self.numFields)
      self.absSourceClosenessSumsAt[offset] = numpy.zeros(self.numFields)
      self.rmseSourceClosenessSumsAt[offset] = numpy.zeros(self.numFields)


    # Where we are within a sequence, used to figure out which burn-in
    # is appropriate
    self.idxWithinSequence = 0

    # Capture the sequence lengths
    self.seqLengths = []


    # -----------------------------------------------------------------------
    # Are we capturing prediction score details at a particular offset?
    detailsAt = options['ipsDetailsFor']
    if detailsAt is not None:
      (fieldName, offset, maxPathLen) = detailsAt.split(',')
      assert fieldName in self.sourceFieldNames
      offset = eval(offset)
      maxPathLen = eval(maxPathLen)
      self.ipsDetailsAt = IpsDetails(netInfo, fieldName, offset, maxPathLen,
                            clientName="TP")
    else:
      self.ipsDetailsAt = None


    plotTemporalHistograms = options['plotTemporalHistograms']
    if plotTemporalHistograms:
      self.temporalHistogram = TemporalHistogram(netInfo, maxOffset=25,
          temporalHistogramFilename = self.options['temporalHistogramFilename'])
    else:
      self.temporalHistogram = None

    if options['logPredictions']:
      self.predictionLogger = PredictionLogger(netInfo, options, label='TP')
    else:
      self.predictionLogger = None


  #########################################################################
  def compute(self, sampleIdx, data):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           Logged data for this sample

    """

    # Get the data we need
    resetOutput = data['reset']
    spTDOutput = data['spTDOut']
    sensorBUInput = data['sourceScalars']


    # Compute the sensor top-down out
    #if sampleIdx >= 413:
    #  import pdb; pdb.set_trace()
    sensorTDOutputResults = self.netInfo['encoder'].topDownCompute(spTDOutput)
    sensorTDOutput = [x.scalar for x in sensorTDOutputResults]
    sensorTDOutputValues = [x.value for x in sensorTDOutputResults]

    ##################################################################################################################
    ### this is a temporary hack until we decide how to deal with missing input values when evaluating a network
    ### for now, error is always 0 for missing values
    ##################################################################################################################
    for i in range(len(sensorBUInput)):
        if sensorBUInput[i] == SENTINEL_VALUE_FOR_MISSING_DATA:
            sensorBUInput[i] = sensorTDOutput[i]

    #print sensorBUInput

    if self.spTDOutputPrev is None:
      self.spTDOutputPrev = sensorTDOutput


    # Which element within a sequence are we in?
    if resetOutput:
      if sampleIdx > 0:
        self.seqLengths.append(self.idxWithinSequence+1)
      self.idxWithinSequence = 0
      #self.sensorTDOutputPrev.fill(0)   # Prediction not applicable
      self.sensorTDOutputPrev = [0.0] * len(self.sensorTDOutputPrev)
    else:
      self.idxWithinSequence += 1


    # ------------------------------------------------------------------
    # Compute IPS details if requested
    if self.ipsDetailsAt is not None:
      self.ipsDetailsAt.compute(sampleIdx, resetOutput=resetOutput,
          sourceScalars = sensorBUInput,
          predictedSourceScalars = self.sensorTDOutputPrev)


    # -------------------------------------------------------------------
    # Log actual and predicted values to a file
    if self.predictionLogger:
      # TODO log strings instead of indices
      self.predictionLogger.log(reset=resetOutput,
                                actualScalarValues=sensorBUInput,
                                predictedScalarValues=self.sensorTDOutputValuePrev)


    # ------------------------------------------------------------------
    # Compute the errors at the sensor input level. This is the difference
    #  between the scalar values read directly from the data source and the
    #  scalar values computed from the top-down output from the encoders
    # expressed as a fractional value of the total range
    sourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                self.sensorTDOutputPrev)


    # ------------------------------------------------------------------
    # Compute the errors at the sensor input level. This is the difference
    #  between the scalar values read directly from the data source and the
    #  scalar values computed from the top-down output from the encoders
    # expressed in the absolute units of the input data
    absSourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                self.sensorTDOutputPrev, fractional=False)


    # Update the sums for the burn-ins that are applicable
    for burnIn in self.options['burnIns']:
      if self.idxWithinSequence < burnIn:
        continue
      self.numSamples[burnIn] += 1
      self.sourceClosenessSums[burnIn] += sourceCloseness
      self.absSourceClosenessSums[burnIn] += absSourceCloseness
      self.rmseSourceClosenessSums[burnIn] += numpy.square(absSourceCloseness)

    # Update the sums for the ipsAt's that are applicable
    if self.idxWithinSequence in self.options['ipsAt']:
      self.numSamplesAt[self.idxWithinSequence] += 1
      self.sourceClosenessSumsAt[self.idxWithinSequence] += sourceCloseness
      self.absSourceClosenessSumsAt[self.idxWithinSequence] += absSourceCloseness
      self.rmseSourceClosenessSumsAt[self.idxWithinSequence] += \
                                                numpy.square(absSourceCloseness)

    if self.temporalHistogram is not None:
      self.temporalHistogram.compute(sampleIdx, resetOutput=resetOutput,
          sourceScalars = sensorBUInput,
          predictedSourceScalars = self.sensorTDOutputPrev,
          absSourceCloseness = absSourceCloseness)

    # ------------------------------------------------------------------------
    # Verbose printing
    if self.options['verbosity'] >= 2:
      self.netInfo['encoder'].pprint(self.spTDOutputPrev,  prefix="  prevSPTDOut:")
      nzs =  self.spTDOutputPrev.nonzero()[0]
      for nz in nzs:
        print "%d:%f, " % (nz, self.spTDOutputPrev[nz]),
      print
      #print "sensorTDDesc:", self.netInfo['encoder'].decodedToStr(
      #                        self.netInfo['encoder'].decode(spTDOutput))
      print " prevEncTDOut:", self.netInfo['encoder'].scalarsToStr(
                                                self.sensorTDOutputPrev,
                                                self.sourceFieldNames)
      print "    closeness:", self.netInfo['encoder'].scalarsToStr(
                                                sourceCloseness,
                                                self.sourceFieldNames)
      print "abs closeness:", self.netInfo['encoder'].scalarsToStr(
                                                absSourceCloseness,
                                                self.sourceFieldNames)

    # Update the previous values
    self.sensorTDOutputPrev = sensorTDOutput
    self.sensorTDOutputValuePrev = sensorTDOutputValues
    self.spTDOutputPrev = spTDOutput


  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    # -------------------------------------------------------------------
    # Summarize the sequence length statistics
    if len(self.seqLengths) == 0:
      self.seqLengths = [self.idxWithinSequence]
    seqLengths = numpy.array(self.seqLengths)
    stats['seqLengthMin'] = seqLengths.min()
    stats['seqLengthMax'] = seqLengths.max()
    stats['seqLengthAvg'] = seqLengths.mean()
    stats['numSequences'] = len(seqLengths)


    # -------------------------------------------------------------------
    # Summarize the input prediction score at various burn-ins
    for burnIn in self.options['burnIns']:
      numSamples = self.numSamples[burnIn]
      sourceClosenessSums = self.sourceClosenessSums[burnIn]
      absSourceClosenessSums = self.absSourceClosenessSums[burnIn]
      rmseSourceClosenessSums = self.rmseSourceClosenessSums[burnIn]

      burnInLabel = '_burnIn%d' % (burnIn)
      if burnIn == 1 and len(self.options['burnIns']) == 1:
        burnInLabel = ''

      # Compute closeness from 0 to 1.0
      fieldScores = sourceClosenessSums / max(1.0, numSamples)
      if len(fieldScores) >= 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['inputPredScore%s_%s' % (burnInLabel, fieldName)] = score
      stats['inputPredScore%s' % (burnInLabel)] = fieldScores.mean()

      # Closeness in absolute units
      # Doesn't make sense to take a mean across all fields
      fieldScores = absSourceClosenessSums / max(1.0, numSamples)
      if len(fieldScores) >= 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['inputPredScore%s_%s_abs' % (burnInLabel, fieldName)] = score

      # Closeness in absolute units
      fieldScores = numpy.sqrt(rmseSourceClosenessSums / max(1.0, numSamples))
      if len(fieldScores) >= 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['inputPredScore%s_%s_rmse' % (burnInLabel, fieldName)] = score



    # -------------------------------------------------------------------
    # Summarize the input prediction score at various offsets
    for offset in self.options['ipsAt']:
      numSamples = self.numSamplesAt[offset]
      sourceClosenessSums = self.sourceClosenessSumsAt[offset]
      absSourceClosenessSums = self.absSourceClosenessSumsAt[offset]
      rmseSourceClosenessSums = self.rmseSourceClosenessSumsAt[offset]

      atLabel = '_at%d' % (offset)

      # Compute closeness from 0 to 1.0
      fieldScores = sourceClosenessSums / max(1.0, numSamples)
      if len(fieldScores) > 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['inputPredScore%s_%s' % (atLabel, fieldName)] = score
      stats['inputPredScore%s' % (atLabel)] = fieldScores.mean()

      # Closeness in absolute units
      # Doesn't make sense to take a mean across all fields
      fieldScores = absSourceClosenessSums / max(1.0, numSamples)
      if len(fieldScores) > 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['inputPredScore%s_%s_abs' % (atLabel, fieldName)] = score

      # Closeness in rmse units
      # Doesn't make sense to take a mean across all fields
      fieldScores = numpy.sqrt(rmseSourceClosenessSums / max(1.0, numSamples))
      if len(fieldScores) > 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['inputPredScore%s_%s_rmse' % (atLabel, fieldName)] = score


    # -------------------------------------------------------------------
    # Print out IPS details if requested
    if self.ipsDetailsAt is not None:
      self.ipsDetailsAt.printStats()

    if self.temporalHistogram is not None:
      self.temporalHistogram.getStats(stats)

#############################################################################
class MultiStepPredictionStats(object):
  """ This class calculates various metrics related to predicting the
  future inputs using top-down computations.
  """

  #########################################################################
  @staticmethod
  def isSupported(netInfo, options, baseline, logNames):
    """ Return true if we support collecting stats in the passed in
    configuration.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    return  ('reset' in logNames) and \
            ('sourceScalars' in logNames) and \
            ('multiStepPrediction' in logNames)


  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for calculating the SP stats on a given
    data set.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """

    # Get info about the network
    self.netInfo = netInfo
    self.options = options

    # Init variables
    self._nMultiStepPrediction    = netInfo['nMultiStepPrediction']
    self._burnIn                  = netInfo['burnIn']
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()

    # Variables to hold statistics
    self._nFields         = len(self.sourceFieldNames)
    # tp + top-down reconstruction prediction
    self._predictionStats       = numpy.zeros((self._nMultiStepPrediction,
                                         self._nFields))
    self._nPredictions          = numpy.zeros(self._nMultiStepPrediction)
    # Poor man's prediction
    self._trivialPredictionStats= numpy.zeros((self._nMultiStepPrediction,
                                         self._nFields))
    self._nTrivialPredictions   = numpy.zeros(self._nMultiStepPrediction)


    self.displayMultiStepPrediction = self.options['displayMultiStepPrediction']

    self._reset()

  #########################################################################
  def _reset(self,):
    """
    """
    # Reset all counters and logs to avoid using predictions from previous
    # sequence
    self._nTimeStepsSinceReset    = 0
    if hasattr(self, '_sequenceIdx'):
      self._sequenceIdx          += 1
    else:
      self._sequenceIdx           =-1
    self._inputLog                = []
    self._predictionLog           = []

    if self.displayMultiStepPrediction:
      if hasattr(self, '_sequenceInputLog'):
        sequenceLength  = len(self._sequenceInputLog)
        # The sequencelength has to be greater than self._burnIn otherwise there
        # are no predictions to be plotted
        if sequenceLength > self._burnIn:
          # Converting logs into numpy arrays for easier slicing operations
          # inputArray has the dimensions (sequenceLength, numFields)
          inputArray      = numpy.array(self._sequenceInputLog)
          # predictionArray has the dimensions
          # (sequenceLength, nMultiStepPrediction, numFields)
          predictionArray = numpy.array(self._sequencePredictionLog)

          # We start predicting after <burnIn> time steps
          startTime = self._burnIn
          # Sequence length limits the length of multistep prediction
          endTime   = min(sequenceLength,
                            startTime + self._nMultiStepPrediction)

          # We generate a seperate plot for each field
          for fieldIdx, fieldName in enumerate(self.sourceFieldNames):
            #import pylab
            pylab.figure()
            pylab.plot(range(endTime), inputArray[:endTime,fieldIdx], 'g.',
                       label='input')
            pylab.plot(range(startTime, endTime),
                       predictionArray[startTime-1,:endTime - startTime,fieldIdx],
                       'b',label='prediction')
            pylab.title('Multi-step prediction for %s from timestep %d' %
                                                      (fieldName, startTime))
            pylab.xlabel('Time Steps')
            pylab.ylabel('Field Units')
            pylab.legend()
            baseFileName, _ = \
                      os.path.splitext(self.options['multiStepDisplayFilename'])
            saveFileName = baseFileName + \
                           "_field%s_seq%d.pdf" % (fieldName, self._sequenceIdx)
            pylab.savefig(saveFileName)

      self._sequenceInputLog      = []
      self._sequencePredictionLog = []


  #########################################################################
  def compute(self, sampleIdx, data):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           Logged data for this sample


    """

    # Get the data we need
    resetOutput = data['reset']
    sensorBUInput = data['sourceScalars']
    multiStepPrediction = data['multiStepPrediction']

    nSteps = len(multiStepPrediction)
    assert self._nMultiStepPrediction == nSteps

    # Reset?
    if resetOutput:
      self._reset()

    # Update the counter for time steps since begining of the sequence
    self._nTimeStepsSinceReset += 1

    # Update the log with the current BU input and predictions
    # Compute the sensor top-down out for each future prediction
    currPrediction = []
    for i in range(nSteps):
      spTopDownOut = multiStepPrediction[i]
      sensorTopDownOut = self.netInfo['encoder'].topDownCompute(spTopDownOut)
      currPrediction.append(sensorTopDownOut)

    if self.displayMultiStepPrediction:
      self._sequenceInputLog.append(deepcopy(sensorBUInput))
      self._sequencePredictionLog.append(deepcopy(currPrediction))

    # Update prediction stats only after <burnIn> time steps since reset
    if self._nTimeStepsSinceReset < self._burnIn:
      return

    # Update prediction accuracy for the current BU input using past predictions
    nPredictionsLogged = len(self._predictionLog)
    for pastTimeStep in range(1, nPredictionsLogged+1):
      predictionFromPast = self._predictionLog[-pastTimeStep][pastTimeStep-1]
      # ------------------------------------------------------------------
      # Compute the errors at the sensor input level. This is the difference
      #  between the scalar values read directly from the data source and the
      #  scalar values computed from the top-down output from the encoders
      # expressed in the absolute units of the input data
      absCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                              predictionFromPast,
                                                              fractional=False)
      self._predictionStats[pastTimeStep-1] += absCloseness
      self._nPredictions[pastTimeStep-1]    += 1

    # Update prediction accuracy for the current BU input using past BU inputs
    nInputsLogged = len(self._inputLog)
    for pastTimeStep in range(1, nInputsLogged+1):
      inputFromPast = self._inputLog[-pastTimeStep]
      # ------------------------------------------------------------------
      # Compute the errors at the sensor input level. This is the difference
      #  between the scalar values read directly from the data source and the
      #  scalar values computed from the top-down output from the encoders
      # expressed in the absolute units of the input data
      absCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                    inputFromPast,
                                                    fractional=False)
      self._trivialPredictionStats[pastTimeStep-1] += absCloseness
      self._nTrivialPredictions[pastTimeStep-1]    += 1


    self._inputLog.append(sensorBUInput)
    self._inputLog = self._inputLog[-self._nMultiStepPrediction:]
    self._predictionLog.append(currPrediction)
    self._predictionLog = self._predictionLog[-self._nMultiStepPrediction:]


    # Verbose printing
    if self.options['verbosity'] >= 2:
      pass

  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    # Send in a reset to clear any pending data
    self._reset()

    for i in range(self._nMultiStepPrediction):
      if self._nPredictions[i]:
        fieldScores = self._predictionStats[i]/self._nPredictions[i]
      else:
        fieldScores = [None] * len(self._predictionStats[i])
      if self._nTrivialPredictions[i]:
        trivialFieldScores = \
                    self._trivialPredictionStats[i]/self._nTrivialPredictions[i]
      else:
        trivialFieldScores = [None] * len(self._trivialPredictionStats[i])

      for fieldName, score, trivialScore in zip(self.sourceFieldNames,
                                              fieldScores, trivialFieldScores):
        stats['multiStep_%s_%02d' % (fieldName, i+1)] = score
        stats['multiStep_%s_%02d_PM' % (fieldName, i+1)] = trivialScore
