import numpy

from nupic.bindings.math import (GetNTAReal,
                                 Random as NupicRandom)

realDType = GetNTAReal()



class Boosting(object):
  """
  Implements boosting for columns of the spatial pooler.
  Boosting is an optional process that helps the spatial pooler (SP) to adapt
  faster to changes in the input stream. Boosting acts on 2 levels: "duplicit
  peer columns activity" and "mismatched input overlap". 

  1/ Boosting of mispatched input:
  Triggered when the column is "growing" (connected to) the inputs that are 
  not used (anymore). This can happen in two cases, when a part of the input
  vector is never used (wrongly, too generic designed encoder, etc.), or when
  a part of the input that had been used before is not useful anymore for a long
  period of time. 
  Biologically the unmatched synapses would die out of hunger, in the current 
  implementation we increase their improtance in hope that (a few) will start 
  to act on a subset of the input and become a new feature. 
  This process is computed from the '*OverlapDutyCycles', and implemented in the
  'bumpUpWeakColumns()' method.

  2/ Boosting for duplicit peer activity:
  In this scenario, the column has a good synaptic overlap over the input,
  but it is very similar to the input field of the neighboring column(s). 
  It results in a SDR that is not well (D)istributed, and we are wasting 
  resources on the columns activity, as it is duplicit to others'. This leads
  to the column never being active (winning in inhobotion). 
  In this implementation the fix is to temporarily artificially boost 
  the column's "importance" by a boosting factor, thus giving it a chance to
  win in some scenario and creating it's niche. 
  This process is computed from the '*ActivityDutyCycles' and implemented in the
  'getBoostingFactors()' method.
  
  Main methods this class provides are:
  'updateBoosting()' which keeps track of the internal states, and
  'getBoostingFactors()' and 'bumpUpWeakColumns()' that apply boosting methods
  #1 and #2 described above the the columns of the SP.
  """

  def __init__(self,
               numColumns,
               maxBoost,
               minPctOverlapDutyCycle,
               minPctActiveDutyCycle,
               dutyCyclePeriod):
    """
    construct a boosting object for the SpatialPooler

    (See SpatialPooler for descriptions of these parameters.)
    """
    self._boostFactors = numpy.ones(numColumns, dtype=realDType)
    self._maxBoost = maxBoost
    self._minActiveDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._activeDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._overlapDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._minOverlapDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._minPctOverlapDutyCycles = minPctOverlapDutyCycle
    self._minPctActiveDutyCycles = minPctActiveDutyCycle
    self._dutyCyclePeriod = dutyCyclePeriod



  def getBoostFactors(self):
    """
    get boosting for the #2 method - duplicit peer columns
    """
    return self._boostFactors[:]


  def setBoostFactors(self, newBoost):
    """
    set new boosting paramethers for #2 Boosting method
    @param newBoost - 1D numpy array of floats, size as SP.numColumns
    """
    self._boostFactors[:] = newBoost[:]


  def getMaxBoost(self):
    """Returns the maximum boost value"""
    return self._maxBoost


  def setMaxBoost(self, maxBoost):
    """Sets the maximum boost value"""
    self._maxBoost = maxBoost


  def getMinActiveDutyCycles(self):
    """Returns the minimum activity duty cycles for all columns."""
    return self._minActiveDutyCycles[:]


  def setMinActiveDutyCycles(self, minActiveDutyCycles):
    """Sets the minimum activity duty cycles for all columns.
    '_minActiveDutyCycles' size must match the number of columns"""
    self._minActiveDutyCycles = minActiveDutyCycles


  def getActiveDutyCycles(self):
    """Returns the activity duty cycles for all columns."""
    return self._activeDutyCycles[:]


  def setActiveDutyCycles(self, activeDutyCycles):
    """Sets the activity duty cycles for all columns. 'activeDutyCycles'
    size must match the number of columns"""
    self._activeDutyCycles[:] = activeDutyCycles


  def getOverlapDutyCycles(self, overlapDutyCycles):
    """Returns the overlap duty cycles for all columns."""
    return self._overlapDutyCycles[:]


  def setOverlapDutyCycles(self, overlapDutyCycles):
    """Sets the overlap duty cycles for all columns. 'overlapDutyCycles'
    size must match the number of columns"""
    self._overlapDutyCycles[:] = overlapDutyCycles


  def getMinOverlapDutyCycles(self, minOverlapDutyCycles):
    """Returns the minimum overlap duty cycles for all columns."""
    return self._minOverlapDutyCycles[:]


  def setMinOverlapDutyCycles(self, minOverlapDutyCycles):
    """Sets the minimum overlap duty cycles for all columns.
    '_minOverlapDutyCycles' size must match the number of columns"""
    self._minOverlapDutyCycles[:] = minOverlapDutyCycles[:]


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


  def getDutyCyclePeriod(self):
    """Returns the duty cycle period"""
    return self._dutyCyclePeriod


  def setDutyCyclePeriod(self, dutyCyclePeriod):
    """Sets the duty cycle period"""
    self._dutyCyclePeriod = dutyCyclePeriod


# Boosting core logic:

  def update(self, overlaps, activeColumns, sp):
    """
    @param sp - Instance of the Spatial Pooler we want to modify
    """
    doUpdateRound = sp._isUpdateRound()
    doGlobal = sp._globalInhibition or sp._inhibitionRadius > sp._numInputs
    iteration = sp._iterationNum

    self._updateDutyCycles(overlaps, activeColumns, iteration)
    # Boosting #1 - boost columns with weak inputs
    self._bumpUpWeakColumns(sp)
    self._updateBoostFactors()
    if doUpdateRound:
      self._updateMinDutyCycles(sp, doGlobal)


  def _updateBoostFactors(self):
    """
    Update the boost factors for all columns. The boost factors are used to
    increase the overlap of inactive columns to improve their chances of
    becoming active. and hence encourage participation of more columns in the
    learning process. This is a line defined as: y = mx + b boost =
    (1-maxBoost)/minDuty * dutyCycle + maxBoost. Intuitively this means
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

    self._boostFactors[self._activeDutyCycles > self._minActiveDutyCycles] = 1.0


  def _bumpUpWeakColumns(self, sp):
    """
    This method increases the permanence values of synapses of columns whose
    activity level has been too low. Such columns are identified by having an
    overlap duty cycle that drops too much below those of their peers. The
    permanence values for such columns are increased.

    @param sp - Instance of the Spatial Pooler we want to modify
    """
    weakColumns = numpy.where(self._overlapDutyCycles
                                < self._minOverlapDutyCycles)[0]
    for columnIndex in weakColumns:
      perm = numpy.array([sp.getInputDimensions()], dtype=realDType)
      sp.getPermanence(columnIndex, perm)
      pot = numpy.array([sp.getInputDimensions()], dtype=realDType)
      sp.getPotential(columnIndex, pot)
      maskPotential = numpy.where(pot > 0)[0]
      perm[maskPotential] += self._synPermBelowStimulusInc
      sp._updatePermanencesForColumn(perm, columnIndex, raisePerm=False)


# Time keeping methods, counters:

  def _updateMinDutyCycles(self, sp, doGlobal=False):
    """
    Updates the minimum duty cycles defining normal activity for a column. A
    column with activity duty cycle below this minimum threshold is boosted.
    """
    if doGlobal:
      self._updateMinDutyCyclesGlobal()
    else:
      self._updateMinDutyCyclesLocal(sp)


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


  def _updateMinDutyCyclesLocal(self, sp):
    """
    Updates the minimum duty cycles. The minimum duty cycles are determined
    locally. Each column's minimum duty cycles are set to be a percent of the
    maximum duty cycles in the column's neighborhood. Unlike
    _updateMinDutyCyclesGlobal, here the values can be quite different for
    different columns.

    @param sp - SpatialPooler instance we act on.
    """
    for i in xrange(sp._numColumns):
      maskNeighbors = numpy.append(i,
        sp._getNeighborsND(i, sp._columnDimensions,
        sp._inhibitionRadius))
      self._minOverlapDutyCycles[i] = (
        self._overlapDutyCycles[maskNeighbors].max() *
        self._minPctOverlapDutyCycles
      )
      self._minActiveDutyCycles[i] = (
        self._activeDutyCycles[maskNeighbors].max() *
        self._minPctActiveDutyCycles
      )


  def _updateDutyCycles(self, overlaps, activeColumns, iteration):
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
    @param iteration step of the SP/Boosting
    """
    nCols = overlaps.size
    overlapArray = numpy.zeros(nCols, dtype=realDType)
    activeArray = numpy.zeros(nCols, dtype=realDType)
    overlapArray[overlaps > 0] = 1
    activeArray[activeColumns] = 1
    period = min(self._dutyCyclePeriod, iteration)

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
    return (dutyCycles * (period -1.0) + newInput) / period #FIXME #2673

