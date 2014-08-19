#! /usr/bin/env python
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

import random

import numpy


class TrivialPredictor(object):
  def __init__(self, numberOfCols, verbosity,
               methods="zeroth last lots"):

    """
    Create a predictor that uses all of the given methods.
    Supported methods are
    (n = half the number of average input columns on)
    "random" - predict n random columns
    "zeroth" - predict the n most common columns learned from the input
    "last"   - predict the last input
    "all"    - predict all columns
    "lots"   - predict the 2n most common columns learned from the input

    Both "random" and "all" should give a prediction score of zero"
    """

    self.methods = [x.strip() for x in methods.split()]
    self.activeState = dict()
    self.predictedState = dict()
    self.confidence = dict()

    for m in self.methods:
      if m not in ["random", "zeroth", "last", "all", "lots"]:
        raise RuntimeError("Unknown trivial predictor method %s" % m)

      self.activeState[m] = dict()
      self.activeState[m]['t'] = numpy.zeros((numberOfCols, 1), dtype='int32')
      self.activeState[m]['t-1'] = numpy.zeros((numberOfCols, 1), dtype='int32')

      self.predictedState[m] = dict()
      self.predictedState[m]['t'] = numpy.zeros((numberOfCols, 1), dtype='int32')
      self.predictedState[m]['t-1'] = numpy.zeros((numberOfCols, 1), dtype='int32')

      self.confidence[m] = dict()
      self.confidence[m]['t'] = numpy.zeros((numberOfCols, 1), dtype='float32')
      self.confidence[m]['t-1'] = numpy.zeros((numberOfCols, 1), dtype='float32')

    self.numberOfCols = numberOfCols
    self.verbosity = verbosity

    self._internalStats = dict()
    for m in self.methods:
      self._internalStats[m] = dict()

    self.resetStats() # initialize all stats structures


    #---------------------------------------------------------------------------------
    # "Learned" features: keep track of column statistics

    # Number of times each column has been active during learning
    self.columnCount = numpy.zeros(numberOfCols, dtype="int32")

    # Running average of input density
    self.averageDensity = 0.05


  #############################################################################
  def learn(self, activeColumns):
    """
    Do one iteration of the temporal pooler learning.
    Returns TP output
    """

    # Running average of bottom up density
    density = len(activeColumns) / float(self.numberOfCols)
    self.averageDensity = 0.95*self.averageDensity + 0.05*density

    # Running count of how often each column has been active

    self.columnCount[activeColumns] += 1

    # Do "inference"
    self.infer(activeColumns)



  ################################################################################
  def resetStats(self):
    """ Reset the learning and inference stats. This will usually be called by
    user code at the start of each inference run (for a particular data set).
    """

    self.reset()

    # Additionally, reset all of the "total" values
    for m in self.methods:
      self._internalStats[m]['nInfersSinceReset'] = 0
      self._internalStats[m]['nPredictions'] = 0

      #To be removed
      self._internalStats[m]['predictionScoreTotal'] = 0.0
      #New prediction score
      self._internalStats[m]['predictionScoreTotal2']   = 0.0
      self._internalStats[m]['falseNegativeScoreTotal'] = 0.0
      self._internalStats[m]['falsePositiveScoreTotal'] = 0.0

      self._internalStats[m]['pctExtraTotal'] = 0.0
      self._internalStats[m]['pctMissingTotal'] = 0.0

      self._internalStats[m]['totalMissing'] = 0.0
      self._internalStats[m]['totalExtra'] = 0.0




  ################################################################################
  def reset(self):
    """ Reset the state of all cells.
    This is normally used between sequences while training. All internal states
    are reset to 0.
    """

    for m in self.methods:

      self.activeState[m]['t-1'].fill(0)
      self.activeState[m]['t'].fill(0)
      self.predictedState[m]['t-1'].fill(0)
      self.predictedState[m]['t'].fill(0)
      self.confidence[m]['t-1'].fill(0)
      self.confidence[m]['t'].fill(0)

      self._internalStats[m]['nInfersSinceReset'] = 0

      #To be removed
      self._internalStats[m]['curPredictionScore'] = 0.0
      #New prediction score
      self._internalStats[m]['curPredictionScore2']   = 0.0
      self._internalStats[m]['curFalseNegativeScore'] = 0.0
      self._internalStats[m]['curFalsePositiveScore'] = 0.0

      self._internalStats[m]['curMissing'] = 0.0
      self._internalStats[m]['curExtra'] = 0.0



  def infer(self, activeColumns):
    numColsToPredict = int(0.5+self.averageDensity * self.numberOfCols)

    for method in self.methods:

      # Copy t-1 into t
      self.activeState[method]['t-1'][:,:] = self.activeState[method]['t'][:,:]
      self.predictedState[method]['t-1'][:,:] = self.predictedState[method]['t'][:,:]
      self.confidence[method]['t-1'][:,:] = self.confidence[method]['t'][:,:]

      self.activeState[method]['t'].fill(0)
      self.predictedState[method]['t'].fill(0)
      self.confidence[method]['t'].fill(0.0)

      self.activeState[method]['t'][activeColumns] = 1

      if method == "random":
        # Randomly predict N columns
        predictedCols = numpy.array(random.sample(xrange(self.numberOfCols),
                      numColsToPredict), dtype=numpy.uint32)

      elif method == "zeroth":
        # Always predict the top N most frequent columns
        predictedCols = self.columnCount.argsort()[-numColsToPredict:]

      elif method == "last":
        # Always predict the last input
        predictedCols = self.activeState[method]['t'].nonzero()[0]

      elif method == "all":
        # Always predict all columns
        predictedCols = range(self.numberOfCols)

      elif method == "lots":
        # Always predict 2 * the top N most frequent columns
        numColsToPredict = min(2*numColsToPredict, self.numberOfCols)
        predictedCols = self.columnCount.argsort()[-numColsToPredict:]

      else:
        print "***No such prediction method:", method
        assert False

      self.predictedState[method]['t'][predictedCols] = 1
      self.confidence[method]['t'][predictedCols] = 1.0
      if self.verbosity > 1:
        print "Random prediction:", method,
        print "  numColsToPredict:",numColsToPredict
        print predictedCols
