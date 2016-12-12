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

import numpy
from numpy import *

import nupic.math
from nupic.research.TP import TP

from nupic.bindings.algorithms import Cells4


# Default verbosity while running unit tests
VERBOSITY = 0

# The numpy equivalent to the floating point type used by NTA
dtype = nupic.math.GetNTAReal()



def _extractCallingMethodArgs():
  """
  Returns args dictionary from the calling method
  """
  import inspect
  import copy

  callingFrame = inspect.stack()[1][0]

  argNames, _, _, frameLocalVarDict = inspect.getargvalues(callingFrame)

  argNames.remove("self")

  args = copy.copy(frameLocalVarDict)


  for varName in frameLocalVarDict:
    if varName not in argNames:
      args.pop(varName)

  return args



class TP10X2(TP):
  """Class implementing the temporal pooler algorithm as described in the
  published Cortical Learning Algorithm documentation.  The implementation here
  attempts to closely match the pseudocode in the documentation. This
  implementation does contain several additional bells and whistles such as
  a column confidence measure.
  """


  # We use the same keyword arguments as TP()
  def __init__(self,
               numberOfCols = 500,
               cellsPerColumn = 10,
               initialPerm = 0.11, # TODO: check perm numbers with Ron
               connectedPerm = 0.50,
               minThreshold = 8,
               newSynapseCount = 15,
               permanenceInc = 0.10,
               permanenceDec = 0.10,
               permanenceMax = 1.0, # never exceed this value
               globalDecay = 0.10,
               activationThreshold = 12, # 3/4 of newSynapseCount TODO make fraction
               doPooling = False, # allows to turn off pooling
               segUpdateValidDuration = 5,
               burnIn = 2,             # Used for evaluating the prediction score
               collectStats = False,    # If true, collect training and inference stats
               seed = 42,
               verbosity = VERBOSITY,
               checkSynapseConsistency = False,

               pamLength = 1,
               maxInfBacktrack = 10,
               maxLrnBacktrack = 5,
               maxAge = 100000,
               maxSeqLength = 32,

               # Fixed size mode params
               maxSegmentsPerCell = -1,
               maxSynapsesPerSegment = -1,

               # Output control
               outputType = 'normal',
               ):

    #---------------------------------------------------------------------------------
    # Save our __init__ args for debugging
    self._initArgsDict = _extractCallingMethodArgs()

    #---------------------------------------------------------------------------------
    # These two variables are for testing

    # If set to True, Cells4 will perform (time consuming) invariance checks
    self.checkSynapseConsistency = checkSynapseConsistency

    # If set to False, Cells4 will *not* be treated as an ephemeral member
    # and full TP10X pickling is possible. This is useful for testing
    # pickle/unpickle without saving Cells4 to an external file
    self.makeCells4Ephemeral = True

    #---------------------------------------------------------------------------------
    # Init the base class
    TP.__init__(self,
               numberOfCols = numberOfCols,
               cellsPerColumn = cellsPerColumn,
               initialPerm = initialPerm,
               connectedPerm = connectedPerm,
               minThreshold = minThreshold,
               newSynapseCount = newSynapseCount,
               permanenceInc = permanenceInc,
               permanenceDec = permanenceDec,
               permanenceMax = permanenceMax, # never exceed this value
               globalDecay = globalDecay,
               activationThreshold = activationThreshold,
               doPooling = doPooling,
               segUpdateValidDuration = segUpdateValidDuration,
               burnIn = burnIn,
               collectStats = collectStats,
               seed = seed,
               verbosity = verbosity,
               pamLength = pamLength,
               maxInfBacktrack = maxInfBacktrack,
               maxLrnBacktrack = maxLrnBacktrack,
               maxAge = maxAge,
               maxSeqLength = maxSeqLength,
               maxSegmentsPerCell = maxSegmentsPerCell,
               maxSynapsesPerSegment = maxSynapsesPerSegment,
               outputType = outputType,
               )


  def __setstate__(self, state):
    """
    Set the state of ourself from a serialized state.
    """
    super(TP10X2, self).__setstate__(state)
    if self.makeCells4Ephemeral:
      self.cells4 = Cells4(self.numberOfCols,
                 self.cellsPerColumn,
                 self.activationThreshold,
                 self.minThreshold,
                 self.newSynapseCount,
                 self.segUpdateValidDuration,
                 self.initialPerm,
                 self.connectedPerm,
                 self.permanenceMax,
                 self.permanenceDec,
                 self.permanenceInc,
                 self.globalDecay,
                 self.doPooling,
                 self.seed,
                 self.allocateStatesInCPP,
                 self.checkSynapseConsistency)

      self.cells4.setVerbosity(self.verbosity)
      self.cells4.setPamLength(self.pamLength)
      self.cells4.setMaxAge(self.maxAge)
      self.cells4.setMaxInfBacktrack(self.maxInfBacktrack)
      self.cells4.setMaxLrnBacktrack(self.maxLrnBacktrack)
      self.cells4.setMaxSeqLength(self.maxSeqLength)
      self.cells4.setMaxSegmentsPerCell(self.maxSegmentsPerCell)
      self.cells4.setMaxSynapsesPerCell(self.maxSynapsesPerSegment)

    # Reset internal C++ pointers to states
    self._setStatePointers()


  def _getEphemeralMembers(self):
    """
    List of our member variables that we don't need to be saved
    """
    e = TP._getEphemeralMembers(self)
    if self.makeCells4Ephemeral:
      e.extend(['cells4'])
    return e


  def _initEphemerals(self):
    """
    Initialize all ephemeral members after being restored to a pickled state.
    """
    TP._initEphemerals(self)
    #---------------------------------------------------------------------------------
    # cells4 specific initialization

    # If True, let C++ allocate memory for activeState, predictedState, and
    # learnState. In this case we can retrieve copies of these states but can't
    # set them directly from Python. If False, Python can allocate them as
    # numpy arrays and we can pass pointers to the C++ using setStatePointers
    self.allocateStatesInCPP = False

    # Set this to true for debugging or accessing learning states
    self.retrieveLearningStates = False

    if self.makeCells4Ephemeral:
      self.cells4 = Cells4(self.numberOfCols,
                 self.cellsPerColumn,
                 self.activationThreshold,
                 self.minThreshold,
                 self.newSynapseCount,
                 self.segUpdateValidDuration,
                 self.initialPerm,
                 self.connectedPerm,
                 self.permanenceMax,
                 self.permanenceDec,
                 self.permanenceInc,
                 self.globalDecay,
                 self.doPooling,
                 self.seed,
                 self.allocateStatesInCPP,
                 self.checkSynapseConsistency)

      self.cells4.setVerbosity(self.verbosity)
      self.cells4.setPamLength(self.pamLength)
      self.cells4.setMaxAge(self.maxAge)
      self.cells4.setMaxInfBacktrack(self.maxInfBacktrack)
      self.cells4.setMaxLrnBacktrack(self.maxLrnBacktrack)
      self.cells4.setMaxSeqLength(self.maxSeqLength)
      self.cells4.setMaxSegmentsPerCell(self.maxSegmentsPerCell)
      self.cells4.setMaxSynapsesPerCell(self.maxSynapsesPerSegment)

      self._setStatePointers()

  def saveToFile(self, filePath):
    """
    Save Cells4 state to this file
    """
    self.cells4.saveToFile(filePath)

  def loadFromFile(self, filePath):
    """
    Load Cells4 state from this file
    """
    self.cells4.loadFromFile(filePath)


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


  def compute(self, bottomUpInput, enableLearn, computeInfOutput=None):
    """ Handle one compute, possibly learning.

    By default, we don't compute the inference output when learning because it
    slows things down, but you can override this by passing in True for
    computeInfOutput
    """
    # The C++ TP takes 32 bit floats as input. uint32 works as well since the
    # code only checks whether elements are non-zero
    assert (bottomUpInput.dtype == numpy.dtype('float32')) or \
           (bottomUpInput.dtype == numpy.dtype('uint32')) or \
           (bottomUpInput.dtype == numpy.dtype('int32'))

    self.iterationIdx = self.iterationIdx + 1

    #if self.iterationIdx >= 1000040:
    #  self.verbosity=4                           # DEBUG
    #  self.cells4.setVerbosity(self.verbosity)   # DEBUG

    # As a speed optimization for now (until we need online learning), skip
    #  computing the inference output while learning
    if computeInfOutput is None:
      if enableLearn:
        computeInfOutput = False
      else:
        computeInfOutput = True

    # ====================================================================
    # Run compute and retrieve selected state and member variables
    self._setStatePointers()
    y = self.cells4.compute(bottomUpInput, computeInfOutput, enableLearn)
    self.currentOutput = y.reshape((self.numberOfCols, self.cellsPerColumn))
    self.avgLearnedSeqLength = self.cells4.getAvgLearnedSeqLength()
    self._copyAllocatedStates()


    # ========================================================================
    # Update the prediction score stats
    # Learning always includes inference
    if self.collectStats:
      activeColumns = bottomUpInput.nonzero()[0]
      if computeInfOutput:
        predictedState = self.infPredictedState['t-1']
      else:
        predictedState = self.lrnPredictedState['t-1']
      self._updateStatsInferEnd(self._internalStats,
                                activeColumns,
                                predictedState,
                                self.colConfidence['t-1'])



    # Finally return the TP output
    output = self.computeOutput()

    # Print diagnostic information based on the current verbosity level
    self.printComputeEnd(output, learn=enableLearn)

    self.resetCalled = False
    return output

  def inferPhase2(self):
    """
    This calls phase 2 of inference (used in multistep prediction).
    """

    self._setStatePointers()
    self.cells4.inferPhase2()
    self._copyAllocatedStates()


  def getLearnActiveStateT(self):
    if self.verbosity > 1 or self.retrieveLearningStates:
      return self.lrnActiveState['t']
    else:
      (activeT, _, _, _) = self.cells4.getLearnStates()
      return activeT.reshape((self.numberOfCols, self.cellsPerColumn))


  def _copyAllocatedStates(self):
    """If state is allocated in CPP, copy over the data into our numpy arrays."""

    # Get learn states if we need to print them out
    if self.verbosity > 1 or self.retrieveLearningStates:
      (activeT, activeT1, predT, predT1) = self.cells4.getLearnStates()
      self.lrnActiveState['t-1'] = activeT1.reshape((self.numberOfCols, self.cellsPerColumn))
      self.lrnActiveState['t'] = activeT.reshape((self.numberOfCols, self.cellsPerColumn))
      self.lrnPredictedState['t-1'] = predT1.reshape((self.numberOfCols, self.cellsPerColumn))
      self.lrnPredictedState['t'] = predT.reshape((self.numberOfCols, self.cellsPerColumn))

    if self.allocateStatesInCPP:
      assert False
      (activeT, activeT1, predT, predT1, colConfidenceT, colConfidenceT1, confidenceT,
       confidenceT1) = self.cells4.getStates()
      self.confidence['t-1'] = confidenceT1.reshape((self.numberOfCols, self.cellsPerColumn))
      self.confidence['t'] = confidenceT.reshape((self.numberOfCols, self.cellsPerColumn))
      self.colConfidence['t'] = colConfidenceT.reshape(self.numberOfCols)
      self.colConfidence['t-1'] = colConfidenceT1.reshape(self.numberOfCols)
      self.infActiveState['t-1'] = activeT1.reshape((self.numberOfCols, self.cellsPerColumn))
      self.infActiveState['t'] = activeT.reshape((self.numberOfCols, self.cellsPerColumn))
      self.infPredictedState['t-1'] = predT1.reshape((self.numberOfCols, self.cellsPerColumn))
      self.infPredictedState['t'] = predT.reshape((self.numberOfCols, self.cellsPerColumn))

  def _setStatePointers(self):
    """If we are having CPP use numpy-allocated buffers, set these buffer
    pointers. This is a relatively fast operation and, for safety, should be
    done before every call to the cells4 compute methods.  This protects us
    in situations where code can cause Python or numpy to create copies."""
    if not self.allocateStatesInCPP:
      self.cells4.setStatePointers(
          self.infActiveState["t"], self.infActiveState["t-1"],
          self.infPredictedState["t"], self.infPredictedState["t-1"],
          self.colConfidence["t"], self.colConfidence["t-1"],
          self.cellConfidence["t"], self.cellConfidence["t-1"])


  def reset(self):
    """ Reset the state of all cells.
    This is normally used between sequences while training. All internal states
    are reset to 0.
    """
    if self.verbosity >= 3:
      print "TP Reset"
    self._setStatePointers()
    self.cells4.reset()
    TP.reset(self)


  def finishLearning(self):
    """Called when learning has been completed. This method just calls
    trimSegments. (finishLearning is here for backward compatibility)
    """
    # Keep weakly formed synapses around because they contain confidence scores
    #  for paths out of learned sequenced and produce a better prediction than
    #  chance.
    self.trimSegments(minPermanence=0.0001)


  def trimSegments(self, minPermanence=None, minNumSyns=None):
    """This method deletes all synapses where permanence value is strictly
    less than self.connectedPerm. It also deletes all segments where the
    number of connected synapses is strictly less than self.activationThreshold.
    Returns the number of segments and synapses removed. This often done
    after formal learning has completed so that subsequence inference runs
    faster.

    Parameters:
    --------------------------------------------------------------
    minPermanence:      Any syn whose permamence is 0 or < minPermanence will
                        be deleted. If None is passed in, then
                        self.connectedPerm is used.
    minNumSyns:         Any segment with less than minNumSyns synapses remaining
                        in it will be deleted. If None is passed in, then
                        self.activationThreshold is used.
    retval:             (numSegsRemoved, numSynsRemoved)
    """

    # Fill in defaults
    if minPermanence is None:
      minPermanence = 0.0
    if minNumSyns is None:
      minNumSyns = 0

    # Print all cells if verbosity says to
    if self.verbosity >= 5:
      print "Cells, all segments:"
      self.printCells(predictedOnly=False)

    return self.cells4.trimSegments(minPermanence=minPermanence, minNumSyns=minNumSyns)

  ################################################################################
  # The following print functions for debugging.
  ################################################################################


  def printSegment(self, s):

    # TODO: need to add C++ accessors to get segment details
    assert False

    prevAct = self.getSegmentActivityLevel(s, 't-1')
    currAct = self.getSegmentActivityLevel(s, 't')

    # Sequence segment or pooling segment
    if s[0][1] == True:
      print "S",
    else:
      print 'P',

    # Frequency count
    print s[0][2],

    if self.isSegmentActive(s, 't'):
      ss = '[' + str(currAct) + ']'
    else:
      ss = str(currAct)
    ss = ss + '/'
    if self.isSegmentActive(s,'t-1'):
      ss = ss + '[' + str(prevAct) + ']'
    else:
      ss = ss + str(prevAct)
    ss = ss + ':'
    print ss,

    for i,synapse in enumerate(s[1:]):

      if synapse[2] >= self.connectedPerm:
        ss = '['
      else:
        ss = ''
      ss = ss + str(synapse[0]) + '/' + str(synapse[1])
      if self.infActiveState['t'][synapse[0],synapse[1]] == 1:
        ss = ss + '/ON'
      ss = ss + '/'
      sf = str(synapse[2])
      ss = ss + sf[:4]
      if synapse[2] >= self.connectedPerm:
        ss = ss + ']'
      if i < len(s)-2:
        ss = ss + ' |'
      print ss,

    if self.verbosity > 3:
      if self.isSegmentActive(s, 't') and \
             prevAct < self.activationThreshold and currAct >= self.activationThreshold:
        print "reached activation",
      if prevAct < self.minThreshold and currAct >= self.minThreshold:
        print "reached min threshold",
      if self.isSegmentActive(s, 't-1') and \
             prevAct >= self.activationThreshold and currAct < self.activationThreshold:
        print "dropped below activation",
      if prevAct >= self.minThreshold and currAct < self.minThreshold:
        print "dropped below min",
      if self.isSegmentActive(s, 't') and self.isSegmentActive(s, 't-1') and \
             prevAct >= self.activationThreshold and currAct >= self.activationThreshold:
        print "maintained activation",

  def printSegmentUpdates(self):
    # TODO: need to add C++ accessors to implement this method
    assert False
    print "=== SEGMENT UPDATES ===, Num = ",len(self.segmentUpdates)
    for key, updateList in self.segmentUpdates.iteritems():
      c,i = key[0],key[1]
      print c,i,updateList


  def slowIsSegmentActive(self, seg, timeStep):
    """
    A segment is active if it has >= activationThreshold connected
    synapses that are active due to infActiveState.

    """

    numSyn = seg.size()
    numActiveSyns = 0
    for synIdx in xrange(numSyn):
      if seg.getPermanence(synIdx) < self.connectedPerm:
        continue
      sc, si = self.getColCellIdx(seg.getSrcCellIdx(synIdx))
      if self.infActiveState[timeStep][sc, si]:
        numActiveSyns += 1
        if numActiveSyns >= self.activationThreshold:
          return True

    return numActiveSyns >= self.activationThreshold


  def printCell(self, c, i, onlyActiveSegments=False):

    nSegs = self.cells4.nSegmentsOnCell(c,i)
    if nSegs > 0:
      segList = self.cells4.getNonEmptySegList(c,i)
      gidx = c * self.cellsPerColumn + i
      print "Column", c, "Cell", i, "(%d)"%(gidx),":", nSegs, "segment(s)"
      for k,segIdx in enumerate(segList):
        seg = self.cells4.getSegment(c, i, segIdx)
        isActive = self.slowIsSegmentActive(seg, 't')
        if onlyActiveSegments and not isActive:
          continue
        isActiveStr = "*" if isActive else " "
        print "  %sSeg #%-3d" % (isActiveStr, segIdx),
        print seg.size(),
        print seg.isSequenceSegment(), "%9.7f" % (seg.dutyCycle(
              self.cells4.getNLrnIterations(), False, True)),

        # numPositive/totalActivations
        print "(%4d/%-4d)" % (seg.getPositiveActivations(),
                           seg.getTotalActivations()),
        # Age
        print "%4d" % (self.cells4.getNLrnIterations()
                       - seg.getLastActiveIteration()),

        numSyn = seg.size()
        for s in xrange(numSyn):
          sc, si = self.getColCellIdx(seg.getSrcCellIdx(s))
          print "[%d,%d]%4.2f"%(sc, si, seg.getPermanence(s)),
        print


  def getAvgLearnedSeqLength(self):
    """ Return our moving average of learned sequence length.
    """
    return self.cells4.getAvgLearnedSeqLength()


  def getColCellIdx(self, idx):
    """Get column and cell within column from a global cell index.
    The global index is idx = colIdx * nCellsPerCol() + cellIdxInCol
    This method returns (colIdx, cellIdxInCol)
    """
    c = idx//self.cellsPerColumn
    i = idx - c*self.cellsPerColumn
    return c,i


  def getSegmentOnCell(self, c, i, segIdx):
    """Return segment number segIdx on cell (c,i).
    Returns the segment as following list:
      [  [segIdx, sequenceSegmentFlag, positive activations,
          total activations, last active iteration],
         [col1, idx1, perm1],
         [col2, idx2, perm2], ...
      ]

    """
    segList = self.cells4.getNonEmptySegList(c,i)
    seg = self.cells4.getSegment(c, i, segList[segIdx])
    numSyn = seg.size()
    assert numSyn != 0

    # Accumulate segment information
    result = []
    result.append([int(segIdx), bool(seg.isSequenceSegment()),
                   seg.getPositiveActivations(),
                   seg.getTotalActivations(), seg.getLastActiveIteration(),
                   seg.getLastPosDutyCycle(),
                   seg.getLastPosDutyCycleIteration()])

    for s in xrange(numSyn):
      sc, si = self.getColCellIdx(seg.getSrcCellIdx(s))
      result.append([int(sc), int(si), seg.getPermanence(s)])

    return result


  def getNumSegments(self):
    """ Return the total number of segments. """
    return self.cells4.nSegments()


  def getNumSynapses(self):
    """ Return the total number of synapses. """
    return self.cells4.nSynapses()


  def getNumSegmentsInCell(self, c, i):
    """ Return the total number of segments in cell (c,i)"""
    return self.cells4.nSegmentsOnCell(c,i)


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
      distAges,         # a list of tuples (ageRange, numSegments)
    )

    nActiveSegs and nActiveSynapses are 0 if collectActiveData is False
    """

    # Requires appropriate accessors in C++ cells4 (currently unimplemented)
    assert collectActiveData == False

    nSegments, nSynapses = self.getNumSegments(), self.cells4.nSynapses()
    distSegSizes, distNSegsPerCell = {}, {}
    nActiveSegs, nActiveSynapses = 0, 0
    distPermValues = {}   # Num synapses with given permanence values

    numAgeBuckets = 20
    distAges = []
    ageBucketSize = int((self.iterationIdx+20) / 20)
    for i in range(numAgeBuckets):
      distAges.append(['%d-%d' % (i*ageBucketSize, (i+1)*ageBucketSize-1), 0])


    for c in xrange(self.numberOfCols):
      for i in xrange(self.cellsPerColumn):

        # Update histogram counting cell sizes
        nSegmentsThisCell = self.getNumSegmentsInCell(c,i)
        if nSegmentsThisCell > 0:
          if distNSegsPerCell.has_key(nSegmentsThisCell):
            distNSegsPerCell[nSegmentsThisCell] += 1
          else:
            distNSegsPerCell[nSegmentsThisCell] = 1

          # Update histogram counting segment sizes.
          segList = self.cells4.getNonEmptySegList(c,i)
          for segIdx in xrange(nSegmentsThisCell):
            seg = self.getSegmentOnCell(c, i, segIdx)
            nSynapsesThisSeg = len(seg) - 1
            if nSynapsesThisSeg > 0:
              if distSegSizes.has_key(nSynapsesThisSeg):
                distSegSizes[nSynapsesThisSeg] += 1
              else:
                distSegSizes[nSynapsesThisSeg] = 1

              # Accumulate permanence value histogram
              for syn in seg[1:]:
                p = int(syn[2]*10)
                if distPermValues.has_key(p):
                  distPermValues[p] += 1
                else:
                  distPermValues[p] = 1

            segObj = self.cells4.getSegment(c, i, segList[segIdx])
            age = self.iterationIdx - segObj.getLastActiveIteration()
            ageBucket = int(age/ageBucketSize)
            distAges[ageBucket][1] += 1


    return (nSegments, nSynapses, nActiveSegs, nActiveSynapses, \
            distSegSizes, distNSegsPerCell, distPermValues, distAges)


  def getActiveSegment(self, c,i, timeStep):
    """ For a given cell, return the segment with the strongest _connected_
    activation, i.e. sum up the activations of the connected synapses of the
    segments only. That is, a segment is active only if it has enough connected
    synapses.
    """

    # TODO: add C++ accessor to implement this
    assert False


  def getBestMatchingCell(self, c, timeStep, learnState = False):
    """Find weakly activated cell in column. Returns index and segment of most
    activated segment above minThreshold.
    """

    # TODO: add C++ accessor to implement this
    assert False


  def getLeastAllocatedCell(self, c):
    """For the given column, return the cell with the fewest number of
    segments."""

    # TODO: add C++ accessor to implement this or implement our own variation
    assert False

  ################################################################################
  # The following methods are implemented in the base class but should never
  # be called in this implementation.
  ################################################################################


  def isSegmentActive(self, seg, timeStep):
    """    """
    # Should never be called in this subclass
    assert False


  def getSegmentActivityLevel(self, seg, timeStep, connectedSynapsesOnly =False,
                              learnState = False):
    """   """
    # Should never be called in this subclass
    assert False


  def isSequenceSegment(self, s):
    """   """
    # Should never be called in this subclass
    assert False


  def getBestMatchingSegment(self, c, i, timeStep, learnState = False):
    """     """
    # Should never be called in this subclass
    assert False


  def getSegmentActiveSynapses(self, c,i,s, timeStep, newSynapses =False):
    """  """
    # Should never be called in this subclass
    assert False


  def updateSynapse(self, segment, synapse, delta):
    """ """
    # Should never be called in this subclass
    assert False


  def adaptSegment(self, update, positiveReinforcement):
    """    """
    # Should never be called in this subclass
    assert False
