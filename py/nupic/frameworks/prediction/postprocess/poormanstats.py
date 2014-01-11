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




#############################################################################
class PoorMansStats(object):
  """ "Poor-man's" prediction - simply assume the value will stay the same
  on each iteration.

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
            ('sourceScalars' in logNames)



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
    self.numSamples = 0
    self.sensorBUInputPrev = None

    self.sourceClosenessSums = None
    self.absSourceClosenessSums = None
    self.sourceFieldNames = self.netInfo['encoder'].getScalarNames()


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

    # If this is the start of a new sequence, don't bother checking
    #   prediction accuracy
    if not resetOutput and self.sensorBUInputPrev is not None:

      # One more sample
      self.numSamples += 1

      # ------------------------------------------------------------------
      # Compute the errors at the sensor input level. This is the difference
      #  between the scalar values read directly from the data source and the
      #  scalar values computed from the top-down output from the encoders
      # expressed as a fractional value of the total range
      sourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                  self.sensorBUInputPrev)

      if self.sourceClosenessSums is None:
        self.sourceClosenessSums = numpy.array(sourceCloseness)
      else:
        self.sourceClosenessSums += sourceCloseness


      # ------------------------------------------------------------------
      # Compute the errors at the sensor input level. This is the difference
      #  between the scalar values read directly from the data source and the
      #  scalar values computed from the top-down output from the encoders
      # expressed in the absolute units of the input data
      absSourceCloseness = self.netInfo['encoder'].closenessScores(sensorBUInput,
                                  self.sensorBUInputPrev, fractional=False)

      if self.absSourceClosenessSums is None:
        self.absSourceClosenessSums = numpy.array(absSourceCloseness)
      else:
        self.absSourceClosenessSums += absSourceCloseness


    # Update the previous values
    self.sensorBUInputPrev = sensorBUInput


  #########################################################################
  def getStats(self, stats):
    """ Insert the stats we computed into the passed in 'stats' dict.

    Parameters:
    ------------------------------------------------------------
    stats:      dict in which to place the stats we computed

    """

    if self.sourceClosenessSums is None:
      self.sourceClosenessSums = numpy.zeros(len(self.sourceFieldNames))

    fieldScores = self.sourceClosenessSums / max(1.0, self.numSamples)
    for fieldName, score in zip(self.sourceFieldNames, fieldScores):
      stats['inputPredScore_%s_PM' % fieldName] = score
    stats['inputPredScore_PM'] = fieldScores.mean()

    # Closeness in absolute units
    # Doesn't make sense to take a mean across all fields
    if self.absSourceClosenessSums is None:
      self.absSourceClosenessSums = numpy.zeros(len(self.sourceFieldNames))

    fieldScores = self.absSourceClosenessSums / max(1.0, self.numSamples)
    for fieldName, score in zip(self.sourceFieldNames, fieldScores):
      stats['inputPredScore_%s_abs_PM' % fieldName] = score
