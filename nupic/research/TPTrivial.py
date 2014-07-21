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

import cPickle as pickle
import random

import numpy
from numpy import *
import nupic.math
from nupic.research.TP import TP

random.seed(42)
numpy.random.seed(42)

# Default verbosity while running unit tests
VERBOSITY = 0

# The numpy equivalent to the floating point type used by NTA
dtype = nupic.math.GetNTAReal()

class TPTrivial(TP):
  """Class implementing a trivial temporal pooler algorithm.  This temporal
  pooler will measure the following input statistics: how often each column
  is active, and average input density.

  It will various trivial predictions depending on the predictionMethod
  parameter:

  random    : output a random set of columns, maintaining average density
  zeroth    : output the most frequent columns, maintaining average density
  all       : always predict all the columns
  last      : always predict the last input
  lots      : output the most frequent columns, maintaining 5*average density

  output random or zero'th order
  predictions.

  The main purpose is to provide baseline data for comparison to other temporal
  pooler implementations.
  """

  ##############################################################################
  # We use the same keyword arguments as TP()
  def __init__(self,
               numberOfCols =500,
               burnIn =2,             # Used for evaluating the prediction score
               collectStats =False,   # If true, collect training and inference stats
               seed =42,
               verbosity =VERBOSITY,
               predictionMethod = 'random',  # "random" or "zeroth"
               **kwargs
               ):

    # Init the base class
    TP.__init__(self,
               numberOfCols = numberOfCols,
               cellsPerColumn = 1,
               burnIn = burnIn,
               collectStats = collectStats,
               seed = seed,
               verbosity = verbosity)

    self.predictionMethod = predictionMethod

    #---------------------------------------------------------------------------------
    # Create basic data structures for keeping track of column statistics

    # Number of times each column has been active during learning
    self.columnCount = numpy.zeros(numberOfCols, dtype="int32")

    # Running average of input density
    self.averageDensity = 0.05



  #############################################################################
  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """

    self.__dict__.update(state)
    self._random = pickle.loads(self._random)  # Must be done manually
    self._initEphemerals()

  ###########################################################################
  def __getattr__(self, name):
    """
    Patch __getattr__ so that we can catch the first access to 'cells' and load.

    This function is only called when we try to access an attribute that doesn't
    exist.  We purposely make sure that "self.cells" doesn't exist after
    unpickling so that we'll hit this, then we can load it on the first access.

    If this is called at any other time, it will raise an AttributeError.
    That's because:
    - If 'name' is "cells", after the first call, self._realCells won't exist
      so we'll get an implicit AttributeError.
    - If 'name' isn't "cells", I'd expect our super wouldn't have __getattr__,
      so we'll raise our own Attribute error.  If the super did get __getattr__,
      we'll just return what it gives us.
    """

    try:
      return super(TP, self).__getattr__(name)
    except AttributeError:
      raise AttributeError("'TP' object has no attribute '%s'" % name)

  #############################################################################
  def infer(self, bottomUpInput):
    """
    Do one iteration of the temporal pooler inference.

    Parameters:
    --------------------------------------------
    bottomUpInput:        Current bottom-up input, dense
    retval:               ?
    """
    self.iterationIdx = self.iterationIdx + 1
    numColsToPredict = int(0.5+self.averageDensity * self.numberOfCols)
    activeColumns = bottomUpInput.nonzero()[0]

    # Copy t-1 into t
    self.infActiveState['t-1'][:,:] = self.infActiveState['t'][:,:]
    self.infPredictedState['t-1'][:,:] = self.infPredictedState['t'][:,:]
    self.cellConfidence['t-1'][:,:] = self.cellConfidence['t'][:,:]

    self.infActiveState['t'].fill(0)
    self.infPredictedState['t'].fill(0)
    self.cellConfidence['t'].fill(0.0)

    self.infActiveState['t'][activeColumns] = 1

    if self.predictionMethod == "random":
      # Randomly predict N columns
      predictedCols = numpy.array(random.sample(xrange(self.numberOfCols),
                    numColsToPredict), dtype=numpy.uint32)

    elif self.predictionMethod == "zeroth":
      # Always predict the top N most frequent columns
      predictedCols = self.columnCount.argsort()[-numColsToPredict:]

    elif self.predictionMethod == "last":
      # Always predict the last input
      predictedCols = self.infActiveState['t'].nonzero()[0]

    elif self.predictionMethod == "all":
      # Always predict all columns
      predictedCols = range(self.numberOfCols)

    elif self.predictionMethod == "lots":
      # Always predict 2 * the top N most frequent columns
      numColsToPredict = min(2*numColsToPredict, self.numberOfCols)
      predictedCols = self.columnCount.argsort()[-numColsToPredict:]

    else:
      print "***No such prediction method:", self.predictionMethod
      assert False

    self.infPredictedState['t'][predictedCols] = 1
    self.cellConfidence['t'][predictedCols] = 1.0
    if self.verbosity > 1:
      print "Random prediction:", self.predictionMethod,
      print "  numColsToPredict:",numColsToPredict
      print predictedCols

    # Update the prediction score stats. We need to retrieve the predicted state
    # and confidence information for _updateStatsInferEnd
    if self.collectStats:
      self._updateStatsInferEnd(self._internalStats,
                                activeColumns,
                                self.infPredictedState['t-1'],
                                self.cellConfidence['t-1'].sum(axis=1))

    # Return the output
    return self.computeOutput()


  #############################################################################
  def learn(self, bottomUpInput):
    """
    Do one iteration of the temporal pooler learning.

    Parameters:
    --------------------------------------------
    bottomUpInput:        Current bottom-up input, dense
    retval:               ?
    """

    # Do not increment iterationidx because it is incremented in infer()
    # self.iterationIdx = self.iterationIdx + 1

    activeColumns = bottomUpInput.nonzero()[0]

    # Running average of bottom up density
    density = len(activeColumns) / float(self.numberOfCols)
    self.averageDensity = 0.95*self.averageDensity + 0.05*density

    # Running count of how often each column has been active
    self.columnCount[activeColumns] += 1

    # Do "inference"
    y = self.infer(bottomUpInput)
    return y


  ################################################################################
  def reset(self):
    """ Reset the state of all cells.
    This is normally used between sequences while training. All internal states
    are reset to 0.
    """
    TP.reset(self)


  ################################################################################
  def trimSegments(self):
    """This method does nothing in this implementation."""

    return (0,0)

  ################################################################################
  # The following print functions for debugging.
  ################################################################################

  ################################################################################
  def printSegment(self, s):

    # TODO: need to add C++ accessors to get segment details
    assert False


  def printSegmentUpdates(self):
    # TODO: need to add C++ accessors to implement this method
    assert False


  ################################################################################
  def printCell(self, c, i):

    print "Column", c, "Cell", i, "(%d)"%(gidx),":", nSegs, "segment(s)"
    print self.cellConfidence[c]

  ################################################################################
  def printCells(self):

    print "=== ALL COLUMNS ==="

    for c in xrange(self.numberOfCols):
        self.printCell(c,0)

  ################################################################################
  def getColCellIdx(self, idx):
    """Get column and cell within column from a global cell index.
    The global index is idx = colIdx * nCellsPerCol() + cellIdxInCol
    This method returns (colIdx, cellIdxInCol)
    """
    c = idx//self.cellsPerColumn
    i = idx - c*self.cellsPerColumn
    return c,i

  ################################################################################
  def getSegmentOnCell(self, c, i, segIdx):
    """Return segment number segIdx on cell (c,i).
    Returns the segment as following list:
      [  [segIdx, sequenceSegmentFlag, frequency],
         [col1, idx1, perm1],
         [col2, idx2, perm2], ...
      ]

    """
    segList = self.cells3.getNonEmptySegList(c,i)
    seg = self.cells3.getSegment(c, i, segList[segIdx])
    numSyn = seg.size()
    assert numSyn != 0

    # Accumulate segment information
    result = []
    result.append([int(segIdx), bool(seg.isSequenceSegment()), seg.getFrequency()])

    for s in xrange(numSyn):
      sc, si = self.getColCellIdx(seg.getSrcCellIdx(s))
      result.append([int(sc), int(si), seg.getPermanence(s)])

    return result

  #############################################################################
  def getNumSegments(self):
    """ Return the total number of segments. """
    return 0

  #############################################################################
  def getNumSynapses(self):
    """ Return the total number of synapses. """
    return 0

  #############################################################################
  def getNumSegmentsInCell(self, c, i):
    """ Return the total number of segments in cell (c,i)"""
    return 0

  ################################################################################
  def getSegmentInfo(self, collectActiveData = False):
    """Returns information about the distribution of segments, synapses and
    permanence values in the current TP. If requested, also returns information
    regarding the number of currently active segments and synapses.

    The method returns the following tuple:

    (
      nSegments,        # total number of segments
      nSynapses,        # total number of synapses
      nActiveSegs,      # total no. of active segments
      nActiveSynapses,  # total no. of active synapses
      distSegSizes,     # a dict where d[n] = number of segments with n synapses
      distNSegsPerCell, # a dict where d[n] = number of cells with n segments
      distPermValues,   # a dict where d[p] = number of synapses with perm = p/10
    )

    nActiveSegs and nActiveSynapses are 0 if collectActiveData is False
    """


    return (0, 0, 0, 0, {}, {}, {})


  ################################################################################
  # The following methods are implemented in the base class but should never
  # be called in this implementation.
  ################################################################################


  #############################################################################
  def getActiveSegment(self, c,i, timeStep):
    """ For a given cell, return the segment with the strongest _connected_
    activation, i.e. sum up the activations of the connected synapses of the
    segments only. That is, a segment is active only if it has enough connected
    synapses.
    """
    assert False

  #############################################################################
  def getBestMatchingCell(self, c, timeStep, learnState = False):
    """Find weakly activated cell in column. Returns index and segment of most
    activated segment above minThreshold.
    """
    assert False


  #############################################################################
  def getLeastAllocatedCell(self, c):
    """For the given column, return the cell with the fewest number of
    segments."""
    assert False

  #############################################################################
  def isSegmentActive(self, seg, timeStep):
    """    """
    # Should never be called in this subclass
    assert False

  #############################################################################
  def getSegmentActivityLevel(self, seg, timeStep, connectedSynapsesOnly =False,
                              learnState = False):
    """   """
    # Should never be called in this subclass
    assert False


  #############################################################################
  def isSequenceSegment(self, s):
    """   """
    # Should never be called in this subclass
    assert False


  #############################################################################
  def getBestMatchingSegment(self, c, i, timeStep, learnState = False):
    """     """
    # Should never be called in this subclass
    assert False


  ##############################################################################
  def getSegmentActiveSynapses(self, c,i,s, timeStep, newSynapses =False):
    """  """
    # Should never be called in this subclass
    assert False


  ################################################################################
  def updateSynapse(self, segment, synapse, delta):
    """ """
    # Should never be called in this subclass
    assert False

  ################################################################################
  def adaptSegments(self, update, positiveReinforcement):
    """    """
    # Should never be called in this subclass
    assert False


################################################################################
################################################################################
