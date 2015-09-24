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

""" @file TP.py

Temporal pooler implementation.

This is the Python implementation and is used as the base class for the C++
implementation.
"""

import copy
import cPickle as pickle
import itertools

import numpy
from nupic.bindings.math import Random
from nupic.bindings.algorithms import getSegmentActivityLevel, isSegmentActive
from nupic.math import GetNTAReal
from nupic.support.consoleprinter import ConsolePrinterMixin


# Default verbosity while running unit tests
VERBOSITY = 0

# The current TP version used to track the checkpoint state.
TP_VERSION = 1

# The numpy equivalent to the floating point type used by NTA
dtype = GetNTAReal()



class TP(ConsolePrinterMixin):
  """
  Class implementing the temporal pooler algorithm as described in the
  published Cortical Learning Algorithm documentation.  The implementation here
  attempts to closely match the pseudocode in the documentation. This
  implementation does contain several additional bells and whistles such as
  a column confidence measure.

  @todo Document other constructor parameters.
  @todo Have some higher level flags for fast learning, HiLo, Pooling, etc.
  """

  def __init__(self,
               numberOfCols=500,
               cellsPerColumn=10,
               initialPerm=0.11,
               connectedPerm=0.50,
               minThreshold=8,
               newSynapseCount=15,
               permanenceInc=0.10,
               permanenceDec=0.10,
               permanenceMax=1.0,
               globalDecay=0.10,
               activationThreshold=12,
               doPooling=False,
               segUpdateValidDuration=5,
               burnIn=2,
               collectStats=False,
               seed=42,
               verbosity=VERBOSITY,
               checkSynapseConsistency=False,  # for cpp only -- ignored
               pamLength=1,
               maxInfBacktrack=10,
               maxLrnBacktrack=5,
               maxAge=100000,
               maxSeqLength=32,
               maxSegmentsPerCell=-1,
               maxSynapsesPerSegment=-1,
               outputType='normal',
              ):
    """
    Construct the TP

    @param pamLength Number of time steps to remain in "Pay Attention Mode" after
                  we detect we've reached the end of a learned sequence. Setting
                  this to 0 disables PAM mode. When we are in PAM mode, we do
                  not burst unpredicted columns during learning, which in turn
                  prevents us from falling into a previously learned sequence
                  for a while (until we run through another 'pamLength' steps).
                  The advantge of PAM mode is that it requires fewer
                  presentations to learn a set of sequences which share
                  elements. The disadvantage of PAM mode is that if a learned
                  sequence is immediately followed by set set of elements that
                  should be learned as a 2nd sequence, the first pamLength
                  elements of that sequence will not be learned as part of that
                  2nd sequence.

    @param maxAge Controls global decay. Global decay will only decay segments
                  that have not been activated for maxAge iterations, and will
                  only do the global decay loop every maxAge iterations. The
                  default (maxAge=1) reverts to the behavior where global decay
                  is applied every iteration to every segment. Using maxAge > 1
                  can significantly speed up the TP when global decay is used.

    @param maxSeqLength If not 0, we will never learn more than maxSeqLength inputs
                  in a row without starting over at start cells. This sets an
                  upper bound on the length of learned sequences and thus is
                  another means (besides maxAge and globalDecay) by which to
                  limit how much the TP tries to learn.

    @param maxSegmentsPerCell The maximum number of segments allowed on a cell. This
                  is used to turn on "fixed size CLA" mode. When in effect,
                  globalDecay is not applicable and must be set to 0 and
                  maxAge must be set to 0. When this is used (> 0),
                  maxSynapsesPerSegment must also be > 0.

    @param maxSynapsesPerSegment The maximum number of synapses allowed in a segment.
                  This is used to turn on "fixed size CLA" mode. When in effect,
                  globalDecay is not applicable and must be set to 0 and maxAge
                  must be set to 0. When this is used (> 0), maxSegmentsPerCell
                  must also be > 0.

    @param outputType Can be one of the following: 'normal', 'activeState',
                  'activeState1CellPerCol'.
                  'normal': output the OR of the active and predicted state. 
                  'activeState': output only the active state. 
                  'activeState1CellPerCol': output only the active state, and at
                  most 1 cell/column. If more than 1 cell is active in a column,
                  the one with the highest confidence is sent up.
                  Default is 'normal'.

    @param doPooling If True, pooling is enabled. False is the default.

    @param burnIn Used for evaluating the prediction score. Default is 2.

    @param collectStats If True, collect training / inference stats. Default is
                        False.

    """

    ## @todo document
    self.version = TP_VERSION

    ConsolePrinterMixin.__init__(self, verbosity)

    # Check arguments
    assert pamLength > 0, "This implementation must have pamLength > 0"

    # Fixed size CLA mode?
    if maxSegmentsPerCell != -1 or maxSynapsesPerSegment != -1:
      assert (maxSegmentsPerCell > 0 and maxSynapsesPerSegment > 0)
      assert (globalDecay == 0.0)
      assert (maxAge == 0)

      assert maxSynapsesPerSegment >= newSynapseCount, ("TP requires that "
          "maxSynapsesPerSegment >= newSynapseCount. (Currently %s >= %s)" % (
          maxSynapsesPerSegment, newSynapseCount))

    # Seed random number generator
    if seed >= 0:
      self._random = Random(seed)
    else:
      self._random = Random(numpy.random.randint(256))

    # Store creation parameters
    ## @todo document
    self.numberOfCols = numberOfCols
    ## @todo document
    self.cellsPerColumn = cellsPerColumn
    self._numberOfCells = numberOfCols * cellsPerColumn
    ## @todo document
    self.initialPerm = numpy.float32(initialPerm)
    ## @todo document
    self.connectedPerm = numpy.float32(connectedPerm)
    ## @todo document
    self.minThreshold = minThreshold
    ## @todo document
    self.newSynapseCount = newSynapseCount
    ## @todo document
    self.permanenceInc = numpy.float32(permanenceInc)
    ## @todo document
    self.permanenceDec = numpy.float32(permanenceDec)
    ## @todo document
    self.permanenceMax = numpy.float32(permanenceMax)
    ## @todo document
    self.globalDecay = numpy.float32(globalDecay)
    ## @todo document
    self.activationThreshold = activationThreshold
    ## Allows to turn off pooling
    self.doPooling = doPooling
    ## @todo document
    self.segUpdateValidDuration = segUpdateValidDuration
    ## Used for evaluating the prediction score
    self.burnIn = burnIn
    ## If true, collect training/inference stats
    self.collectStats = collectStats
    ## @todo document
    self.seed = seed
    ## @todo document
    self.verbosity = verbosity
    ## @todo document
    self.pamLength = pamLength
    ## @todo document
    self.maxAge = maxAge
    ## @todo document
    self.maxInfBacktrack = maxInfBacktrack
    ## @todo document
    self.maxLrnBacktrack = maxLrnBacktrack
    ## @todo document
    self.maxSeqLength = maxSeqLength
    ## @todo document
    self.maxSegmentsPerCell = maxSegmentsPerCell
    ## @todo document
    self.maxSynapsesPerSegment = maxSynapsesPerSegment
    assert outputType in ('normal', 'activeState', 'activeState1CellPerCol')
    ## @todo document
    self.outputType = outputType

    # No point having larger expiration if we are not doing pooling
    if not doPooling:
      self.segUpdateValidDuration = 1

    # Create data structures
    ## @todo document
    self.activeColumns = [] # list of indices of active columns

    ## Cells are indexed by column and index in the column
    # Every self.cells[column][index] contains a list of segments
    # Each segment is a structure of class Segment
    self.cells = []
    for c in xrange(self.numberOfCols):
      self.cells.append([])
      for _ in xrange(self.cellsPerColumn):
        self.cells[c].append([])

    ## @todo document
    self.lrnIterationIdx = 0
    ## @todo document
    self.iterationIdx = 0
    ## unique segment id, so we can put segments in hashes
    self.segID = 0 
    ## @todo document
    self.currentOutput = None # for checkPrediction

    ## pamCounter gets reset to pamLength whenever we detect that the learning
    # state is making good predictions (at least half the columns predicted).
    # Whenever we do not make a good prediction, we decrement pamCounter.
    # When pamCounter reaches 0, we start the learn state over again at start
    # cells.
    self.pamCounter = self.pamLength


    ## If True, the TP will compute a signature for each sequence
    self.collectSequenceStats = False

    ## This gets set when we receive a reset and cleared on the first compute
    # following a reset.
    self.resetCalled = False

    ## We keep track of the average input density here
    self.avgInputDensity = None

    ## Keeps track of the length of the sequence currently being learned.
    self.learnedSeqLength = 0
    ## Keeps track of the moving average of all learned sequence length.
    self.avgLearnedSeqLength = 0.0

    # Set attributes intialized later on.
    self._prevLrnPatterns = None
    self._prevInfPatterns = None
    self.segmentUpdates = None

    # Set attributes that are initialized in _initEphemerals.
    self._stats = None
    ## @todo document
    self.cellConfidence = None
    ## @todo document
    self.colConfidence = None
    ## @todo document
    self.lrnActiveState = None
    ## @todo document
    self.infActiveState = None
    ## @todo document
    self.lrnPredictedState = None
    ## @todo document
    self.infPredictedState = None
    self._internalStats = None

    # All other members are ephemeral - don't need to be saved when we save
    # state. So they get separated out into _initEphemerals, which also
    # gets called when we are being restored from a saved state (via
    # __setstate__)
    self._initEphemerals()


  def _getEphemeralMembers(self):
    """
    List of our member variables that we don't need to be saved.
    """
    return []


  def _initEphemerals(self):
    """
    Initialize all ephemeral members after being restored to a pickled state.
    """
    ## We store the lists of segments updates, per cell, so that they can be
    # applied later during learning, when the cell gets bottom-up activation.
    # We store one list per cell. The lists are identified with a hash key which
    # is a tuple (column index, cell index).
    self.segmentUpdates = {}

    # Allocate and reset all stats
    self.resetStats()

    # NOTE: We don't use the same backtrack buffer for inference and learning
    # because learning has a different metric for determining if an input from
    # the past is potentially useful again for backtracking.
    #
    # Our inference backtrack buffer. This keeps track of up to
    # maxInfBacktrack of previous input. Each entry is a list of active column
    # inputs.
    self._prevInfPatterns = []

    # Our learning backtrack buffer. This keeps track of up to maxLrnBacktrack
    # of previous input. Each entry is a list of active column inputs
    self._prevLrnPatterns = []

    # Keep integers rather than bools. Float?
    stateShape = (self.numberOfCols, self.cellsPerColumn)

    self.lrnActiveState = {}
    self.lrnActiveState["t"] = numpy.zeros(stateShape, dtype="int8")
    self.lrnActiveState["t-1"] = numpy.zeros(stateShape, dtype="int8")

    self.lrnPredictedState = {}
    self.lrnPredictedState["t"] = numpy.zeros(stateShape, dtype="int8")
    self.lrnPredictedState["t-1"] = numpy.zeros(stateShape, dtype="int8")

    self.infActiveState = {}
    self.infActiveState["t"] = numpy.zeros(stateShape, dtype="int8")
    self.infActiveState["t-1"] = numpy.zeros(stateShape, dtype="int8")
    self.infActiveState["backup"] = numpy.zeros(stateShape, dtype="int8")
    self.infActiveState["candidate"] = numpy.zeros(stateShape, dtype="int8")

    self.infPredictedState = {}
    self.infPredictedState["t"] = numpy.zeros(stateShape, dtype="int8")
    self.infPredictedState["t-1"] = numpy.zeros(stateShape, dtype="int8")
    self.infPredictedState["backup"] = numpy.zeros(stateShape, dtype="int8")
    self.infPredictedState["candidate"] = numpy.zeros(stateShape, dtype="int8")

    self.cellConfidence = {}
    self.cellConfidence["t"] = numpy.zeros(stateShape, dtype="float32")
    self.cellConfidence["t-1"] = numpy.zeros(stateShape, dtype="float32")
    self.cellConfidence["candidate"] = numpy.zeros(stateShape, dtype="float32")

    self.colConfidence = {}
    self.colConfidence["t"] = numpy.zeros(self.numberOfCols, dtype="float32")
    self.colConfidence["t-1"] = numpy.zeros(self.numberOfCols, dtype="float32")
    self.colConfidence["candidate"] = numpy.zeros(self.numberOfCols,
                                                  dtype="float32")


  def __getstate__(self):
    """ @internal
    Return serializable state.  This function will return a version of the
    __dict__ with all "ephemeral" members stripped out.  "Ephemeral" members
    are defined as those that do not need to be (nor should be) stored
    in any kind of persistent file (e.g., NuPIC network XML file.)
    """
    state = self.__dict__.copy()

    for ephemeralMemberName in self._getEphemeralMembers():
      state.pop(ephemeralMemberName, None)

    state['_random'] = self.getRandomState()

    return state


  def __setstate__(self, state):
    """ @internal
    Set the state of ourself from a serialized state.
    """
    self.setRandomState(state['_random'])
    del state['_random']
    self.__dict__.update(state)
    # Check the version of the checkpointed TP and update it to the current
    # version if necessary.
    if not hasattr(self, 'version'):
      self._initEphemerals()
      self.version = TP_VERSION


  def __getattr__(self, name):
    """ @internal
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


  def __del__(self):
    pass


  def __ne__(self, tp):
    return not self == tp


  def __eq__(self, tp):
    return not self.diff(tp)


  def diff(self, tp):
    diff = []
    toCheck = [((), self.__getstate__(), tp.__getstate__())]
    while toCheck:
      keys, a, b = toCheck.pop()
      if type(a) != type(b):
        diff.append((keys, a, b))
      elif isinstance(a, dict):
        keys1 = set(a.keys())
        keys2 = set(b.keys())
        # If there are missing keys, add them to the diff.
        if keys1 != keys2:
          for k in keys1 - keys2:
            diff.append((keys + (k,), d[k], None))
          for k in keys2 - keys1:
            diff.append((keys + (k,), None, b[k]))
        # For matching keys, add the values to the list of things to check.
        for k in keys1.union(keys2):
          toCheck.append((keys + (k,), a[k], b[k]))
      elif (isinstance(a, numpy.ndarray) or isinstance(a, list) or
            isinstance(a, tuple)):
        if len(a) != len(b):
          diff.append((keys + (k, 'len'), len(a), len(b)))
        elif not numpy.array_equal(a, b):
          diff.append((keys + (k,), a, b))
        #for i in xrange(len(a)):
        #  toCheck.append((keys + (k, i), a[i], b[i]))
      elif isinstance(a, Random):
        if a.getState() != b.getState():
          diff.append((keys + (k,), a.getState(), b.getState()))
      elif (a.__class__.__name__ == 'Cells4' and
            b.__class__.__name__ == 'Cells4'):
        continue
      else:
        try:
          _ = a != b
        except ValueError:
          raise ValueError(type(a))
        if a != b:
          diff.append((keys + (k,), a, b))
    return diff


  def getLearnActiveStateT(self):
    return self.lrnActiveState['t']


  def saveToFile(self, filePath):
    """
    Implemented in TP10X2.TP10X2.saveToFile
    """
    pass


  def loadFromFile(self, filePath):
    """
    Implemented in TP10X2.TP10X2.loadFromFile
    """
    pass


  def setRandomSeed(self, seed):
    """ @internal 
    Seed the random number generator.
    This is used during unit testing to generate repeatable results.
    """
    self._random = Random(seed)


  def getRandomState(self):
    """ @internal 
    Return the random number state.

    This is used during unit testing to generate repeatable results.
    """
    return pickle.dumps(self._random)


  def setRandomState(self, state):
    """ @internal Set the random number state.

    This is used during unit testing to generate repeatable results.
    """
    self._random = pickle.loads(state)


  def reset(self,):
    """
    Reset the state of all cells.

    This is normally used between sequences while training. All internal states
    are reset to 0.
    """
    if self.verbosity >= 3:
      print "\n==== RESET ====="

    self.lrnActiveState['t-1'].fill(0)
    self.lrnActiveState['t'].fill(0)
    self.lrnPredictedState['t-1'].fill(0)
    self.lrnPredictedState['t'].fill(0)

    self.infActiveState['t-1'].fill(0)
    self.infActiveState['t'].fill(0)
    self.infPredictedState['t-1'].fill(0)
    self.infPredictedState['t'].fill(0)

    self.cellConfidence['t-1'].fill(0)
    self.cellConfidence['t'].fill(0)

    # Flush the segment update queue
    self.segmentUpdates = {}

    self._internalStats['nInfersSinceReset'] = 0

    #To be removed
    self._internalStats['curPredictionScore'] = 0
    #New prediction score
    self._internalStats['curPredictionScore2']   = 0
    self._internalStats['curFalseNegativeScore'] = 0
    self._internalStats['curFalsePositiveScore'] = 0

    self._internalStats['curMissing'] = 0
    self._internalStats['curExtra'] = 0

    # When a reset occurs, set prevSequenceSignature to the signature of the
    # just-completed sequence and start accumulating histogram for the next
    # sequence.
    self._internalStats['prevSequenceSignature'] = None
    if self.collectSequenceStats:
      if self._internalStats['confHistogram'].sum() > 0:
        sig = self._internalStats['confHistogram'].copy()
        sig.reshape(self.numberOfCols * self.cellsPerColumn)
        self._internalStats['prevSequenceSignature'] = sig
      self._internalStats['confHistogram'].fill(0)

    self.resetCalled = True

    # Clear out input history
    self._prevInfPatterns = []
    self._prevLrnPatterns = []


  def resetStats(self):
    """
    Reset the learning and inference stats. This will usually be called by
    user code at the start of each inference run (for a particular data set).
    """
    self._stats = dict()
    self._internalStats = dict()

    self._internalStats['nInfersSinceReset'] = 0
    self._internalStats['nPredictions'] = 0

    #New prediction score
    self._internalStats['curPredictionScore2']     = 0
    self._internalStats['predictionScoreTotal2']   = 0
    self._internalStats['curFalseNegativeScore']   = 0
    self._internalStats['falseNegativeScoreTotal'] = 0
    self._internalStats['curFalsePositiveScore']   = 0
    self._internalStats['falsePositiveScoreTotal'] = 0

    self._internalStats['pctExtraTotal'] = 0
    self._internalStats['pctMissingTotal'] = 0
    self._internalStats['curMissing'] = 0
    self._internalStats['curExtra'] = 0
    self._internalStats['totalMissing'] = 0
    self._internalStats['totalExtra'] = 0

    # Sequence signature statistics. Note that we don't reset the sequence
    # signature list itself.
    self._internalStats['prevSequenceSignature'] = None
    if self.collectSequenceStats:
      self._internalStats['confHistogram'] = (
          numpy.zeros((self.numberOfCols, self.cellsPerColumn),
                      dtype="float32"))


  def getStats(self):
    """
    Return the current learning and inference stats. This returns a dict
    containing all the learning and inference stats we have collected since the
    last resetStats(). If @ref collectStats is False, then None is returned.

    @returns dict

    The following keys are returned in the dict when @ref collectStats is True:

      @retval nPredictions the number of predictions. This is the total
                              number of inferences excluding burn-in and the
                              last inference.

      @retval curPredictionScore the score for predicting the current input
                              (predicted during the previous inference)

      @retval curMissing the number of bits in the current input that were
                              not predicted to be on.

      @retval curExtra the number of bits in the predicted output that
                              are not in the next input

      @retval predictionScoreTotal the sum of every prediction score to date

      @retval predictionScoreAvg predictionScoreTotal / nPredictions

      @retval pctMissingTotal the total number of bits that were missed over all
                              predictions

      @retval pctMissingAvg pctMissingTotal / nPredictions

      @retval prevSequenceSignature signature for the sequence immediately preceding
                              the last reset. 'None' if collectSequenceStats is
                              False
    """
    if not self.collectStats:
      return None

    self._stats['nPredictions'] = self._internalStats['nPredictions']
    self._stats['curMissing'] = self._internalStats['curMissing']
    self._stats['curExtra'] = self._internalStats['curExtra']
    self._stats['totalMissing'] = self._internalStats['totalMissing']
    self._stats['totalExtra'] = self._internalStats['totalExtra']

    nPredictions = max(1, self._stats['nPredictions'])

    # New prediction score
    self._stats['curPredictionScore2'] = (
        self._internalStats['curPredictionScore2'])
    self._stats['predictionScoreAvg2'] = (
        self._internalStats['predictionScoreTotal2'] / nPredictions)
    self._stats['curFalseNegativeScore'] = (
        self._internalStats['curFalseNegativeScore'])
    self._stats['falseNegativeAvg'] = (
        self._internalStats['falseNegativeScoreTotal'] / nPredictions)
    self._stats['curFalsePositiveScore'] = (
        self._internalStats['curFalsePositiveScore'])
    self._stats['falsePositiveAvg'] = (
        self._internalStats['falsePositiveScoreTotal'] / nPredictions)

    self._stats['pctExtraAvg'] = (self._internalStats['pctExtraTotal'] /
                                  nPredictions)
    self._stats['pctMissingAvg'] = (self._internalStats['pctMissingTotal'] /
                                    nPredictions)

    # This will be None if collectSequenceStats is False
    self._stats['prevSequenceSignature'] = (
        self._internalStats['prevSequenceSignature'])

    return self._stats


  def _updateStatsInferEnd(self, stats, bottomUpNZ, predictedState,
                           colConfidence):
    """
    Called at the end of learning and inference, this routine will update
    a number of stats in our _internalStats dictionary, including our computed 
    prediction score.

    @param stats            internal stats dictionary
    @param bottomUpNZ       list of the active bottom-up inputs
    @param predictedState   The columns we predicted on the last time step (should
                            match the current bottomUpNZ in the best case)
    @param colConfidence    Column confidences we determined on the last time step
    """
    # Return if not collecting stats
    if not self.collectStats:
      return
    stats['nInfersSinceReset'] += 1

    # Compute the prediction score, how well the prediction from the last
    # time step predicted the current bottom-up input
    (numExtra2, numMissing2, confidences2) = self.checkPrediction2(
        patternNZs=[bottomUpNZ], output=predictedState,
        colConfidence=colConfidence)
    predictionScore, positivePredictionScore, negativePredictionScore = (
        confidences2[0])

    # Store the stats that don't depend on burn-in
    stats['curPredictionScore2'] = float(predictionScore)
    stats['curFalseNegativeScore'] = 1.0 - float(positivePredictionScore)
    stats['curFalsePositiveScore'] = float(negativePredictionScore)

    stats['curMissing'] = numMissing2
    stats['curExtra'] = numExtra2

    # If we are passed the burn-in period, update the accumulated stats
    # Here's what various burn-in values mean:
    #   0: try to predict the first element of each sequence and all subsequent
    #   1: try to predict the second element of each sequence and all subsequent
    #   etc.
    if stats['nInfersSinceReset'] <= self.burnIn:
      return

    # Burn-in related stats
    stats['nPredictions'] += 1
    numExpected = max(1.0, float(len(bottomUpNZ)))

    stats['totalMissing'] += numMissing2
    stats['totalExtra'] += numExtra2
    stats['pctExtraTotal'] += 100.0 * numExtra2 / numExpected
    stats['pctMissingTotal'] += 100.0 * numMissing2 / numExpected
    stats['predictionScoreTotal2'] += float(predictionScore)
    stats['falseNegativeScoreTotal'] += 1.0 - float(positivePredictionScore)
    stats['falsePositiveScoreTotal'] += float(negativePredictionScore)

    if self.collectSequenceStats:
      # Collect cell confidences for every cell that correctly predicted current
      # bottom up input. Normalize confidence across each column
      cc = self.cellConfidence['t-1'] * self.infActiveState['t']
      sconf = cc.sum(axis=1)
      for c in range(self.numberOfCols):
        if sconf[c] > 0:
          cc[c, :] /= sconf[c]

      # Update cell confidence histogram: add column-normalized confidence
      # scores to the histogram
      self._internalStats['confHistogram'] += cc


  def printState(self, aState):
    """
    Print an integer array that is the same shape as activeState.
    
    @param aState TODO: document
    """
    def formatRow(var, i):
      s = ''
      for c in range(self.numberOfCols):
        if c > 0 and c % 10 == 0:
          s += ' '
        s += str(var[c, i])
      s += ' '
      return s

    for i in xrange(self.cellsPerColumn):
      print formatRow(aState, i)


  def printConfidence(self, aState, maxCols = 20):
    """
    Print a floating point array that is the same shape as activeState.
    
    @param aState TODO: document
    @param maxCols TODO: document
    """
    def formatFPRow(var, i):
      s = ''
      for c in range(min(maxCols, self.numberOfCols)):
        if c > 0 and c % 10 == 0:
          s += '   '
        s += ' %5.3f' % var[c, i]
      s += ' '
      return s

    for i in xrange(self.cellsPerColumn):
      print formatFPRow(aState, i)


  def printColConfidence(self, aState, maxCols = 20):
    """
    Print up to maxCols number from a flat floating point array.
    
    @param aState TODO: document
    @param maxCols TODO: document
    """
    def formatFPRow(var):
      s = ''
      for c in range(min(maxCols, self.numberOfCols)):
        if c > 0 and c % 10 == 0:
          s += '   '
        s += ' %5.3f' % var[c]
      s += ' '
      return s

    print formatFPRow(aState)

  def printStates(self, printPrevious = True, printLearnState = True):
    """
    @todo document
    """
    def formatRow(var, i):
      s = ''
      for c in range(self.numberOfCols):
        if c > 0 and c % 10 == 0:
          s += ' '
        s += str(var[c, i])
      s += ' '
      return s

    print "\nInference Active state"
    for i in xrange(self.cellsPerColumn):
      if printPrevious:
        print formatRow(self.infActiveState['t-1'], i),
      print formatRow(self.infActiveState['t'], i)

    print "Inference Predicted state"
    for i in xrange(self.cellsPerColumn):
      if printPrevious:
        print formatRow(self.infPredictedState['t-1'], i),
      print formatRow(self.infPredictedState['t'], i)

    if printLearnState:
      print "\nLearn Active state"
      for i in xrange(self.cellsPerColumn):
        if printPrevious:
          print formatRow(self.lrnActiveState['t-1'], i),
        print formatRow(self.lrnActiveState['t'], i)

      print "Learn Predicted state"
      for i in xrange(self.cellsPerColumn):
        if printPrevious:
          print formatRow(self.lrnPredictedState['t-1'], i),
        print formatRow(self.lrnPredictedState['t'], i)


  def printOutput(self, y):
    """
    @todo document
    """
    print "Output"
    for i in xrange(self.cellsPerColumn):
      for c in xrange(self.numberOfCols):
        print int(y[c, i]),
      print


  def printInput(self, x):
    """
    @todo document
    """
    print "Input"
    for c in xrange(self.numberOfCols):
      print int(x[c]),
    print


  def printParameters(self):
    """
    Print the parameter settings for the TP.
    """
    print "numberOfCols=", self.numberOfCols
    print "cellsPerColumn=", self.cellsPerColumn
    print "minThreshold=", self.minThreshold
    print "newSynapseCount=", self.newSynapseCount
    print "activationThreshold=", self.activationThreshold
    print
    print "initialPerm=", self.initialPerm
    print "connectedPerm=", self.connectedPerm
    print "permanenceInc=", self.permanenceInc
    print "permanenceDec=", self.permanenceDec
    print "permanenceMax=", self.permanenceMax
    print "globalDecay=", self.globalDecay
    print
    print "doPooling=", self.doPooling
    print "segUpdateValidDuration=", self.segUpdateValidDuration
    print "pamLength=", self.pamLength


  def printActiveIndices(self, state, andValues=False):
    """
    Print the list of [column, cellIdx] indices for each of the active
    cells in state. 
    
    @param state TODO: document
    @param andValues TODO: document
    """
    if len(state.shape) == 2:
      (cols, cellIdxs) = state.nonzero()
    else:
      cols = state.nonzero()[0]
      cellIdxs = numpy.zeros(len(cols))

    if len(cols) == 0:
      print "NONE"
      return

    prevCol = -1
    for (col, cellIdx) in zip(cols, cellIdxs):
      if col != prevCol:
        if prevCol != -1:
          print "] ",
        print "Col %d: [" % (col),
        prevCol = col

      if andValues:
        if len(state.shape) == 2:
          value = state[col, cellIdx]
        else:
          value = state[col]
        print "%d: %s," % (cellIdx, value),
      else:
        print "%d," % (cellIdx),
    print "]"


  def printComputeEnd(self, output, learn=False):
    """
    Called at the end of inference to print out various diagnostic
    information based on the current verbosity level.
    
    @param output TODO: document
    @param learn TODO: document
    """
    if self.verbosity >= 3:
      print "----- computeEnd summary: "
      print "learn:", learn
      print "numBurstingCols: %s, " % (
          self.infActiveState['t'].min(axis=1).sum()),
      print "curPredScore2: %s, " % (
          self._internalStats['curPredictionScore2']),
      print "curFalsePosScore: %s, " % (
          self._internalStats['curFalsePositiveScore']),
      print "1-curFalseNegScore: %s, " % (
          1 - self._internalStats['curFalseNegativeScore'])
      print "numSegments: ", self.getNumSegments(),
      print "avgLearnedSeqLength: ", self.avgLearnedSeqLength

      print "----- infActiveState (%d on) ------" % (
          self.infActiveState['t'].sum())
      self.printActiveIndices(self.infActiveState['t'])
      if self.verbosity >= 6:
        self.printState(self.infActiveState['t'])

      print "----- infPredictedState (%d on)-----" % (
          self.infPredictedState['t'].sum())
      self.printActiveIndices(self.infPredictedState['t'])
      if self.verbosity >= 6:
        self.printState(self.infPredictedState['t'])

      print "----- lrnActiveState (%d on) ------" % (
          self.lrnActiveState['t'].sum())
      self.printActiveIndices(self.lrnActiveState['t'])
      if self.verbosity >= 6:
        self.printState(self.lrnActiveState['t'])

      print "----- lrnPredictedState (%d on)-----" % (
          self.lrnPredictedState['t'].sum())
      self.printActiveIndices(self.lrnPredictedState['t'])
      if self.verbosity >= 6:
        self.printState(self.lrnPredictedState['t'])


      print "----- cellConfidence -----"
      self.printActiveIndices(self.cellConfidence['t'], andValues=True)
      if self.verbosity >= 6:
        self.printConfidence(self.cellConfidence['t'])

      print "----- colConfidence -----"
      self.printActiveIndices(self.colConfidence['t'], andValues=True)

      print "----- cellConfidence[t-1] for currently active cells -----"
      cc = self.cellConfidence['t-1'] * self.infActiveState['t']
      self.printActiveIndices(cc, andValues=True)

      if self.verbosity == 4:
        print "Cells, predicted segments only:"
        self.printCells(predictedOnly=True)
      elif self.verbosity >= 5:
        print "Cells, all segments:"
        self.printCells(predictedOnly=False)
      print

    elif self.verbosity >= 1:
      print "TP: learn:", learn
      print "TP: active outputs(%d):" % len(output.nonzero()[0]),
      self.printActiveIndices(output.reshape(self.numberOfCols,
                                             self.cellsPerColumn))


  def printSegmentUpdates(self):
    """
    @todo document
    """
    print "=== SEGMENT UPDATES ===, Num = ", len(self.segmentUpdates)
    for key, updateList in self.segmentUpdates.iteritems():
      c, i = key[0], key[1]
      print c, i, updateList


  def printCell(self, c, i, onlyActiveSegments=False):
    """
    @todo document
    """
    
    if len(self.cells[c][i]) > 0:
      print "Column", c, "Cell", i, ":",
      print len(self.cells[c][i]), "segment(s)"
      for j, s in enumerate(self.cells[c][i]):
        isActive = self.isSegmentActive(s, self.infActiveState['t'])
        if not onlyActiveSegments or isActive:
          isActiveStr = "*" if isActive else " "
          print "  %sSeg #%-3d" % (isActiveStr, j),
          s.debugPrint()


  def printCells(self, predictedOnly=False):
    """
    @todo document
    """
    if predictedOnly:
      print "--- PREDICTED CELLS ---"
    else:
      print "--- ALL CELLS ---"
    print "Activation threshold=", self.activationThreshold,
    print "min threshold=", self.minThreshold,
    print "connected perm=", self.connectedPerm

    for c in xrange(self.numberOfCols):
      for i in xrange(self.cellsPerColumn):
        if not predictedOnly or self.infPredictedState['t'][c, i]:
          self.printCell(c, i, predictedOnly)


  def getNumSegmentsInCell(self, c, i):
    """
    @param c column index
    @param i cell index within column
    @returns the total number of synapses in cell (c, i)
    """
    return len(self.cells[c][i])


  def getNumSynapses(self):
    """
    @returns the total number of synapses
    """
    nSyns = self.getSegmentInfo()[1]
    return nSyns


  def getNumStrongSynapses(self):
    """
    @todo implement this, it is used by the node's getParameter() call
    """
    return 0


  def getNumStrongSynapsesPerTimeSlot(self):
    """
    @todo implement this, it is used by the node's getParameter() call
    """
    return 0


  def getNumSynapsesPerSegmentMax(self):
    """
    @todo implement this, it is used by the node's getParameter() call, it should return the max # of synapses seen in any one segment.
    """
    return 0


  def getNumSynapsesPerSegmentAvg(self):
    """
    @returns the average number of synapses per segment
    """
    return float(self.getNumSynapses()) / max(1, self.getNumSegments())


  def getNumSegments(self):
    """
    @returns the total number of segments
    """
    nSegs = self.getSegmentInfo()[0]
    return nSegs


  def getNumCells(self):
    """
    @returns the total number of cells
    """
    return self.numberOfCols * self.cellsPerColumn


  def getSegmentOnCell(self, c, i, segIdx):
    """
    @param c column index
    @param i cell index in column
    @param segIdx TODO: document

    @returns list representing the the segment on cell (c, i) with index sidx.
    
    Returns the segment as following list:

        [  [segmentID, sequenceSegmentFlag, positiveActivations,
            totalActivations, lastActiveIteration,
            lastPosDutyCycle, lastPosDutyCycleIteration],
           [col1, idx1, perm1],
           [col2, idx2, perm2], ...
        ]

    @retval segmentId TODO: document
    @retval sequenceSegmentFlag TODO: document
    @retval positiveActivations TODO: document
    @retval totalActivations TODO: document
    @retval lastActiveIteration TODO: document
    @retval lastPosDutyCycle TODO: document
    @retval lastPosDutyCycleIteration TODO: document
    @retval [col1, idx1, perm1] TODO: document
    """
    seg = self.cells[c][i][segIdx]
    retlist = [[seg.segID, seg.isSequenceSeg, seg.positiveActivations,
                seg.totalActivations, seg.lastActiveIteration,
                seg._lastPosDutyCycle, seg._lastPosDutyCycleIteration]]
    retlist += seg.syns
    return retlist


  class SegmentUpdate(object):
    """
    Class used to carry instructions for updating a segment.
    """

    def __init__(self, c, i, seg=None, activeSynapses=[]):
      self.columnIdx = c
      self.cellIdx = i
      self.segment = seg # The segment object itself, not an index (can be None)
      self.activeSynapses = activeSynapses
      self.sequenceSegment = False
      self.phase1Flag = False

      # Set true if segment only reaches activationThreshold when including
      #  not fully connected synapses.
      self.weaklyPredicting = False

    def __eq__(self, other):
      if set(self.__dict__.keys()) != set(other.__dict__.keys()):
        return False
      for k in self.__dict__:
        if self.__dict__[k] != other.__dict__[k]:
          return False
      return True

    def __ne__(self, other):
      return not self == other

    # Just for debugging
    def __str__(self):
      return ("Seg update: cell=[%d,%d]" % (self.columnIdx, self.cellIdx) +
              ", seq seg=" + str(self.sequenceSegment) +
              ", seg=" + str(self.segment) +
              ", synapses=" + str(self.activeSynapses))


  def addToSegmentUpdates(self, c, i, segUpdate):
    """
    Store a dated potential segment update. The "date" (iteration index) is used
    later to determine whether the update is too old and should be forgotten.
    This is controlled by parameter segUpdateValidDuration.

    @param c TODO: document
    @param i TODO: document
    @param segUpdate TODO: document
    """
    # Sometimes we might be passed an empty update
    if segUpdate is None or len(segUpdate.activeSynapses) == 0:
      return

    key = (c, i) # key = (column index, cell index in column)

    # TODO: scan list of updates for that cell and consolidate?
    # But watch out for dates!
    if self.segmentUpdates.has_key(key):
      self.segmentUpdates[key] += [(self.lrnIterationIdx, segUpdate)]
    else:
      self.segmentUpdates[key] = [(self.lrnIterationIdx, segUpdate)]


  def removeSegmentUpdate(self, updateInfo):
    """
    Remove a segment update (called when seg update expires or is processed)

    @param updateInfo tuple (creationDate, SegmentUpdate)
    """
    # An updateInfo contains (creationDate, SegmentUpdate)
    (creationDate, segUpdate) = updateInfo

    # Key is stored in segUpdate itself...
    key = (segUpdate.columnIdx, segUpdate.cellIdx)

    self.segmentUpdates[key].remove(updateInfo)


  def computeOutput(self):
    """Computes output for both learning and inference. In both cases, the
    output is the boolean OR of activeState and predictedState at t.
    Stores currentOutput for checkPrediction."""
    # TODO: This operation can be sped up by:
    #  1.)  Pre-allocating space for the currentOutput
    #  2.)  Making predictedState and activeState of type 'float32' up front
    #  3.)  Using logical_or(self.predictedState['t'], self.activeState['t'],
    #          self.currentOutput)

    if self.outputType == 'activeState1CellPerCol':

      # Fire only the most confident cell in columns that have 2 or more
      #  active cells
      mostActiveCellPerCol = self.cellConfidence['t'].argmax(axis=1)
      self.currentOutput = numpy.zeros(self.infActiveState['t'].shape,
                                       dtype='float32')

      # Turn on the most confident cell in each column. Note here that
      #  Columns refers to TP columns, even though each TP column is a row
      #  in the numpy array.
      numCols = self.currentOutput.shape[0]
      self.currentOutput[(xrange(numCols), mostActiveCellPerCol)] = 1

      # Don't turn on anything in columns which are not active at all
      activeCols = self.infActiveState['t'].max(axis=1)
      inactiveCols = numpy.where(activeCols==0)[0]
      self.currentOutput[inactiveCols, :] = 0


    elif self.outputType == 'activeState':
      self.currentOutput = self.infActiveState['t']

    elif self.outputType == 'normal':
      self.currentOutput = numpy.logical_or(self.infPredictedState['t'],
                                            self.infActiveState['t'])

    else:
      raise RuntimeError("Unimplemented outputType")

    return self.currentOutput.reshape(-1).astype('float32')


  def getActiveState(self):
    """ Return the current active state. This is called by the node to
    obtain the sequence output of the TP.
    """
    # TODO: This operation can be sped up by making  activeState of
    #         type 'float32' up front.
    return self.infActiveState['t'].reshape(-1).astype('float32')


  def getPredictedState(self):
    """
    Return a numpy array, predictedCells, representing the current predicted
    state.
    
    predictedCells[c][i] represents the state of the i'th cell in the c'th
    column.

    @returns numpy array of predicted cells, representing the current predicted
    state. predictedCells[c][i] represents the state of the i'th cell in the c'th
    column.
    """
    return self.infPredictedState['t']


  def predict(self, nSteps):
    """
    This function gives the future predictions for <nSteps> timesteps starting
    from the current TP state. The TP is returned to its original state at the
    end before returning.

    -# We save the TP state.
    -# Loop for nSteps
      -# Turn-on with lateral support from the current active cells
      -# Set the predicted cells as the next step's active cells. This step
         in learn and infer methods use input here to correct the predictions.
         We don't use any input here.
    -# Revert back the TP state to the time before prediction

    @param nSteps The number of future time steps to be predicted
    @returns      all the future predictions - a numpy array of type "float32" and
                  shape (nSteps, numberOfCols).
                  The ith row gives the tp prediction for each column at
                  a future timestep (t+i+1).
    """
    # Save the TP dynamic state, we will use to revert back in the end
    pristineTPDynamicState = self._getTPDynamicState()

    assert (nSteps>0)

    # multiStepColumnPredictions holds all the future prediction.
    multiStepColumnPredictions = numpy.zeros((nSteps, self.numberOfCols),
                                             dtype="float32")

    # This is a (nSteps-1)+half loop. Phase 2 in both learn and infer methods
    # already predicts for timestep (t+1). We use that prediction for free and
    # save the half-a-loop of work.

    step = 0
    while True:
      # We get the prediction for the columns in the next time step from
      # the topDownCompute method. It internally uses confidences.
      multiStepColumnPredictions[step, :] = self.topDownCompute()

      # Cleanest way in python to handle one and half loops
      if step == nSteps-1:
        break
      step += 1

      # Copy t-1 into t
      self.infActiveState['t-1'][:, :] = self.infActiveState['t'][:, :]
      self.infPredictedState['t-1'][:, :] = self.infPredictedState['t'][:, :]
      self.cellConfidence['t-1'][:, :] = self.cellConfidence['t'][:, :]

      # Predicted state at "t-1" becomes the active state at "t"
      self.infActiveState['t'][:, :] = self.infPredictedState['t-1'][:, :]

      # Predicted state and confidence are set in phase2.
      self.infPredictedState['t'].fill(0)
      self.cellConfidence['t'].fill(0.0)
      self.inferPhase2()

    # Revert the dynamic state to the saved state
    self._setTPDynamicState(pristineTPDynamicState)

    return multiStepColumnPredictions


  def _getTPDynamicStateVariableNames(self):
    """
    Any newly added dynamic states in the TP should be added to this list.

    Parameters:
    --------------------------------------------
    retval:       The list of names of TP dynamic state variables.
    """
    return ["infActiveState",
            "infPredictedState",
            "lrnActiveState",
            "lrnPredictedState",
            "cellConfidence",
            "colConfidence",
            ]


  def _getTPDynamicState(self,):
    """
    Parameters:
    --------------------------------------------
    retval:       A dict with all the dynamic state variable names as keys and
                  their values at this instant as values.
    """
    tpDynamicState = dict()
    for variableName in self._getTPDynamicStateVariableNames():
      tpDynamicState[variableName] = copy.deepcopy(self.__dict__[variableName])
    return tpDynamicState


  def _setTPDynamicState(self, tpDynamicState):
    """
    Set all the dynamic state variables from the <tpDynamicState> dict.

    <tpDynamicState> dict has all the dynamic state variable names as keys and
    their values at this instant as values.

    We set the dynamic state variables in the tp object with these items.
    """
    for variableName in self._getTPDynamicStateVariableNames():
      self.__dict__[variableName] = tpDynamicState.pop(variableName)


  def _updateAvgLearnedSeqLength(self, prevSeqLength):
    """Update our moving average of learned sequence length."""
    if self.lrnIterationIdx < 100:
      alpha = 0.5
    else:
      alpha = 0.1

    self.avgLearnedSeqLength = ((1.0 - alpha) * self.avgLearnedSeqLength +
                                (alpha * prevSeqLength))


  def getAvgLearnedSeqLength(self):
    """
    @returns Moving average of learned sequence length
    """
    return self.avgLearnedSeqLength


  def inferBacktrack(self, activeColumns):
    """
    This "backtracks" our inference state, trying to see if we can lock onto
    the current set of inputs by assuming the sequence started up to N steps
    ago on start cells.

    @param activeColumns The list of active column indices

    This will adjust @ref infActiveState['t'] if it does manage to lock on to a
    sequence that started earlier. It will also compute infPredictedState['t']
    based on the possibly updated @ref infActiveState['t'], so there is no need to
    call inferPhase2() after calling inferBacktrack().

    This looks at:
        - @ref infActiveState['t']

    This updates/modifies:
        - @ref infActiveState['t']
        - @ref infPredictedState['t']
        - @ref colConfidence['t']
        - @ref cellConfidence['t']

    How it works:
    -------------------------------------------------------------------
    This method gets called from updateInferenceState when we detect either of
    the following two conditions:
    
    -# The current bottom-up input had too many un-expected columns
    -# We fail to generate a sufficient number of predicted columns for the
       next time step.

    Either of these two conditions indicate that we have fallen out of a
    learned sequence.

    Rather than simply "giving up" and bursting on the unexpected input
    columns, a better approach is to see if perhaps we are in a sequence that
    started a few steps ago. The real world analogy is that you are driving
    along and suddenly hit a dead-end, you will typically go back a few turns
    ago and pick up again from a familiar intersection.

    This back-tracking goes hand in hand with our learning methodology, which
    always tries to learn again from start cells after it loses context. This
    results in a network that has learned multiple, overlapping paths through
    the input data, each starting at different points. The lower the global
    decay and the more repeatability in the data, the longer each of these
    paths will end up being.

    The goal of this function is to find out which starting point in the past
    leads to the current input with the most context as possible. This gives us
    the best chance of predicting accurately going forward. Consider the
    following example, where you have learned the following sub-sequences which
    have the given frequencies:

                      ? - Q - C - D - E      10X      seq 0
                      ? - B - C - D - F      1X       seq 1
                      ? - B - C - H - I      2X       seq 2
                      ? - B - C - D - F      3X       seq 3
              ? - Z - A - B - C - D - J      2X       seq 4
              ? - Z - A - B - C - H - I      1X       seq 5
              ? - Y - A - B - C - D - F      3X       seq 6

            ----------------------------------------
          W - X - Z - A - B - C - D          <= input history
                                  ^
                                  current time step

    Suppose, in the current time step, the input pattern is D and you have not
    predicted D, so you need to backtrack. Suppose we can backtrack up to 6
    steps in the past, which path should we choose? From the table above, we can
    see that the correct answer is to assume we are in seq 4. How do we
    implement the backtrack to give us this right answer? The current
    implementation takes the following approach:

    -# Start from the farthest point in the past.
    -# For each starting point S, calculate the confidence of the current
       input, conf(startingPoint=S), assuming we followed that sequence.
       Note that we must have learned at least one sequence that starts at
       point S.
    -# If conf(startingPoint=S) is significantly different from
       conf(startingPoint=S-1), then choose S-1 as the starting point.

    The assumption here is that starting point S-1 is the starting point of
    a learned sub-sequence that includes the current input in it's path and
    that started the longest ago. It thus has the most context and will be
    the best predictor going forward.

    From the statistics in the above table, we can compute what the confidences
    will be for each possible starting point:

        startingPoint           confidence of D
        -----------------------------------------
        B (t-2)               4/6  = 0.667   (seq 1,3)/(seq 1,2,3)
        Z (t-4)               2/3  = 0.667   (seq 4)/(seq 4,5)

    First of all, we do not compute any confidences at starting points t-1, t-3,
    t-5, t-6 because there are no learned sequences that start at those points.

    Notice here that Z is the starting point of the longest sub-sequence leading
    up to the current input. Event though starting at t-2 and starting at t-4
    give the same confidence value, we choose the sequence starting at t-4
    because it gives the most context, and it mirrors the way that learning
    extends sequences.
    """
    # How much input history have we accumulated?
    # The current input is always at the end of self._prevInfPatterns (at
    # index -1), but it is also evaluated as a potential starting point by
    # turning on it's start cells and seeing if it generates sufficient
    # predictions going forward.
    numPrevPatterns = len(self._prevInfPatterns)
    if numPrevPatterns <= 0:
      return

    # This is an easy to use label for the current time step
    currentTimeStepsOffset = numPrevPatterns - 1

    # Save our current active state in case we fail to find a place to restart
    # todo: save infActiveState['t-1'], infPredictedState['t-1']?
    self.infActiveState['backup'][:, :] = self.infActiveState['t'][:, :]

    # Save our t-1 predicted state because we will write over it as as evaluate
    # each potential starting point.
    self.infPredictedState['backup'][:, :] = self.infPredictedState['t-1'][:, :]

    # We will record which previous input patterns did not generate predictions
    # up to the current time step and remove all the ones at the head of the
    # input history queue so that we don't waste time evaluating them again at
    # a later time step.
    badPatterns = []

    # Let's go back in time and replay the recent inputs from start cells and
    #  see if we can lock onto this current set of inputs that way.
    #
    # Start the farthest back and work our way forward. For each starting point,
    #  See if firing on start cells at that point would predict the current
    #  input as well as generate sufficient predictions for the next time step.
    #
    # We want to pick the point closest to the current time step that gives us
    # the relevant confidence. Think of this example, where we are at D and need
    # to
    #   A - B - C - D
    # decide if we should backtrack to C, B, or A. Suppose B-C-D is a high order
    # sequence and A is unrelated to it. If we backtrock to B would we get a
    # certain confidence of D, but if went went farther back, to A, the
    # confidence wouldn't change, since A has no impact on the B-C-D series.
    #
    # So, our strategy will be to pick the "B" point, since choosing the A point
    #  does not impact our confidences going forward at all.
    inSequence = False
    candConfidence = None
    candStartOffset = None
    for startOffset in range(0, numPrevPatterns):

      # If we have a candidate already in the past, don't bother falling back
      #  to start cells on the current input.
      if startOffset == currentTimeStepsOffset and candConfidence is not None:
        break

      if self.verbosity >= 3:
        print (
            "Trying to lock-on using startCell state from %d steps ago:" % (
                numPrevPatterns - 1 - startOffset),
            self._prevInfPatterns[startOffset])

      # Play through starting from starting point 'startOffset'
      inSequence = False
      for offset in range(startOffset, numPrevPatterns):
        # If we are about to set the active columns for the current time step
        # based on what we predicted, capture and save the total confidence of
        # predicting the current input
        if offset == currentTimeStepsOffset:
          totalConfidence = self.colConfidence['t'][activeColumns].sum()

        # Compute activeState[t] given bottom-up and predictedState[t-1]
        self.infPredictedState['t-1'][:, :] = self.infPredictedState['t'][:, :]
        inSequence = self.inferPhase1(self._prevInfPatterns[offset],
                         useStartCells = (offset == startOffset))
        if not inSequence:
          break

        # Compute predictedState['t'] given activeState['t']
        if self.verbosity >= 3:
          print ("  backtrack: computing predictions from ",
                 self._prevInfPatterns[offset])
        inSequence = self.inferPhase2()
        if not inSequence:
          break

      # If starting from startOffset got lost along the way, mark it as an
      # invalid start point.
      if not inSequence:
        badPatterns.append(startOffset)
        continue

      # If we got to here, startOffset is a candidate starting point.
      # Save this state as a candidate state. It will become the chosen state if
      # we detect a change in confidences starting at a later startOffset
      candConfidence = totalConfidence
      candStartOffset = startOffset

      if self.verbosity >= 3 and startOffset != currentTimeStepsOffset:
        print ("  # Prediction confidence of current input after starting %d "
               "steps ago:" % (numPrevPatterns - 1 - startOffset),
               totalConfidence)

      if candStartOffset == currentTimeStepsOffset:  # no more to try
        break
      self.infActiveState['candidate'][:, :] = self.infActiveState['t'][:, :]
      self.infPredictedState['candidate'][:, :] = (
          self.infPredictedState['t'][:, :])
      self.cellConfidence['candidate'][:, :] = self.cellConfidence['t'][:, :]
      self.colConfidence['candidate'][:] = self.colConfidence['t'][:]
      break

    # If we failed to lock on at any starting point, fall back to the original
    # active state that we had on entry
    if candStartOffset is None:
      if self.verbosity >= 3:
        print "Failed to lock on. Falling back to bursting all unpredicted."
      self.infActiveState['t'][:, :] = self.infActiveState['backup'][:, :]
      self.inferPhase2()

    else:
      if self.verbosity >= 3:
        print ("Locked on to current input by using start cells from %d "
               " steps ago:" % (numPrevPatterns - 1 - candStartOffset),
               self._prevInfPatterns[candStartOffset])
      # Install the candidate state, if it wasn't the last one we evaluated.
      if candStartOffset != currentTimeStepsOffset:
        self.infActiveState['t'][:, :] = self.infActiveState['candidate'][:, :]
        self.infPredictedState['t'][:, :] = (
            self.infPredictedState['candidate'][:, :])
        self.cellConfidence['t'][:, :] = self.cellConfidence['candidate'][:, :]
        self.colConfidence['t'][:] = self.colConfidence['candidate'][:]

    # Remove any useless patterns at the head of the previous input pattern
    # queue.
    for i in range(numPrevPatterns):
      if (i in badPatterns or
          (candStartOffset is not None and i <= candStartOffset)):
        if self.verbosity >= 3:
          print ("Removing useless pattern from history:",
                 self._prevInfPatterns[0])
        self._prevInfPatterns.pop(0)
      else:
        break

    # Restore the original predicted state.
    self.infPredictedState['t-1'][:, :] = self.infPredictedState['backup'][:, :]


  def inferPhase1(self, activeColumns, useStartCells):
    """
    Update the inference active state from the last set of predictions
    and the current bottom-up.

    This looks at:
        - @ref infPredictedState['t-1']
    This modifies:
        - @ref infActiveState['t']

    @param activeColumns  list of active bottom-ups
    @param useStartCells  If true, ignore previous predictions and simply turn on
                      the start cells in the active columns
    @returns        True if the current input was sufficiently predicted, OR
                    if we started over on startCells.
                    False indicates that the current input was NOT predicted,
                    and we are now bursting on most columns.
    """
    # Init to zeros to start
    self.infActiveState['t'].fill(0)

    # Phase 1 - turn on predicted cells in each column receiving bottom-up
    # If we are following a reset, activate only the start cell in each
    # column that has bottom-up
    numPredictedColumns = 0
    if useStartCells:
      for c in activeColumns:
        self.infActiveState['t'][c, 0] = 1

    # else, turn on any predicted cells in each column. If there are none, then
    # turn on all cells (burst the column)
    else:
      for c in activeColumns:
        predictingCells = numpy.where(self.infPredictedState['t-1'][c] == 1)[0]
        numPredictingCells = len(predictingCells)

        if numPredictingCells > 0:
          self.infActiveState['t'][c, predictingCells] = 1
          numPredictedColumns += 1

        else:
          self.infActiveState['t'][c, :] = 1 # whole column bursts

    # Did we predict this input well enough?
    if useStartCells or numPredictedColumns >= 0.50 * len(activeColumns):
      return True
    else:
      return False


  def inferPhase2(self):
    """
    Phase 2 for the inference state. The computes the predicted state, then
    checks to insure that the predicted state is not over-saturated, i.e.
    look too close like a burst. This indicates that there were so many
    separate paths learned from the current input columns to the predicted
    input columns that bursting on the current input columns is most likely
    generated mix and match errors on cells in the predicted columns. If
    we detect this situation, we instead turn on only the start cells in the
    current active columns and re-generate the predicted state from those.

    @returns True if we have a decent guess as to the next input.
             Returing False from here indicates to the caller that we have
             reached the end of a learned sequence.

    This looks at:
        - @ref infActiveState['t']

    This modifies:
        - @ref infPredictedState['t']
        - @ref colConfidence['t']
        - @ref cellConfidence['t']
    """
    # Init to zeros to start
    self.infPredictedState['t'].fill(0)
    self.cellConfidence['t'].fill(0)
    self.colConfidence['t'].fill(0)

    # Phase 2 - Compute new predicted state and update cell and column
    #   confidences
    for c in xrange(self.numberOfCols):

      # For each cell in the column
      for i in xrange(self.cellsPerColumn):

        # For each segment in the cell
        for s in self.cells[c][i]:

          # See if it has the min number of active synapses
          numActiveSyns = self.getSegmentActivityLevel(
              s, self.infActiveState['t'], connectedSynapsesOnly=False)
          if numActiveSyns < self.activationThreshold:
            continue

          # Incorporate the confidence into the owner cell and column
          if self.verbosity >= 6:
            print "incorporating DC from cell[%d,%d]:   " % (c, i),
            s.debugPrint()
          dc = s.dutyCycle()
          self.cellConfidence['t'][c, i] += dc
          self.colConfidence['t'][c] += dc

          # If we reach threshold on the connected synapses, predict it
          # If not active, skip over it
          if self.isSegmentActive(s, self.infActiveState['t']):
            self.infPredictedState['t'][c, i] = 1

    # Normalize column and cell confidences
    sumConfidences = self.colConfidence['t'].sum()
    if sumConfidences > 0:
      self.colConfidence['t'] /= sumConfidences
      self.cellConfidence['t'] /= sumConfidences

    # Are we predicting the required minimum number of columns?
    numPredictedCols = self.infPredictedState['t'].max(axis=1).sum()
    if numPredictedCols >= 0.5 * self.avgInputDensity:
      return True
    else:
      return False


  def updateInferenceState(self, activeColumns):
    """
    Update the inference state. Called from compute() on every iteration.
    @param activeColumns The list of active column indices.
    """
    # Copy t to t-1
    self.infActiveState['t-1'][:, :] = self.infActiveState['t'][:, :]
    self.infPredictedState['t-1'][:, :] = self.infPredictedState['t'][:, :]
    self.cellConfidence['t-1'][:, :] = self.cellConfidence['t'][:, :]
    self.colConfidence['t-1'][:] = self.colConfidence['t'][:]

    # Each phase will zero/initilize the 't' states that it affects

    # Update our inference input history
    if self.maxInfBacktrack > 0:
      if len(self._prevInfPatterns) > self.maxInfBacktrack:
        self._prevInfPatterns.pop(0)
      self._prevInfPatterns.append(activeColumns)

    # Compute the active state given the predictions from last time step and
    # the current bottom-up
    inSequence = self.inferPhase1(activeColumns, self.resetCalled)

    # If this input was considered unpredicted, let's go back in time and
    # replay the recent inputs from start cells and see if we can lock onto
    # this current set of inputs that way.
    if not inSequence:
      if self.verbosity >= 3:
        print ("Too much unpredicted input, re-tracing back to try and lock on "
               "at an earlier timestep.")
      # inferBacktrack() will call inferPhase2() for us.
      self.inferBacktrack(activeColumns)
      return

    # Compute the predicted cells and the cell and column confidences
    inSequence = self.inferPhase2()
    if not inSequence:
      if self.verbosity >= 3:
        print ("Not enough predictions going forward, "
               "re-tracing back to try and lock on at an earlier timestep.")
      # inferBacktrack() will call inferPhase2() for us.
      self.inferBacktrack(activeColumns)


  def learnBacktrackFrom(self, startOffset, readOnly=True):
    """ @internal
    A utility method called from learnBacktrack. This will backtrack
    starting from the given startOffset in our prevLrnPatterns queue.

    It returns True if the backtrack was successful and we managed to get
    predictions all the way up to the current time step.

    If readOnly, then no segments are updated or modified, otherwise, all
    segment updates that belong to the given path are applied.

    This updates/modifies:
        - lrnActiveState['t']

    This trashes:
        - lrnPredictedState['t']
        - lrnPredictedState['t-1']
        - lrnActiveState['t-1']

    @param startOffset Start offset within the prevLrnPatterns input history
    @returns           True if we managed to lock on to a sequence that started
                       earlier.
                       If False, we lost predictions somewhere along the way
                       leading up to the current time.
    """
    # How much input history have we accumulated?
    # The current input is always at the end of self._prevInfPatterns (at
    # index -1), but it is also evaluated as a potential starting point by
    # turning on it's start cells and seeing if it generates sufficient
    # predictions going forward.
    numPrevPatterns = len(self._prevLrnPatterns)

    # This is an easy to use label for the current time step
    currentTimeStepsOffset = numPrevPatterns - 1

    # Clear out any old segment updates. learnPhase2() adds to the segment
    # updates if we're not readOnly
    if not readOnly:
      self.segmentUpdates = {}

    # Status message
    if self.verbosity >= 3:
      if readOnly:
        print (
            "Trying to lock-on using startCell state from %d steps ago:" % (
                numPrevPatterns - 1 - startOffset),
            self._prevLrnPatterns[startOffset])
      else:
        print (
            "Locking on using startCell state from %d steps ago:" % (
                numPrevPatterns - 1 - startOffset),
            self._prevLrnPatterns[startOffset])

    # Play through up to the current time step
    inSequence = True
    for offset in range(startOffset, numPrevPatterns):

      # Copy predicted and active states into t-1
      self.lrnPredictedState['t-1'][:, :] = self.lrnPredictedState['t'][:, :]
      self.lrnActiveState['t-1'][:, :] = self.lrnActiveState['t'][:, :]

      # Get the input pattern
      inputColumns = self._prevLrnPatterns[offset]

      # Apply segment updates from the last set of predictions
      if not readOnly:
        self.processSegmentUpdates(inputColumns)

      # Phase 1:
      # Compute activeState[t] given bottom-up and predictedState[t-1]
      if offset == startOffset:
        self.lrnActiveState['t'].fill(0)
        for c in inputColumns:
          self.lrnActiveState['t'][c, 0] = 1
        inSequence = True
      else:
        # Uses lrnActiveState['t-1'] and lrnPredictedState['t-1']
        # computes lrnActiveState['t']
        inSequence = self.learnPhase1(inputColumns, readOnly=readOnly)

      # Break out immediately if we fell out of sequence or reached the current
      # time step
      if not inSequence or offset == currentTimeStepsOffset:
        break

      # Phase 2:
      # Computes predictedState['t'] given activeState['t'] and also queues
      # up active segments into self.segmentUpdates, unless this is readOnly
      if self.verbosity >= 3:
        print "  backtrack: computing predictions from ", inputColumns
      self.learnPhase2(readOnly=readOnly)

    # Return whether or not this starting point was valid
    return inSequence

  def learnBacktrack(self):
    """
    This "backtracks" our learning state, trying to see if we can lock onto
    the current set of inputs by assuming the sequence started up to N steps
    ago on start cells.

    This will adjust @ref lrnActiveState['t'] if it does manage to lock on to a
    sequence that started earlier.

    @returns          >0 if we managed to lock on to a sequence that started
                      earlier. The value returned is how many steps in the
                      past we locked on.
                      If 0 is returned, the caller needs to change active
                      state to start on start cells.

    How it works:
    -------------------------------------------------------------------
    This method gets called from updateLearningState when we detect either of
    the following two conditions:
    
    -# Our PAM counter (@ref pamCounter) expired
    -# We reached the max allowed learned sequence length

    Either of these two conditions indicate that we want to start over on start
    cells.

    Rather than start over on start cells on the current input, we can
    accelerate learning by backtracking a few steps ago and seeing if perhaps
    a sequence we already at least partially know already started.

    This updates/modifies:
        - @ref lrnActiveState['t']

    This trashes:
        - @ref lrnActiveState['t-1']
        - @ref lrnPredictedState['t']
        - @ref lrnPredictedState['t-1']

    """
    # How much input history have we accumulated?
    # The current input is always at the end of self._prevInfPatterns (at
    # index -1), and is not a valid startingOffset to evaluate.
    numPrevPatterns = len(self._prevLrnPatterns) - 1
    if numPrevPatterns <= 0:
      if self.verbosity >= 3:
        print "lrnBacktrack: No available history to backtrack from"
      return False

    # We will record which previous input patterns did not generate predictions
    # up to the current time step and remove all the ones at the head of the
    # input history queue so that we don't waste time evaluating them again at
    # a later time step.
    badPatterns = []

    # Let's go back in time and replay the recent inputs from start cells and
    # see if we can lock onto this current set of inputs that way.
    #
    # Start the farthest back and work our way forward. For each starting point,
    # See if firing on start cells at that point would predict the current
    # input.
    #
    # We want to pick the point farthest in the past that has continuity
    # up to the current time step
    inSequence = False
    for startOffset in range(0, numPrevPatterns):
      # Can we backtrack from startOffset?
      inSequence = self.learnBacktrackFrom(startOffset, readOnly=True)

      # Done playing through the sequence from starting point startOffset
      # Break out as soon as we find a good path
      if inSequence:
        break

      # Take this bad starting point out of our input history so we don't
      # try it again later.
      badPatterns.append(startOffset)

    # If we failed to lock on at any starting point, return failure. The caller
    # will start over again on start cells
    if not inSequence:
      if self.verbosity >= 3:
        print ("Failed to lock on. Falling back to start cells on current "
               "time step.")
      # Nothing in our input history was a valid starting point, so get rid
      #  of it so we don't try any of them again at a later iteration
      self._prevLrnPatterns = []
      return False

    # We did find a valid starting point in the past. Now, we need to
    # re-enforce all segments that became active when following this path.
    if self.verbosity >= 3:
      print ("Discovered path to current input by using start cells from %d "
             "steps ago:" % (numPrevPatterns - startOffset),
             self._prevLrnPatterns[startOffset])

    self.learnBacktrackFrom(startOffset, readOnly=False)

    # Remove any useless patterns at the head of the input pattern history
    # queue.
    for i in range(numPrevPatterns):
      if i in badPatterns or i <= startOffset:
        if self.verbosity >= 3:
          print ("Removing useless pattern from history:",
                 self._prevLrnPatterns[0])
        self._prevLrnPatterns.pop(0)
      else:
        break

    return numPrevPatterns - startOffset


  def learnPhase1(self, activeColumns, readOnly=False):
    """
    Compute the learning active state given the predicted state and
    the bottom-up input.

    @param activeColumns list of active bottom-ups
    @param readOnly      True if being called from backtracking logic.
                         This tells us not to increment any segment
                         duty cycles or queue up any updates.
    @returns True if the current input was sufficiently predicted, OR
             if we started over on startCells. False indicates that the current 
             input was NOT predicted, well enough to consider it as "inSequence"

    This looks at:
        - @ref lrnActiveState['t-1']
        - @ref lrnPredictedState['t-1']

    This modifies:
        - @ref lrnActiveState['t']
        - @ref lrnActiveState['t-1']
    """
    # Save previous active state and start out on a clean slate
    self.lrnActiveState['t'].fill(0)

    # For each column, turn on the predicted cell. There will always be at most
    # one predicted cell per column
    numUnpredictedColumns = 0
    for c in activeColumns:
      predictingCells = numpy.where(self.lrnPredictedState['t-1'][c] == 1)[0]
      numPredictedCells = len(predictingCells)
      assert numPredictedCells <= 1

      # If we have a predicted cell, turn it on. The segment's posActivation
      # count will have already been incremented by processSegmentUpdates
      if numPredictedCells == 1:
        i = predictingCells[0]
        self.lrnActiveState['t'][c, i] = 1
        continue

      numUnpredictedColumns += 1
      if readOnly:
        continue

      # If no predicted cell, pick the closest matching one to reinforce, or
      # if none exists, create a new segment on a cell in that column
      i, s, numActive = self.getBestMatchingCell(
          c, self.lrnActiveState['t-1'], self.minThreshold)
      if s is not None and s.isSequenceSegment():
        if self.verbosity >= 4:
          print "Learn branch 0, found segment match. Learning on col=", c
        self.lrnActiveState['t'][c, i] = 1
        segUpdate = self.getSegmentActiveSynapses(
            c, i, s, self.lrnActiveState['t-1'], newSynapses = True)
        s.totalActivations += 1
        # This will update the permanences, posActivationsCount, and the
        # lastActiveIteration (age).
        trimSegment = self.adaptSegment(segUpdate)
        if trimSegment:
          self.trimSegmentsInCell(c, i, [s], minPermanence = 0.00001,
              minNumSyns = 0)

      # If no close match exists, create a new one
      else:
        # Choose a cell in this column to add a new segment to
        i = self.getCellForNewSegment(c)
        if (self.verbosity >= 4):
          print "Learn branch 1, no match. Learning on col=", c,
          print ", newCellIdxInCol=", i
        self.lrnActiveState['t'][c, i] = 1
        segUpdate = self.getSegmentActiveSynapses(
            c, i, None, self.lrnActiveState['t-1'], newSynapses=True)
        segUpdate.sequenceSegment = True # Make it a sequence segment
        self.adaptSegment(segUpdate)  # No need to check whether perm reached 0

    # Determine if we are out of sequence or not and reset our PAM counter
    # if we are in sequence
    numBottomUpColumns = len(activeColumns)
    if numUnpredictedColumns < numBottomUpColumns / 2:
      return True   # in sequence
    else:
      return False  # out of sequence


  def learnPhase2(self, readOnly=False):
    """
    Compute the predicted segments given the current set of active cells.

    @param readOnly       True if being called from backtracking logic.
                          This tells us not to increment any segment
                          duty cycles or queue up any updates.

    This computes the lrnPredictedState['t'] and queues up any segments that
    became active (and the list of active synapses for each segment) into
    the segmentUpdates queue

    This looks at:
        - @ref lrnActiveState['t']

    This modifies:
        - @ref lrnPredictedState['t']
        - @ref segmentUpdates
    """
    # Clear out predicted state to start with
    self.lrnPredictedState['t'].fill(0)

    # Compute new predicted state. When computing predictions for
    # phase 2, we predict at  most one cell per column (the one with the best
    # matching segment).
    for c in xrange(self.numberOfCols):

      # Is there a cell predicted to turn on in this column?
      i, s, numActive = self.getBestMatchingCell(
          c, self.lrnActiveState['t'], minThreshold = self.activationThreshold)
      if i is None:
        continue

      # Turn on the predicted state for the best matching cell and queue
      #  the pertinent segment up for an update, which will get processed if
      #  the cell receives bottom up in the future.
      self.lrnPredictedState['t'][c, i] = 1
      if readOnly:
        continue

      # Queue up this segment for updating
      segUpdate = self.getSegmentActiveSynapses(
          c, i, s, activeState=self.lrnActiveState['t'],
          newSynapses=(numActive < self.newSynapseCount))

      s.totalActivations += 1    # increment totalActivations
      self.addToSegmentUpdates(c, i, segUpdate)

      if self.doPooling:
        # creates a new pooling segment if no best matching segment found
        # sum(all synapses) >= minThreshold, "weak" activation
        predSegment = self.getBestMatchingSegment(c, i,
                                self.lrnActiveState['t-1'])
        segUpdate = self.getSegmentActiveSynapses(c, i, predSegment,
                          self.lrnActiveState['t-1'], newSynapses=True)
        self.addToSegmentUpdates(c, i, segUpdate)


  def updateLearningState(self, activeColumns):
    """
    Update the learning state. Called from compute() on every iteration
    @param activeColumns List of active column indices
    """
    # Copy predicted and active states into t-1
    self.lrnPredictedState['t-1'][:, :] = self.lrnPredictedState['t'][:, :]
    self.lrnActiveState['t-1'][:, :] = self.lrnActiveState['t'][:, :]

    # Update our learning input history
    if self.maxLrnBacktrack > 0:
      if len(self._prevLrnPatterns) > self.maxLrnBacktrack:
        self._prevLrnPatterns.pop(0)
      self._prevLrnPatterns.append(activeColumns)
      if self.verbosity >= 4:
        print "Previous learn patterns: \n"
        print self._prevLrnPatterns

    # Process queued up segment updates, now that we have bottom-up, we
    # can update the permanences on the cells that we predicted to turn on
    # and did receive bottom-up
    self.processSegmentUpdates(activeColumns)

    # Decrement the PAM counter if it is running and increment our learned
    # sequence length
    if self.pamCounter > 0:
      self.pamCounter -= 1
    self.learnedSeqLength += 1

    # Phase 1 - turn on the predicted cell in each column that received
    # bottom-up. If there was no predicted cell, pick one to learn to.
    if not self.resetCalled:
      # Uses lrnActiveState['t-1'] and lrnPredictedState['t-1']
      # computes lrnActiveState['t']
      inSequence = self.learnPhase1(activeColumns)

      # Reset our PAM counter if we are in sequence
      if inSequence:
        self.pamCounter = self.pamLength

    # Print status of PAM counter, learned sequence length
    if self.verbosity >= 3:
      print "pamCounter = ", self.pamCounter, "seqLength = ", \
          self.learnedSeqLength

    # Start over on start cells if any of the following occur:
    #  1.) A reset was just called
    #  2.) We have been loo long out of sequence (the pamCounter has expired)
    #  3.) We have reached maximum allowed sequence length.
    #
    # Note that, unless we are following a reset, we also just learned or
    # re-enforced connections to the current set of active columns because
    # this input is still a valid prediction to learn.
    #
    # It is especially helpful to learn the connections to this input when
    # you have a maxSeqLength constraint in place. Otherwise, you will have
    # no continuity at all between sub-sequences of length maxSeqLength.
    if (self.resetCalled or self.pamCounter == 0 or
        (self.maxSeqLength != 0 and
         self.learnedSeqLength >= self.maxSeqLength)):
      if  self.verbosity >= 3:
        if self.resetCalled:
          print "Starting over:", activeColumns, "(reset was called)"
        elif self.pamCounter == 0:
          print "Starting over:", activeColumns, "(PAM counter expired)"
        else:
          print "Starting over:", activeColumns, "(reached maxSeqLength)"

      # Update average learned sequence length - this is a diagnostic statistic
      if self.pamCounter == 0:
        seqLength = self.learnedSeqLength - self.pamLength
      else:
        seqLength = self.learnedSeqLength
      if  self.verbosity >= 3:
        print "  learned sequence length was:", seqLength
      self._updateAvgLearnedSeqLength(seqLength)

      # Backtrack to an earlier starting point, if we find one
      backSteps = 0
      if not self.resetCalled:
        backSteps = self.learnBacktrack()

      # Start over in the current time step if reset was called, or we couldn't
      # backtrack.
      if self.resetCalled or backSteps == 0:
        self.lrnActiveState['t'].fill(0)
        for c in activeColumns:
          self.lrnActiveState['t'][c, 0] = 1

        # Remove any old input history patterns
        self._prevLrnPatterns = []

      # Reset PAM counter
      self.pamCounter =  self.pamLength
      self.learnedSeqLength = backSteps

      # Clear out any old segment updates from prior sequences
      self.segmentUpdates = {}

    # Phase 2 - Compute new predicted state. When computing predictions for
    # phase 2, we predict at  most one cell per column (the one with the best
    # matching segment).
    self.learnPhase2()


  def compute(self, bottomUpInput, enableLearn, computeInfOutput=None):
    """
    Handle one compute, possibly learning.

    @param bottomUpInput     The bottom-up input, typically from a spatial pooler
    @param enableLearn       If true, perform learning
    @param computeInfOutput  If None, default behavior is to disable the inference
                             output when enableLearn is on.
                             If true, compute the inference output
                             If false, do not compute the inference output

    @returns TODO: document

    It is an error to have both enableLearn and computeInfOutput set to False

    By default, we don't compute the inference output when learning because it
    slows things down, but you can override this by passing in True for
    computeInfOutput
    """
    # As a speed optimization for now (until we need online learning), skip
    # computing the inference output while learning
    if computeInfOutput is None:
      if enableLearn:
        computeInfOutput = False
      else:
        computeInfOutput = True

    assert (enableLearn or computeInfOutput)

    # Get the list of columns that have bottom-up
    activeColumns = bottomUpInput.nonzero()[0]
    if enableLearn:
      self.lrnIterationIdx += 1
    self.iterationIdx +=  1

    if self.verbosity >= 3:
      print "\n==== PY Iteration: %d =====" % (self.iterationIdx)
      print "Active cols:", activeColumns

    # Update segment duty cycles if we are crossing a "tier"
    # We determine if it's time to update the segment duty cycles. Since the
    # duty cycle calculation is a moving average based on a tiered alpha, it is
    # important that we update all segments on each tier boundary
    if enableLearn:
      if self.lrnIterationIdx in Segment.dutyCycleTiers:
        for c, i in itertools.product(xrange(self.numberOfCols),
                                      xrange(self.cellsPerColumn)):
          for segment in self.cells[c][i]:
            segment.dutyCycle()

    # Update the average input density
    if self.avgInputDensity is None:
      self.avgInputDensity = len(activeColumns)
    else:
      self.avgInputDensity = (0.99 * self.avgInputDensity +
                              0.01 * len(activeColumns))

    # First, update the inference state
    # As a speed optimization for now (until we need online learning), skip
    # computing the inference output while learning
    if computeInfOutput:
      self.updateInferenceState(activeColumns)

    # Next, update the learning state
    if enableLearn:
      self.updateLearningState(activeColumns)

      # Apply global decay, and remove synapses and/or segments.
      # Synapses are removed if their permanence value is <= 0.
      # Segments are removed when they don't have synapses anymore.
      # Removal of synapses can trigger removal of whole segments!
      # todo: isolate the synapse/segment retraction logic so that
      # it can be called in adaptSegments, in the case where we
      # do global decay only episodically.
      if self.globalDecay > 0.0 and ((self.lrnIterationIdx % self.maxAge) == 0):
        for c, i in itertools.product(xrange(self.numberOfCols),
                                      xrange(self.cellsPerColumn)):

          segsToDel = [] # collect and remove outside the loop
          for segment in self.cells[c][i]:
            age = self.lrnIterationIdx - segment.lastActiveIteration
            if age <= self.maxAge:
              continue

            synsToDel = [] # collect and remove outside the loop
            for synapse in segment.syns:

              synapse[2] = synapse[2] - self.globalDecay # decrease permanence

              if synapse[2] <= 0:
                synsToDel.append(synapse) # add to list to delete

            # 1 for sequenceSegment flag
            if len(synsToDel) == segment.getNumSynapses():
              segsToDel.append(segment) # will remove the whole segment
            elif len(synsToDel) > 0:
              for syn in synsToDel: # remove some synapses on segment
                segment.syns.remove(syn)

          for seg in segsToDel: # remove some segments of this cell
            self.cleanUpdatesList(c, i, seg)
            self.cells[c][i].remove(seg)

    # Update the prediction score stats
    # Learning always includes inference
    if self.collectStats:
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


  def infer(self, bottomUpInput):
    """
    @todo document
    """
    return self.compute(bottomUpInput, enableLearn=False)


  def learn(self, bottomUpInput, computeInfOutput=None):
    """
    @todo document
    """
    return self.compute(bottomUpInput, enableLearn=True,
                        computeInfOutput=computeInfOutput)


  def updateSegmentDutyCycles(self):
    """
    This gets called on every compute. It determines if it's time to
    update the segment duty cycles. Since the duty cycle calculation is a
    moving average based on a tiered alpha, it is important that we update
    all segments on each tier boundary.
    """
    if self.lrnIterationIdx not in [100, 1000, 10000]:
      return

    for c, i in itertools.product(xrange(self.numberOfCols),
                                  xrange(self.cellsPerColumn)):
      for segment in self.cells[c][i]:
        segment.dutyCycle()


  def columnConfidences(self, cellConfidences=None):
    """
    Compute the column confidences given the cell confidences. If
    None is passed in for cellConfidences, it uses the stored cell confidences
    from the last compute.

    @param cellConfidences Cell confidences to use, or None to use the
                           the current cell confidences.

    @returns Column confidence scores
    """
    return self.colConfidence['t']


  def topDownCompute(self, topDownIn=None):
    """
    Top-down compute - generate expected input given output of the TP

    @param topDownIn top down input from the level above us

    @returns best estimate of the TP input that would have generated bottomUpOut.
    """
    # For now, we will assume there is no one above us and that bottomUpOut is
    # simply the output that corresponds to our currently stored column
    # confidences.

    # Simply return the column confidences
    return self.columnConfidences()


  def trimSegmentsInCell(self, colIdx, cellIdx, segList, minPermanence,
                         minNumSyns):
    """
    This method goes through a list of segments for a given cell and
    deletes all synapses whose permanence is less than minPermanence and deletes
    any segments that have less than minNumSyns synapses remaining.

    @param colIdx        Column index
    @param cellIdx       Cell index within the column
    @param segList       List of segment references
    @param minPermanence Any syn whose permamence is 0 or < minPermanence will
                         be deleted.
    @param minNumSyns    Any segment with less than minNumSyns synapses remaining
                         in it will be deleted.

    @returns tuple (numSegsRemoved, numSynsRemoved)
    """
    # Fill in defaults
    if minPermanence is None:
      minPermanence = self.connectedPerm
    if minNumSyns is None:
      minNumSyns = self.activationThreshold

    # Loop through all segments
    nSegsRemoved, nSynsRemoved = 0, 0
    segsToDel = [] # collect and remove segments outside the loop
    for segment in segList:

      # List if synapses to delete
      synsToDel = [syn for syn in segment.syns if syn[2] < minPermanence]

      if len(synsToDel) == len(segment.syns):
        segsToDel.append(segment) # will remove the whole segment
      else:
        if len(synsToDel) > 0:
          for syn in synsToDel: # remove some synapses on segment
            segment.syns.remove(syn)
            nSynsRemoved += 1
        if len(segment.syns) < minNumSyns:
          segsToDel.append(segment)

    # Remove segments that don't have enough synapses and also take them
    # out of the segment update list, if they are in there
    nSegsRemoved += len(segsToDel)
    for seg in segsToDel: # remove some segments of this cell
      self.cleanUpdatesList(colIdx, cellIdx, seg)
      self.cells[colIdx][cellIdx].remove(seg)
      nSynsRemoved += len(seg.syns)

    return nSegsRemoved, nSynsRemoved


  def trimSegments(self, minPermanence=None, minNumSyns=None):
    """
    This method deletes all synapses whose permanence is less than
    minPermanence and deletes any segments that have less than
    minNumSyns synapses remaining.

    @param minPermanence Any syn whose permamence is 0 or < minPermanence will
                         be deleted. If None is passed in, then
                         self.connectedPerm is used.
    @param minNumSyns    Any segment with less than minNumSyns synapses remaining
                         in it will be deleted. If None is passed in, then
                         self.activationThreshold is used.
    @returns             tuple (numSegsRemoved, numSynsRemoved)
    """
    # Fill in defaults
    if minPermanence is None:
      minPermanence = self.connectedPerm
    if minNumSyns is None:
      minNumSyns = self.activationThreshold

    # Loop through all cells
    totalSegsRemoved, totalSynsRemoved = 0, 0
    for c, i in itertools.product(xrange(self.numberOfCols),
                                  xrange(self.cellsPerColumn)):

      (segsRemoved, synsRemoved) = self.trimSegmentsInCell(
          colIdx=c, cellIdx=i, segList=self.cells[c][i],
          minPermanence=minPermanence, minNumSyns=minNumSyns)
      totalSegsRemoved += segsRemoved
      totalSynsRemoved += synsRemoved

    # Print all cells if verbosity says to
    if self.verbosity >= 5:
      print "Cells, all segments:"
      self.printCells(predictedOnly=False)

    return totalSegsRemoved, totalSynsRemoved


  def cleanUpdatesList(self, col, cellIdx, seg):
    """
    Removes any update that would be for the given col, cellIdx, segIdx.
    
    NOTE: logically, we need to do this when we delete segments, so that if
    an update refers to a segment that was just deleted, we also remove
    that update from the update list. However, I haven't seen it trigger
    in any of the unit tests yet, so it might mean that it's not needed
    and that situation doesn't occur, by construction.
    """
    # TODO: check if the situation described in the docstring above actually 
    #       occurs.
    for key, updateList in self.segmentUpdates.iteritems():
      c, i = key[0], key[1]
      if c == col and i == cellIdx:
        for update in updateList:
          if update[1].segment == seg:
            self.removeSegmentUpdate(update)


  def finishLearning(self):
    """
    Called when learning has been completed. This method just calls
    trimSegments(). (finishLearning is here for backward compatibility)
    """
    # Keep weakly formed synapses around because they contain confidence scores
    # for paths out of learned sequenced and produce a better prediction than
    # chance.
    self.trimSegments(minPermanence=0.0001)

    # Update all cached duty cycles for better performance right after loading
    # in the trained network.
    for c, i in itertools.product(xrange(self.numberOfCols),
                                  xrange(self.cellsPerColumn)):
      for segment in self.cells[c][i]:
        segment.dutyCycle()

    # For error checking purposes, make sure no start cell has incoming
    # connections
    if self.cellsPerColumn > 1:
      for c in xrange(self.numberOfCols):
        assert self.getNumSegmentsInCell(c, 0) == 0


  def checkPrediction2(self, patternNZs, output=None, colConfidence=None,
                       details=False):
    """ 
    This function will replace checkPrediction.

    This function produces goodness-of-match scores for a set of input patterns,
    by checking for their presence in the current and predicted output of the
    TP. Returns a global count of the number of extra and missing bits, the
    confidence scores for each input pattern, and (if requested) the
    bits in each input pattern that were not present in the TP's prediction.

    @param patternNZs a list of input patterns that we want to check for. Each
                      element is a list of the non-zeros in that pattern.
    @param output     The output of the TP. If not specified, then use the
                      TP's current output. This can be specified if you are
                      trying to check the prediction metric for an output from
                      the past.
    @param colConfidence The column confidences. If not specified, then use the
                         TP's current self.colConfidence. This can be specified if you
                         are trying to check the prediction metrics for an output
                         from the past.
    @param details    if True, also include details of missing bits per pattern.

    @returns  list containing:

              [
                totalExtras,
                totalMissing,
                [conf_1, conf_2, ...],
                [missing1, missing2, ...]
              ]

    @retval totalExtras a global count of the number of 'extras', i.e. bits that
                        are on in the current output but not in the or of all the
                        passed in patterns
    @retval totalMissing a global count of all the missing bits, i.e. the bits 
                         that are on in the or of the patterns, but not in the 
                         current output
    @retval conf_i the confidence score for the i'th pattern inpatternsToCheck
                   This consists of 3 items as a tuple:
                   (predictionScore, posPredictionScore, negPredictionScore)
    @retval missing_i the bits in the i'th pattern that were missing
                      in the output. This list is only returned if details is 
                      True.
    """

    # TODO: Add option to check predictedState only.

    # Get the non-zeros in each pattern
    numPatterns = len(patternNZs)

    # Compute the union of all the expected patterns
    orAll = set()
    orAll = orAll.union(*patternNZs)

    # Get the list of active columns in the output
    if output is None:
      assert self.currentOutput is not None
      output = self.currentOutput
    output = set(output.sum(axis=1).nonzero()[0])

    # Compute the total extra and missing in the output
    totalExtras = len(output.difference(orAll))
    totalMissing = len(orAll.difference(output))

    # Get the percent confidence level per column by summing the confidence
    # levels of the cells in the column. During training, each segment's
    # confidence number is computed as a running average of how often it
    # correctly predicted bottom-up activity on that column. A cell's
    # confidence number is taken from the first active segment found in the
    # cell. Note that confidence will only be non-zero for predicted columns.
    if colConfidence is None:
      colConfidence = self.colConfidence['t']

    # Assign confidences to each pattern
    confidences = []
    for i in xrange(numPatterns):
      # Sum of the column confidences for this pattern
      positivePredictionSum = colConfidence[patternNZs[i]].sum()
      # How many columns in this pattern
      positiveColumnCount   = len(patternNZs[i])

      # Sum of all the column confidences
      totalPredictionSum    = colConfidence.sum()
      # Total number of columns
      totalColumnCount      = len(colConfidence)

      negativePredictionSum = totalPredictionSum - positivePredictionSum
      negativeColumnCount   = totalColumnCount   - positiveColumnCount

      # Compute the average confidence score per column for this pattern
      if positiveColumnCount != 0:
        positivePredictionScore = positivePredictionSum
      else:
        positivePredictionScore = 0.0

      # Compute the average confidence score per column for the other patterns
      if negativeColumnCount != 0:
        negativePredictionScore = negativePredictionSum
      else:
        negativePredictionScore = 0.0

      # Scale the positive and negative prediction scores so that they sum to
      # 1.0
      currentSum = negativePredictionScore + positivePredictionScore
      if currentSum > 0:
        positivePredictionScore *= 1.0/currentSum
        negativePredictionScore *= 1.0/currentSum

      predictionScore = positivePredictionScore - negativePredictionScore

      confidences.append((predictionScore,
                          positivePredictionScore,
                          negativePredictionScore))

    # Include detail? (bits in each pattern that were missing from the output)
    if details:
      missingPatternBits = [set(pattern).difference(output)
                            for pattern in patternNZs]

      return (totalExtras, totalMissing, confidences, missingPatternBits)
    else:
      return (totalExtras, totalMissing, confidences)


  def isSegmentActive(self, seg, activeState):
    """
    A segment is active if it has >= activationThreshold connected
    synapses that are active due to activeState.

    Notes: studied various cutoffs, none of which seem to be worthwhile
           list comprehension didn't help either

    @param seg TODO: document
    @param activeState TODO: document
    """
    # Computing in C - *much* faster
    return isSegmentActive(seg.syns, activeState,
                           self.connectedPerm, self.activationThreshold)


  def getSegmentActivityLevel(self, seg, activeState,
                              connectedSynapsesOnly=False):
    """
    This routine computes the activity level of a segment given activeState.
    It can tally up only connected synapses (permanence >= connectedPerm), or
    all the synapses of the segment, at either t or t-1.

    @param seg TODO: document
    @param activeState TODO: document
    @param connectedSynapsesOnly TODO: document
    """
    # Computing in C - *much* faster
    return getSegmentActivityLevel(seg.syns, activeState, connectedSynapsesOnly,
                                   self.connectedPerm)


  def getBestMatchingCell(self, c, activeState, minThreshold):
    """
    Find weakly activated cell in column with at least minThreshold active
    synapses.

    @param c            which column to look at
    @param activeState  the active cells
    @param minThreshold minimum number of synapses required

    @returns tuple (cellIdx, segment, numActiveSynapses)
    """
    # Collect all cells in column c that have at least minThreshold in the most
    # activated segment
    bestActivityInCol = minThreshold
    bestSegIdxInCol = -1
    bestCellInCol = -1

    for i in xrange(self.cellsPerColumn):

      maxSegActivity = 0
      maxSegIdx = 0

      for j, s in enumerate(self.cells[c][i]):

        activity = self.getSegmentActivityLevel(s, activeState)

        if activity > maxSegActivity:
          maxSegActivity = activity
          maxSegIdx = j

      if maxSegActivity >= bestActivityInCol:
        bestActivityInCol = maxSegActivity
        bestSegIdxInCol = maxSegIdx
        bestCellInCol = i

    if bestCellInCol == -1:
      return (None, None, None)
    else:
      return (bestCellInCol, self.cells[c][bestCellInCol][bestSegIdxInCol],
                bestActivityInCol)


  def getBestMatchingSegment(self, c, i, activeState):
    """
    For the given cell, find the segment with the largest number of active
    synapses. This routine is aggressive in finding the best match. The
    permanence value of synapses is allowed to be below connectedPerm. The number
    of active synapses is allowed to be below activationThreshold, but must be
    above minThreshold. The routine returns the segment index. If no segments are
    found, then an index of -1 is returned.

    @param c TODO: document
    @param i TODO: document
    @param activeState TODO: document
    """
    maxActivity, which = self.minThreshold, -1

    for j, s in enumerate(self.cells[c][i]):
      activity = self.getSegmentActivityLevel(s, activeState,
                                              connectedSynapsesOnly=False)

      if activity >= maxActivity:
        maxActivity, which = activity, j

    if which == -1:
      return None
    else:
      return self.cells[c][i][which]


  def getCellForNewSegment(self, colIdx):
    """
    Return the index of a cell in this column which is a good candidate
    for adding a new segment.

    When we have fixed size resources in effect, we insure that we pick a
    cell which does not already have the max number of allowed segments. If
    none exists, we choose the least used segment in the column to re-allocate.

    @param colIdx which column to look at
    @returns cell index
    """
    # Not fixed size CLA, just choose a cell randomly
    if self.maxSegmentsPerCell < 0:
      if self.cellsPerColumn > 1:
        # Don't ever choose the start cell (cell # 0) in each column
        i = self._random.getUInt32(self.cellsPerColumn-1) + 1
      else:
        i = 0
      return i

    # Fixed size CLA, choose from among the cells that are below the maximum
    # number of segments.
    # NOTE: It is important NOT to always pick the cell with the fewest number
    # of segments. The reason is that if we always do that, we are more likely
    # to run into situations where we choose the same set of cell indices to
    # represent an 'A' in both context 1 and context 2. This is because the
    # cell indices we choose in each column of a pattern will advance in
    # lockstep (i.e. we pick cell indices of 1, then cell indices of 2, etc.).
    candidateCellIdxs = []
    if self.cellsPerColumn == 1:
      minIdx = 0
      maxIdx = 0
    else:
      minIdx = 1                      # Don't include startCell in the mix
      maxIdx = self.cellsPerColumn-1
    for i in xrange(minIdx, maxIdx+1):
      numSegs = len(self.cells[colIdx][i])
      if numSegs < self.maxSegmentsPerCell:
        candidateCellIdxs.append(i)

    # If we found one, return with it. Note we need to use _random to maintain
    # correspondence with CPP code.
    if len(candidateCellIdxs) > 0:
      #candidateCellIdx = random.choice(candidateCellIdxs)
      candidateCellIdx = (
          candidateCellIdxs[self._random.getUInt32(len(candidateCellIdxs))])
      if self.verbosity >= 5:
        print "Cell [%d,%d] chosen for new segment, # of segs is %d" % (
            colIdx, candidateCellIdx, len(self.cells[colIdx][candidateCellIdx]))
      return candidateCellIdx

    # All cells in the column are full, find a segment to free up
    candidateSegment = None
    candidateSegmentDC = 1.0
    # For each cell in this column
    for i in xrange(minIdx, maxIdx+1):
      # For each segment in this cell
      for s in self.cells[colIdx][i]:
        dc = s.dutyCycle()
        if dc < candidateSegmentDC:
          candidateCellIdx = i
          candidateSegmentDC = dc
          candidateSegment = s

    # Free up the least used segment
    if self.verbosity >= 5:
      print ("Deleting segment #%d for cell[%d,%d] to make room for new "
             "segment" % (candidateSegment.segID, colIdx, candidateCellIdx))
      candidateSegment.debugPrint()
    self.cleanUpdatesList(colIdx, candidateCellIdx, candidateSegment)
    self.cells[colIdx][candidateCellIdx].remove(candidateSegment)
    return candidateCellIdx


  def getSegmentActiveSynapses(self, c, i, s, activeState, newSynapses=False):
    """
    Return a segmentUpdate data structure containing a list of proposed
    changes to segment s. Let activeSynapses be the list of active synapses
    where the originating cells have their activeState output = 1 at time step
    t. (This list is empty if s is None since the segment doesn't exist.)
    newSynapses is an optional argument that defaults to false. If newSynapses
    is true, then newSynapseCount - len(activeSynapses) synapses are added to
    activeSynapses. These synapses are randomly chosen from the set of cells
    that have learnState = 1 at timeStep.

    @param c TODO: document
    @param i TODO: document
    @param s TODO: document
    @param activeState TODO: document
    @param newSynapses TODO: document
    """
    activeSynapses = []

    if s is not None: # s can be None, if adding a new segment
      # Here we add *integers* to activeSynapses
      activeSynapses = [idx for idx, syn in enumerate(s.syns) \
                        if activeState[syn[0], syn[1]]]

    if newSynapses: # add a few more synapses

      nSynapsesToAdd = self.newSynapseCount - len(activeSynapses)

      # Here we add *pairs* (colIdx, cellIdx) to activeSynapses
      activeSynapses += self.chooseCellsToLearnFrom(c, i, s, nSynapsesToAdd,
                                                    activeState)

    # It's still possible that activeSynapses is empty, and this will
    # be handled in addToSegmentUpdates

    # NOTE: activeSynapses contains a mixture of integers and pairs of integers
    # - integers are indices of synapses already existing on the segment,
    #   that we will need to update.
    # - pairs represent source (colIdx, cellIdx) of new synapses to create on
    #   the segment
    update = TP.SegmentUpdate(c, i, s, activeSynapses)

    return update


  def chooseCellsToLearnFrom(self, c, i, s, n, activeState):
    """
    Choose n random cells to learn from.

    This function is called several times while learning with timeStep = t-1, so
    we cache the set of candidates for that case. It's also called once with
    timeStep = t, and we cache that set of candidates.

    @returns tuple (column index, cell index).
    """
    if n <= 0:
      return []

    tmpCandidates = numpy.where(activeState == 1)

    # Candidates can be empty at this point, in which case we return
    # an empty segment list. adaptSegments will do nothing when getting
    # that list.
    if len(tmpCandidates[0]) == 0:
      return []

    if s is None: # new segment
      cands = [syn for syn in zip(tmpCandidates[0], tmpCandidates[1])]
    else:
      # We exclude any synapse that is already in this segment.
      synapsesAlreadyInSegment = set((syn[0], syn[1]) for syn in s.syns)
      cands = [syn for syn in zip(tmpCandidates[0], tmpCandidates[1])
               if (syn[0], syn[1]) not in synapsesAlreadyInSegment]

    # If we have no more candidates than requested, return all of them,
    # no shuffle necessary.
    if len(cands) <= n:
      return cands

    if n == 1: # so that we don't shuffle if only one is needed
      idx = self._random.getUInt32(len(cands))
      return [cands[idx]]  # col and cell idx in col

    # If we need more than one candidate
    indices = numpy.array([j for j in range(len(cands))], dtype='uint32')
    tmp = numpy.zeros(min(n, len(indices)), dtype='uint32')
    self._random.sample(indices, tmp)
    return sorted([cands[j] for j in tmp])


  def processSegmentUpdates(self, activeColumns):
    """
    Go through the list of accumulated segment updates and process them
    as follows:

    if the segment update is too old, remove the update
    else if the cell received bottom-up, update its permanences
    else if it's still being predicted, leave it in the queue
    else remove it.

    @param activeColumns TODO: document
    """
    # The segmentUpdates dict has keys which are the column,cellIdx of the
    # owner cell. The values are lists of segment updates for that cell
    removeKeys = []
    trimSegments = []
    for key, updateList in self.segmentUpdates.iteritems():

      # Get the column number and cell index of the owner cell
      c, i = key[0], key[1]

      # If the cell received bottom-up, update its segments
      if c in activeColumns:
        action = 'update'

      # If not, either keep it around if it's still predicted, or remove it
      else:
        # If it is still predicted, and we are pooling, keep it around
        if self.doPooling and self.lrnPredictedState['t'][c, i] == 1:
          action = 'keep'
        else:
          action = 'remove'

      # Process each segment for this cell. Each segment entry contains
      # [creationDate, SegmentInfo]
      updateListKeep = []
      if action != 'remove':
        for (createDate, segUpdate) in updateList:

          if self.verbosity >= 4:
            print "_nLrnIterations =", self.lrnIterationIdx,
            print segUpdate

          # If this segment has expired. Ignore this update (and hence remove it
          # from list)
          if self.lrnIterationIdx - createDate > self.segUpdateValidDuration:
            continue

          if action == 'update':
            trimSegment = self.adaptSegment(segUpdate)
            if trimSegment:
              trimSegments.append((segUpdate.columnIdx, segUpdate.cellIdx,
                                        segUpdate.segment))
          else:
            # Keep segments that haven't expired yet (the cell is still being
            #   predicted)
            updateListKeep.append((createDate, segUpdate))

      self.segmentUpdates[key] = updateListKeep
      if len(updateListKeep) == 0:
        removeKeys.append(key)

    # Clean out empty segment updates
    for key in removeKeys:
      self.segmentUpdates.pop(key)

    # Trim segments that had synapses go to 0
    for (c, i, segment) in trimSegments:
      self.trimSegmentsInCell(c, i, [segment], minPermanence = 0.00001,
              minNumSyns = 0)


  def adaptSegment(self, segUpdate):
    """
    This function applies segment update information to a segment in a
    cell.

    Synapses on the active list get their permanence counts incremented by
    permanenceInc. All other synapses get their permanence counts decremented
    by permanenceDec.

    We also increment the positiveActivations count of the segment.

    @param segUpdate SegmentUpdate instance
    @returns True if some synapses were decremented to 0 and the segment is a 
             candidate for trimming
    """
    # This will be set to True if detect that any syapses were decremented to
    #  0
    trimSegment = False

    # segUpdate.segment is None when creating a new segment
    c, i, segment = segUpdate.columnIdx, segUpdate.cellIdx, segUpdate.segment

    # update.activeSynapses can be empty.
    # If not, it can contain either or both integers and tuples.
    # The integers are indices of synapses to update.
    # The tuples represent new synapses to create (src col, src cell in col).
    # We pre-process to separate these various element types.
    # synToCreate is not empty only if positiveReinforcement is True.
    # NOTE: the synapse indices start at *1* to skip the segment flags.
    activeSynapses = segUpdate.activeSynapses
    synToUpdate = set([syn for syn in activeSynapses if type(syn) == int])

    # Modify an existing segment
    if segment is not None:

      if self.verbosity >= 4:
        print "Reinforcing segment #%d for cell[%d,%d]" % (segment.segID, c, i)
        print "  before:",
        segment.debugPrint()

      # Mark it as recently useful
      segment.lastActiveIteration = self.lrnIterationIdx

      # Update frequency and positiveActivations
      segment.positiveActivations += 1       # positiveActivations += 1
      segment.dutyCycle(active=True)

      # First, decrement synapses that are not active
      # s is a synapse *index*, with index 0 in the segment being the tuple
      # (segId, sequence segment flag). See below, creation of segments.
      lastSynIndex = len(segment.syns) - 1
      inactiveSynIndices = [s for s in xrange(0, lastSynIndex+1) \
                            if s not in synToUpdate]
      trimSegment = segment.updateSynapses(inactiveSynIndices,
                                           -self.permanenceDec)

      # Now, increment active synapses
      activeSynIndices = [syn for syn in synToUpdate if syn <= lastSynIndex]
      segment.updateSynapses(activeSynIndices, self.permanenceInc)

      # Finally, create new synapses if needed
      # syn is now a tuple (src col, src cell)
      synsToAdd = [syn for syn in activeSynapses if type(syn) != int]
      # If we have fixed resources, get rid of some old syns if necessary
      if self.maxSynapsesPerSegment > 0 \
          and len(synsToAdd) + len(segment.syns) > self.maxSynapsesPerSegment:
        numToFree = (len(segment.syns) + len(synsToAdd) -
                     self.maxSynapsesPerSegment)
        segment.freeNSynapses(numToFree, inactiveSynIndices, self.verbosity)
      for newSyn in synsToAdd:
        segment.addSynapse(newSyn[0], newSyn[1], self.initialPerm)

      if self.verbosity >= 4:
        print "   after:",
        segment.debugPrint()

    # Create a new segment
    else:

      # (segID, sequenceSegment flag, frequency, positiveActivations,
      #          totalActivations, lastActiveIteration)
      newSegment = Segment(tp=self, isSequenceSeg=segUpdate.sequenceSegment)

      # numpy.float32 important so that we can match with C++
      for synapse in activeSynapses:
        newSegment.addSynapse(synapse[0], synapse[1], self.initialPerm)

      if self.verbosity >= 3:
        print "New segment #%d for cell[%d,%d]" % (self.segID-1, c, i),
        newSegment.debugPrint()

      self.cells[c][i].append(newSegment)

    return trimSegment


  def getSegmentInfo(self, collectActiveData = False):
    """Returns information about the distribution of segments, synapses and
    permanence values in the current TP. If requested, also returns information
    regarding the number of currently active segments and synapses.

    @returns tuple described below:

        (
          nSegments,
          nSynapses,
          nActiveSegs,
          nActiveSynapses,
          distSegSizes,
          distNSegsPerCell,
          distPermValues,
          distAges
        )

    @retval nSegments        total number of segments
    @retval nSynapses        total number of synapses
    @retval nActiveSegs      total no. of active segments (0 if collectActiveData
                             is False)
    @retval nActiveSynapses  total no. of active synapses 0 if collectActiveData
                             is False
    @retval distSegSizes     a dict where d[n] = number of segments with n synapses
    @retval distNSegsPerCell a dict where d[n] = number of cells with n segments
    @retval distPermValues   a dict where d[p] = number of synapses with perm = p/10
    @retval distAges         a list of tuples (ageRange, numSegments)
    """
    nSegments, nSynapses = 0, 0
    nActiveSegs, nActiveSynapses = 0, 0
    distSegSizes, distNSegsPerCell = {}, {}
    distPermValues = {}   # Num synapses with given permanence values

    numAgeBuckets = 20
    distAges = []
    ageBucketSize = int((self.lrnIterationIdx+20) / 20)
    for i in range(numAgeBuckets):
      distAges.append(['%d-%d' % (i*ageBucketSize, (i+1)*ageBucketSize-1), 0])

    for c in xrange(self.numberOfCols):
      for i in xrange(self.cellsPerColumn):

        if len(self.cells[c][i]) > 0:
          nSegmentsThisCell = len(self.cells[c][i])
          nSegments += nSegmentsThisCell
          if distNSegsPerCell.has_key(nSegmentsThisCell):
            distNSegsPerCell[nSegmentsThisCell] += 1
          else:
            distNSegsPerCell[nSegmentsThisCell] = 1
          for seg in self.cells[c][i]:
            nSynapsesThisSeg = seg.getNumSynapses()
            nSynapses += nSynapsesThisSeg
            if distSegSizes.has_key(nSynapsesThisSeg):
              distSegSizes[nSynapsesThisSeg] += 1
            else:
              distSegSizes[nSynapsesThisSeg] = 1

            # Accumulate permanence value histogram
            for syn in seg.syns:
              p = int(syn[2]*10)
              if distPermValues.has_key(p):
                distPermValues[p] += 1
              else:
                distPermValues[p] = 1

            # Accumulate segment age histogram
            age = self.lrnIterationIdx - seg.lastActiveIteration
            ageBucket = int(age/ageBucketSize)
            distAges[ageBucket][1] += 1

            # Get active synapse statistics if requested
            if collectActiveData:
              if self.isSegmentActive(seg, self.infActiveState['t']):
                nActiveSegs += 1
              for syn in seg.syns:
                if self.activeState['t'][syn[0]][syn[1]] == 1:
                  nActiveSynapses += 1

    return (nSegments, nSynapses, nActiveSegs, nActiveSynapses,
            distSegSizes, distNSegsPerCell, distPermValues, distAges)



class Segment(object):
  """
  The Segment class is a container for all of the segment variables and
  the synapses it owns.
  """

  ## These are iteration count tiers used when computing segment duty cycle.
  dutyCycleTiers =  [0,       100,      320,    1000,
                     3200,    10000,    32000,  100000,
                     320000]

  ## This is the alpha used in each tier. dutyCycleAlphas[n] is used when
  #  `iterationIdx > dutyCycleTiers[n]`.
  dutyCycleAlphas = [None,    0.0032,    0.0010,  0.00032,
                     0.00010, 0.000032,  0.00001, 0.0000032,
                     0.0000010]


  def __init__(self, tp, isSequenceSeg):
    self.tp = tp
    self.segID = tp.segID
    tp.segID += 1

    self.isSequenceSeg = isSequenceSeg
    self.lastActiveIteration = tp.lrnIterationIdx

    self.positiveActivations = 1
    self.totalActivations = 1

    # These are internal variables used to compute the positive activations
    #  duty cycle.
    # Callers should use dutyCycle()
    self._lastPosDutyCycle = 1.0 / tp.lrnIterationIdx
    self._lastPosDutyCycleIteration = tp.lrnIterationIdx

    # Each synapse is a tuple (srcCellCol, srcCellIdx, permanence)
    self.syns = []


  def __ne__(self, s):
    return not self == s


  def __eq__(self, s):
    d1 = self.__dict__
    d2 = s.__dict__
    if set(d1) != set(d2):
      return False
    for k, v in d1.iteritems():
      if k in ('tp',):
        continue
      elif v != d2[k]:
        return False
    return True


  def dutyCycle(self, active=False, readOnly=False):
    """Compute/update and return the positive activations duty cycle of
    this segment. This is a measure of how often this segment is
    providing good predictions.

    @param active   True if segment just provided a good prediction
    
    @param readOnly If True, compute the updated duty cycle, but don't change
               the cached value. This is used by debugging print statements.

    @returns The duty cycle, a measure of how often this segment is
    providing good predictions.

    **NOTE:** This method relies on different schemes to compute the duty cycle
    based on how much history we have. In order to support this tiered
    approach **IT MUST BE CALLED ON EVERY SEGMENT AT EACH DUTY CYCLE TIER**
    (@ref dutyCycleTiers).

    When we don't have a lot of history yet (first tier), we simply return
    number of positive activations / total number of iterations

    After a certain number of iterations have accumulated, it converts into
    a moving average calculation, which is updated only when requested
    since it can be a bit expensive to compute on every iteration (it uses
    the pow() function).

    The duty cycle is computed as follows:

        dc[t] = (1-alpha) * dc[t-1] + alpha * value[t]

    If the value[t] has been 0 for a number of steps in a row, you can apply
    all of the updates at once using:

        dc[t] = (1-alpha)^(t-lastT) * dc[lastT]

    We use the alphas and tiers as defined in @ref dutyCycleAlphas and
    @ref dutyCycleTiers.
    """
    # For tier #0, compute it from total number of positive activations seen
    if self.tp.lrnIterationIdx <= self.dutyCycleTiers[1]:
      dutyCycle = float(self.positiveActivations) \
                                    / self.tp.lrnIterationIdx
      if not readOnly:
        self._lastPosDutyCycleIteration = self.tp.lrnIterationIdx
        self._lastPosDutyCycle = dutyCycle
      return dutyCycle

    # How old is our update?
    age = self.tp.lrnIterationIdx - self._lastPosDutyCycleIteration

    # If it's already up to date, we can returned our cached value.
    if age == 0 and not active:
      return self._lastPosDutyCycle

    # Figure out which alpha we're using
    for tierIdx in range(len(self.dutyCycleTiers)-1, 0, -1):
      if self.tp.lrnIterationIdx > self.dutyCycleTiers[tierIdx]:
        alpha = self.dutyCycleAlphas[tierIdx]
        break

    # Update duty cycle
    dutyCycle = pow(1.0-alpha, age) * self._lastPosDutyCycle
    if active:
      dutyCycle += alpha

    # Update cached values if not read-only
    if not readOnly:
      self._lastPosDutyCycleIteration = self.tp.lrnIterationIdx
      self._lastPosDutyCycle = dutyCycle

    return dutyCycle


  def debugPrint(self):
    """Print segment information for verbose messaging and debugging.
    This uses the following format:

     ID:54413 True 0.64801 (24/36) 101 [9,1]0.75 [10,1]0.75 [11,1]0.75

    where:
      54413 - is the unique segment id
      True - is sequence segment
      0.64801 - moving average duty cycle
      (24/36) - (numPositiveActivations / numTotalActivations)
      101 - age, number of iterations since last activated
      [9,1]0.75 - synapse from column 9, cell #1, strength 0.75
      [10,1]0.75 - synapse from column 10, cell #1, strength 0.75
      [11,1]0.75 - synapse from column 11, cell #1, strength 0.75
    """
    # Segment ID
    print "ID:%-5d" % (self.segID),

    # Sequence segment or pooling segment
    if self.isSequenceSeg:
      print "True",
    else:
      print "False",

    # Duty cycle
    print "%9.7f" % (self.dutyCycle(readOnly=True)),

    # numPositive/totalActivations
    print "(%4d/%-4d)" % (self.positiveActivations,
                          self.totalActivations),

    # Age
    print "%4d" % (self.tp.lrnIterationIdx - self.lastActiveIteration),

    # Print each synapses on this segment as: srcCellCol/srcCellIdx/perm
    # if the permanence is above connected, put [] around the synapse info
    # For aid in comparing to the C++ implementation, print them in sorted
    #  order
    sortedSyns = sorted(self.syns)
    for _, synapse in enumerate(sortedSyns):
      print "[%d,%d]%4.2f" % (synapse[0], synapse[1], synapse[2]),
    print


  def isSequenceSegment(self):
    return self.isSequenceSeg


  def getNumSynapses(self):
    return len(self.syns)


  def freeNSynapses(self, numToFree, inactiveSynapseIndices, verbosity= 0):
    """Free up some synapses in this segment. We always free up inactive
    synapses (lowest permanence freed up first) before we start to free up
    active ones.

    @param numToFree              number of synapses to free up
    @param inactiveSynapseIndices list of the inactive synapse indices.
    """
    # Make sure numToFree isn't larger than the total number of syns we have
    assert (numToFree <= len(self.syns))

    if (verbosity >= 4):
      print "\nIn PY freeNSynapses with numToFree =", numToFree,
      print "inactiveSynapseIndices =",
      for i in inactiveSynapseIndices:
        print self.syns[i][0:2],
      print

    # Remove the lowest perm inactive synapses first
    if len(inactiveSynapseIndices) > 0:
      perms = numpy.array([self.syns[i][2] for i in inactiveSynapseIndices])
      candidates = numpy.array(inactiveSynapseIndices)[
          perms.argsort()[0:numToFree]]
      candidates = list(candidates)
    else:
      candidates = []

    # Do we need more? if so, remove the lowest perm active synapses too
    if len(candidates) < numToFree:
      activeSynIndices = [i for i in xrange(len(self.syns))
                          if i not in inactiveSynapseIndices]
      perms = numpy.array([self.syns[i][2] for i in activeSynIndices])
      moreToFree = numToFree - len(candidates)
      moreCandidates = numpy.array(activeSynIndices)[
          perms.argsort()[0:moreToFree]]
      candidates += list(moreCandidates)

    if verbosity >= 4:
      print "Deleting %d synapses from segment to make room for new ones:" % (
          len(candidates)), candidates
      print "BEFORE:",
      self.debugPrint()

    # Free up all the candidates now
    synsToDelete = [self.syns[i] for i in candidates]
    for syn in synsToDelete:
      self.syns.remove(syn)

    if verbosity >= 4:
      print "AFTER:",
      self.debugPrint()


  def addSynapse(self, srcCellCol, srcCellIdx, perm):
    """Add a new synapse

    @param srcCellCol source cell column
    @param srcCellIdx source cell index within the column
    @param perm       initial permanence
    """
    self.syns.append([int(srcCellCol), int(srcCellIdx), numpy.float32(perm)])


  def updateSynapses(self, synapses, delta):
    """Update a set of synapses in the segment.

    @param tp       The owner TP
    @param synapses List of synapse indices to update
    @param delta    How much to add to each permanence

    @returns   True if synapse reached 0
    """
    reached0 = False

    if delta > 0:
      for synapse in synapses:
        self.syns[synapse][2] = newValue = self.syns[synapse][2] + delta

        # Cap synapse permanence at permanenceMax
        if newValue > self.tp.permanenceMax:
          self.syns[synapse][2] = self.tp.permanenceMax

    else:
      for synapse in synapses:
        self.syns[synapse][2] = newValue = self.syns[synapse][2] + delta

        # Cap min synapse permanence to 0 in case there is no global decay
        if newValue <= 0:
          self.syns[synapse][2] = 0
          reached0 = True

    return reached0



# This is necessary for unpickling objects that have instances of the nested
# class since the loading process looks for the class at the top level of the
# module.
SegmentUpdate = TP.SegmentUpdate
