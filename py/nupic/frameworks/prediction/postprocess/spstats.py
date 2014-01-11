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

import nupic.research.fdrutilities as fdru

from inputpredictionstats import PredictionLogger

#############################################################################
class SPStats(object):
  """ This class calculates various statistics on the SP
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

    return  ('sensorBUOut' in logNames) and \
            ('spBUOut' in logNames)

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

    # Get info about the data going in and out
    self.netInfo = netInfo
    self.options = options
    self.baseline = baseline
    self.hasTopDown = 'spReconstructedIn' in logNames

    # network info
    self.inputSize = netInfo['encoder'].getWidth()
    self.outputSize = netInfo['outputSize']
    self.coincSizes = netInfo['cm'].rowSums()


    # Init accumulated stats
    self.numSamples = 0
    self.classificationErrs = 0
    self.classificationSamples = 0

    self.underCoveragePctTotal = 0
    self.underCoveragePctMax = 0
    self.overCoveragePctTotal = 0
    self.overCoveragePctMax = 0

    self.numCellsOnTotal = 0
    self.numCellsOnMin = numpy.inf
    self.numCellsOnMax = 0

    self.numInputsOnTotal = 0
    self.numInputsOnMin = numpy.inf
    self.numInputsOnMax = 0

    self.activeCellOverlapAvg = 0
    self.activeCellPctOverlapAvg = 0

    self.inputBitErr = numpy.zeros(self.inputSize)          # reconstruction err
    self.inputBitErrWhenOn = numpy.zeros(self.inputSize)    # reconstruction err when input ON
    self.inputBitErrWhenOff = numpy.zeros(self.inputSize)   # reconstruction err when input OFF

    self.coincActiveCount = numpy.zeros(self.outputSize)
    self.inputBitActiveCount = numpy.zeros(self.inputSize)


    # These are dense matrices used to compute the stability of the first N
    #  samples of input and output from the SP
    self.nStabilitySamples = 1000
    self.inputStabilityVectors = numpy.zeros((self.nStabilitySamples,
                                self.inputSize), dtype='bool')
    self.outputStabilityVectors = numpy.zeros((self.nStabilitySamples,
                                self.outputSize), dtype='bool')



    # Get the field names
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()
    self.numFields = len(self.sourceFieldNames)

    if self.hasTopDown:
      self.sourceClosenessSums    = numpy.zeros(self.numFields)
      self.absSourceClosenessSums = numpy.zeros(self.numFields)
      self.rmseSourceClosenessSums = numpy.zeros(self.numFields)

      if options['logPredictions']:
        self.predictionLogger = PredictionLogger(netInfo, options, label='SP')
      else:
        self.predictionLogger = None

  #########################################################################
  def compute(self, sampleIdx, data):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           Available logged data


    """

    # One more sample
    self.numSamples += 1

    # Get the data we need
    (buInputNZ, buInput) = data['sensorBUOut']
    #print "buInputNZ: " , buInputNZ

    (buOutputNZ, buOutput) = data['spBUOut']
    if self.hasTopDown:
      tdIntOutput = data['spReconstructedIn']
      sensorBUInput = data['sourceScalars']
      sensorTDOutputResults = self.netInfo['encoder'].topDownCompute(tdIntOutput)
      sensorTDOutput = [x.scalar for x in sensorTDOutputResults]
      sensorTDOutputValues = [x.value for x in sensorTDOutputResults]

    # Verbose printing
    if self.options['verbosity'] >= 2:
      print "SP activeOutputs (%d):" % (len(buOutputNZ)),  buOutputNZ
      if tdIntOutput is not None:
        self.netInfo['encoder'].pprint(tdIntOutput, prefix=" spReconstIn:")




    # ---------------------------------------------------------------------
    # Update cell activity (output) stats
    numCellsOn = len(buOutputNZ)
    self.numCellsOnTotal += numCellsOn
    self.numCellsOnMin = min(numCellsOn, self.numCellsOnMin)
    self.numCellsOnMax = max(numCellsOn, self.numCellsOnMax)

    # Keep track of which inputs and  coincidences were active
    self.coincActiveCount[buOutputNZ] += 1
    self.inputBitActiveCount[buInputNZ] += 1
    #print "inputBitActiveCount: ", self.inputBitActiveCount

    # Update input stats
    numInputsOn = len(buInputNZ)
    self.numInputsOnTotal += numInputsOn
    self.numInputsOnMin = min(numInputsOn, self.numInputsOnMin)
    self.numInputsOnMax = max(numInputsOn, self.numInputsOnMax)


    # ------------------------------------------------------------------------
    # What was the average overlap of the active cells?
    overlaps = self.netInfo['cm'].rightVecSumAtNZ(buInput)
    overlapsActive = overlaps[buOutputNZ]
    if len(overlapsActive) > 0:
      self.activeCellOverlapAvg += overlapsActive.mean()

      pctOverlaps = overlapsActive / self.coincSizes[buOutputNZ]
      self.activeCellPctOverlapAvg += pctOverlaps.mean()


    # ------------------------------------------------------------------------
    # Capture for stability measures
    if sampleIdx < self.nStabilitySamples:
      self.inputStabilityVectors[sampleIdx][:] = buInput
      self.outputStabilityVectors[sampleIdx][:] = buOutput



    # ------------------------------------------------------------------------
    # Plot the overlaps?
    if False:
      pylab.ion()
      pylab.figure(3)
      pylab.ioff()
      overlaps.sort()
      pylab.clf()
      pylab.plot(overlaps[::-1])
      threshold = overlapsActive.min() - 0.1
      pylab.plot(threshold*numpy.ones(overlaps.size))
      pylab.draw()
      import pdb; pdb.set_trace()


    # ------------------------------------------------------------------
    # Compute the reconstruction errors at the SP input level. This is the
    #  difference between the input to the SP and the top-down from the SP.
    # If this is a variant test, compare top-down to the baseline's SP input.
    if self.hasTopDown:
      if self.baseline is not None:
        inputCl = self.baseline['classificationStats'].inputCl
        inputCategories = self.baseline['classificationStats'].category
        refBUInput = inputCl.getPattern(idx=None,
                                  cat=inputCategories[sampleIdx])
      else:
        refBUInput = buInput
      # Compute the error per bit. If this is a variant test set,
      bitErrs = numpy.abs(tdIntOutput - refBUInput)
      self.inputBitErr += bitErrs

      # Compute the error for just the input bits that are OFF, and for just the
      #  input bits that are ON.
      inputOff = numpy.where(buInput==0)[0]
      self.inputBitErrWhenOff[inputOff] += bitErrs[inputOff]
      self.inputBitErrWhenOn[buInputNZ] += bitErrs[buInputNZ]

      if self.predictionLogger:
        # TODO Log strings instead of indices
        self.predictionLogger.log(reset=data['reset'],
                                  actualScalarValues=sensorBUInput,
                                  predictedScalarValues=sensorTDOutputValues)

      # ------------------------------------------------------------------
      # Compute the errors at the sensor input level. This is the difference
      #  between the scalar values read directly from the data source and the
      #  scalar values computed from the top-down output from the encoders
      # expressed as a fractional value of the total range
      sourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                                   sensorTDOutput)


      # ------------------------------------------------------------------
      # Compute the errors at the sensor input level. This is the difference
      #  between the scalar values read directly from the data source and the
      #  scalar values computed from the top-down output from the encoders
      # expressed in the absolute units of the input data
      absSourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                 sensorTDOutput, fractional=False)


      self.sourceClosenessSums     += sourceCloseness
      self.absSourceClosenessSums  += absSourceCloseness
      self.rmseSourceClosenessSums += numpy.square(absSourceCloseness)

  #############################################################################
  def _printLearnedCoincidences(self):
    """ Print the learned coincidences of the SP, in order of frequency of
    use.

    Parameters:
    ----------------------------------------------------------
    """

    print "\nLEARNED COINCIDENCES, HIGHEST TO LOWEST FREQUENCY OF USAGE..."
    freqOrder = self.coincActiveCount.argsort()[::-1]
    self.netInfo['encoder'].pprintHeader(prefix=" " * 7)
    for i in freqOrder:
      denseCoinc = self.netInfo['cm'].getRow(i)
      permanences = self.netInfo['sp'].getMasterHistogram(i).reshape(-1)
      self.netInfo['encoder'].pprint(denseCoinc, prefix="%6d:" % (i))

      # Format the permanences as a string
      perms = []
      lastField = None
      for nz in denseCoinc.nonzero()[0]:
        (field, offset) = self.netInfo['encoder'].encodedBitDescription(nz)
        if field != lastField:
          if lastField is not None:
            perms.append('], ')
          perms.append('%s: [' % field)
          lastField = field
        else:
          perms.append(', ')
        perms.append('%.2f' % (permanences[nz]))
      perms.append(']')
      print " perms:", "".join(perms)

      # Print the duty cycle and input description
      print "dcycle: %f" % (self.coincActiveCount[i] / self.numSamples)
      decoded = self.netInfo['encoder'].decode(denseCoinc)
      print "  desc:", self.netInfo['encoder'].decodedToStr(decoded)
      print


  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    # --------------------------------------------------------------------
    # Generic bottom-up stats
    stats['outputActiveCountAvg'] = float(self.numCellsOnTotal) / self.numSamples
    stats['outputActiveCountMin'] = self.numCellsOnMin
    stats['outputActiveCountMax'] = self.numCellsOnMax

    stats['inputActiveCountAvg'] = float(self.numInputsOnTotal) / self.numSamples
    stats['inputActiveCountMin'] = self.numInputsOnMin
    stats['inputActiveCountMax'] = self.numInputsOnMax

    stats['inputDensityPctAvg'] = 100.0 * stats['inputActiveCountAvg'] \
                                      / self.inputSize
    stats['outputDensityPctAvg'] = 100.0 * stats['outputActiveCountAvg'] \
                                      / self.outputSize

    stats['cellDutyCycleAvg'] = self.coincActiveCount.mean() / self.numSamples
    stats['cellDutyCycleMin'] = self.coincActiveCount.min() / self.numSamples
    stats['cellDutyCycleMax'] = self.coincActiveCount.max() / self.numSamples

    stats['activeCellOverlapAvg'] = float(self.activeCellOverlapAvg) \
                                        / self.numSamples
    stats['activeCellOverlapPctAvg'] = \
                    100.0 * float(self.activeCellPctOverlapAvg) / self.numSamples

    stats['unusedCells'] = numpy.where(self.coincActiveCount == 0)[0]
    stats['unusedCellsCount'] = len(stats['unusedCells'])


    stats['inputBitDutyCycles'] = self.inputBitActiveCount / self.numSamples
    stats['inputBitInLearnedCoinc'] = self.netInfo['cm'].colSums()

    stats['inputBitsStuckOff'] = numpy.where(self.inputBitActiveCount==0)[0]
    stats['inputBitsStuckOn'] = numpy.where(self.inputBitActiveCount \
                                              == self.numSamples)[0]

    stats['inputBitsStuckOffAndConnected'] = numpy.where(
                    numpy.logical_and(self.inputBitActiveCount==0,
                                      stats['inputBitInLearnedCoinc'] != 0))[0]


    # --------------------------------------------------------------------
    # Measure input/output stability
    stats['inputOnTimeAvg'] = fdru.averageOnTime(
                            self.inputStabilityVectors[0:self.numSamples])[0]
    stats['outputOnTimeAvg'] = fdru.averageOnTime(
                            self.outputStabilityVectors[0:self.numSamples])[0]


    # --------------------------------------------------------------------
    # These stats are only applicable when we have top-down information
    if self.hasTopDown:
      stats['reconstructErrAvg'] = self.inputBitErr.sum() / self.numSamples \
                                                          / self.inputSize
      stats['inputBitErrAvg'] = self.inputBitErr / self.numSamples
      stats['inputBitErrWhenOnAvg'] = self.inputBitErrWhenOn \
                                  / numpy.maximum(1, self.inputBitActiveCount)
      stats['inputBitErrWhenOffAvg'] = self.inputBitErrWhenOff \
                / numpy.maximum(1, self.numSamples - self.inputBitActiveCount)


      # -----------------------------------------------------------------------
      # Break down the SP input bit reconstruction errors by field
      fieldNames = [name for (name,offset) in \
                                  self.netInfo['encoder'].getDescription()]
      if len(fieldNames) > 0:
        for field in fieldNames:
          (offset, width) = self.netInfo['encoder'].getFieldDescription(field)
          print "offset: %d  width: %d" % (offset, width)

          totalErrs = self.inputBitErr[offset:offset+width].sum()
          if self.baseline is not None:
            totalActivity = self.baseline['inputBitActiveCount']\
                                          [offset:offset+width].sum()
          else:
            totalActivity = self.inputBitActiveCount[offset:offset+width].sum()

          print "field: ", field, "totalErrs: ", totalErrs, "totalActivity: ", totalActivity

          ####################################################################################
#          if False:
#              if totalErrs == 0:
#                  for e in self.inputBitErr[offset:offset+width]:
#                      print "inputBitErr: ", e
#
#              if totalActivity == 0:
#                  if self.baseline is not None:
#                      print "self.baseline: " , self.baseline['inputBitActiveCount'][offset:offset+width]
#                  else:
#                      print "inputBitActiveCount: " , self.inputBitActiveCount[offset:offset+width]

          errAvg = totalErrs / totalActivity
          stats['inputFieldErrAvg_%s' % field] = errAvg

      # -----------------------------------------------------------------------
      # Compute closeness from 0 to 1.0
      fieldScores = self.sourceClosenessSums / max(1.0, self.numSamples)
      if len(fieldScores) >= 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['regressionErr_%s' % (fieldName,)] = score

      # Closeness in absolute units
      # Doesn't make sense to take a mean across all fields
      fieldScores = self.absSourceClosenessSums / max(1.0, self.numSamples)
      if len(fieldScores) >= 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['regressionErr_%s_abs' % (fieldName)] = score

      # Closeness in rmse units
      # Doesn't make sense to take a mean across all fields
      fieldScores = \
            numpy.sqrt(self.rmseSourceClosenessSums / max(1.0, self.numSamples))
      if len(fieldScores) >= 1:
        for fieldName, score in zip(self.sourceFieldNames, fieldScores):
          stats['regressionErr_%s_rmse' % (fieldName)] = score


    # ===========================================================================
    # Print out the learned coincidences?
    if self.options['printLearnedCoincidences']:
      self._printLearnedCoincidences()
