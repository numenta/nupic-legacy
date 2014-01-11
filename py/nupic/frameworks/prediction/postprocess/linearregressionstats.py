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


gTrainedLinearClassifierState = None
#############################################################################
class LinearRegressionStats(object):
  """ This class calculates regression capability using linear model
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
     LinearRegressionStats._getComputeModeAndRegressionField(options['linearRegression'])

    if computeMode == 'None':
      return False


    sourceFieldNames = netInfo['encoder'].getScalarNames()
    if regressionField is not None and regressionField not in sourceFieldNames:
      print "\nWARNING: The selected regression field %s is not present in the "\
            "available field names - %s" % (regressionField, sourceFieldNames)
      print "No linear regression will be performed."
      return False

    return  ('sourceScalars' in logNames) and \
            (computeMode is not None or regressionField is not None)

  #########################################################################
  @staticmethod
  def _getComputeModeAndRegressionField(option):
    return option.split(',')

  #########################################################################
  def __init__(self, netInfo, options, baseline, logNames):
    """ Instantiate data structures for calculating the linear regression stats on
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
                self._getComputeModeAndRegressionField(options['linearRegression'])

    # If testing, make sure we have a trained classifier state
    if self.computeMode == 'test':
      self.training = False
      global gTrainedLinearClassifierState
      if gTrainedLinearClassifierState is None:
        print "\nWARNING: You are using the option 'linearRegression=test,FIELD', "\
              " but haven't trained the classifier using "\
              " 'linearRegression=train,FIELD', "\
              " No regression will be performed."
      else:
        if gTrainedLinearClassifierState['regressionField'] != self.regressionField:
          print "\nWARNING: You are using different regression fields for testing,"\
                " and training. No regression will be performed."
      self.trainedState = gTrainedLinearClassifierState
    else:
      self.training = True
      self.trainedState = dict()
      self.trainedState['regressionField'] = self.regressionField
      self.X = []
      self.Y = []


    # -----------------------------------------------------------------------
    # Init variables
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()
    self.numFields = len(self.sourceFieldNames)
    self.regressionFieldIdx = self.sourceFieldNames.index(self.regressionField)

    # Accumuated closeness scores
    self.numSamples = 0
    self.sourceClosenessSum = 0.0
    self.absSourceClosenessSum = 0.0
    self.rmseSouceClosenessSum = 0.0


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
    sensorBUInput = data['sourceScalars']
    sensorBUInputCopy = sensorBUInput.tolist()

    # =====================================================================
    # Training
    if self.training:
      # Store dependent and independent variables
      y = sensorBUInputCopy.pop(self.regressionFieldIdx)
      x = sensorBUInputCopy
      self.Y.append(y)
      self.X.append(x)

    # =====================================================================
    # Testing
    else:
      coefficients = self.trainedState['coefficients']

      sensorBUInputCopy.pop(self.regressionFieldIdx)
      sensorBUInputCopy.insert(0,1.0)
      prediction = numpy.dot(coefficients, sensorBUInputCopy)

      sensorTDPrediction = sensorBUInput.copy()
      sensorTDPrediction[self.regressionFieldIdx] = prediction

      # Compute the closeness between the predicted value and the
      #  actual value in the same iteration.
      sourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                          sensorTDPrediction)
      absSourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                                          sensorTDPrediction,
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

      # Fit to least squares model
      # Prepare datamatrix
      X = numpy.array(self.X)
      # Augment with constant term
      X = numpy.hstack((numpy.ones((X.shape[0],1)), X))

      Y = numpy.array(self.Y)
      linearCoefficients,_,_,_ = numpy.linalg.lstsq(X, Y)

      self.trainedState['coefficients'] = linearCoefficients


      global gTrainedLinearClassifierState
      gTrainedLinearClassifierState = self.trainedState


    # ====================================================================
    # Compute overall prediction score and store stats
    else:
      numSamples = max(1, self.numSamples)
      stats['regressionErr_%s_linear'%self.regressionField] = \
                                              self.sourceClosenessSum/numSamples
      stats['regressionErr_%s_abs_linear'%self.regressionField] = \
                                           self.absSourceClosenessSum/numSamples
      stats['regressionErr_%s_rmse_linear'%self.regressionField] = \
                                pow(self.rmseSourceClosenessSum/numSamples, 0.5)
