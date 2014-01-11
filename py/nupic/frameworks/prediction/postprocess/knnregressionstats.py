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

from nupic.algorithms.KNNClassifier import KNNClassifier

gTrainedKNNClassifierState = None
#############################################################################
class KNNRegressionStats(object):
  """ This class calculates regression capability using knn classifier
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

    computeMode, regressionField = \
      KNNRegressionStats._getComputeModeAndRegressionField(options['knnRegression'])

    if computeMode == 'None':
      return False

    sourceFieldNames = netInfo['encoder'].getScalarNames()
    if regressionField is not None and regressionField not in sourceFieldNames:
      print "\nWARNING: The selected regression field %s is not present in the "\
            "available field names - %s" % (regressionField, sourceFieldNames)
      print "No knn regression will be performed."
      return False
    return  ('sensorBUOut' in logNames) and \
            ('sourceScalars' in logNames) and \
            (computeMode is not None or regressionField is not None)

  #########################################################################
  @staticmethod
  def _getComputeModeAndRegressionField(option):
    return option.split(',')

  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for calculating the knn regression stats on
    a given data set.

    Parameters:
    ------------------------------------------------------------
    netInfo:      trained network info
    options:      object containing all "command-line" options for post-processsing
    baseline:     dictionary of information from the corresponding baseline test set
                    if any, or None
    logNames:     Names of the available log files
    """


    # -----------------------------------------------------------------------
    # Get info about the network
    self.netInfo = netInfo
    self.options = options
    self.verbosity = self.options['verbosity']
    #self.verbosity = 3    # Uncomment for verbosity only in this module

    self.computeMode, self.regressionField = \
                self._getComputeModeAndRegressionField(options['knnRegression'])

    # If testing, make sure we have a trained classifier state
    if self.computeMode == 'test':
      self.training = False
      global gTrainedKNNClassifierState
      if gTrainedKNNClassifierState is None:
        print "\nWARNING: You are using the option 'knnRegression=test,FIELD', "\
              " but haven't trained the classifier using "\
              " 'knnRegression=train,FIELD', "\
              " No regression will be performed."
      else:
        if gTrainedKNNClassifierState['regressionField'] != self.regressionField:
          print "\nWARNING: You are using different regression fields for testing,"\
                " and training. No regression will be performed."
      self.trainedState = gTrainedKNNClassifierState
    else:
      self.training = True
      self.trainedState = dict()
      self.trainedState['classifier'] = KNNClassifier(k=1, distanceNorm=1.0,
                                  distThreshold=0.0, useSparseMemory = True)
      self.trainedState['regressionField'] = self.regressionField
      self.trainedState['categoryMap'] = []


    # -----------------------------------------------------------------------
    # Init variables
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()
    self.numFields = len(self.sourceFieldNames)
    self.regressionFieldIdx = self.sourceFieldNames.index(self.regressionField)

    # Accumuated closeness scores
    self.numSamples = 0
    self.sourceClosenessSum = 0.0
    self.absSourceClosenessSum = 0.0
    self.rmseSourceClosenessSum = 0.0


  #########################################################################
  def compute(self, sampleIdx, data):
    """ Feed in the next data sample and accumulate stats on it.

    Parameters:
    ------------------------------------------------------------
    sampleIdx:      The index assigned to this sample
    data:           Logged data for this sample

    """

    # Return quietly if no training available
    if self.trainedState is None:
      return

    # Get the data we need
    sensorBUOutput = data['sensorBUOut'][1]
    sensorBUInput = data['sourceScalars']

    classifier = self.trainedState['classifier']
    categoryMap = self.trainedState['categoryMap']

    # =====================================================================
    # Training
    if self.training:
      # This is a hacky trick to use old KNNClassifier code for regression
      classifier.learn(sensorBUOutput, len(categoryMap))
      categoryMap.append(sensorBUInput.tostring())

    # =====================================================================
    # Testing
    else:
      (winner, dist, topNCats) =  classifier.getClosest(sensorBUOutput, 0)
      #sensorTDPrediction = numpy.fromstring(categoryMap[winner], numpy.float32)
      encoderTDOutput = classifier.getPattern(winner)
      sensorTDPrediction = self.netInfo['encoder'].topDownCompute(encoderTDOutput)
      sensorScalars = [x.scalar for x in sensorTDPrediction]
      # Compute the closeness between the predicted value and the
      #  actual value in the same iteration.
      sourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                          sensorScalars)
      absSourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                          sensorScalars,
                                                          fractional=False)
      self.numSamples += 1
      self.sourceClosenessSum += sourceCloseness[self.regressionFieldIdx]
      self.absSourceClosenessSum += absSourceCloseness[self.regressionFieldIdx]
      self.rmseSourceClosenessSum += \
                           pow(absSourceCloseness[self.regressionFieldIdx], 2)




  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """
    # Return quietly if no training state available
    if self.trainedState is None:
      return

    # ====================================================================
    # Finish up the trained state
    if self.training:

      global gTrainedKNNClassifierState
      gTrainedKNNClassifierState = self.trainedState


    # ====================================================================
    # Compute overall prediction score and store stats
    else:
      numSamples = max(1, self.numSamples)
      stats['regressionErr_%s_knn'%self.regressionField] = \
                                              self.sourceClosenessSum/numSamples
      stats['regressionErr_%s_abs_knn'%self.regressionField] = \
                                           self.absSourceClosenessSum/numSamples
      stats['regressionErr_%s_rmse_knn'%self.regressionField] = \
                                 pow(self.rmseSourceClosenessSum/numSamples, 0.5)
