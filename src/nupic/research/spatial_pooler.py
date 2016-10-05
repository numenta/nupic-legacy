# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2016, Numenta, Inc.  Unless you have an agreement
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
from nupic.bindings.math import (SM32 as SparseMatrix,
                                 SM_01_32_32 as SparseBinaryMatrix,
                                 GetNTAReal,
                                 Random as NupicRandom)
from nupic.math import topology



realDType = GetNTAReal()
uintType = "uint32"

VERSION = 3



class InvalidSPParamValueError(ValueError):
  """The user passed an invalid value for a SpatialPooler parameter
  """
  pass



class _SparseMatrixCorticalColumnAdapter(object):
  """ Many functions in SpatialPooler operate on a columnIndex but use an
  underlying storage implementation based on a Sparse Matrix in which cortical
  columns are represented as rows.  This can be confusing to someone trying to
  follow the algorithm, confusing terminology between matrix math and cortical
  columns.  This class is provided to abstract away some of the details of the
  underlying implementation, providing a cleaner API that isn't specific to
  sparse matrices.
  """

  def __getitem__(self, columnIndex):
    """ Wraps getRow() such that instances may be indexed by columnIndex.
    """
    return super(_SparseMatrixCorticalColumnAdapter, self).getRow(columnIndex)


  def replace(self, columnIndex, bitmap):
    """ Wraps replaceSparseRow()
    """
    return super(_SparseMatrixCorticalColumnAdapter, self).replaceSparseRow(
      columnIndex, bitmap
    )


  def update(self, columnIndex, vector):
    """ Wraps setRowFromDense()
    """
    return super(_SparseMatrixCorticalColumnAdapter, self).setRowFromDense(
      columnIndex, vector
    )



class CorticalColumns(_SparseMatrixCorticalColumnAdapter, SparseMatrix):
  """ SparseMatrix variant of _SparseMatrixCorticalColumnAdapter.  Use in cases
  where column connections are represented as float values, such as permanence
  values
  """
  pass



class BinaryCorticalColumns(_SparseMatrixCorticalColumnAdapter,
                            SparseBinaryMatrix):
  """ SparseBinaryMatrix variant of _SparseMatrixCorticalColumnAdapter.  Use in
  cases where column connections are represented as bitmaps.
  """
  pass



class SpatialPooler(object):
  """
  This class implements the spatial pooler. It is in charge of handling the
  relationships between the columns of a region and the inputs bits. The
  primary public interface to this function is the "compute" method, which
  takes in an input vector and returns a list of activeColumns columns.
  Example Usage:
  >
  > sp = SpatialPooler(...)
  > for line in file:
  >   inputVector = numpy.array(line)
  >   sp.compute(inputVector)
  >   ...
  """

  def __init__(self,
               inputDimensions=(32, 32),
               columnDimensions=(64, 64),
               potentialRadius=16,
               potentialPct=0.5,
               globalInhibition=False,
               localAreaDensity=-1.0,
               numActiveColumnsPerInhArea=10.0,
               stimulusThreshold=0,
               synPermInactiveDec=0.008,
               synPermActiveInc=0.05,
               synPermConnected=0.10,
               minPctOverlapDutyCycle=0.001,
               minPctActiveDutyCycle=0.001,
               dutyCyclePeriod=1000,
               maxBoost=10.0,
               seed=-1,
               spVerbosity=0,
               wrapAround=True
               ):
    """
    Parameters:
    ----------------------------
    @param inputDimensions:
      A sequence representing the dimensions of the input vector. Format is
      (height, width, depth, ...), where each value represents the size of the
      dimension.  For a topology of one dimension with 100 inputs use 100, or
      (100,). For a two dimensional topology of 10x5 use (10,5).
    @param columnDimensions:
      A sequence representing the dimensions of the columns in the region.
      Format is (height, width, depth, ...), where each value represents the
      size of the dimension.  For a topology of one dimension with 2000 columns
      use 2000, or (2000,). For a three dimensional topology of 32x64x16 use
      (32, 64, 16).
    @param potentialRadius:
      This parameter determines the extent of the input that each column can
      potentially be connected to.  This can be thought of as the input bits
      that are visible to each column, or a 'receptiveField' of the field of
      vision. A large enough value will result in 'global coverage', meaning
      that each column can potentially be connected to every input bit. This
      parameter defines a square (or hyper
      square) area: a column will have a max square potential pool with sides of
      length 2 * potentialRadius + 1.
    @param potentialPct:
      The percent of the inputs, within a column's potential radius, that a
      column can be connected to.  If set to 1, the column will be connected
      to every input within its potential radius. This parameter is used to
      give each column a unique potential pool when a large potentialRadius
      causes overlap between the columns. At initialization time we choose
      ((2*potentialRadius + 1)^(# inputDimensions) * potentialPct) input bits
      to comprise the column's potential pool.
    @param globalInhibition:
      If true, then during inhibition phase the winning columns are selected
      as the most active columns from the region as a whole. Otherwise, the
      winning columns are selected with respect to their local neighborhoods.
      Using global inhibition boosts performance x60.
    @param localAreaDensity:
      The desired density of active columns within a local inhibition area
      (the size of which is set by the internally calculated inhibitionRadius,
      which is in turn determined from the average size of the connected
      potential pools of all columns). The inhibition logic will insure that
      at most N columns remain ON within a local inhibition area, where
      N = localAreaDensity * (total number of columns in inhibition area).
    @param numActiveColumnsPerInhArea:
      An alternate way to control the density of the active columns. If
      numActiveColumnsPerInhArea is specified then localAreaDensity must be
      less than 0, and vice versa.  When using numActiveColumnsPerInhArea, the
      inhibition logic will insure that at most 'numActiveColumnsPerInhArea'
      columns remain ON within a local inhibition area (the size of which is
      set by the internally calculated inhibitionRadius, which is in turn
      determined from the average size of the connected receptive fields of all
      columns). When using this method, as columns learn and grow their
      effective receptive fields, the inhibitionRadius will grow, and hence the
      net density of the active columns will *decrease*. This is in contrast to
      the localAreaDensity method, which keeps the density of active columns
      the same regardless of the size of their receptive fields.
    @param stimulusThreshold:
      This is a number specifying the minimum number of synapses that must be
      on in order for a columns to turn ON. The purpose of this is to prevent
      noise input from activating columns. Specified as a percent of a fully
      grown synapse.
    @param synPermInactiveDec:
      The amount by which an inactive synapse is decremented in each round.
      Specified as a percent of a fully grown synapse.
    @param synPermActiveInc:
      The amount by which an active synapse is incremented in each round.
      Specified as a percent of a fully grown synapse.
    @param synPermConnected:
      The default connected threshold. Any synapse whose permanence value is
      above the connected threshold is a "connected synapse", meaning it can
      contribute to the cell's firing.
    @param minPctOverlapDutyCycle:
      A number between 0 and 1.0, used to set a floor on how often a column
      should have at least stimulusThreshold active inputs. Periodically, each
      column looks at the overlap duty cycle of all other columns within its
      inhibition radius and sets its own internal minimal acceptable duty cycle
      to: minPctDutyCycleBeforeInh * max(other columns' duty cycles).  On each
      iteration, any column whose overlap duty cycle falls below this computed
      value will  get all of its permanence values boosted up by
      synPermActiveInc. Raising all permanences in response to a sub-par duty
      cycle before  inhibition allows a cell to search for new inputs when
      either its previously learned inputs are no longer ever active, or when
      the vast majority of them have been "hijacked" by other columns.
    @param minPctActiveDutyCycle:
      A number between 0 and 1.0, used to set a floor on how often a column
      should be activate.  Periodically, each column looks at the activity duty
      cycle of all other columns within its inhibition radius and sets its own
      internal minimal acceptable duty cycle to: minPctDutyCycleAfterInh *
      max(other columns' duty cycles).  On each iteration, any column whose duty
      cycle after inhibition falls below this computed value will get its
      internal boost factor increased.
    @param dutyCyclePeriod:
      The period used to calculate duty cycles. Higher values make it take
      longer to respond to changes in boost or synPerConnectedCell. Shorter
      values make it more unstable and likely to oscillate.
    @param maxBoost:
      The maximum overlap boost factor. Each column's overlap gets multiplied
      by a boost factor before it gets considered for inhibition.  The actual
      boost factor for a column is number between 1.0 and maxBoost. A boost
      factor of 1.0 is used if the duty cycle is >= minOverlapDutyCycle,
      maxBoost is used if the duty cycle is 0, and any duty cycle in between is
      linearly extrapolated from these 2 endpoints.
    @param seed:
      Seed for our own pseudo-random number generator.
    @param spVerbosity:
      spVerbosity level: 0, 1, 2, or 3
    @param wrapAround:
      Determines if inputs at the beginning and end of an input dimension should
      be considered neighbors when mapping columns to inputs.
    """
    if (numActiveColumnsPerInhArea == 0 and
        (localAreaDensity == 0 or localAreaDensity > 0.5)):
      raise InvalidSPParamValueError("Inhibition parameters are invalid")

    columnDimensions = numpy.array(columnDimensions, ndmin=1)
    numColumns = columnDimensions.prod()

    if not isinstance(numColumns, (int, long)) or numColumns <= 0:
      raise InvalidSPParamValueError("Invalid number of columns ({})"
                                     .format(repr(numColumns)))
    inputDimensions = numpy.array(inputDimensions, ndmin=1)
    numInputs = inputDimensions.prod()

    if not isinstance(numInputs, (int, long)) or numInputs <= 0:
      raise InvalidSPParamValueError("Invalid number of inputs ({}"
                                     .format(repr(numInputs)))

    if inputDimensions.size != columnDimensions.size:
      raise InvalidSPParamValueError(
        "Input dimensions must match column dimensions")

    self._seed(seed)

    self._numInputs = int(numInputs)
    self._numColumns = int(numColumns)
    self._columnDimensions = columnDimensions
    self._inputDimensions = inputDimensions
    self._potentialRadius = int(min(potentialRadius, numInputs))
    self._potentialPct = potentialPct
    self._globalInhibition = globalInhibition
    self._numActiveColumnsPerInhArea = int(numActiveColumnsPerInhArea)
    self._localAreaDensity = localAreaDensity
    self._stimulusThreshold = stimulusThreshold
    self._synPermInactiveDec = synPermInactiveDec
    self._synPermActiveInc = synPermActiveInc
    self._synPermBelowStimulusInc = synPermConnected / 10.0
    self._synPermConnected = synPermConnected
    self._minPctOverlapDutyCycles = minPctOverlapDutyCycle
    self._minPctActiveDutyCycles = minPctActiveDutyCycle
    self._dutyCyclePeriod = dutyCyclePeriod
    self._maxBoost = maxBoost
    self._spVerbosity = spVerbosity
    self._wrapAround = wrapAround
    self._synPermMin = 0.0
    self._synPermMax = 1.0
    self._synPermTrimThreshold = synPermActiveInc / 2.0
    self._overlaps = numpy.zeros(self._numColumns, dtype=realDType)
    self._boostedOverlaps = numpy.zeros(self._numColumns, dtype=realDType)

    if self._synPermTrimThreshold >= self._synPermConnected:
      raise InvalidSPParamValueError(
        "synPermTrimThreshold ({}) must be less than synPermConnected ({})"
        .format(repr(self._synPermTrimThreshold),
                repr(self._synPermConnected)))

    self._updatePeriod = 50
    initConnectedPct = 0.5
    self._version = VERSION
    self._iterationNum = 0
    self._iterationLearnNum = 0

    # Store the set of all inputs within each columns potential pool as a
    # single adjacency matrix such that matrix rows map to cortical columns,
    # and matrix columns map to input buts.  If potentialPools[i][j] == 1,
    # then input bit 'j' is in column 'i's potential pool. A column can only be
    # connected to inputs in its potential pool.  Here, BinaryCorticalColumns
    # is used to provide cortical column-centric semantics for what is
    # otherwise a sparse binary matrix implementation.  Sparse binary matrix is
    # used as an optimization since a column will only be connected to a small
    # fraction of input bits.
    self._potentialPools = BinaryCorticalColumns(numInputs)
    self._potentialPools.resize(numColumns, numInputs)

    # Initialize the permanences for each column. Similar to the
    # 'self._potentialPools', the permanences are stored in a matrix whose rows
    # represent the cortical columns, and whose columns represent the input
    # bits. If self._permanences[i][j] = 0.2, then the synapse connecting
    # cortical column 'i' to input bit 'j'  has a permanence of 0.2. Here,
    # CorticalColumns is used to provide cortical column-centric semantics for
    # what is otherwise a sparse matrix implementation.  Sparse matrix is used
    # as an optimization to improve computation time of alforithms that
    # require iterating over the data  structure. This permanence matrix is
    # only allowed to have non-zero elements where the potential pool is
    # non-zero.
    self._permanences = CorticalColumns(numColumns, numInputs)

    # Initialize a tiny random tie breaker. This is used to determine winning
    # columns where the overlaps are identical.
    self._tieBreaker = numpy.array([0.01 * self._random.getReal64() for i in
                                      xrange(self._numColumns)],
                                    dtype=realDType)

    # 'self._connectedSynapses' is a similar matrix to 'self._permanences'
    # (rows represent cortical columns, columns represent input bits) whose
    # entries represent whether the cortical column is connected to the input
    # bit, i.e. its permanence value is greater than 'synPermConnected'. While
    # this information is readily available from the 'self._permanence' matrix,
    # it is stored separately for efficiency purposes.
    self._connectedSynapses = BinaryCorticalColumns(numInputs)
    self._connectedSynapses.resize(numColumns, numInputs)

    # Stores the number of connected synapses for each column. This is simply
    # a sum of each row of 'self._connectedSynapses'. again, while this
    # information is readily available from 'self._connectedSynapses', it is
    # stored separately for efficiency purposes.
    self._connectedCounts = numpy.zeros(numColumns, dtype=realDType)

    # Initialize the set of permanence values for each column. Ensure that
    # each column is connected to enough input bits to allow it to be
    # activated.
    for columnIndex in xrange(numColumns):
      potential = self._mapPotential(columnIndex)
      self._potentialPools.replace(columnIndex, potential.nonzero()[0])
      perm = self._initPermanence(potential, initConnectedPct)
      self._updatePermanencesForColumn(perm, columnIndex, raisePerm=True)

    self._overlapDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._activeDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._minOverlapDutyCycles = numpy.zeros(numColumns,
                                             dtype=realDType)
    self._minActiveDutyCycles = numpy.zeros(numColumns,
                                            dtype=realDType)
    self._boostFactors = numpy.ones(numColumns, dtype=realDType)

    # The inhibition radius determines the size of a column's local
    # neighborhood.  A cortical column must overcome the overlap score of
    # columns in its neighborhood in order to become active. This radius is
    # updated every learning round. It grows and shrinks with the average
    # number of connected synapses per column.
    self._inhibitionRadius = 0
    self._updateInhibitionRadius()

    if self._spVerbosity > 0:
      self.printParameters()


  def getColumnDimensions(self):
    """Returns the dimensions of the columns in the region"""
    return self._columnDimensions


  def getInputDimensions(self):
    """Returns the dimensions of the input vector"""
    return self._inputDimensions


  def getNumColumns(self):
    """Returns the total number of columns"""
    return self._numColumns


  def getNumInputs(self):
    """Returns the total number of inputs"""
    return self._numInputs


  def getPotentialRadius(self):
    """Returns the potential radius"""
    return self._potentialRadius


  def setPotentialRadius(self, potentialRadius):
    """Sets the potential radius"""
    self._potentialRadius = potentialRadius


  def getPotentialPct(self):
    """Returns the potential percent"""
    return self._potentialPct


  def setPotentialPct(self, potentialPct):
    """Sets the potential percent"""
    self._potentialPct = potentialPct


  def getGlobalInhibition(self):
    """Returns whether global inhibition is enabled"""
    return self._globalInhibition


  def setGlobalInhibition(self, globalInhibition):
    """Sets global inhibition"""
    self._globalInhibition = globalInhibition


  def getNumActiveColumnsPerInhArea(self):
    """Returns the number of active columns per inhibition area. Returns a
    value less than 0 if parameter is unused"""
    return self._numActiveColumnsPerInhArea


  def setNumActiveColumnsPerInhArea(self, numActiveColumnsPerInhArea):
    """Sets the number of active columns per inhibition area. Invalidates the
    'localAreaDensity' parameter"""
    assert(numActiveColumnsPerInhArea > 0)
    self._numActiveColumnsPerInhArea = numActiveColumnsPerInhArea
    self._localAreaDensity = 0


  def getLocalAreaDensity(self):
    """Returns the local area density. Returns a value less than 0 if parameter
    is unused"""
    return self._localAreaDensity


  def setLocalAreaDensity(self, localAreaDensity):
    """Sets the local area density. Invalidates the 'numActiveColumnsPerInhArea'
    parameter"""
    assert(localAreaDensity > 0 and localAreaDensity <= 1)
    self._localAreaDensity = localAreaDensity
    self._numActiveColumnsPerInhArea = 0


  def getStimulusThreshold(self):
    """Returns the stimulus threshold"""
    return self._stimulusThreshold


  def setStimulusThreshold(self, stimulusThreshold):
    """Sets the stimulus threshold"""
    self._stimulusThreshold = stimulusThreshold


  def getInhibitionRadius(self):
    """Returns the inhibition radius"""
    return self._inhibitionRadius


  def setInhibitionRadius(self, inhibitionRadius):
    """Sets the inhibition radius"""
    self._inhibitionRadius = inhibitionRadius


  def getDutyCyclePeriod(self):
    """Returns the duty cycle period"""
    return self._dutyCyclePeriod


  def setDutyCyclePeriod(self, dutyCyclePeriod):
    """Sets the duty cycle period"""
    self._dutyCyclePeriod = dutyCyclePeriod


  def getMaxBoost(self):
    """Returns the maximum boost value"""
    return self._maxBoost


  def setMaxBoost(self, maxBoost):
    """Sets the maximum boost value"""
    self._maxBoost = maxBoost


  def getIterationNum(self):
    """Returns the iteration number"""
    return self._iterationNum


  def setIterationNum(self, iterationNum):
    """Sets the iteration number"""
    self._iterationNum = iterationNum


  def getIterationLearnNum(self):
    """Returns the learning iteration number"""
    return self._iterationLearnNum


  def setIterationLearnNum(self, iterationLearnNum):
    """Sets the learning iteration number"""
    self._iterationLearnNum = iterationLearnNum


  def getSpVerbosity(self):
    """Returns the verbosity level"""
    return self._spVerbosity


  def setSpVerbosity(self, spVerbosity):
    """Sets the verbosity level"""
    self._spVerbosity = spVerbosity


  def getUpdatePeriod(self):
    """Returns the update period"""
    return self._updatePeriod


  def setUpdatePeriod(self, updatePeriod):
    """Sets the update period"""
    self._updatePeriod = updatePeriod


  def getSynPermTrimThreshold(self):
    """Returns the permanence trim threshold"""
    return self._synPermTrimThreshold


  def setSynPermTrimThreshold(self, synPermTrimThreshold):
    """Sets the permanence trim threshold"""
    self._synPermTrimThreshold = synPermTrimThreshold


  def getSynPermActiveInc(self):
    """Returns the permanence increment amount for active synapses
    inputs"""
    return self._synPermActiveInc


  def setSynPermActiveInc(self, synPermActiveInc):
    """Sets the permanence increment amount for active synapses"""
    self._synPermActiveInc = synPermActiveInc


  def getSynPermInactiveDec(self):
    """Returns the permanence decrement amount for inactive synapses"""
    return self._synPermInactiveDec


  def setSynPermInactiveDec(self, synPermInactiveDec):
    """Sets the permanence decrement amount for inactive synapses"""
    self._synPermInactiveDec = synPermInactiveDec


  def getSynPermBelowStimulusInc(self):
    """Returns the permanence increment amount for columns that have not been
    recently active """
    return self._synPermBelowStimulusInc


  def setSynPermBelowStimulusInc(self, synPermBelowStimulusInc):
    """Sets the permanence increment amount for columns that have not been
    recently active """
    self._synPermBelowStimulusInc = synPermBelowStimulusInc


  def getSynPermConnected(self):
    """Returns the permanence amount that qualifies a synapse as
    being connected"""
    return self._synPermConnected


  def setSynPermConnected(self, synPermConnected):
    """Sets the permanence amount that qualifies a synapse as being
    connected"""
    self._synPermConnected = synPermConnected


  def getMinPctOverlapDutyCycles(self):
    """Returns the minimum tolerated overlaps, given as percent of
    neighbors overlap score"""
    return self._minPctOverlapDutyCycles


  def setMinPctOverlapDutyCycles(self, minPctOverlapDutyCycles):
    """Sets the minimum tolerated activity duty cycle, given as percent of
    neighbors' activity duty cycle"""
    self._minPctOverlapDutyCycles = minPctOverlapDutyCycles


  def getMinPctActiveDutyCycles(self):
    """Returns the minimum tolerated activity duty cycle, given as percent of
    neighbors' activity duty cycle"""
    return self._minPctActiveDutyCycles


  def setMinPctActiveDutyCycles(self, minPctActiveDutyCycles):
    """Sets the minimum tolerated activity duty, given as percent of
    neighbors' activity duty cycle"""
    self._minPctActiveDutyCycles = minPctActiveDutyCycles


  def getBoostFactors(self, boostFactors):
    """Returns the boost factors for all columns. 'boostFactors' size must
    match the number of columns"""
    boostFactors[:] = self._boostFactors[:]


  def setBoostFactors(self, boostFactors):
    """Sets the boost factors for all columns. 'boostFactors' size must match
    the number of columns"""
    self._boostFactors[:] = boostFactors[:]


  def getOverlapDutyCycles(self, overlapDutyCycles):
    """Returns the overlap duty cycles for all columns. 'overlapDutyCycles'
    size must match the number of columns"""
    overlapDutyCycles[:] = self._overlapDutyCycles[:]


  def setOverlapDutyCycles(self, overlapDutyCycles):
    """Sets the overlap duty cycles for all columns. 'overlapDutyCycles'
    size must match the number of columns"""
    self._overlapDutyCycles[:] = overlapDutyCycles


  def getActiveDutyCycles(self, activeDutyCycles):
    """Returns the activity duty cycles for all columns. 'activeDutyCycles'
    size must match the number of columns"""
    activeDutyCycles[:] = self._activeDutyCycles[:]


  def setActiveDutyCycles(self, activeDutyCycles):
    """Sets the activity duty cycles for all columns. 'activeDutyCycles'
    size must match the number of columns"""
    self._activeDutyCycles[:] = activeDutyCycles


  def getMinOverlapDutyCycles(self, minOverlapDutyCycles):
    """Returns the minimum overlap duty cycles for all columns.
    '_minOverlapDutyCycles' size must match the number of columns"""
    minOverlapDutyCycles[:] = self._minOverlapDutyCycles[:]


  def setMinOverlapDutyCycles(self, minOverlapDutyCycles):
    """Sets the minimum overlap duty cycles for all columns.
    '_minOverlapDutyCycles' size must match the number of columns"""
    self._minOverlapDutyCycles[:] = minOverlapDutyCycles[:]


  def getMinActiveDutyCycles(self, minActiveDutyCycles):
    """Returns the minimum activity duty cycles for all columns.
    '_minActiveDutyCycles' size must match the number of columns"""
    minActiveDutyCycles[:] = self._minActiveDutyCycles[:]


  def setMinActiveDutyCycles(self, minActiveDutyCycles):
    """Sets the minimum activity duty cycles for all columns.
    '_minActiveDutyCycles' size must match the number of columns"""
    self._minActiveDutyCycles = minActiveDutyCycles


  def getPotential(self, columnIndex, potential):
    """Returns the potential mapping for a given column. 'potential' size
    must match the number of inputs"""
    assert(columnIndex < self._numColumns)
    potential[:] = self._potentialPools[columnIndex]


  def setPotential(self, columnIndex, potential):
    """Sets the potential mapping for a given column. 'potential' size
    must match the number of inputs, and must be greater than _stimulusThreshold """
    assert(column < self._numColumns)

    potentialSparse = numpy.where(potential > 0)[0]
    if len(potentialSparse) < self._stimulusThreshold:
      raise Exception("This is likely due to a " +
      "value of stimulusThreshold that is too large relative " +
      "to the input size.")

    self._potentialPools.replace(columnIndex, potentialSparse)


  def getPermanence(self, columnIndex, permanence):
    """Returns the permanence values for a given column. 'permanence' size
    must match the number of inputs"""
    assert(columnIndex < self._numColumns)
    permanence[:] = self._permanences[columnIndex]


  def setPermanence(self, columnIndex, permanence):
    """Sets the permanence values for a given column. 'permanence' size
    must match the number of inputs"""
    assert(columnIndex < self._numColumns)
    self._updatePermanencesForColumn(permanence, columnIndex, raisePerm=False)


  def getConnectedSynapses(self, columnIndex, connectedSynapses):
    """Returns the connected synapses for a given column.
    'connectedSynapses' size must match the number of inputs"""
    assert(columnIndex < self._numColumns)
    connectedSynapses[:] = self._connectedSynapses[columnIndex]


  def getConnectedCounts(self, connectedCounts):
    """Returns the number of connected synapses for all columns.
    'connectedCounts' size must match the number of columns"""
    connectedCounts[:] = self._connectedCounts[:]


  def getOverlaps(self):
    """Returns the overlap score for each column."""
    return self._overlaps


  def getBoostedOverlaps(self):
    """Returns the boosted overlap score for each column."""
    return self._boostedOverlaps


  def compute(self, inputVector, learn, activeArray):
    """
    This is the primary public method of the SpatialPooler class. This
    function takes a input vector and outputs the indices of the active columns.
    If 'learn' is set to True, this method also updates the permanences of the
    columns.

    @param inputVector: A numpy array of 0's and 1's that comprises the input
        to the spatial pooler. The array will be treated as a one dimensional
        array, therefore the dimensions of the array do not have to match the
        exact dimensions specified in the class constructor. In fact, even a
        list would suffice. The number of input bits in the vector must,
        however, match the number of bits specified by the call to the
        constructor. Therefore there must be a '0' or '1' in the array for
        every input bit.
    @param learn: A boolean value indicating whether learning should be
        performed. Learning entails updating the  permanence values of the
        synapses, and hence modifying the 'state' of the model. Setting
        learning to 'off' freezes the SP and has many uses. For example, you
        might want to feed in various inputs and examine the resulting SDR's.
    @param activeArray: An array whose size is equal to the number of columns.
        Before the function returns this array will be populated with 1's at
        the indices of the active columns, and 0's everywhere else.
    """
    if not isinstance(inputVector, numpy.ndarray):
      raise TypeError("Input vector must be a numpy array, not %s" %
                      str(type(inputVector)))

    if inputVector.size != self._numInputs:
      raise ValueError(
          "Input vector dimensions don't match. Expecting %s but got %s" % (
              inputVector.size, self._numInputs))

    self._updateBookeepingVars(learn)
    inputVector = numpy.array(inputVector, dtype=realDType)
    inputVector.reshape(-1)
    self._overlaps = self._calculateOverlap(inputVector)

    # Apply boosting when learning is on
    if learn:
      self._boostedOverlaps = self._boostFactors * self._overlaps
    else:
      self._boostedOverlaps = self._overlaps

    # Apply inhibition to determine the winning columns
    activeColumns = self._inhibitColumns(self._boostedOverlaps)

    if learn:
      self._adaptSynapses(inputVector, activeColumns)
      self._updateDutyCycles(self._overlaps, activeColumns)
      self._bumpUpWeakColumns()
      self._updateBoostFactors()
      if self._isUpdateRound():
        self._updateInhibitionRadius()
        self._updateMinDutyCycles()

    activeArray.fill(0)
    activeArray[activeColumns] = 1


  def stripUnlearnedColumns(self, activeArray):
    """Removes the set of columns who have never been active from the set of
    active columns selected in the inhibition round. Such columns cannot
    represent learned pattern and are therefore meaningless if only inference
    is required. This should not be done when using a random, unlearned SP
    since you would end up with no active columns.

    @param activeArray: An array whose size is equal to the number of columns.
        Any columns marked as active with an activeDutyCycle of 0 have
        never been activated before and therefore are not active due to
        learning. Any of these (unlearned) columns will be disabled (set to 0).
    """
    neverLearned = numpy.where(self._activeDutyCycles == 0)[0]
    activeArray[neverLearned] = 0


  def _updateMinDutyCycles(self):
    """
    Updates the minimum duty cycles defining normal activity for a column. A
    column with activity duty cycle below this minimum threshold is boosted.
    """
    if self._globalInhibition or self._inhibitionRadius > self._numInputs:
      self._updateMinDutyCyclesGlobal()
    else:
      self._updateMinDutyCyclesLocal()


  def _updateMinDutyCyclesGlobal(self):
    """
    Updates the minimum duty cycles in a global fashion. Sets the minimum duty
    cycles for the overlap and activation of all columns to be a percent of the
    maximum in the region, specified by minPctOverlapDutyCycle and
    minPctActiveDutyCycle respectively. Functionality it is equivalent to
    _updateMinDutyCyclesLocal, but this function exploits the globality of the
    computation to perform it in a straightforward, and more efficient manner.
    """
    self._minOverlapDutyCycles.fill(
        self._minPctOverlapDutyCycles * self._overlapDutyCycles.max()
      )
    self._minActiveDutyCycles.fill(
        self._minPctActiveDutyCycles * self._activeDutyCycles.max()
      )


  def _updateMinDutyCyclesLocal(self):
    """
    Updates the minimum duty cycles. The minimum duty cycles are determined
    locally. Each column's minimum duty cycles are set to be a percent of the
    maximum duty cycles in the column's neighborhood. Unlike
    _updateMinDutyCyclesGlobal, here the values can be quite different for
    different columns.
    """
    for column in xrange(self._numColumns):
      neighborhood = self._getColumnNeighborhood(column)

      maxActiveDuty = self._activeDutyCycles[neighborhood].max()
      maxOverlapDuty = self._overlapDutyCycles[neighborhood].max()

      self._minActiveDutyCycles[column] = (maxActiveDuty *
                                           self._minPctActiveDutyCycles)
      self._minOverlapDutyCycles[column] = (maxOverlapDuty *
                                            self._minPctOverlapDutyCycles)





  def _updateDutyCycles(self, overlaps, activeColumns):
    """
    Updates the duty cycles for each column. The OVERLAP duty cycle is a moving
    average of the number of inputs which overlapped with the each column. The
    ACTIVITY duty cycles is a moving average of the frequency of activation for
    each column.

    Parameters:
    ----------------------------
    @param overlaps:
                    An array containing the overlap score for each column.
                    The overlap score for a column is defined as the number
                    of synapses in a "connected state" (connected synapses)
                    that are connected to input bits which are turned on.
    @param activeColumns:
                    An array containing the indices of the active columns,
                    the sparse set of columns which survived inhibition
    """
    overlapArray = numpy.zeros(self._numColumns, dtype=realDType)
    activeArray = numpy.zeros(self._numColumns, dtype=realDType)
    overlapArray[overlaps > 0] = 1
    activeArray[activeColumns] = 1

    period = self._dutyCyclePeriod
    if (period > self._iterationNum):
      period = self._iterationNum

    self._overlapDutyCycles = self._updateDutyCyclesHelper(
                                self._overlapDutyCycles,
                                overlapArray,
                                period
                              )

    self._activeDutyCycles = self._updateDutyCyclesHelper(
                                self._activeDutyCycles,
                                activeArray,
                                period
                              )



  def _updateInhibitionRadius(self):
    """
    Update the inhibition radius. The inhibition radius is a measure of the
    square (or hypersquare) of columns that each a column is "connected to"
    on average. Since columns are are not connected to each other directly, we
    determine this quantity by first figuring out how many *inputs* a column is
    connected to, and then multiplying it by the total number of columns that
    exist for each input. For multiple dimension the aforementioned
    calculations are averaged over all dimensions of inputs and columns. This
    value is meaningless if global inhibition is enabled.
    """
    if self._globalInhibition:
      self._inhibitionRadius = int(self._columnDimensions.max())
      return

    avgConnectedSpan = numpy.average(
                          [self._avgConnectedSpanForColumnND(i)
                          for i in xrange(self._numColumns)]
                        )
    columnsPerInput = self._avgColumnsPerInput()
    diameter = avgConnectedSpan * columnsPerInput
    radius = (diameter - 1) / 2.0
    radius = max(1.0, radius)
    self._inhibitionRadius = int(radius + 0.5)


  def _avgColumnsPerInput(self):
    """
    The average number of columns per input, taking into account the topology
    of the inputs and columns. This value is used to calculate the inhibition
    radius. This function supports an arbitrary number of dimensions. If the
    number of column dimensions does not match the number of input dimensions,
    we treat the missing, or phantom dimensions as 'ones'.
    """
    #TODO: extend to support different number of dimensions for inputs and
    # columns
    numDim = max(self._columnDimensions.size, self._inputDimensions.size)
    colDim = numpy.ones(numDim)
    colDim[:self._columnDimensions.size] = self._columnDimensions

    inputDim = numpy.ones(numDim)
    inputDim[:self._inputDimensions.size] = self._inputDimensions

    columnsPerInput = colDim.astype(realDType) / inputDim
    return numpy.average(columnsPerInput)


  def _avgConnectedSpanForColumn1D(self, columnIndex):
    """
    The range of connected synapses for column. This is used to
    calculate the inhibition radius. This variation of the function only
    supports a 1 dimensional column topology.

    Parameters:
    ----------------------------
    @param columnIndex:   The index identifying a column in the permanence,
                          potential and connectivity matrices
    """
    assert(self._inputDimensions.size == 1)
    connected = self._connectedSynapses[columnIndex].nonzero()[0]
    if connected.size == 0:
      return 0
    else:
      return max(connected) - min(connected) + 1


  def _avgConnectedSpanForColumn2D(self, columnIndex):
    """
    The range of connectedSynapses per column, averaged for each dimension.
    This value is used to calculate the inhibition radius. This variation of
    the  function only supports a 2 dimensional column topology.

    Parameters:
    ----------------------------
    @param columnIndex:   The index identifying a column in the permanence,
                          potential and connectivity matrices
    """
    assert(self._inputDimensions.size == 2)
    connected = self._connectedSynapses[columnIndex]
    (rows, cols) = connected.reshape(self._inputDimensions).nonzero()
    if  rows.size == 0 and cols.size == 0:
      return 0
    rowSpan = rows.max() - rows.min() + 1
    colSpan = cols.max() - cols.min() + 1
    return numpy.average([rowSpan, colSpan])


  def _avgConnectedSpanForColumnND(self, columnIndex):
    """
    The range of connectedSynapses per column, averaged for each dimension.
    This value is used to calculate the inhibition radius. This variation of
    the function supports arbitrary column dimensions.

    Parameters:
    ----------------------------
    @param index:   The index identifying a column in the permanence, potential
                    and connectivity matrices.
    """
    dimensions = self._inputDimensions
    connected = self._connectedSynapses[columnIndex].nonzero()[0]
    if connected.size == 0:
      return 0
    maxCoord = numpy.empty(self._inputDimensions.size)
    minCoord = numpy.empty(self._inputDimensions.size)
    maxCoord.fill(-1)
    minCoord.fill(max(self._inputDimensions))
    for i in connected:
      maxCoord = numpy.maximum(maxCoord, numpy.unravel_index(i, dimensions))
      minCoord = numpy.minimum(minCoord, numpy.unravel_index(i, dimensions))
    return numpy.average(maxCoord - minCoord + 1)


  def _adaptSynapses(self, inputVector, activeColumns):
    """
    The primary method in charge of learning. Adapts the permanence values of
    the synapses based on the input vector, and the chosen columns after
    inhibition round. Permanence values are increased for synapses connected to
    input bits that are turned on, and decreased for synapses connected to
    inputs bits that are turned off.

    Parameters:
    ----------------------------
    @param inputVector:
                    A numpy array of 0's and 1's that comprises the input to
                    the spatial pooler. There exists an entry in the array
                    for every input bit.
    @param activeColumns:
                    An array containing the indices of the columns that
                    survived inhibition.
    """
    inputIndices = numpy.where(inputVector > 0)[0]
    permChanges = numpy.zeros(self._numInputs, dtype=realDType)
    permChanges.fill(-1 * self._synPermInactiveDec)
    permChanges[inputIndices] = self._synPermActiveInc
    for columnIndex in activeColumns:
      perm = self._permanences[columnIndex]
      maskPotential = numpy.where(self._potentialPools[columnIndex] > 0)[0]
      perm[maskPotential] += permChanges[maskPotential]
      self._updatePermanencesForColumn(perm, columnIndex, raisePerm=True)


  def _bumpUpWeakColumns(self):
    """
    This method increases the permanence values of synapses of columns whose
    activity level has been too low. Such columns are identified by having an
    overlap duty cycle that drops too much below those of their peers. The
    permanence values for such columns are increased.
    """
    weakColumns = numpy.where(self._overlapDutyCycles
                                < self._minOverlapDutyCycles)[0]
    for columnIndex in weakColumns:
      perm = self._permanences[columnIndex].astype(realDType)
      maskPotential = numpy.where(self._potentialPools[columnIndex] > 0)[0]
      perm[maskPotential] += self._synPermBelowStimulusInc
      self._updatePermanencesForColumn(perm, columnIndex, raisePerm=False)


  def _raisePermanenceToThreshold(self, perm, mask):
    """
    This method ensures that each column has enough connections to input bits
    to allow it to become active. Since a column must have at least
    'self._stimulusThreshold' overlaps in order to be considered during the
    inhibition phase, columns without such minimal number of connections, even
    if all the input bits they are connected to turn on, have no chance of
    obtaining the minimum threshold. For such columns, the permanence values
    are increased until the minimum number of connections are formed.


    Parameters:
    ----------------------------
    @param perm:    An array of permanence values for a column. The array is
                    "dense", i.e. it contains an entry for each input bit, even
                    if the permanence value is 0.
    @param mask:    the indices of the columns whose permanences need to be
                    raised.
    """
    if len(mask) < self._stimulusThreshold:
      raise Exception("This is likely due to a " +
      "value of stimulusThreshold that is too large relative " +
      "to the input size. [len(mask) < self._stimulusThreshold]")

    numpy.clip(perm, self._synPermMin, self._synPermMax, out=perm)
    while True:
      numConnected = numpy.nonzero(perm > self._synPermConnected)[0].size
      if numConnected >= self._stimulusThreshold:
        return
      perm[mask] += self._synPermBelowStimulusInc


  def _updatePermanencesForColumn(self, perm, columnIndex, raisePerm=True):
    """
    This method updates the permanence matrix with a column's new permanence
    values. The column is identified by its index, which reflects the row in
    the matrix, and the permanence is given in 'dense' form, i.e. a full
    array containing all the zeros as well as the non-zero values. It is in
    charge of implementing 'clipping' - ensuring that the permanence values are
    always between 0 and 1 - and 'trimming' - enforcing sparsity by zeroing out
    all permanence values below '_synPermTrimThreshold'. It also maintains
    the consistency between 'self._permanences' (the matrix storing the
    permanence values), 'self._connectedSynapses', (the matrix storing the bits
    each column is connected to), and 'self._connectedCounts' (an array storing
    the number of input bits each column is connected to). Every method wishing
    to modify the permanence matrix should do so through this method.

    Parameters:
    ----------------------------
    @param perm:    An array of permanence values for a column. The array is
                    "dense", i.e. it contains an entry for each input bit, even
                    if the permanence value is 0.
    @param index:   The index identifying a column in the permanence, potential
                    and connectivity matrices
    @param raisePerm: A boolean value indicating whether the permanence values
                    should be raised until a minimum number are synapses are in
                    a connected state. Should be set to 'false' when a direct
                    assignment is required.
    """
    maskPotential = numpy.where(self._potentialPools[columnIndex] > 0)[0]
    if raisePerm:
      self._raisePermanenceToThreshold(perm, maskPotential)
    perm[perm < self._synPermTrimThreshold] = 0
    numpy.clip(perm, self._synPermMin, self._synPermMax, out=perm)
    newConnected = numpy.where(perm >= self._synPermConnected)[0]
    self._permanences.update(columnIndex, perm)
    self._connectedSynapses.replace(columnIndex, newConnected)
    self._connectedCounts[columnIndex] = newConnected.size


  def _initPermConnected(self):
    """
    Returns a randomly generated permanence value for a synapses that is
    initialized in a connected state. The basic idea here is to initialize
    permanence values very close to synPermConnected so that a small number of
    learning steps could make it disconnected or connected.

    Note: experimentation was done a long time ago on the best way to initialize
    permanence values, but the history for this particular scheme has been lost.
    """
    p = self._synPermConnected + (
        self._synPermMax - self._synPermConnected)*self._random.getReal64()

    # Ensure we don't have too much unnecessary precision. A full 64 bits of
    # precision causes numerical stability issues across platforms and across
    # implementations
    p = int(p*100000) / 100000.0
    return p


  def _initPermNonConnected(self):
    """
    Returns a randomly generated permanence value for a synapses that is to be
    initialized in a non-connected state.
    """
    p = self._synPermConnected * self._random.getReal64()

    # Ensure we don't have too much unnecessary precision. A full 64 bits of
    # precision causes numerical stability issues across platforms and across
    # implementations
    p = int(p*100000) / 100000.0
    return p


  def _initPermanence(self, potential, connectedPct):
    """
    Initializes the permanences of a column. The method
    returns a 1-D array the size of the input, where each entry in the
    array represents the initial permanence value between the input bit
    at the particular index in the array, and the column represented by
    the 'index' parameter.

    Parameters:
    ----------------------------
    @param potential: A numpy array specifying the potential pool of the column.
                    Permanence values will only be generated for input bits
                    corresponding to indices for which the mask value is 1.
    @param connectedPct: A value between 0 or 1 governing the chance, for each
                         permanence, that the initial permanence value will
                         be a value that is considered connected.
    """
    # Determine which inputs bits will start out as connected
    # to the inputs. Initially a subset of the input bits in a
    # column's potential pool will be connected. This number is
    # given by the parameter "connectedPct"
    perm = numpy.zeros(self._numInputs, dtype=realDType)
    for i in xrange(self._numInputs):
      if (potential[i] < 1):
        continue

      if (self._random.getReal64() <= connectedPct):
        perm[i] = self._initPermConnected()
      else:
        perm[i] = self._initPermNonConnected()

    # Clip off low values. Since we use a sparse representation
    # to store the permanence values this helps reduce memory
    # requirements.
    perm[perm < self._synPermTrimThreshold] = 0

    return perm


  def _mapColumn(self, index):
    """
    Maps a column to its respective input index, keeping to the topology of
    the region. It takes the index of the column as an argument and determines
    what is the index of the flattened input vector that is to be the center of
    the column's potential pool. It distributes the columns over the inputs
    uniformly. The return value is an integer representing the index of the
    input bit. Examples of the expected output of this method:
    * If the topology is one dimensional, and the column index is 0, this
      method will return the input index 0. If the column index is 1, and there
      are 3 columns over 7 inputs, this method will return the input index 3.
    * If the topology is two dimensional, with column dimensions [3, 5] and
      input dimensions [7, 11], and the column index is 3, the method
      returns input index 8.

    Parameters:
    ----------------------------
    @param index:   The index identifying a column in the permanence, potential
                    and connectivity matrices.
    @param wrapAround: A boolean value indicating that boundaries should be
                    ignored.
    """
    columnCoords = numpy.unravel_index(index, self._columnDimensions)
    columnCoords = numpy.array(columnCoords, dtype=realDType)
    ratios = columnCoords / self._columnDimensions
    inputCoords = self._inputDimensions * ratios
    inputCoords += 0.5 * self._inputDimensions / self._columnDimensions
    inputCoords = inputCoords.astype(int)
    inputIndex = numpy.ravel_multi_index(inputCoords, self._inputDimensions)
    return inputIndex


  def _mapPotential(self, index):
    """
    Maps a column to its input bits. This method encapsulates the topology of
    the region. It takes the index of the column as an argument and determines
    what are the indices of the input vector that are located within the
    column's potential pool. The return value is a list containing the indices
    of the input bits. The current implementation of the base class only
    supports a 1 dimensional topology of columns with a 1 dimensional topology
    of inputs. To extend this class to support 2-D topology you will need to
    override this method. Examples of the expected output of this method:
    * If the potentialRadius is greater than or equal to the largest input
      dimension then each column connects to all of the inputs.
    * If the topology is one dimensional, the input space is divided up evenly
      among the columns and each column is centered over its share of the
      inputs.  If the potentialRadius is 5, then each column connects to the
      input it is centered above as well as the 5 inputs to the left of that
      input and the five inputs to the right of that input, wrapping around if
      wrapAround=True.
    * If the topology is two dimensional, the input space is again divided up
      evenly among the columns and each column is centered above its share of
      the inputs.  If the potentialRadius is 5, the column connects to a square
      that has 11 inputs on a side and is centered on the input that the column
      is centered above.

    Parameters:
    ----------------------------
    @param index:   The index identifying a column in the permanence, potential
                    and connectivity matrices.
    """

    centerInput = self._mapColumn(index)
    columnInputs = self._getInputNeighborhood(centerInput).astype(uintType)

    # Select a subset of the receptive field to serve as the
    # the potential pool
    numPotential = int(columnInputs.size * self._potentialPct + 0.5)
    selectedInputs = numpy.empty(numPotential, dtype=uintType)
    self._random.sample(columnInputs, selectedInputs)

    potential = numpy.zeros(self._numInputs, dtype=uintType)
    potential[selectedInputs] = 1

    return potential


  @staticmethod
  def _updateDutyCyclesHelper(dutyCycles, newInput, period):
    """
    Updates a duty cycle estimate with a new value. This is a helper
    function that is used to update several duty cycle variables in
    the Column class, such as: overlapDutyCucle, activeDutyCycle,
    minPctDutyCycleBeforeInh, minPctDutyCycleAfterInh, etc. returns
    the updated duty cycle. Duty cycles are updated according to the following
    formula:

                  (period - 1)*dutyCycle + newValue
      dutyCycle := ----------------------------------
                              period

    Parameters:
    ----------------------------
    @param dutyCycles: An array containing one or more duty cycle values that need
                    to be updated
    @param newInput: A new numerical value used to update the duty cycle
    @param period:  The period of the duty cycle
    """
    assert(period >= 1)
    return (dutyCycles * (period -1.0) + newInput) / period


  def _updateBoostFactors(self):
    r"""
    Update the boost factors for all columns. The boost factors are used to
    increase the overlap of inactive columns to improve their chances of
    becoming active. and hence encourage participation of more columns in the
    learning process. This is a line defined as: y = mx + b boost =
    (1-maxBoost)/minDuty * dutyCycle + maxFiringBoost. Intuitively this means
    that columns that have been active enough have a boost factor of 1, meaning
    their overlap is not boosted. Columns whose active duty cycle drops too much
    below that of their neighbors are boosted depending on how infrequently they
    have been active. The more infrequent, the more they are boosted. The exact
    boost factor is linearly interpolated between the points (dutyCycle:0,
    boost:maxFiringBoost) and (dutyCycle:minDuty, boost:1.0).

            boostFactor
                ^
    maxBoost _  |
                |\
                | \
          1  _  |  \ _ _ _ _ _ _ _
                |
                +--------------------> activeDutyCycle
                   |
            minActiveDutyCycle
    """

    mask = numpy.where(self._minActiveDutyCycles > 0)[0]
    self._boostFactors[mask] = ((1 - self._maxBoost) /
      self._minActiveDutyCycles[mask] * self._activeDutyCycles[mask]
        ).astype(realDType) + self._maxBoost

    self._boostFactors[self._activeDutyCycles >
      self._minActiveDutyCycles] = 1.0


  def _updateBookeepingVars(self, learn):
    """
    Updates counter instance variables each round.

    Parameters:
    ----------------------------
    @param learn:   a boolean value indicating whether learning should be
                    performed. Learning entails updating the  permanence
                    values of the synapses, and hence modifying the 'state'
                    of the model. setting learning to 'off' might be useful
                    for indicating separate training vs. testing sets.
    """
    self._iterationNum += 1
    if learn:
      self._iterationLearnNum += 1


  def _calculateOverlap(self, inputVector):
    """
    This function determines each column's overlap with the current input
    vector. The overlap of a column is the number of synapses for that column
    that are connected (permanence value is greater than '_synPermConnected')
    to input bits which are turned on. The implementation takes advantage of
    the SparseBinaryMatrix class to perform this calculation efficiently.

    Parameters:
    ----------------------------
    @param inputVector: a numpy array of 0's and 1's that comprises the input to
                    the spatial pooler.
    """
    overlaps = numpy.zeros(self._numColumns, dtype=realDType)
    self._connectedSynapses.rightVecSumAtNZ_fast(inputVector.astype(realDType),
                                                 overlaps)
    return overlaps


  def _calculateOverlapPct(self, overlaps):
    return overlaps.astype(realDType) / self._connectedCounts


  def _inhibitColumns(self, overlaps):
    """
    Performs inhibition. This method calculates the necessary values needed to
    actually perform inhibition and then delegates the task of picking the
    active columns to helper functions.

    Parameters:
    ----------------------------
    @param overlaps: an array containing the overlap score for each  column.
                    The overlap score for a column is defined as the number
                    of synapses in a "connected state" (connected synapses)
                    that are connected to input bits which are turned on.
    """
    # determine how many columns should be selected in the inhibition phase.
    # This can be specified by either setting the 'numActiveColumnsPerInhArea'
    # parameter or the 'localAreaDensity' parameter when initializing the class
    if (self._localAreaDensity > 0):
      density = self._localAreaDensity
    else:
      inhibitionArea = ((2*self._inhibitionRadius + 1)
                                    ** self._columnDimensions.size)
      inhibitionArea = min(self._numColumns, inhibitionArea)
      density = float(self._numActiveColumnsPerInhArea) / inhibitionArea
      density = min(density, 0.5)

    if self._globalInhibition or \
      self._inhibitionRadius > max(self._columnDimensions):
      return self._inhibitColumnsGlobal(overlaps, density)
    else:
      return self._inhibitColumnsLocal(overlaps, density)


  def _inhibitColumnsGlobal(self, overlaps, density):
    """
    Perform global inhibition. Performing global inhibition entails picking the
    top 'numActive' columns with the highest overlap score in the entire
    region. At most half of the columns in a local neighborhood are allowed to
    be active. Columns with an overlap score below the 'stimulusThreshold' are
    always inhibited.

    @param overlaps: an array containing the overlap score for each  column.
                    The overlap score for a column is defined as the number
                    of synapses in a "connected state" (connected synapses)
                    that are connected to input bits which are turned on.
    @param density: The fraction of columns to survive inhibition.
    @return list with indices of the winning columns
    """
    #calculate num active per inhibition area
    numActive = int(density * self._numColumns)

    # Calculate winners using stable sort algorithm (mergesort)
    # for compatibility with C++
    sortedWinnerIndices = numpy.argsort(overlaps, kind='mergesort')

    # Enforce the stimulus threshold
    start = len(sortedWinnerIndices) - numActive
    while start < len(sortedWinnerIndices):
      i = sortedWinnerIndices[start]
      if overlaps[i] >= self._stimulusThreshold:
        break
      else:
        start += 1

    return sortedWinnerIndices[start:][::-1]


  def _inhibitColumnsLocal(self, overlaps, density):
    """
    Performs local inhibition. Local inhibition is performed on a column by
    column basis. Each column observes the overlaps of its neighbors and is
    selected if its overlap score is within the top 'numActive' in its local
    neighborhood. At most half of the columns in a local neighborhood are
    allowed to be active. Columns with an overlap score below the
    'stimulusThreshold' are always inhibited.

    @param overlaps: an array containing the overlap score for each  column.
                    The overlap score for a column is defined as the number
                    of synapses in a "connected state" (connected synapses)
                    that are connected to input bits which are turned on.
    @param density: The fraction of columns to survive inhibition. This
                    value is only an intended target. Since the surviving
                    columns are picked in a local fashion, the exact fraction
                    of surviving columns is likely to vary.
    @return list with indices of the winning columns
    """

    # When a column is selected, add a small number to its overlap. If it was
    # tied with other not-yet-processed columns, those columns will now lose the
    # tie-breaker when they're processed.
    addToWinners = max(overlaps) / 1000.0
    if addToWinners == 0:
      addToWinners = 0.001
    tieBrokenOverlaps = numpy.array(overlaps, dtype=realDType)

    winners = []
    for column, overlap in enumerate(overlaps):
      if overlap >= self._stimulusThreshold:
        neighborhood = self._getColumnNeighborhood(column)
        neighborhoodOverlaps = tieBrokenOverlaps[neighborhood]

        numBigger = numpy.count_nonzero(neighborhoodOverlaps > overlap)

        numActive = int(0.5 + density * len(neighborhood))
        if numBigger < numActive:
          winners.append(column)
          tieBrokenOverlaps[column] += addToWinners

    return numpy.array(winners, dtype=uintType)


  def _isUpdateRound(self):
    """
    returns true if enough rounds have passed to warrant updates of
    duty cycles
    """
    return (self._iterationNum % self._updatePeriod) == 0


  def _getColumnNeighborhood(self, centerColumn):
    """
    Gets a neighborhood of columns.

    Simply calls topology.neighborhood or topology.wrappingNeighborhood

    A subclass can insert different topology behavior by overriding this method.

    @param centerColumn (int)
    The center of the neighborhood.

    @returns (1D numpy array of integers)
    The columns in the neighborhood.
    """
    if self._wrapAround:
      return topology.wrappingNeighborhood(centerColumn,
                                           self._inhibitionRadius,
                                           self._columnDimensions)

    else:
      return topology.neighborhood(centerColumn,
                                   self._inhibitionRadius,
                                   self._columnDimensions)



  def _getInputNeighborhood(self, centerInput):
    """
    Gets a neighborhood of inputs.

    Simply calls topology.wrappingNeighborhood or topology.neighborhood.

    A subclass can insert different topology behavior by overriding this method.

    @param centerInput (int)
    The center of the neighborhood.

    @returns (1D numpy array of integers)
    The inputs in the neighborhood.
    """
    if self._wrapAround:
      return topology.wrappingNeighborhood(centerInput,
                                           self._potentialRadius,
                                           self._inputDimensions)
    else:
      return topology.neighborhood(centerInput,
                                   self._potentialRadius,
                                   self._inputDimensions)


  def _seed(self, seed=-1):
    """
    Initialize the random seed
    """
    if seed != -1:
      self._random = NupicRandom(seed)
    else:
      self._random = NupicRandom()


  def __setstate__(self, state):
    """
    Initialize class properties from stored values.
    """
    # original version was a float so check for anything less than 2
    if state['_version'] < 2:
      # the wrapAround property was added in version 2,
      # in version 1 the wrapAround parameter was True for SP initialization
      state['_wrapAround'] = True
    if state['_version'] < 3:
      # the overlaps and boostedOverlaps properties were added in version 3,
      state['_overlaps'] = numpy.zeros(self._numColumns, dtype=realDType)
      state['_boostedOverlaps'] = numpy.zeros(self._numColumns, dtype=realDType)
    
    # update version property to current SP version
    state['_version'] = VERSION
    self.__dict__.update(state)


  def write(self, proto):
    self._random.write(proto.random)
    proto.numInputs = self._numInputs
    proto.numColumns = self._numColumns
    cdimsProto = proto.init("columnDimensions", len(self._columnDimensions))
    for i, dim in enumerate(self._columnDimensions):
      cdimsProto[i] = int(dim)
    idimsProto = proto.init("inputDimensions", len(self._inputDimensions))
    for i, dim in enumerate(self._inputDimensions):
      idimsProto[i] = int(dim)
    proto.potentialRadius = self._potentialRadius
    proto.potentialPct = self._potentialPct
    proto.inhibitionRadius = self._inhibitionRadius
    proto.globalInhibition = bool(self._globalInhibition)
    proto.numActiveColumnsPerInhArea = self._numActiveColumnsPerInhArea
    proto.localAreaDensity = self._localAreaDensity
    proto.stimulusThreshold = self._stimulusThreshold
    proto.synPermInactiveDec = self._synPermInactiveDec
    proto.synPermActiveInc = self._synPermActiveInc
    proto.synPermBelowStimulusInc = self._synPermBelowStimulusInc
    proto.synPermConnected = self._synPermConnected
    proto.minPctOverlapDutyCycles = self._minPctOverlapDutyCycles
    proto.minPctActiveDutyCycles = self._minPctActiveDutyCycles
    proto.dutyCyclePeriod = self._dutyCyclePeriod
    proto.maxBoost = self._maxBoost
    proto.wrapAround = self._wrapAround
    proto.spVerbosity = self._spVerbosity

    proto.synPermMin = self._synPermMin
    proto.synPermMax = self._synPermMax
    proto.synPermTrimThreshold = self._synPermTrimThreshold
    proto.updatePeriod = self._updatePeriod

    proto.version = self._version
    proto.iterationNum = self._iterationNum
    proto.iterationLearnNum = self._iterationLearnNum

    self._potentialPools.write(proto.potentialPools)
    self._permanences.write(proto.permanences)

    tieBreakersProto = proto.init("tieBreaker", len(self._tieBreaker))
    for i, v in enumerate(self._tieBreaker):
      tieBreakersProto[i] = float(v)

    overlapDutyCyclesProto = proto.init("overlapDutyCycles",
                                        len(self._overlapDutyCycles))
    for i, v in enumerate(self._overlapDutyCycles):
      overlapDutyCyclesProto[i] = float(v)

    activeDutyCyclesProto = proto.init("activeDutyCycles",
                                       len(self._activeDutyCycles))
    for i, v in enumerate(self._activeDutyCycles):
      activeDutyCyclesProto[i] = float(v)

    minOverlapDutyCyclesProto = proto.init("minOverlapDutyCycles",
                                           len(self._minOverlapDutyCycles))
    for i, v in enumerate(self._minOverlapDutyCycles):
      minOverlapDutyCyclesProto[i] = float(v)

    minActiveDutyCyclesProto = proto.init("minActiveDutyCycles",
                                          len(self._minActiveDutyCycles))
    for i, v in enumerate(self._minActiveDutyCycles):
      minActiveDutyCyclesProto[i] = float(v)

    boostFactorsProto = proto.init("boostFactors", len(self._boostFactors))
    for i, v in enumerate(self._boostFactors):
      boostFactorsProto[i] = float(v) 


  @classmethod
  def read(cls, proto):
    numInputs = int(proto.numInputs)
    numColumns = int(proto.numColumns)

    instance = cls()

    instance._random.read(proto.random)
    instance._numInputs = numInputs
    instance._numColumns = numColumns
    instance._columnDimensions = numpy.array(proto.columnDimensions)
    instance._inputDimensions = numpy.array(proto.inputDimensions)
    instance._potentialRadius = proto.potentialRadius
    instance._potentialPct = proto.potentialPct
    instance._inhibitionRadius = proto.inhibitionRadius
    instance._globalInhibition = proto.globalInhibition
    instance._numActiveColumnsPerInhArea = proto.numActiveColumnsPerInhArea
    instance._localAreaDensity = proto.localAreaDensity
    instance._stimulusThreshold = proto.stimulusThreshold
    instance._synPermInactiveDec = proto.synPermInactiveDec
    instance._synPermActiveInc = proto.synPermActiveInc
    instance._synPermBelowStimulusInc = proto.synPermBelowStimulusInc
    instance._synPermConnected = proto.synPermConnected
    instance._minPctOverlapDutyCycles = proto.minPctOverlapDutyCycles
    instance._minPctActiveDutyCycles = proto.minPctActiveDutyCycles
    instance._dutyCyclePeriod = proto.dutyCyclePeriod
    instance._maxBoost = proto.maxBoost
    instance._wrapAround = proto.wrapAround
    instance._spVerbosity = proto.spVerbosity

    instance._synPermMin = proto.synPermMin
    instance._synPermMax = proto.synPermMax
    instance._synPermTrimThreshold = proto.synPermTrimThreshold
    instance._updatePeriod = proto.updatePeriod

    instance._version = VERSION
    instance._iterationNum = proto.iterationNum
    instance._iterationLearnNum = proto.iterationLearnNum

    instance._potentialPools.read(proto.potentialPools)

    instance._permanences.read(proto.permanences)
    # Initialize ephemerals and make sure they get updated
    instance._connectedCounts = numpy.zeros(numColumns, dtype=realDType)
    instance._connectedSynapses = BinaryCorticalColumns(numInputs)
    instance._connectedSynapses.resize(numColumns, numInputs)
    for columnIndex in xrange(proto.numColumns):
      instance._updatePermanencesForColumn(
        instance._permanences[columnIndex], columnIndex, False
      )

    instance._tieBreaker = numpy.array(proto.tieBreaker, dtype=realDType)

    instance._overlapDutyCycles = numpy.array(proto.overlapDutyCycles,
                                          dtype=realDType)
    instance._activeDutyCycles = numpy.array(proto.activeDutyCycles,
                                         dtype=realDType)
    instance._minOverlapDutyCycles = numpy.array(proto.minOverlapDutyCycles,
                                             dtype=realDType)
    instance._minActiveDutyCycles = numpy.array(proto.minActiveDutyCycles,
                                            dtype=realDType)
    instance._boostFactors = numpy.array(proto.boostFactors, dtype=realDType)
    
    return instance


  def printParameters(self):
    """
    Useful for debugging.
    """
    print "------------PY  SpatialPooler Parameters ------------------"
    print "numInputs                  = ", self.getNumInputs()
    print "numColumns                 = ", self.getNumColumns()
    print "columnDimensions           = ", self._columnDimensions
    print "numActiveColumnsPerInhArea = ", self.getNumActiveColumnsPerInhArea()
    print "potentialPct               = ", self.getPotentialPct()
    print "globalInhibition           = ", self.getGlobalInhibition()
    print "localAreaDensity           = ", self.getLocalAreaDensity()
    print "stimulusThreshold          = ", self.getStimulusThreshold()
    print "synPermActiveInc           = ", self.getSynPermActiveInc()
    print "synPermInactiveDec         = ", self.getSynPermInactiveDec()
    print "synPermConnected           = ", self.getSynPermConnected()
    print "minPctOverlapDutyCycle     = ", self.getMinPctOverlapDutyCycles()
    print "minPctActiveDutyCycle      = ", self.getMinPctActiveDutyCycles()
    print "dutyCyclePeriod            = ", self.getDutyCyclePeriod()
    print "maxBoost                   = ", self.getMaxBoost()
    print "spVerbosity                = ", self.getSpVerbosity()
    print "version                    = ", self._version
