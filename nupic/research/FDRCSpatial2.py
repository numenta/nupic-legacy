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

"""Spatial pooler implementation.

TODO: Change print statements to use the logging module.
"""

import copy
import cPickle
import inspect
import itertools
import random
import sys
import time

import numpy
import numpy.random
from nupic.bindings.algorithms import (adjustMasterValidPermanence, cpp_overlap,
                                       Inhibition2)
from nupic.bindings.math import (count_gte, GetNTAReal, Random as NupicRandom,
                                 SM_01_32_32, SM32)
from nupic.math.cross import cross
from nupic.research import fdrutilities as fdru


realDType = GetNTAReal()

gPylabInitialized = False
# kDutyCycleFactor add dutyCycleAfterInh to overlap in Inhibition step to be a
# tie breaker
kDutyCycleFactor = 0.01



def _extractCallingMethodArgs():
  """
  Returns args dictionary from the calling method
  """
  callingFrame = inspect.stack()[1][0]

  argNames, _, _, frameLocalVarDict = inspect.getargvalues(callingFrame)

  argNames.remove("self")

  args = copy.copy(frameLocalVarDict)

  for varName in frameLocalVarDict:
    if varName not in argNames:
      args.pop(varName)

  return args



class FDRCSpatial2(object):
  """
  Class for spatial pooling based on fixed random distributed
  representation (FDR).

  This version of FDRCSpatial inlcudes adaptive receptive fields, no-dupe rules
  and gradual boosting. It supports 1-D and 2-D topologies with cloning.
  """


  def __init__(self,
               inputShape=(32, 32),
               inputBorder=8,
               inputDensity=1.0,
               coincidencesShape=(48, 48),
               coincInputRadius=16,
               coincInputPoolPct=1.0,
               gaussianDist=False,
               commonDistributions=False,
               localAreaDensity=-1.0,
               numActivePerInhArea=10.0,
               stimulusThreshold=0,
               synPermInactiveDec=0.01,
               synPermActiveInc=0.1,
               synPermActiveSharedDec=0.0,
               synPermOrphanDec=0.0,
               synPermConnected=0.10,
               minPctDutyCycleBeforeInh=0.001,
               minPctDutyCycleAfterInh=0.001,
               dutyCyclePeriod=1000,
               maxFiringBoost=10.0,
               maxSSFiringBoost=2.0,
               maxSynPermBoost=10.0,
               minDistance=0.0,
               cloneMap=None,
               numCloneMasters=-1,
               seed=-1,
               spVerbosity=0,
               printPeriodicStats=0,
               testMode=False,
               globalInhibition=False,
               spReconstructionParam="unweighted_mean",
               useHighTier=True,
               randomSP=False,
              ):
    """
    Parameters:
    ----------------------------
    inputShape:           The dimensions of the input vector. Format is (height,
                          width) e.g. (24, 72). If the input is from a sensor,
                          it is interpreted as having a 2-D topology of 24
                          pixels high and 72 wide.
    inputBorder:          The first column from an edge will be centered
                          over an input which is 'inputBorder' inputs from the
                          edge.
    inputDensity:         The density of the input. This is only to aid in
                          figuring out the initial number of connected synapses
                          to place on each column. The lower the inputDensity,
                          the more initial connections will be assigned to each
                          column.
    coincidencesShape:    The dimensions of column layout. Format is (height,
                          width) e.g. (80,100) means a total of 80*100 = 800 are
                          arranged in a 2-D topology with 80 rows and
                          100 columns.
    coincInputRadius:     This defines the max radius of the receptive field of
                          each column. This is used to limit memory requirements
                          and processing time. It could be set large enough to
                          encompass the entire input field and the SP would
                          still work fine, but require more memory and
                          processing time.
                          This parameter defines a square area: a column will
                          have a max square RF with sides of length
                          2 * coincInputRadius + 1.
    coincInputPoolPct     What percent of the columns's receptive field is
                          available for potential synapses. At initialization
                          time, we will choose
                          coincInputPoolPct * (2*coincInputRadius + 1)^2
                          potential synapses from the receptive field.
    gaussianDist:         If true, the initial permanences assigned to each
                          column will have a gaussian distribution to them,
                          making the column favor inputs directly below it over
                          inputs farther away. If false, the initial permanences
                          will have a random distribution across the column's
                          entire potential receptive field.
    commonDistributions:  If set to True (the default, faster startup time),
                          each column will be given the same initial permanence
                          values.
                          This is normally OK when you will be training, but if
                          you will be sticking with the untrained network,
                          you will want to set this to False (which makes
                          startup take longer).
    localAreaDensity:     The desired density of active columns within a local
                          inhibition area (the size of which is set by the
                          internally calculated inhibitionRadius, which is in
                          turn determined from the average size of the connected
                          receptive fields of all columns). The inhibition logic
                          will insure that at most N columns remain ON within a
                          local inhibition area, where N = localAreaDensity *
                          (total number of columns in inhibition area).
    numActivePerInhArea:  An alternate way to control the density of the active
                          columns. If numActivePerInhArea is specified then
                          localAreaDensity must be -1, and vice versa. When
                          using numActivePerInhArea, the inhibition logic will
                          insure that at most 'numActivePerInhArea' columns
                          remain ON within a local inhibition area (the size of
                          which is set by the internally calculated
                          inhibitionRadius, which is in turn determined from the
                          average size of the connected receptive fields of all
                          columns). When using this method, as columns learn and
                          grow their effective receptive fields, the
                          inhibitionRadius will grow, and hence the net density
                          of the active columns will *decrease*. This is in
                          contrast to the localAreaDensity method, which keeps
                          the density of active columns the same regardless of
                          the size of their receptive fields.
    stimulusThreshold:    This is a number specifying the minimum number of
                          synapses that must be on in order for a columns to
                          turn ON.
                          The purpose of this is to prevent noise input from
                          activating columns.
    synPermInactiveDec:   How much an inactive synapse is decremented, specified
                          as a percent of a fully grown synapse.
    synPermActiveInc:     How much to increase the permanence of an active
                          synapse, specified as a percent of a fully grown
                          synapse.
    synPermActiveSharedDec: How much to decrease the permanence of an active
                          synapse which is connected to another column that is
                          active at the same time. Specified as a percent of a
                          fully grown synapse.
    synPermOrphanDec:     How much to decrease the permanence of an active
                          synapse on a column which has high overlap with the
                          input, but was inhibited (an "orphan" column).
    synPermConnected:     The default connected threshold. Any synapse whose
                          permanence value is above the connected threshold is
                          a "connected synapse", meaning it can contribute to
                          the cell's firing. Typical value is 0.10. Cells whose
                          activity level before inhibition falls below
                          minDutyCycleBeforeInh will have their own internal
                          synPermConnectedCell threshold set below this default
                          value.
                          (This concept applies to both SP and TP and so 'cells'
                          is correct here as opposed to 'columns')
    minPctDutyCycleBeforeInh: A number between 0 and 1.0, used to set a floor on
                          how often a column should have at least
                          stimulusThreshold active inputs. Periodically, each
                          column looks at the duty cycle before inhibition of
                          all other column within its inhibition radius and sets
                          its own internal minimal acceptable duty cycle to:
                            minPctDutyCycleBeforeInh *
                            max(other columns' duty cycles).
                          On each iteration, any column whose duty cycle before
                          inhibition falls below this computed value will  get
                          all of its permanence values boosted up by
                          synPermActiveInc. Raising all permanences in response
                          to a sub-par duty cycle before  inhibition allows a
                          cell to search for new inputs when either its
                          previously learned inputs are no longer ever active,
                          or when the vast majority of them have been "hijacked"
                          by other columns due to the no-dupe rule.
    minPctDutyCycleAfterInh: A number between 0 and 1.0, used to set a floor on
                          how often a column should turn ON after inhibition.
                          Periodically, each column looks at the duty cycle
                          after inhibition of all other columns within its
                          inhibition radius and sets its own internal minimal
                          acceptable duty cycle to:
                            minPctDutyCycleAfterInh *
                            max(other columns' duty cycles).
                          On each iteration, any column whose duty cycle after
                          inhibition falls below this computed value will get
                          its internal boost factor increased.
    dutyCyclePeriod:      The period used to calculate duty cycles. Higher
                          values make it take longer to respond to changes in
                          boost or synPerConnectedCell. Shorter values make it
                          more unstable and likely to oscillate.
    maxFiringBoost:       The maximum firing level boost factor. Each column's
                          raw firing strength gets multiplied by a boost factor
                          before it gets considered for inhibition.
                          The actual boost factor for a column is number between
                          1.0 and maxFiringBoost. A boost factor of 1.0 is used
                          if the duty cycle is >= minDutyCycle, maxFiringBoost
                          is used if the duty cycle is 0, and any duty cycle in
                          between is linearly extrapolated from these 2
                          endpoints.
    maxSSFiringBoost:     Once a column turns ON, it's boost will immediately
                          fall down to maxSSFiringBoost if it is above it. This
                          is accomplished by internally raising it's computed
                          duty cycle accordingly. This prevents a cell which has
                          had it's boost raised extremely high from turning ON
                          for too many diverse inputs in a row within a short
                          period of time.
    maxSynPermBoost:      The maximum synPermActiveInc boost factor. Each
                          column's synPermActiveInc gets multiplied by a boost
                          factor to make the column more or less likely to form
                          new connections.
                          The actual boost factor used is a number between
                          1.0 and maxSynPermBoost. A boost factor of 1.0 is used
                          if the duty cycle is >= minDutyCycle, maxSynPermBoost
                          is used if the duty cycle is 0, and any duty cycle
                          in between is linearly extrapolated from these 2
                          endpoints.
    minDistance:          This parameter impacts how finely the input space is
                          quantized. It is a value between 0 and 1.0. If set
                          to 0, then every unique input presentation will
                          generate a unique output representation, within the
                          limits of the total number of columns available.
                          Higher values will tend to group similar inputs
                          together into the same output representation. Only
                          column which overlap with the input less than
                          100*(1.0-minDistance) percent will
                          have a possibility of losing the inhibition
                          competition against a boosted, 'bored' cell.
    cloneMap:             An array (numColumnsHigh, numColumnsWide) that
                          contains the clone index to use for each column.
    numCloneMasters:      The number of distinct clones in the map.  This
                          is just outputCloningWidth*outputCloningHeight.
    seed:                 Seed for our own pseudo-random number generator.
    spVerbosity:          spVerbosity level: 0, 1, 2, or 3
    printPeriodicStats:   If > 0, then every 'printPeriodicStats' iterations,
                          the SP will print to stdout some statistics related to
                          learning, such as the average pct under and
                          over-coverage, average number of active columns, etc.
                          in the last 'showLearningStats' iterations.
    testMode:             If True, run the SP in test mode. This runs both the
                          C++ and python implementations on all internal
                          functions that support both and insures that both
                          produce the same result.
    globalInhibition:     If true, enforce the
                          localAreaDensity/numActivePerInhArea
                          globally over the entire region, ignoring any
                          dynamically calculated inhibitionRadius. In effect,
                          this is the same as setting the inhibition radius to
                          include the entire region.
    spReconstructionParam:Specifies which SP reconstruction optimization to be
                          used. Each column's firing strength is weighted by the
                          percent Overlap, permanence or duty Cycle if this
                          parameter is set to 'pctOverlap', 'permanence', or
                          'dutycycle' respectively. If parameter is set to
                          'maximum_firingstrength', the maximum of the firing
                          strengths (weighted by permanence) is used instead of
                          the weighted sum.

    useHighTier:          The "high tier" feature is to deal with sparse input
                          spaces. If over (1-minDistance) percent of a column's
                          connected synapses are active, it will automatically
                          become one of the winning columns.

                          If False, columns are activated based on their absolute
                          overlap with the input. Also, boosting will be
                          disabled to prevent pattern oscillation

    randomSP:             If True, the SP will not update its permanences and
                          will instead use it's initial configuration for all
                          inferences.
    """

    # Save our __init__ args for debugging
    self._initArgsDict = _extractCallingMethodArgs()

    # Handle people instantiating us directly that don't pass in a cloneMap...
    # This creates a clone map without any cloning
    if cloneMap is None:
      cloneMap, numCloneMasters = fdru.makeCloneMap(
        columnsShape=coincidencesShape,
        outputCloningWidth=coincidencesShape[1],
        outputCloningHeight=coincidencesShape[0]
      )
    self.numCloneMasters = numCloneMasters
    self._cloneMapFlat = cloneMap.reshape((-1,))

    # Save creation parameters
    self.inputShape = int(inputShape[0]), int(inputShape[1])
    self.inputBorder = inputBorder
    self.inputDensity = inputDensity
    self.coincidencesShape = coincidencesShape
    self.coincInputRadius = coincInputRadius
    self.coincInputPoolPct = coincInputPoolPct
    self.gaussianDist = gaussianDist
    self.commonDistributions = commonDistributions
    self.localAreaDensity = localAreaDensity
    self.numActivePerInhArea = numActivePerInhArea
    self.stimulusThreshold = stimulusThreshold
    self.synPermInactiveDec = synPermInactiveDec
    self.synPermActiveInc = synPermActiveInc
    self.synPermActiveSharedDec = synPermActiveSharedDec
    self.synPermOrphanDec = synPermOrphanDec
    self.synPermConnected = synPermConnected
    self.minPctDutyCycleBeforeInh = minPctDutyCycleBeforeInh
    self.minPctDutyCycleAfterInh = minPctDutyCycleAfterInh
    self.dutyCyclePeriod = dutyCyclePeriod
    self.requestedDutyCyclePeriod = dutyCyclePeriod
    self.maxFiringBoost = maxFiringBoost
    self.maxSSFiringBoost = maxSSFiringBoost
    self.maxSynPermBoost = maxSynPermBoost
    self.minDistance = minDistance
    self.spVerbosity = spVerbosity
    self.printPeriodicStats = printPeriodicStats
    self.testMode = testMode
    self.globalInhibition = globalInhibition
    self.spReconstructionParam = spReconstructionParam
    self.useHighTier= useHighTier != 0
    self.randomSP = randomSP != 0

    self.fileCount = 0
    self._runIter = 0

    # Start at iteration #0
    self._iterNum = 0             # Number of learning iterations
    self._inferenceIterNum = 0    # Number of inference iterations

    # Print creation parameters
    if spVerbosity >= 1:
      self.printParams()
      print "seed =", seed

    # Check for errors
    assert (self.numActivePerInhArea == -1 or self.localAreaDensity == -1)
    assert (self.inputShape[1] > 2 * self.inputBorder)
    # 1D layouts have inputShape[0] == 1
    if self.inputShape[0] > 1:
      assert self.inputShape[0] > 2 * self.inputBorder

    # Calculate other member variables
    self._coincCount = int(self.coincidencesShape[0] *
                           self.coincidencesShape[1])
    self._inputCount = int(self.inputShape[0] * self.inputShape[1])
    self._synPermMin = 0.0
    self._synPermMax = 1.0
    self._pylabInitialized = False
    # The rate at which we bump up all synapses in response to not passing
    # stimulusThreshold
    self._synPermBelowStimulusInc = self.synPermConnected / 10.0
    self._hasTopology = True
    if self.inputShape[0] == 1:       # 1-D layout
      self._coincRFShape = (1, (2 * coincInputRadius + 1))
      # If we only have 1 column of coincidences, then assume the user wants
      # each coincidence to cover the entire input
      if self.coincidencesShape[1] == 1:
        assert self.inputBorder >= (self.inputShape[1] - 1) // 2
        assert coincInputRadius >= (self.inputShape[1] - 1) // 2
        self._coincRFShape =  (1, self.inputShape[1])
        self._hasTopology = False
    else:                             # 2-D layout
      self._coincRFShape = ((2*coincInputRadius + 1), (2*coincInputRadius + 1))
    # This gets set to True in finishLearning. Once set, we don't allow
    # learning anymore and delete all member variables needed only for
    # learning.
    self._doneLearning = False

    # Init random seed
    self._seed(seed)
    # Hard-coded in the current case
    self.randomTieBreakingFraction = 0.5

    # The permanence values used to initialize the master coincs are from
    # this initial permanence array
    # The initial permanence is gaussian shaped with mean at center and variance
    # carefully chosen to have connected synapses
    initialPermanence = self._initialPermanence()

    # masterPotentialM, masterPermanenceM and masterConnectedM are numpy arrays
    # of dimensions (coincCount, coincRfShape[0], coincRFShape[1])
    #
    # masterPotentialM:   Keeps track of the potential synapses of each
    #                     master. Potential synapses are marked as True
    # masterPermanenceM:  Holds the permanence values of the potential synapses.
    #                     The values can range from 0.0 to 1.0
    # masterConnectedM:   Keeps track of the connected synapses of each
    #                     master. Connected synapses are the potential synapses
    #                     with permanence values greater than synPermConnected.
    self._masterPotentialM, self._masterPermanenceM = (
        self._makeMasterCoincidences(self.numCloneMasters, self._coincRFShape,
                                     self.coincInputPoolPct, initialPermanence,
                                     self.random))

    # Update connected coincidences, the connected synapses have permanence
    # values greater than synPermConnected.
    self._masterConnectedM = []
    dense = numpy.zeros(self._coincRFShape)
    for i in xrange(self.numCloneMasters):
      self._masterConnectedM.append(SM_01_32_32(dense))

    # coinc sizes are used in normalizing the raw overlaps
    self._masterConnectedCoincSizes = numpy.empty(self.numCloneMasters,
                                                  'uint32')

    # Make one mondo coincidence matrix for all cells at once. It has one row
    # per cell. The width of each row is the entire input width. There will be
    # ones in each row where that cell has connections. When we have cloning,
    # and we modify the connections for a clone master, we will update all
    # cells that share that clone master with the new connections.
    self._allConnectedM = SM_01_32_32(self._inputCount)
    self._allConnectedM.resize(self._coincCount, self._inputCount)

    # Initialize the dutyCycles and boost factors per clone master
    self._dutyCycleBeforeInh = numpy.zeros(self.numCloneMasters,
                                           dtype=realDType)
    self._minDutyCycleBeforeInh = numpy.zeros(self.numCloneMasters,
                                              dtype=realDType)

    self._dutyCycleAfterInh = numpy.zeros(self.numCloneMasters,
                                          dtype=realDType)
    self._minDutyCycleAfterInh = numpy.zeros(self.numCloneMasters,
                                             dtype=realDType)

    # TODO: We don't need to store _boostFactors, can be calculated from duty
    # cycle
    self._firingBoostFactors = numpy.ones(self.numCloneMasters,
                                          dtype=realDType)
    if self.useHighTier:
      self._firingBoostFactors *= maxFiringBoost

    # Selectively turn on/off C++ for various methods
    # TODO: Can we remove the conditional?
    if self.testMode:
      self._computeOverlapsImp = "py" # "py or "cpp" or "test"
      self._updatePermanenceGivenInputImp = "py" # "py" or "cpp or "test"

    else:
      self._computeOverlapsImp = "py" # "py or "cpp" or "test"
      self._updatePermanenceGivenInputImp = "py" # "py" or "cpp or "test"

    # This is used to hold our learning stats (via getLearningStats())
    self._learningStats = dict()

    # These will hold our random state, which we return from __getstate__ and
    # reseed our random number generators from in __setstate__ so that 
    # a saved/restored SP produces the exact same behavior as one that
    # continues. This behavior allows us to write unit tests that verify that
    # the behavior of an SP does not change due to saving/loading from a
    # checkpoint
    self._randomState = None
    self._numpyRandomState = None
    self._nupicRandomState = None

    # Init ephemeral members
    # This also calculates the slices and global inhibitionRadius and allocates
    # the inhibitionObj
    self._initEphemerals()

    # If we have no cloning, make sure no column has potential or connected
    # synapses outside the input area
    if self.numCloneMasters == self._coincCount:
      validMask = numpy.zeros(self._coincRFShape, dtype=realDType)
      for masterNum in xrange(self._coincCount):
        coincSlice  = self._coincSlices[masterNum]
        validMask.fill(0)
        validMask[coincSlice] = 1
        self._masterPotentialM[masterNum].logicalAnd(SM_01_32_32(validMask))
        self._masterPermanenceM[masterNum].elementMultiply(validMask)

        # Raise all permanences up until the number of connected is above
        # our desired target,
        self._raiseAllPermanences(masterNum,
                minConnections = self.stimulusThreshold / self.inputDensity)

    # Calculate the number of connected synapses in each master coincidence now
    self._updateConnectedCoincidences()


  def _getEphemeralMembers(self):
    """
    List of our member variables that we don't need to be saved
    """
    return ['_inputLayout',
            '_cellsForMaster',
            '_columnCenters',
            #'_cellRFClipped',
            '_inputSlices',
            '_coincSlices',
            '_activeInput',
            '_permChanges',
            '_dupeInput',
            '_onCells',
            '_masterOnCells',
            '_onCellIndices',
            '_inhibitionObj',
            '_denseOutput',
            '_overlaps',
            '_anomalyScores',
            '_inputUse',
            '_updatePermanenceGivenInputFP',
            '_computeOverlapsFP',
            '_stats',
            '_rfRadiusAvg',
            '_rfRadiusMin',
            '_rfRadiusMax',
            '_topDownOut',
            '_topDownParentCounts',
            ]


  def _initEphemerals(self):
    """
    Initialize all ephemeral members after being restored to a pickled state.
    """
    # Used by functions which refers to inputs in absolute space
    # getLearnedCM, cm,....
    self._inputLayout = numpy.arange(self._inputCount,
                          dtype=numpy.uint32).reshape(self.inputShape)

    # This array returns the list of cell indices that correspond to each master
    cloningOn = (self.numCloneMasters != self._coincCount)
    if cloningOn:
      self._cellsForMaster = []
      for masterNum in xrange(self.numCloneMasters):
        self._cellsForMaster.append(
          numpy.where(self._cloneMapFlat == masterNum)[0])
    else:
      self._cellsForMaster = None

    # TODO: slices are not required for the C++ helper functions
    # Figure out the slices of shaped input that each column sees...
    # Figure out the valid region of each column
    # The reason these slices are in initEphemerals is because numpy slices
    # can't be pickled
    self._setSlices()

    # This holds the output of the inhibition computation - which cells are
    # on after inhibition
    self._onCells = numpy.zeros(self._coincCount, dtype=realDType)
    self._masterOnCells = numpy.zeros(self.numCloneMasters, dtype=realDType)
    self._onCellIndices = numpy.zeros(self._coincCount, dtype='uint32')

    # The inhibition object gets allocated by _updateInhibitionObj() during
    # the first compute and re-allocated periodically during learning
    self._inhibitionObj = None
    self._rfRadiusAvg = 0     # Also calculated by _updateInhibitionObj
    self._rfRadiusMin = 0
    self._rfRadiusMax = 0

    # Used by the caller to optionally cache the dense output
    self._denseOutput = None

    # This holds the overlaps (in absolute number of connected synapses) of each
    # coinc with input.
    self._overlaps = numpy.zeros(self._coincCount, dtype=realDType)

    # This holds the percent overlaps (number of active inputs / number of
    # connected synapses) of each coinc with input.
    self._pctOverlaps = numpy.zeros(self._coincCount, dtype=realDType)

    # This is the value of the anomaly score for each column (after inhibition).
    self._anomalyScores = numpy.zeros_like(self._overlaps)

    # This holds the overlaps before stimulus threshold - used for verbose
    # messages only.
    self._overlapsBST = numpy.zeros(self._coincCount, dtype=realDType)

    # This holds the number of coincs connected to an input.
    if not self._doneLearning:
      self._inputUse = numpy.zeros(self.inputShape, dtype=realDType)

    # These are boolean matrices, the same shape as the input.
    if not self._doneLearning:
      self._activeInput = numpy.zeros(self.inputShape, dtype='bool')
      self._dupeInput = numpy.zeros(self.inputShape, dtype='bool')

    # This is used to hold self.synPermActiveInc where the input is on
    # and -self.synPermInctiveDec where the input is off
    if not self._doneLearning:
      self._permChanges = numpy.zeros(self.inputShape, dtype=realDType)

    # These are used to compute and hold the output from topDownCompute
    # self._topDownOut = numpy.zeros(self.inputShape, dtype=realDType)
    # self._topDownParentCounts = numpy.zeros(self.inputShape, dtype='int')

    # Fill in the updatePermanenceGivenInput method pointer, which depends on
    # chosen language.
    if self._updatePermanenceGivenInputImp == "py":
      self._updatePermanenceGivenInputFP = self._updatePermanenceGivenInputPy
    elif self._updatePermanenceGivenInputImp == "cpp":
      self._updatePermanenceGivenInputFP = self._updatePermanenceGivenInputCPP
    elif self._updatePermanenceGivenInputImp == "test":
      self._updatePermanenceGivenInputFP = self._updatePermanenceGivenInputTest
    else:
      assert False

    # Fill in the computeOverlaps method pointer, which depends on
    # chosen language.
    if self._computeOverlapsImp == "py":
      self._computeOverlapsFP = self._computeOverlapsPy
    elif self._computeOverlapsImp == "cpp":
      self._computeOverlapsFP = self._computeOverlapsCPP
    elif self._computeOverlapsImp == "test":
      self._computeOverlapsFP = self._computeOverlapsTest
    else:
      assert False

    # These variables are used for keeping track of learning statistics (when
    #  self.printPeriodicStats is used).
    self._periodicStatsCreate()


  def compute(self, flatInput, learn=False, infer=True, computeAnomaly=False):
    """Compute with the current input vector.

    Parameters:
    ----------------------------
    input        : the input vector (numpy array)
    learn        : if True, adapt the input histogram based on this input
    infer        : whether to do inference or not
    """

    # If we are using a random SP, ignore the learn parameter
    if self.randomSP:
      learn = False

    # If finishLearning has been called, don't allow learning anymore
    if learn and self._doneLearning:
      raise RuntimeError("Learning can not be performed once finishLearning"
        " has been called.")

    assert (learn or infer)

    assert (flatInput.ndim == 1) and (flatInput.shape[0] == self._inputCount)
    assert (flatInput.dtype == realDType)
    input = flatInput.reshape(self.inputShape)

    # Make sure we've allocated the inhibition object lazily
    if self._inhibitionObj is None:
      self._updateInhibitionObj()

    # Reset first timer
    if self.printPeriodicStats > 0 and self._iterNum == 0:
      self._periodicStatsReset()

    # Using cloning?
    cloningOn = (self.numCloneMasters != self._coincCount)

    # If we have high verbosity, save the overlaps before stimulus threshold
    # so we can print them out at the end
    if self.spVerbosity >= 2:
      print "==============================================================="
      print "Iter:%d" % self._iterNum, "inferenceIter:%d" % \
            self._inferenceIterNum
      self._computeOverlapsFP(input, stimulusThreshold=0)
      self._overlapsBST[:] = self._overlaps
      connectedCountsOnEntry = self._masterConnectedCoincSizes.copy()
      if self.spVerbosity >= 3:
        inputNZ = flatInput.nonzero()[0]
        print "active inputs: (%d)" % len(inputNZ), inputNZ

    # TODO: Port to C++, arguments may be different - t1YXArr,
    # coincInputRadius,...
    # Calculate the raw overlap of each cell
    # Overlaps less than stimulus threshold are set to zero in
    # _calculateOverlaps
    # This places the result into self._overlaps
    self._computeOverlapsFP(input, stimulusThreshold=self.stimulusThreshold)

    # Save the original overlap values, before boosting, for the purpose of
    # anomaly detection
    if computeAnomaly:
      self._anomalyScores[:]  = self._overlaps[:]

    if learn:
      # Update each cell's duty cycle before inhibition
      # Only cells with overlaps greater stimulus threshold are considered as
      # active.
      # Stimulus threshold has already been applied
      # TODO: Port to C++? Loops over all coincs
      # Only updating is carried out here, bump up happens later
      onCellIndices = numpy.where(self._overlaps > 0)
      if cloningOn:
        onMasterIndices = self._cloneMapFlat[onCellIndices]
        self._masterOnCells.fill(0)
        self._masterOnCells[onMasterIndices] = 1
        denseOn = self._masterOnCells
      else:
        self._onCells.fill(0)
        self._onCells[onCellIndices] = 1
        denseOn = self._onCells

      # dutyCyclePeriod = self._iterNum + 1 let _dutyCycleBeforeInh
      # and _dutyCycleAfterInh represent real firing percentage at the
      # beginning of learning. This will effect boosting and let unlearned
      # coincidences have high boostFactor at beginning.
      self.dutyCyclePeriod = min(self._iterNum + 1,
                                 self.requestedDutyCyclePeriod)

      # Compute a moving average of the duty cycle before inhibition
      self._dutyCycleBeforeInh = (
          ((self.dutyCyclePeriod - 1) * self._dutyCycleBeforeInh + denseOn) /
          self.dutyCyclePeriod)

    # Compute firing levels based on boost factor and raw overlap. Update
    # self._overlaps in place, replacing it with the boosted overlap. We also
    # computes percent overlap of each column and store that into
    # self._pctOverlaps
    if cloningOn:
      self._pctOverlaps[:] = self._overlaps
      self._pctOverlaps /= self._masterConnectedCoincSizes[self._cloneMapFlat]
      boostFactors = self._firingBoostFactors[self._cloneMapFlat]
    else:
      self._pctOverlaps[:] = self._overlaps
      potentials = self._masterConnectedCoincSizes
      self._pctOverlaps /= numpy.maximum(1, potentials)
      boostFactors = self._firingBoostFactors

    # To process minDistance, we do the following:
    # 1.) All cells which do not overlap the input "highly" (less than
    #      minDistance), are considered to be in the "low tier" and get their
    #      overlap multiplied by their respective boost factor.
    # 2.) All other cells, which DO overlap the input highly, get a "high tier
    #      offset" added to their overlaps, and boost is not applied. The
    #      "high tier offset" is computed as the max of all the boosted
    #      overlaps from step #1. This insures that a cell in this high tier
    #      will never lose to a cell from the low tier.

    if self.useHighTier:
      highTier = numpy.where(self._pctOverlaps >= (1.0 - self.minDistance))[0]
    else:
      highTier = []

    someInHighTier = len(highTier) > 0

    if someInHighTier:
      boostFactors = numpy.array(boostFactors)
      boostFactors[highTier] = 1.0
    # Apply boostFactors only in learning phase not in inference phase.
    if learn:
      self._overlaps *= boostFactors
    if someInHighTier:
      highTierOffset = self._overlaps.max() + 1.0
      self._overlaps[highTier] += highTierOffset

    # Cache the dense output for debugging.
    if self._denseOutput is not None:
      self._denseOutput = self._overlaps.copy()

    # Incorporate inhibition and see who is firing after inhibition.
    # We don't need this method to process stimulusThreshold because we
    # already processed it.
    # Also, we pass in a small 'addToWinners' amount which gets added to the
    # winning elements as we go along. This prevents us from choosing more than
    # topN winners per inhibition region when more than topN elements all have
    # the same max high score.

    learnedCellsOverlaps = numpy.array(self._overlaps)
    if infer and not learn:
      # Cells that have never learnt are not allowed to win during inhibition
      if not self.randomSP:
        learnedCellsOverlaps[numpy.where(self._dutyCycleAfterInh == 0)[0]] = 0
    else:
      # Boost the unlearned cells to 1000 so that the winning columns are
      # picked randomly. From the set of unlearned columns. Boost columns that
      # havent been learned with uniformly to 1000 so that inhibition picks
      # randomly from them.
      if self.useHighTier:
        learnedCellsOverlaps[numpy.where(self._dutyCycleAfterInh == 0)[0]] = (
            learnedCellsOverlaps.max() + 1)
        # Boost columns that are in highTier (ie. they match the input very
        # well).
        learnedCellsOverlaps[highTier] += learnedCellsOverlaps.max() + 1

      # Small random tiebreaker for columns with equal overlap
      tieBreaker = numpy.random.rand(*learnedCellsOverlaps.shape).astype(
          realDType)
      learnedCellsOverlaps += 0.1 * tieBreaker

    numOn = self._inhibitionObj.compute(
        learnedCellsOverlaps,
        self._onCellIndices,
        0.0, # stimulusThreshold
        max(learnedCellsOverlaps)/1000.0, # addToWinners
    )

    self._onCells.fill(0)
    if numOn > 0:
      onCellIndices = self._onCellIndices[0:numOn]
      self._onCells[onCellIndices] = 1
    else:
      onCellIndices = []

    # Compute the anomaly scores only for the winning columns.
    if computeAnomaly:
      self._anomalyScores *= self._onCells
      self._anomalyScores *= self._dutyCycleAfterInh

    if self.spVerbosity >= 2:
      print "inhRadius", self._inhibitionObj.getInhibitionRadius()
      print "inhLocalAreaDensity", self._inhibitionObj.getLocalAreaDensity()
      print "numFiring", numOn

    # Capturing learning stats? If so, capture the cell overlap statistics
    if self.printPeriodicStats > 0:
      activePctOverlaps = self._pctOverlaps[onCellIndices]
      self._stats['cellPctOverlapSums'] += activePctOverlaps.sum()
      if cloningOn:
        onMasterIndices = self._cloneMapFlat[onCellIndices]
      else:
        onMasterIndices = onCellIndices
      self._stats['cellOverlapSums'] += (
          activePctOverlaps *
          self._masterConnectedCoincSizes[onMasterIndices]).sum()

    # Compute which cells had very high overlap, but were still
    # inhibited. These we are calling our "orphan cells", because they are
    # representing an input which is already better represented by another
    # cell.
    if self.synPermOrphanDec > 0:
      orphanCellIndices = set(numpy.where(self._pctOverlaps >= 1.0)[0])
      orphanCellIndices.difference_update(onCellIndices)
    else:
      orphanCellIndices = []

    if learn:
      # Update the number of coinc connections per input
      # During learning (adapting permanence values), we need to be able to
      # recognize dupe inputs - inputs that go two 2 or more active cells
      if self.synPermActiveSharedDec != 0:
        self._updateInputUse(onCellIndices)

      # For the firing cells, update permanence values.
      onMasterIndices = self._adaptSynapses(onCellIndices, orphanCellIndices,
                                            input)

      # Increase the permanence values of columns which haven't passed
      # stimulus threshold of overlap with at least a minimum frequency
      self._bumpUpWeakCoincidences()

      # Update each cell's after-inhibition duty cycle
      if cloningOn:
        self._masterOnCells.fill(0)
        self._masterOnCells[onMasterIndices] = 1
        denseOn = self._masterOnCells
      else:
        denseOn = self._onCells
      # Compute a moving average of the duty cycle after inhibition
      self._dutyCycleAfterInh = ((
          (self.dutyCyclePeriod - 1) * self._dutyCycleAfterInh + denseOn) /
          self.dutyCyclePeriod)

      # Update the boost factors based on firings rate after inhibition.
      self._updateBoostFactors()

      # Increment iteration number and perform our periodic tasks if it's time.
      if (self._iterNum + 1) % 50 == 0:
        self._updateInhibitionObj()
        self._updateMinDutyCycles(
            self._dutyCycleBeforeInh, self.minPctDutyCycleBeforeInh,
            self._minDutyCycleBeforeInh)
        self._updateMinDutyCycles(
            self._dutyCycleAfterInh, self.minPctDutyCycleAfterInh,
            self._minDutyCycleAfterInh)

    # Next iteration
    if learn:
      self._iterNum += 1
    if infer:
      self._inferenceIterNum += 1

    if learn:
      # Capture and possibly print the periodic stats
      if self.printPeriodicStats > 0:
        self._periodicStatsComputeEnd(onCellIndices, flatInput.nonzero()[0])

    # Verbose print other stats
    if self.spVerbosity >= 3:
      cloning = (self.numCloneMasters != self._coincCount)
      print " #connected on entry:  ", fdru.numpyStr(
          connectedCountsOnEntry, '%d ', includeIndices=True)
      print " #connected on exit:   ", fdru.numpyStr(
          self._masterConnectedCoincSizes, '%d ', includeIndices=True)
      if self.spVerbosity >= 3 or not cloning:
        print " overlaps:             ", fdru.numpyStr(self._overlapsBST, '%d ',
                                        includeIndices=True, includeZeros=False)
        print " firing levels:        ", fdru.numpyStr(self._overlaps, '%.4f ',
                                        includeIndices=True, includeZeros=False)
      print " on after inhibition:  ", onCellIndices

      if not self._doneLearning:
        print " minDutyCycleBeforeInh:", fdru.numpyStr(
                                           self._minDutyCycleBeforeInh,
                                           '%.4f ', includeIndices=True)
        print " dutyCycleBeforeInh:   ", fdru.numpyStr(self._dutyCycleBeforeInh,
                                           '%.4f ', includeIndices=True)
        print " belowMinBeforeInh:    " % numpy.nonzero(
                                            self._dutyCycleBeforeInh \
                                              < self._minDutyCycleBeforeInh)[0]
        print " minDutyCycleAfterInh: ", fdru.numpyStr(
                                           self._minDutyCycleAfterInh,
                                           '%.4f ', includeIndices=True)
        print " dutyCycleAfterInh:    ", fdru.numpyStr(self._dutyCycleAfterInh,
                                           '%.4f ', includeIndices=True)
        print " belowMinAfterInh:     " % numpy.nonzero(
                                            self._dutyCycleAfterInh \
                                              < self._minDutyCycleAfterInh)[0]

      print " firingBoosts:         ", fdru.numpyStr(self._firingBoostFactors,
                                         '%.4f ', includeIndices=True)
      print

    elif self.spVerbosity >= 2:
      print "SP: learn: ", learn
      print "SP: active outputs(%d):  " % (len(onCellIndices)), onCellIndices

    self._runIter += 1
    # Return inference result
    return self._onCells


  def __getstate__(self):
    # Update our random states
    self._randomState = random.getstate()
    self._numpyRandomState = numpy.random.get_state()
    self._nupicRandomState = self.random.getState()
    
    state = self.__dict__.copy()

    # Delete ephemeral members that we don't want pickled
    for ephemeralMemberName in self._getEphemeralMembers():
      if ephemeralMemberName in state:
        del state[ephemeralMemberName]

    return state


  def __setstate__(self, state):
    self.__dict__.update(state)

    # Support older checkpoints
    # These fields were added on 2010-10-05 and _iterNum was preserved
    if not hasattr(self, '_randomState'):
      self._randomState = random.getstate()
      self._numpyRandomState = numpy.random.get_state()
      self._nupicRandomState = self.random.getState()
      self._iterNum = 0

    # For backward compatibility
    if not hasattr(self, 'requestedDutyCyclePeriod'):
      self.requestedDutyCyclePeriod = 1000
      
    # Init our random number generators
    random.setstate(self._randomState)
    numpy.random.set_state(self._numpyRandomState)
    self.random.setState(self._nupicRandomState)

    # Load things that couldn't be pickled...
    self._initEphemerals()


  def getAnomalyScore(self):
    """Get the aggregate anomaly score for this input pattern

    Returns: A single scalar value for the anomaly score
    """
    numNonzero = len(numpy.nonzero(self._anomalyScores)[0])

    return 1.0 / (numpy.sum(self._anomalyScores) + 1)


  def getLearningStats(self):
    """Return a dictionary containing a set of statistics related to learning.

    Here is a list of what is returned:
    'activeCountAvg':
        The average number of active columns seen over the last
        N training iterations, where N is set by the constructor parameter
        printPeriodicStats.
        If printPeriodicStats is not turned on (== 0), then this is -1
    'underCoveragePct':
        The average under-coverage of the input as seen over the last N training
        iterations, where N is set by the constructor parameter
        printPeriodicStats.
        If printPeriodicStats is not turned on (== 0), then this is -1
    'overCoveragePct':
        The average over-coverage of the input as seen over the last N training
        iterations, where N is set by the constructor parameter
        printPeriodicStats.
        If printPeriodicStats is not turned on (== 0), then this is -1
    'numConnectionChangesAvg':
        The overall average number of connection changes made per active
        column per iteration, over the last N training iterations, where N
        is set by the constructor parameter printPeriodicStats. This gives an
        indication as to how much learning is still occuring.
        If printPeriodicStats is not turned on (== 0), then this is -1
    'numConnectionChangesMin':
        The minimum number of connection changes made to an active column per
        iteration, over the last N training iterations, where N is set by the
        constructor parameter printPeriodicStats. This gives an indication as
        to how much learning is still occuring.
        If printPeriodicStats is not turned on (== 0), then this is -1
    'numConnectionChangesMax':
        The maximum number of connection changes made to an active column per
        iteration, over the last N training iterations, where N is set by the
        constructor parameter printPeriodicStats. This gives an indication as
        to how much learning is still occuring.
        If printPeriodicStats is not turned on (== 0), then this is -1
    'rfSize':
        The average receptive field size of the columns.
    'inhibitionRadius':
        The average inihbition radius of the columns.
    'targetDensityPct':
        The most recent target local area density used, as a percent (0 -> 100)
    'coincidenceSizeAvg':
        The average learned coincidence size
    'coincidenceSizeMin':
        The minimum learned coincidence size
    'coincidenceSizeMax':
        The maximum learned coincidence size
    'coincidenceSizeSum':
        The sum of all coincidence sizes (total number of connected synapses)
    'dcBeforeInhibitionAvg':
        The average of duty cycle before inhbition of all coincidences
    'dcBeforeInhibitionMin':
        The minimum duty cycle before inhbition of all coincidences
    'dcBeforeInhibitionAvg':
        The maximum duty cycle before inhbition of all coincidences
    'dcAfterInhibitionAvg':
        The average of duty cycle after inhbition of all coincidences
    'dcAfterInhibitionMin':
        The minimum duty cycle after inhbition of all coincidences
    'dcAfterInhibitionAvg':
        The maximum duty cycle after inhbition of all coincidences
    'firingBoostAvg':
        The average firing boost
    'firingBoostMin':
        The minimum firing boost
    'firingBoostMax':
        The maximum firing boost
    """

    # Fill in the stats that can be computed on the fly. The transient stats
    #  that depend on printPeriodicStats being on, have already been stored
    self._learningStats['rfRadiusAvg'] = self._rfRadiusAvg
    self._learningStats['rfRadiusMin'] = self._rfRadiusMin
    self._learningStats['rfRadiusMax'] = self._rfRadiusMax
    if self._inhibitionObj is not None:
      self._learningStats['inhibitionRadius'] = (
          self._inhibitionObj.getInhibitionRadius())
      self._learningStats['targetDensityPct'] = (
          100.0 * self._inhibitionObj.getLocalAreaDensity())
    else:
      print "Warning: No inhibitionObj found for getLearningStats"
      self._learningStats['inhibitionRadius'] = 0.0
      self._learningStats['targetDensityPct'] = 0.0

    self._learningStats['coincidenceSizeAvg'] = (
        self._masterConnectedCoincSizes.mean())
    self._learningStats['coincidenceSizeMin'] = (
        self._masterConnectedCoincSizes.min())
    self._learningStats['coincidenceSizeMax'] = (
        self._masterConnectedCoincSizes.max())
    self._learningStats['coincidenceSizeSum'] = (
        self._masterConnectedCoincSizes.sum())

    if not self._doneLearning:
      self._learningStats['dcBeforeInhibitionAvg'] = (
          self._dutyCycleBeforeInh.mean())
      self._learningStats['dcBeforeInhibitionMin'] = (
          self._dutyCycleBeforeInh.min())
      self._learningStats['dcBeforeInhibitionMax'] = (
          self._dutyCycleBeforeInh.max())

      self._learningStats['dcAfterInhibitionAvg'] = (
          self._dutyCycleAfterInh.mean())
      self._learningStats['dcAfterInhibitionMin'] = (
          self._dutyCycleAfterInh.min())
      self._learningStats['dcAfterInhibitionMax'] = (
          self._dutyCycleAfterInh.max())

    self._learningStats['firingBoostAvg'] = self._firingBoostFactors.mean()
    self._learningStats['firingBoostMin'] = self._firingBoostFactors.min()
    self._learningStats['firingBoostMax'] = self._firingBoostFactors.max()

    return self._learningStats


  def resetStats(self):
    """Reset the stats (periodic, ???). This will usually be called by
    user code at the start of each inference run (for a particular data set).

    TODO: which other stats need to be reset?  Learning stats?
    """
    self._periodicStatsReset()


  def _seed(self, seed=-1):
    """
    Initialize the random seed
    """

    if seed != -1:
      self.random = NupicRandom(seed)
      random.seed(seed)
      numpy.random.seed(seed)
    else:
      self.random = NupicRandom()


  def _initialPermanence(self):
    """Create and return a 2D matrix filled with initial permanence values.
    The returned matrix will be of shape:
      (2*coincInputRadius + 1, 2*coincInputRadius + 1).

    The initial permanence values are set between 0 and 1.0, with enough chosen
    above synPermConnected to make it highly likely that a cell will pass
    stimulusThreshold, given the size of the potential RF, the input pool
    sampling percentage, and the expected density of the active inputs.

    If gaussianDist is True, the center of the matrix will contain the highest
    permanence values and lower values will be farther from the center.

    If gaussianDist is False, the highest permanence values will be evenly
    distributed throughout the potential RF.
    """

    # Figure out the target number of connected synapses. We want about 2X
    #  stimulusThreshold
    minOn = 2 * max(self.stimulusThreshold, 10) / self.coincInputPoolPct \
            / self.inputDensity

    # Get the gaussian distribution, with max magnitude just slightly above
    #  synPermConnected. Try to find a sigma that gives us about 2X
    #  stimulusThreshold connected synapses after sub-sampling for
    #  coincInputPoolPct. We will assume everything within +/- sigma will be
    #  connected. This logic uses the fact that an x value of sigma generates a
    #  magnitude of 0.6.
    if self.gaussianDist:

      # Only supported when we have 2D layouts
      if self._coincRFShape[0] != self._coincRFShape[1]:
        raise RuntimeError("Gaussian distibuted permanences are currently only"
              "supported for 2-D layouts")

      # The width and height of the center "blob" in inputs is the square root
      # of the area
      onAreaDim = numpy.sqrt(minOn)

      # Sigma is at the edge of the center blob
      sigma = onAreaDim/2

      # Create the gaussian with a value of 1.0 at the center
      perms = self._gaussianMatrix(dim=max(self._coincRFShape), sigma=sigma)

      # The distance between the min and max values within the gaussian will
      # be given by 'grange'. In a gaussian, the value at sigma away from the
      # center is 0.6 * the value at the center. We want the values at sigma
      # to be synPermConnected
      maxValue = 1.0 / 0.6 * self.synPermConnected
      perms *= maxValue
      perms.shape = (-1,)

      # Now, let's clip off the low values to reduce the number of non-zeros
      # we have and reduce our memory requirements. We'll clip everything
      # farther away than 2 sigma to 0. The value of a gaussing at 2 sigma
      # is 0.135 * the value at the center
      perms[perms < (0.135 * maxValue)] = 0

    # Evenly distribute the permanences through the RF
    else:
      # Create a random distribution from 0 to 1.
      perms = numpy.random.random(self._coincRFShape)
      perms = perms.astype(realDType)

      # Set the range of values to be between 0 and
      # synPermConnected+synPermInctiveDec. This ensures that a pattern
      # will always be learned in 1 iteration
      maxValue = min(1.0, self.synPermConnected + self.synPermInactiveDec)

      # What percentage do we want to be connected?
      connectPct = 0.50

      # What value from the 0 to 1 distribution will map to synPermConnected?
      threshold = 1.0 - connectPct

      # Which will be the connected and unconnected synapses?
      connectedSyns = perms >= threshold
      unconnectedSyns = numpy.logical_not(connectedSyns)

      # Squeeze all values between threshold and 1.0 to be between
      # synPermConnected and synPermConnected + synPermActiveInc / 4
      # This makes sure the firing coincidence perms matching input bit get
      # greater than synPermConnected and other unconnectedSyns get deconnected
      # in one firing learning iteration.
      srcOffset = threshold
      srcRange = 1.0 - threshold
      dstOffset = self.synPermConnected
      dstRange = maxValue - self.synPermConnected
      perms[connectedSyns] = (perms[connectedSyns] - srcOffset)/srcRange \
                           * dstRange / 4.0 + dstOffset

      # Squeeze all values between 0 and threshold to be between 0 and
      # synPermConnected
      srcRange = threshold - 0.0
      dstRange = self.synPermConnected - 0.0
      perms[unconnectedSyns] = perms[unconnectedSyns]/srcRange \
                             * dstRange

      # Now, let's clip off the low values to reduce the number of non-zeros
      # we have and reduce our memory requirements. We'll clip everything
      # below synPermActiveInc/2 to 0
      perms[perms < (self.synPermActiveInc / 2.0)] = 0
      perms.shape = (-1,)

    return perms


  def _gaussianMatrix(self, dim, sigma):
    """
    Create and return a 2D matrix filled with a gaussian distribution. The
    returned matrix will be of shape (dim, dim). The mean of the gaussian
    will be in the center of the matrix and have a value of 1.0.
    """

    gaussian = lambda x, sigma: numpy.exp(-(x**2) / (2*(sigma**2)))

    # Allocate the matrix
    m = numpy.empty((dim, dim), dtype=realDType)

    # Find the center
    center = (dim - 1) / 2.0

    # TODO: Simplify using numpy.meshgrid
    # Fill it in
    for y in xrange(dim):
      for x in xrange(dim):
        dist = numpy.sqrt((x-center)**2 + (y-center)**2)
        m[y,x] = gaussian(dist, sigma)

    return m


  def _makeMasterCoincidences(self, numCloneMasters, coincRFShape,
                              coincInputPoolPct, initialPermanence=None,
                              nupicRandom=None):
    """Make the master coincidence matrices and mater input histograms.

    # TODO: Update this example
    >>> FDRCSpatial._makeMasterCoincidences(1, 2, 0.33)
    (array([[[ True,  True, False, False, False],
            [False,  True, False, False,  True],
            [False,  True, False, False, False],
            [False, False, False,  True, False],
            [ True, False, False, False, False]]], dtype=bool), array([[[ 0.26982325,  0.19995725,  0.        ,  0.        ,  0.        ],
            [ 0.        ,  0.94128972,  0.        ,  0.        ,  0.36316112],
            [ 0.        ,  0.06312726,  0.        ,  0.        ,  0.        ],
            [ 0.        ,  0.        ,  0.        ,  0.29740077,  0.        ],
            [ 0.81071907,  0.        ,  0.        ,  0.        ,  0.        ]]], dtype=float32))

    """

    if nupicRandom is None:
      nupicRandom = NupicRandom(42)

    if initialPermanence is None:
      initialPermanence = self._initialPermanence()

    coincRfArea = (coincRFShape[0] * coincRFShape[1])
    coincInputPool = coincInputPoolPct * coincRfArea

    # We will generate a list of sparse matrices
    masterPotentialM = []
    masterPermanenceM = []

    toSample = numpy.arange(coincRfArea, dtype='uint32')
    toUse = numpy.empty(coincInputPool, dtype='uint32')
    denseM = numpy.zeros(coincRfArea, dtype=realDType)
    for i in xrange(numCloneMasters):
      nupicRandom.sample(toSample, toUse)

      # Put in 1's into the potential locations
      denseM.fill(0)
      denseM[toUse] = 1
      masterPotentialM.append(SM_01_32_32(denseM.reshape(coincRFShape)))

      # Put in the initial permanences
      denseM *= initialPermanence
      masterPermanenceM.append(SM32(denseM.reshape(coincRFShape)))

      # If we are not using common initial permanences, create another
      # unique one for the next cell
      if not self.commonDistributions:
        initialPermanence = self._initialPermanence()

    return masterPotentialM, masterPermanenceM


  def _updateConnectedCoincidences(self, masters=None):
    """Update 'connected' version of the given coincidence.

    Each 'connected' coincidence is effectively a binary matrix (AKA boolean)
    matrix that is the same size as the input histogram matrices.  They have
    a 1 wherever the inputHistogram is "above synPermConnected".
    """
    # If no masterNum given, update all of them
    if masters is None:
      masters = xrange(self.numCloneMasters)

    nCellRows, nCellCols = self._coincRFShape
    cloningOn = (self.numCloneMasters != self._coincCount)
    for masterNum in masters:
      # Where are we connected?
      masterConnectedNZ = (
          self._masterPermanenceM[masterNum].whereGreaterEqual(
              0, nCellRows, 0, nCellCols, self.synPermConnected))
      rowIdxs = masterConnectedNZ[:,0]
      colIdxs = masterConnectedNZ[:,1]
      self._masterConnectedM[masterNum].setAllNonZeros(
          nCellRows, nCellCols, rowIdxs, colIdxs)
      self._masterConnectedCoincSizes[masterNum] = len(rowIdxs)

      # Update the corresponding rows in the super, mondo connected matrix that
      # come from this master
      masterConnected = (
          self._masterConnectedM[masterNum].toDense().astype('bool'))  # 0.2s
      if cloningOn:
        cells = self._cellsForMaster[masterNum]
      else:
        cells = [masterNum]

      for cell in cells:
        inputSlice = self._inputSlices[cell]
        coincSlice = self._coincSlices[cell]
        masterSubset = masterConnected[coincSlice]
        sparseCols = self._inputLayout[inputSlice][masterSubset]

        self._allConnectedM.replaceSparseRow(cell, sparseCols)  # 4s.


  def _setSlices(self):
    """Compute self._columnSlices  and self._inputSlices

    self._inputSlices are used to index into the input (assuming it's been
    shaped to a 2D array) to get the receptive field of each column.  There
    is one item in the list for each column.

    self._coincSlices are used to index into the coinc (assuming it's been
    shaped to a 2D array) to get the valid area of the column.  There
    is one item in the list for each column.

    This function is called upon unpickling, since we can't pickle slices.
    """

    self._columnCenters = numpy.array(self._computeCoincCenters(
        self.inputShape, self.coincidencesShape, self.inputBorder))
    coincInputRadius = self.coincInputRadius
    coincHeight, coincWidth = self._coincRFShape
    inputShape = self.inputShape
    inputBorder = self.inputBorder

    # Compute the input slices for each cell. This is the slice of the entire
    # input which intersects with the cell's permanence matrix.
    if self._hasTopology:
      self._inputSlices = [
          numpy.s_[max(0, cy-coincInputRadius):
                   min(inputShape[0], cy+coincInputRadius + 1),
                   max(0, cx-coincInputRadius):
                   min(inputShape[1], cx+coincInputRadius + 1)]
          for (cy, cx) in self._columnCenters]
    else:
      self._inputSlices = [numpy.s_[0:inputShape[0], 0:inputShape[1]]
                           for (cy, cx) in self._columnCenters]

    self._inputSlices2 = numpy.zeros(4 * len(self._inputSlices),
                                     dtype="uint32")
    k = 0
    for i in range(len(self._inputSlices)):
      self._inputSlices2[k] = self._inputSlices[i][0].start
      self._inputSlices2[k + 1] = self._inputSlices[i][0].stop
      self._inputSlices2[k + 2] = self._inputSlices[i][1].start
      self._inputSlices2[k + 3] = self._inputSlices[i][1].stop
      k = k + 4

    # Compute the coinc slices for each cell. This is which portion of the
    # cell's permanence matrix intersects with the input.
    if self._hasTopology:
      if self.inputShape[0] > 1:
        self._coincSlices = [
            numpy.s_[max(0, coincInputRadius - cy):
                     min(coincHeight, coincInputRadius + inputShape[0] - cy),
                     max(0, coincInputRadius-cx):
                     min(coincWidth, coincInputRadius + inputShape[1] - cx)]
            for (cy, cx) in self._columnCenters]
      else:
        self._coincSlices = [
            numpy.s_[0:1,
                     max(0, coincInputRadius-cx):
                     min(coincWidth, coincInputRadius + inputShape[1] - cx)]
            for (cy, cx) in self._columnCenters]
    else:
        self._coincSlices = [numpy.s_[0:coincHeight, 0:coincWidth]
                             for (cy, cx) in self._columnCenters]

    self._coincSlices2 = numpy.zeros((4*len(self._coincSlices)), dtype="uint32")
    k = 0
    for i in range(len(self._coincSlices)):
      self._coincSlices2[k] = self._coincSlices[i][0].start
      self._coincSlices2[k + 1] = self._coincSlices[i][0].stop
      self._coincSlices2[k + 2] = self._coincSlices[i][1].start
      self._coincSlices2[k + 3] = self._coincSlices[i][1].stop
      k = k + 4


  @staticmethod
  def _computeCoincCenters(inputShape, coincidencesShape, inputBorder):
    """Compute the centers of all coincidences, given parameters.

    This function is semi-public: tools may use it to generate good
    visualizations of what the FDRCSpatial node is doing.

    NOTE: It must be static or global function so that it can be called by
    the ColumnActivityTab inspector *before* the first compute (before the
    SP has been constructed).


    If the input shape is (7,20), shown below with * for each input.

    ********************
    ********************
    ********************
    ********************
    ********************
    ********************
    ********************

    If inputBorder is 1, we distribute the coincidences evenly over the
    the area after removing the edges,  @ shows the allowed input area below.

    ********************
    *@@@@@@@@@@@@@@@@@@*
    *@@@@@@@@@@@@@@@@@@*
    *@@@@@@@@@@@@@@@@@@*
    *@@@@@@@@@@@@@@@@@@*
    *@@@@@@@@@@@@@@@@@@*
    ********************

    Each coincidence is centered at the closest @ and looks at a area with
    coincInputRadius below it.

    This function call returns an iterator over the coincidence centers. Each
    element in iterator is a tuple: (y, x). The iterator returns elements in a
    fixed order.
    """

    # Determine Y centers
    if inputShape[0] > 1:   # 2-D layout
      startHeight = inputBorder
      stopHeight = inputShape[0] - inputBorder
    else:
      startHeight = stopHeight = 0
    heightCenters = numpy.linspace(startHeight,
                                   stopHeight,
                                   coincidencesShape[0],
                                   endpoint=False).astype('int32')

    # Determine X centers
    startWidth = inputBorder
    stopWidth = inputShape[1] - inputBorder
    widthCenters = numpy.linspace(startWidth,
                                  stopWidth,
                                  coincidencesShape[1],
                                  endpoint=False).astype('int32')

    return list(cross(heightCenters, widthCenters))


  def _updateInhibitionObj(self):
    """
    Calculate the average inhibitionRadius to use and update the inhibition
    object accordingly. This looks at the size of the average connected
    receptive field and uses that to determine the inhibition radius.
    """

    # Compute the inhibition radius.
    # If using global inhibition, just set it to include the entire region
    if self.globalInhibition:
      avgRadius = max(self.coincidencesShape)

    # Else, set it based on the average size of the connected synapses area in
    # each cell.
    else:
      totalDim = 0

      # Get the dimensions of the connected receptive fields of each cell to
      # compute the average
      minDim = numpy.inf
      maxDim = 0
      for masterNum in xrange(self.numCloneMasters):
        masterConnected = self._masterConnectedM[masterNum]
        nzs = masterConnected.getAllNonZeros()
        rows, cols = zip(*nzs)
        rows = numpy.array(rows)
        cols = numpy.array(cols)
        if len(rows) >= 2:
          height = rows.max() - rows.min() + 1
        else:
          height = 1
        if len(cols) >= 2:
          width = cols.max() - cols.min() + 1
        else:
          width = 1
        avgDim = (height + width) / 2.0
        minDim = min(minDim, avgDim)
        maxDim = max(maxDim, avgDim)
        totalDim += avgDim

      # Get average width/height in input space
      avgDim = totalDim / self.numCloneMasters
      self._rfRadiusAvg = (avgDim - 1.0) / 2.0
      self._rfRadiusMin = (minDim - 1.0) / 2.0
      self._rfRadiusMax = (maxDim - 1.0) / 2.0

      # How many columns in cell space does it correspond to?
      if self.inputShape[0] > 1:      # 2-D layout
        coincsPerInputX = (float(self.coincidencesShape[1]) /
                           (self.inputShape[1] - 2 * self.inputBorder))
        coincsPerInputY = (float(self.coincidencesShape[0]) /
                           (self.inputShape[0] - 2 * self.inputBorder))
      else:
        coincsPerInputX = coincsPerInputY = (
            float(self.coincidencesShape[1] * self.coincidencesShape[0]) /
            (self.inputShape[1] - 2 * self.inputBorder))

      avgDim *= (coincsPerInputX + coincsPerInputY) / 2
      avgRadius = (avgDim - 1.0) / 2.0
      avgRadius = max(1.0, avgRadius)

      # Can't be greater than the overall width or height of the level
      maxDim = max(self.coincidencesShape)
      avgRadius = min(avgRadius, maxDim)
      avgRadius = int(round(avgRadius))

    # Is there a need to re-instantiate the inhibition object?
    if (self._inhibitionObj is None or
        self._inhibitionObj.getInhibitionRadius() != avgRadius):
      # What is our target density?
      if self.localAreaDensity > 0:
        localAreaDensity = self.localAreaDensity
      else:
        numCellsPerInhArea =  (avgRadius * 2.0 + 1.0) ** 2
        totalCells = self.coincidencesShape[0] * self.coincidencesShape[1]
        numCellsPerInhArea = min(numCellsPerInhArea, totalCells)
        localAreaDensity = float(self.numActivePerInhArea) / numCellsPerInhArea
        # Don't let it be greater than 0.50
        localAreaDensity = min(localAreaDensity, 0.50)

      if self.spVerbosity >= 2:
        print "Updating inhibition object:"
        print "  avg. rfRadius:", self._rfRadiusAvg
        print "  avg. inhRadius:", avgRadius
        print "  Setting density to:", localAreaDensity
      self._inhibitionObj = Inhibition2(self.coincidencesShape[0], # height
                                        self.coincidencesShape[1], # width
                                        avgRadius,                 # inhRadius
                                        localAreaDensity)          # density


  def _updateMinDutyCycles(self, actDutyCycles, minPctDutyCycle, minDutyCycles):
    """
    Calculate and update the minimum acceptable duty cycle for each cell based
    on the duty cycles of the cells within its inhibition radius and the
    minPctDutyCycle.

    Parameters:
    -----------------------------------------------------------------------
    actDutyCycles:    The actual duty cycles of all cells
    minPctDutyCycle:  Each cell's minimum duty cycle will be set to
                      minPctDutyCycle times the duty cycle of the most active
                      cell within its inhibition radius
    minDutyCycles:    This array will be updated in place with the new minimum
                      acceptable duty cycles
    """

    # What is the inhibition radius?
    inhRadius = self._inhibitionObj.getInhibitionRadius()

    # Reshape the actDutyCycles to match the topology of the level
    cloningOn = (self.numCloneMasters != self._coincCount)
    if not cloningOn:
      actDutyCycles = actDutyCycles.reshape(self.coincidencesShape)
      minDutyCycles = minDutyCycles.reshape(self.coincidencesShape)

    # Special, faster handling when inhibition radius includes the entire
    # set of cells.
    if cloningOn or inhRadius >= max(self.coincidencesShape):
      minDutyCycle = minPctDutyCycle * actDutyCycles.max()
      minDutyCycles.fill(minPctDutyCycle * actDutyCycles.max())

    # Else, process each cell
    else:
      (numRows, numCols) = self.coincidencesShape
      for row in xrange(numRows):
        top = max(0, row - inhRadius)
        bottom = min(row + inhRadius + 1, numRows)
        for col in xrange(numCols):
          left = max(0, col - inhRadius)
          right = min(col + inhRadius + 1, numCols)
          maxDutyCycle = actDutyCycles[top:bottom, left:right].max()
          minDutyCycles[row, col] = maxDutyCycle * minPctDutyCycle

    if self.spVerbosity >= 2:
      print "Actual duty cycles:"
      print fdru.numpyStr(actDutyCycles, '%.4f')
      print "Recomputed min duty cycles, using inhRadius of", inhRadius
      print fdru.numpyStr(minDutyCycles, '%.4f')


  def _computeOverlapsPy(self, inputShaped, stimulusThreshold):
    """
    Computes overlaps for every column for the current input in place. The
    overlaps less than stimulus threshold are set to zero here.

    For columns with input RF going off the edge of input field, only regions
    within the input field are considered. This is equivalent to padding the
    input field with zeros.

    Parameters:
    ------------------------------------------------------------------------
    inputShaped:        input at the current time step, shaped to the input
                          topology
    stimulusThreshold:  stimulusThreshold to use


    Member variables used/updated:
    ------------------------------------------------------------------------
    _inputSlices:   Index into the input (assuming it's been shaped to a 2D
                    array) to get the receptive field of each column.
    _coincSlices:   Index into the coinc (assuming it's been shaped to a 2D
                    array) to get the valid region of each column.
    _overlaps:      Result is placed into this array which holds the overlaps of
                    each column with the input
    """

    flatInput = inputShaped.reshape(-1)
    self._allConnectedM.rightVecSumAtNZ_fast(flatInput, self._overlaps)

    # Apply stimulusThreshold
    # TODO: Is there a faster numpy operation for this?
    self._overlaps[self._overlaps < stimulusThreshold] = 0
    self._overlapsNoBoost = self._overlaps.copy()


  def _computeOverlapsCPP(self, inputShaped, stimulusThreshold):
    """
    Same as _computeOverlapsPy, but using a C++ implementation.
    """

    cpp_overlap(self._cloneMapFlat,
                self._inputSlices2, self._coincSlices2,
                inputShaped, self._masterConnectedM,
                stimulusThreshold,
                self._overlaps)


  def _computeOverlapsTest(self, inputShaped, stimulusThreshold):
    """
    Same as _computeOverlapsPy, but compares the python and C++
    implementations.
    """

    # Py version
    self._computeOverlapsPy(inputShaped, stimulusThreshold)
    overlaps2 = copy.deepcopy(self._overlaps)

    # C++ version
    self._computeOverlapsCPP(inputShaped, stimulusThreshold)

    if (abs(self._overlaps - overlaps2) > 1e-6).any():
      print self._overlaps, overlaps2, abs(self._overlaps - overlaps2)
      import pdb; pdb.set_trace()
      sys.exit(0)


  def _raiseAllPermanences(self, masterNum, minConnections=None,
                           densePerm=None, densePotential=None):
    """
    Raise all permanences of the given master. If minConnections is given, the
    permanences will be raised until at least minConnections of them are
    connected strength.

    If minConnections is left at None, all permanences will be raised by
    self._synPermBelowStimulusInc.

    After raising all permanences, we also "sparsify" the permanence matrix
    and set to 0 any permanences which are already very close to 0, this
    keeps the memory requirements of the sparse matrices used to store
    the permanences lower.

    Parameters:
    ----------------------------------------------------------------------------
    masterNum:          Which master to bump up

    minConnections:     Desired number of connected synapses to have
                        If None, then all permanences are simply bumped up
                        by self._synPermBelowStimulusInc

    densePerm:          The dense representation of the master's permanence
                        matrix, if available. If not specified, we will
                        create this from the stored sparse representation.
                        Providing this will avoid some compute overhead.
                        If provided, it is assumed that it is more recent
                        than the stored sparse matrix. The stored sparse
                        matrix will ALWAYS be updated from the densePerm if
                        the densePerm is provided.

    densePotential:     The dense representation of the master's potential
                        synapses matrix, if available. If not specified, we
                        will create this from the stored sparse potential
                        matrix.
                        Providing this will avoid some compute overhead.
                        If provided, it is assumed that it is more recent
                        than the stored sparse matrix.

    retval:             (modified, numConnections)
                          modified:       True if any permanences were raised
                          numConnections: Number of actual connected synapses
                                          (not computed if minConnections was
                                           None, so None is returned in that
                                           case.)
    """

    # It's faster to perform this operation on the dense matrices and
    # then convert to sparse once we're done since we will be potentially
    # introducing and then later removing a bunch of non-zeros.

    # Get references to the sparse perms and potential syns for this master
    sparsePerm = self._masterPermanenceM[masterNum]
    sparsePotential = self._masterPotentialM[masterNum]

    # We will trim off all synapse permanences below this value to 0 in order
    # to keep the memory requirements of the SparseMatrix lower
    trimThreshold = self.synPermActiveInc / 2.0

    # See if we already have the required number of connections. If we don't,
    # get the dense form of the permanences if we don't have them already
    if densePerm is None:
      # See if we already have enough connections, if so, we can avoid the
      # overhead of converting to dense
      if minConnections is not None:
        numConnected = sparsePerm.countWhereGreaterEqual(
            0, self._coincRFShape[0], 0, self._coincRFShape[1],
            self.synPermConnected)
        if numConnected >= minConnections:
          return (False, numConnected)
      densePerm = self._masterPermanenceM[masterNum].toDense()

    elif minConnections is not None:
      numConnected = count_gte(densePerm.reshape(-1), self.synPermConnected)
      if numConnected >= minConnections:
        sparsePerm.fromDense(densePerm)
        sparsePerm.threshold(trimThreshold)
        return (False, numConnected)

    # Get the dense form of the potential synapse locations
    if densePotential is None:
      densePotential = self._masterPotentialM[masterNum].toDense()

    # Form the array with the increments
    incrementM = densePotential.astype(realDType)
    incrementM *= self._synPermBelowStimulusInc

    # Increment until we reach our target number of connections
    assert (densePerm.dtype == realDType)
    while True:
      densePerm += incrementM
      if minConnections is None:
        numConnected = None
        break
      numConnected = count_gte(densePerm.reshape(-1), self.synPermConnected)
      if numConnected >= minConnections:
        break

    # Convert back to sparse form and trim any values that are already
    # close to zero
    sparsePerm.fromDense(densePerm)
    sparsePerm.threshold(trimThreshold)

    return (True, numConnected)


  def _bumpUpWeakCoincidences(self):
    """
    This bump-up ensures every coincidence have non-zero connections. We find
    all coincidences which have overlaps less than stimulus threshold.

    We add synPermActiveInc to all the synapses. This step when repeated over
    time leads to synapses crossing synPermConnected threshold.
    """

    # Update each cell's connected threshold based on the duty cycle before
    # inhibition. The connected threshold is linearly interpolated
    # between the points (dutyCycle:0, thresh:0) and (dutyCycle:minDuty,
    # thresh:synPermConnected). This is a line defined as: y = mx + b
    # thresh = synPermConnected/minDuty * dutyCycle
    bumpUpList = (
        self._dutyCycleBeforeInh < self._minDutyCycleBeforeInh).nonzero()[0]
    for master in bumpUpList:
      self._raiseAllPermanences(master)

    # Update the connected synapses for each master we touched.
    self._updateConnectedCoincidences(bumpUpList)

    if self.spVerbosity >= 2 and len(bumpUpList) > 0:
        print ("Bumping up permanences in following cells due to falling below"
               "minDutyCycleBeforeInh:"), bumpUpList


  def _updateBoostFactors(self):
    """
    Update the boost factors. The boost factors is linearly interpolated
    between the points (dutyCycle:0, boost:maxFiringBoost) and
    (dutyCycle:minDuty, boost:1.0). This is a line defined as: y = mx + b
    boost = (1-maxFiringBoost)/minDuty * dutyCycle + maxFiringBoost

    Parameters:
    ------------------------------------------------------------------------
    boostFactors:   numpy array of boost factors, defined per master
    """
    if self._minDutyCycleAfterInh.sum() > 0:
      self._firingBoostFactors = (
          (1 - self.maxFiringBoost) /
          self._minDutyCycleAfterInh * self._dutyCycleAfterInh +
          self.maxFiringBoost)

    self._firingBoostFactors[self._dutyCycleAfterInh >
                             self._minDutyCycleAfterInh] = 1.0


  def _updateInputUse(self, onCellIndices):
    """
    During learning (adapting permanence values), we need to be able to tell
    which inputs are going to 2 or more active cells at once.

    We step through each coinc and mark all the inputs it is connected to. The
    inputUse array acts as a counter for the number of connections to the coincs
    from each input.

    Parameters:
    ------------------------------------------------------------------------
    inputUse:   numpy array of number of coincs connected to each input
    """

    allConnected = SM32(self._allConnectedM)

    # TODO: avoid this copy
    self._inputUse[:] = allConnected.addListOfRows(
        onCellIndices).reshape(self.inputShape)


  def _adaptSynapses(self, onCellIndices, orphanCellIndices, input):
    """
    This is the main function in learning of SP. The permanence values are
    changed based on the learning rules.

    Parameters:
    ------------------------------------------------------------------------
    onCellIndices:   columns which are turned on after inhibition. The
                     permanence values of these coincs are adapted based on the
                     input.
    orphanCellIndices:  columns which had very high overlap with the input, but
                     ended up being inhibited
    input:           Input, shaped to the input topology

    retval:          list of masterCellIndices that were actually updated, or
                     None if cloning is off
    """

    # Capturing learning stats?
    if self.printPeriodicStats > 0:
      self._stats['explainedInputsCurIteration'] = set()

    # Precompute the active, inactive, and dupe inputs up front for speed
    # TODO: put these into pre-allocated arrays for speed
    self._activeInput[:] = input

    # Create a matrix containing the default permanence deltas for each input
    self._permChanges.fill(-1 * self.synPermInactiveDec)
    self._permChanges[self._activeInput] = self.synPermActiveInc
    if self.synPermActiveSharedDec != 0:
      numpy.logical_and(self._activeInput, self._inputUse>1, self._dupeInput)
      self._permChanges[self._dupeInput] -= self.synPermActiveSharedDec

    # Cloning? If so, scramble the onCells so that we pick a random one to
    # update for each master. We only update a master cell at most one time
    # per input presentation.
    cloningOn = (self.numCloneMasters != self._coincCount)
    if cloningOn:
      # Scramble the onCellIndices so that we pick a random one to update
      onCellIndices = list(onCellIndices)
      random.shuffle(onCellIndices)
      visitedMasters = set()

    # For the firing cells, update permanence values
    for columnNum in itertools.chain(onCellIndices, orphanCellIndices):

      # Get the master number
      masterNum = self._cloneMapFlat[columnNum]

      # If cloning, only visit each master once
      if cloningOn:
        if masterNum in visitedMasters:
          continue
        visitedMasters.add(masterNum)


      # Get the slices of input that overlap with the valid area of this master
      inputSlice = self._inputSlices[columnNum]
      rfActiveInput = self._activeInput[inputSlice]
      rfPermChanges = self._permChanges[inputSlice]

      # Get the potential synapses, permanence values, and connected synapses
      # for this master
      masterPotential = self._masterPotentialM[masterNum].toDense()
      masterPermanence = self._masterPermanenceM[masterNum].toDense()
      masterConnected = (
          self._masterConnectedM[masterNum].toDense().astype('bool'))

      # Make changes only over the areas that overlap the input level. For
      # coincidences near the edge of the level for example, this excludes the
      # synapses outside the edge.
      coincSlice = self._coincSlices[columnNum]
      masterValidPermanence= masterPermanence[coincSlice]

      # Capturing learning stats?
      if self.printPeriodicStats > 0:
        masterValidConnected = masterConnected[coincSlice]
        explainedInputs = self._inputLayout[inputSlice][masterValidConnected]
        self._stats['explainedInputsCurIteration'].update(explainedInputs)

      if self.spVerbosity >= 4:
        print " adapting cell:%d [%d:%d] (master:%d)" % (columnNum,
                    columnNum // self.coincidencesShape[1],
                    columnNum % self.coincidencesShape[1],
                    masterNum)
        print "  initialConnected: %d" % \
              (self._masterConnectedM[masterNum].nNonZeros())
        print "  firingLevel: %d" % (self._overlaps[columnNum])
        print "  firingBoostFactor: %f" % (self._firingBoostFactors[masterNum])
        print "  input slice: \n"
        self._printInputSlice(rfActiveInput, prefix='  ')

      # Update permanences given the active input (NOTE: The "FP" in this
      # function name stands for "Function Pointer").
      if columnNum in orphanCellIndices:
        # Decrease permanence of active inputs
        masterValidPermanence[rfActiveInput] -= self.synPermOrphanDec

      else:
        self._updatePermanenceGivenInputFP(columnNum, masterNum, input,
           self._inputUse, masterPermanence, masterValidPermanence,
           rfActiveInput, rfPermChanges)

      # Clip to absolute min and max permanence values
      numpy.clip(masterPermanence, self._synPermMin, self._synPermMax,
                 out=masterPermanence)

      # Keep only the potential syns for this cell
      numpy.multiply(masterPermanence, masterPotential, masterPermanence)


      # If we are tracking learning stats, prepare to see how many changes
      # were made to the cell connections
      if self.printPeriodicStats > 0:
        masterConnectedOrig = SM_01_32_32(self._masterConnectedM[masterNum])

      # If the number of connected synapses happens to fall below
      #     stimulusThreshold, bump up all permanences a bit.
      # We could also just wait for the "duty cycle falls below
      # minDutyCycleBeforeInb" logic to catch it, but doing it here is
      # pre-emptive and much faster.
      #
      # The "duty cycle falls below minDutyCycleBeforeInb" logic will still
      # catch other possible situations, like:
      #  * if the set of inputs a cell learned suddenly stop firing due to
      #      input statistic changes
      #  * damage to the level below
      #  * input is very sparse and we still don't pass stimulusThreshold even
      #      with stimulusThreshold conneted synapses.
      self._raiseAllPermanences(masterNum,
                                minConnections=self.stimulusThreshold,
                                densePerm=masterPermanence,
                                densePotential=masterPotential)

      # Update the matrices that contain the connected syns for this cell.
      self._updateConnectedCoincidences([masterNum])

      # If we are tracking learning stats, see how many changes were made to
      #  this cell's connections
      if self.printPeriodicStats > 0:
        origNumConnections = masterConnectedOrig.nNonZeros()
        masterConnectedOrig.logicalAnd(self._masterConnectedM[masterNum])
        numUnchanged = masterConnectedOrig.nNonZeros()
        numChanges = origNumConnections - numUnchanged
        numChanges += (self._masterConnectedM[masterNum].nNonZeros() -
                       numUnchanged)
        self._stats['numChangedConnectionsSum'][masterNum] += numChanges
        self._stats['numLearns'][masterNum] += 1

      # Verbose?
      if self.spVerbosity >= 4:
        print " done cell:%d [%d:%d] (master:%d)" % (columnNum,
                    columnNum // self.coincidencesShape[1],
                    columnNum % self.coincidencesShape[1],
                    masterNum)
        print "  newConnected: %d" % \
              (self._masterConnectedM[masterNum].nNonZeros())
        self._printSyns(columnNum, prefix='  ',
                        showValues=(self.spVerbosity >= 4))
        print

    # Return list of updated masters
    if cloningOn:
      return list(visitedMasters)
    else:
      return onCellIndices


  def _updatePermanenceGivenInputPy(
      self, columnNum, masterNum, input, inputUse, permanence, permanenceSlice,
      activeInputSlice, permChangesSlice):
    """
    Given the input to a master coincidence, update it's permanence values
    based on our learning rules.

    On Entry, we are given the slice of the permanence matrix that corresponds
    only to the area of the coincidence master that is within the borders of
    the entire input field.

    Parameters:
    ------------------------------------------------------------------------
    columnNum:        The column number of this cell
    masterNum:        The master coincidence that corresponds to this column
    input:            The entire input, shaped appropriately
    inputUse:         The same shape as input. Each entry is a count of the
                        number of *currently active cells* that are connected
                        to that input.
    permanence:       The entire masterPermanence matrix for this master
    permanenceSlice:  The slice of the masterPermanence matrix for this master
                        that intersects the input field, i.e. does not overhang
                        the outside edges of the input.
    activeInputSlice:   The portion of 'input' that intersects permanenceSlice,
                          set to True where input != 0
    permChangesSlice:   The portion of 'input' that intersects permanenceSlice,
                          set to self.synPermActiveInc where input != 0 and
                          self.synPermInactiveDec where the input == 0. This is
                          used to optimally apply self.synPermActiveInc and
                          self.synPermInactiveDec at the same time and can be
                          used for any cell whose _synPermBoostFactor is set
                          to 1.0.
    """
    # TODO: This function does nothing.

    # Apply the baseline increment/decrements
    permanenceSlice += permChangesSlice

    # If this cell has permanence boost, apply the incremental


  def _updatePermanenceGivenInputCPP(
      self, columnNum, masterNum, input, inputUse, permanence, permanenceSlice,
      activeInputSlice, permChangesSlice):
    """
    Same as _updatePermanenceGivenInputPy, but using a C++ implementation.
    """

    inputNCols = self.inputShape[1]
    masterNCols = self._masterPotentialM[masterNum].shape[1]

    # TODO: synPermBoostFactors has been removed. CPP implementation has not
    # been updated for this.
    adjustMasterValidPermanence(columnNum,
                                masterNum,
                                inputNCols,
                                masterNCols,
                                self.synPermActiveInc,
                                self.synPermInactiveDec,
                                self.synPermActiveSharedDec,
                                input,
                                inputUse,
                                self._inputSlices2,
                                self._coincSlices2,
                                self._synPermBoostFactors,
                                permanence)


  def _updatePermanenceGivenInputTest(
      self, columnNum, masterNum, input, inputUse, permanence, permanenceSlice,
      activeInputSlice, permChangesSlice):
    """
    Same as _updatePermanenceGivenInputPy, but compares the python and C++
    implementations.
    """

    mp2 = copy.deepcopy(permanence)
    mvp2 = copy.deepcopy(permanenceSlice)

    # Py version
    pdb.set_trace()
    self._updatePermanenceGivenInputPy(columnNum, masterNum, input,
         inputUse, permanence, permanenceSlice, activeInputSlice,
         permChangesSlice)

    # C++ version
    self._updatePermanenceGivenInputCPP(columnNum, masterNum, input,
         inputUse, mp2, mvp2, activeInputSlice, permChangesSlice)

    if abs(mp2 - permanence).max() > 1e-6:
      print abs(mp2 - permanence).max()
      import pdb; pdb.set_trace()
      sys.exit(0)


  def _periodicStatsCreate(self):
    """
    Allocate the periodic stats structure
    """

    self._stats = dict()
    self._stats['numChangedConnectionsSum'] = numpy.zeros(
        self.numCloneMasters, dtype=realDType)
    self._stats['numLearns'] = numpy.zeros(
        self.numCloneMasters, dtype=realDType)

    # These keep track of the min and max boost factor seen for each
    # column during each training period
    self._stats['minBoostFactor'] = numpy.zeros(self.numCloneMasters,
                                                dtype=realDType)
    self._stats['maxBoostFactor'] = numpy.zeros(self.numCloneMasters,
                                                dtype=realDType)

    # This dict maintains mappings of specific input patterns to specific
    # output patterns. It is used to detect "thrashing" of cells. We measure
    # how similar the output presentation of a specific input is to the
    # last time we saw it.
    self._stats['inputPatterns'] = dict()
    self._stats['inputPatternsLimit'] = 5000

    self._periodicStatsReset()


  def _periodicStatsReset(self):
    """
    Reset the periodic stats this is done every N iterations before capturing
    a new set of stats.
    """

    self._stats['numSamples'] = 0
    self._stats['numOnSum'] = 0
    self._stats['underCoveragePctSum'] = 0
    self._stats['overCoveragePctSum'] = 0
    self._stats['cellOverlapSums'] = 0
    self._stats['cellPctOverlapSums'] = 0
    self._stats['explainedInputsCurIteration'] = set()
    self._stats['startTime'] = time.time()

    # These keep a count of the # of changed connections per update
    # for each master
    self._stats['numChangedConnectionsSum'].fill(0)
    self._stats['numLearns'].fill(0)

    # These keep track of the min and max boost factor seen for each
    # column during each training period
    self._stats['minBoostFactor'].fill(self.maxFiringBoost)
    self._stats['maxBoostFactor'].fill(0)

    # This keeps track of the average distance between the SP output of
    # a specific input pattern now and the last time we saw it.
    self._stats['outputPatternDistanceSum'] = 0
    self._stats['outputPatternSamples'] = 0


  def _periodicStatsComputeEnd(self, activeCells, activeInputs):
    """
    Called at the end of compute. This increments the number of computes
    and also summarizes the under and over coverage and whatever other
    periodic stats we need.

    If the period is up, it then prints the accumuated stats and resets them
    for the next period

    Parameters:
    ------------------------------------------------------------------
    activeCells:      list of the active cells
    activeInputs:     list of the active inputs
    """

    # Update number of samples
    self._stats['numSamples'] += 1

    # Compute under and over coverage
    numOn = len(activeCells)
    self._stats['numOnSum'] += numOn
    expInput = self._stats['explainedInputsCurIteration']
    inputLen = len(activeInputs)

    underCoverage = len(set(activeInputs).difference(expInput))
    self._stats['underCoveragePctSum'] += float(underCoverage) / inputLen

    expInput.difference_update(activeInputs)
    overCoverage = len(expInput)
    self._stats['overCoveragePctSum'] += float(overCoverage) / inputLen


    # Keep track of the min and max boost factor seen for each column
    numpy.minimum(self._firingBoostFactors, self._stats['minBoostFactor'],
                  self._stats['minBoostFactor'])
    numpy.maximum(self._firingBoostFactors, self._stats['maxBoostFactor'],
                  self._stats['maxBoostFactor'])

    # Calculate the distance in the SP output between this input  now
    # and the last time we saw it.
    inputPattern = str(sorted(activeInputs))
    outputNZ, sampleIdx = self._stats['inputPatterns'].get(inputPattern,
                                                           (None, None))
    activeCellSet = set(activeCells)
    if outputNZ is not None:
      distance = (len(activeCellSet.difference(outputNZ)) +
                  len(outputNZ.difference(activeCellSet)))
      self._stats['inputPatterns'][inputPattern] = (activeCellSet, sampleIdx)
      self._stats['outputPatternDistanceSum'] += distance
      self._stats['outputPatternSamples'] += 1

    # Add this sample to our dict, if it's not too large already
    elif len(self._stats['inputPatterns']) < self._stats['inputPatternsLimit']:
      self._stats['inputPatterns'][inputPattern] = (activeCellSet,
                                                    self._iterNum)

    # If it's not time to print them out, return now.
    if (self._iterNum % self.printPeriodicStats) != 1:
      return

    numSamples = float(self._stats['numSamples'])

    # Calculate number of changes made per master
    masterTouched = numpy.where(self._stats['numLearns'] > 0)
    if len(masterTouched[0]) == 0:
      numMasterChanges = numpy.zeros(1)
    else:
      numMasterChanges = self._stats['numChangedConnectionsSum'][masterTouched]
      numMasterChanges /= self._stats['numLearns'][masterTouched]

    # This fills in the static learning stats into self._learningStats
    self.getLearningStats()

    # Calculate and copy the transient learning stats into the
    # self._learningStats dict, for possible retrieval later by
    # the getLearningStats() method.
    self._learningStats['elapsedTime'] = time.time() - self._stats['startTime']
    self._learningStats['activeCountAvg'] = (self._stats['numOnSum'] /
                                             numSamples)
    self._learningStats['underCoveragePct'] = (
        100.0 * self._stats['underCoveragePctSum'] / numSamples)
    self._learningStats['overCoveragePct'] = (
        (100.0 * self._stats['overCoveragePctSum'] / numSamples))
    self._learningStats['numConnectionChangesAvg'] = numMasterChanges.mean()
    self._learningStats['numConnectionChangesMin'] = numMasterChanges.min()
    self._learningStats['numConnectionChangesMax'] = numMasterChanges.max()
    self._learningStats['avgCellOverlap'] = (
        (float(self._stats['cellOverlapSums']) /
         max(1, self._stats['numOnSum'])))
    self._learningStats['avgCellPctOverlap'] = (
        (100.0 * self._stats['cellPctOverlapSums'] /
         max(1, self._stats['numOnSum'])))

    self._learningStats['firingBoostMaxChangePct'] = (
        100.0 * (self._stats['maxBoostFactor'] /
                 self._stats['minBoostFactor']).max() - 100.0)

    self._learningStats['outputRepresentationChangeAvg'] = (
        float(self._stats['outputPatternDistanceSum']) /
        max(1, self._stats['outputPatternSamples']))
    self._learningStats['outputRepresentationChangePctAvg'] = (
        100.0 * self._learningStats['outputRepresentationChangeAvg'] /
        max(1,self._learningStats['activeCountAvg']))
    self._learningStats['numUniqueInputsSeen'] = (
        len(self._stats['inputPatterns']))
    if (self._learningStats['numUniqueInputsSeen'] >=
        self._stats['inputPatternsLimit']):
      self._learningStats['numUniqueInputsSeen'] = -1

    # Print all stats captured
    print "Learning stats for the last %d iterations:" % (numSamples)
    print "  iteration #:                  %d" % (self._iterNum)
    print "  inference iteration #:        %d" % (self._inferenceIterNum)
    print "  elapsed time:                 %.2f" % (
        self._learningStats['elapsedTime'])
    print "  avg activeCount:              %.1f" % (
        self._learningStats['activeCountAvg'])
    print "  avg under/overCoverage:       %-6.1f / %-6.1f %%" % (
        self._learningStats['underCoveragePct'],
        self._learningStats['overCoveragePct'])
    print "  avg cell overlap:             %-6.1f / %-6.1f %%" % (
        self._learningStats['avgCellOverlap'],
        self._learningStats['avgCellPctOverlap'])
    print "  avg/min/max RF radius:        %-6.1f / %-6.1f / %-6.1f" % (
        self._learningStats['rfRadiusAvg'],
        self._learningStats['rfRadiusMin'],
        self._learningStats['rfRadiusMax'])
    print "  inhibition radius:            %d" % (
        self._learningStats['inhibitionRadius'])
    print "  target density:               %.5f %%" % (
        self._learningStats['targetDensityPct'])
    print "  avg/min/max/sum coinc. size:      %-6.1f / %-6d / %-6d / %-8d" % (
        self._learningStats['coincidenceSizeAvg'],
        self._learningStats['coincidenceSizeMin'],
        self._learningStats['coincidenceSizeMax'],
        self._learningStats['coincidenceSizeSum'])
    print "  avg/min/max DC before inh:    %-6.4f / %-6.4f / %-6.4f" % (
        self._learningStats['dcBeforeInhibitionAvg'],
        self._learningStats['dcBeforeInhibitionMin'],
        self._learningStats['dcBeforeInhibitionMax'])
    print "  avg/min/max DC after inh:     %-6.4f / %-6.4f / %-6.4f" % (
        self._learningStats['dcAfterInhibitionAvg'],
        self._learningStats['dcAfterInhibitionMin'],
        self._learningStats['dcAfterInhibitionMax'])
    print "  avg/min/max boost:            %-6.4f / %-6.4f / %-6.4f" % (
        self._learningStats['firingBoostAvg'],
        self._learningStats['firingBoostMin'],
        self._learningStats['firingBoostMax'])
    print "  avg/min/max # conn. changes:  %-6.4f / %-6.4f / %-6.4f" % (
        self._learningStats['numConnectionChangesAvg'],
        self._learningStats['numConnectionChangesMin'],
        self._learningStats['numConnectionChangesMax'])
    print "  max change in boost:          %.1f %%" % (
        self._learningStats['firingBoostMaxChangePct'])
    print "  avg change in output repr.:   %-6.1f / %-6.1f %%" % (
        self._learningStats['outputRepresentationChangeAvg'],
        100.0 * self._learningStats['outputRepresentationChangeAvg'] /
        max(1,self._learningStats['activeCountAvg']))
    print "  # of unique input pats seen:  %d" % (
        self._learningStats['numUniqueInputsSeen'])
    print "  # of unused columns:  %d" % (
        (self._dutyCycleAfterInh==0).sum())    

    # Reset the stats for the next period.
    self._periodicStatsReset()


  def _printInputSlice(self, inputSlice, prefix=''):
    """Print the given input slice in a nice human readable format.

    Parameters:
    ---------------------------------------------------------------------
    cell:                 The slice of input to print
    prefix:               This is printed at the start of each row of the
                          coincidence
    """

    # Shape of each coincidence
    rfHeight, rfWidth = inputSlice.shape
    syns = inputSlice != 0

    def _synStr(x):
      if not x:
        return ' '
      else:
        return '*'

    # Print them out
    for row in xrange(syns.shape[0]):
      items = map(_synStr, syns[row])
      print prefix, ''.join(items)


  def _printSyns(self, cell, prefix='', showValues=False):
    """Print the synapse permanence values for the given cell in a nice,
    human, readable format.

    Parameters:
    ---------------------------------------------------------------------
    cell:                 which cell to print
    prefix:               This is printed at the start of each row of the
                          coincidence
    showValues:           If True, print the values of each permanence.
                          If False, just print a ' ' if not connected and a '*'
                          if connected
    """

    # Shape of each coincidence
    (rfHeight, rfWidth) = self.inputShape

    # Get the synapse permanences.
    masterNum = self._cloneMapFlat[cell]
    syns = self._masterPermanenceM[masterNum].toDense()

    if showValues:
      def _synStr(x):
        if x == 0:
          return '  -- '
        elif x < 0.001:
          return '   0 '
        elif x >= self.synPermConnected:
          return '#%3.2f' % x
        else:
          return ' %3.2f' % x

    else:
      def _synStr(x):
        if x < self.synPermConnected:
          return ' '
        else:
          return '*'

    # Print them out
    for row in xrange(syns.shape[0]):
      items = map(_synStr, syns[row])
      if showValues:
        print prefix, '  '.join(items)
      else:
        print prefix, ''.join(items)


  def _printMemberSizes(self, over=100):
    """Print the size of each member."""
    members = self.__dict__.keys()
    sizeNamePairs = []
    totalSize = 0

    for member in members:
      item = self.__dict__[member]
      if hasattr(item, '__func__'):
        continue
      try:
        if hasattr(item, '__len__'):
          size = 0
          for i in xrange(len(item)):
            size += len(cPickle.dumps(item[i]))
        else:
          size = len(cPickle.dumps(item))
      except:
        print "WARNING: Can't pickle %s" % (member)
        size = 0
      sizeNamePairs.append((size, member))
      totalSize += size

    # Print them out from highest to lowest
    sizeNamePairs.sort(reverse=True)
    for (size, name) in sizeNamePairs:
      if size > over:
        print "%10d (%10.3fMb)  %s" % (size, size/1000000.0, name)

    print "\nTOTAL: %10d (%10.3fMB) " % (totalSize, totalSize/1000000.0)


  def printParams(self):
    """Print the main creation parameters associated with this instance."""
    print "FDRCSpatial2 creation parameters: "
    print "inputShape =", self.inputShape
    print "inputBorder =", self.inputBorder
    print "inputDensity =", self.inputDensity
    print "coincidencesShape =", self.coincidencesShape
    print "coincInputRadius =", self.coincInputRadius
    print "coincInputPoolPct =", self.coincInputPoolPct
    print "gaussianDist =", self.gaussianDist
    print "commonDistributions =", self.commonDistributions
    print "localAreaDensity =", self.localAreaDensity
    print "numActivePerInhArea =", self.numActivePerInhArea
    print "stimulusThreshold =", self.stimulusThreshold
    print "synPermInactiveDec =", self.synPermInactiveDec
    print "synPermActiveInc =", self.synPermActiveInc
    print "synPermActiveSharedDec =", self.synPermActiveSharedDec
    print "synPermOrphanDec =", self.synPermOrphanDec
    print "synPermConnected =", self.synPermConnected
    print "minPctDutyCycleBeforeInh =", self.minPctDutyCycleBeforeInh
    print "minPctDutyCycleAfterInh =", self.minPctDutyCycleAfterInh
    print "dutyCyclePeriod =", self.dutyCyclePeriod
    print "maxFiringBoost =", self.maxFiringBoost
    print "maxSSFiringBoost =", self.maxSSFiringBoost
    print "maxSynPermBoost =", self.maxSynPermBoost
    print "useHighTier =",self.useHighTier
    print "minDistance =", self.minDistance
    print "spVerbosity =", self.spVerbosity
    print "printPeriodicStats =", self.printPeriodicStats
    print "testMode =", self.testMode
    print "numCloneMasters =", self.numCloneMasters
