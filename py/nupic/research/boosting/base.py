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


import numpy
from nupic.bindings.math import GetNTAReal

realDType = GetNTAReal()

"""
Boosting - abstract class for boosting used in spatial pooler and temporal pooler. 
Alternative implementations must extend from this class.
"""
class Boosting(object):                        
  
  
  def __init__(self, SP, minPctOverlapDutyCycle, minPctActiveDutyCycle, dutyCyclePeriod, maxBoost):
    """
    SP - link to parent object (SpatialPooler)
    minPctOvlerapDutyCycle: A number between 0 and 1.0, used to set a floor on
                          how often a column should have at least
                          stimulusThreshold active inputs. Periodically, each
                          column looks at the overlap duty cycle of
                          all other column within its inhibition radius and
                          sets its own internal minimal acceptable duty cycle
                          to: minPctDutyCycleBeforeInh * max(other columns'
                          duty cycles).
                          On each iteration, any column whose overlap duty
                          cycle falls below this computed value will  get
                          all of its permanence values boosted up by
                          synPermActiveInc. Raising all permanences in response
                          to a sub-par duty cycle before  inhibition allows a
                          cell to search for new inputs when either its
                          previously learned inputs are no longer ever active,
                          or when the vast majority of them have been
                          "hijacked" by other columns.
    minPctActiveDutyCycle: A number between 0 and 1.0, used to set a floor on
                          how often a column should be activate.
                          Periodically, each column looks at the activity duty
                          cycle of all other columns within its inhibition
                          radius and sets its own internal minimal acceptable
                          duty cycle to:
                            minPctDutyCycleAfterInh *
                            max(other columns' duty cycles).
                          On each iteration, any column whose duty cycle after
                          inhibition falls below this computed value will get
                          its internal boost factor increased.
    dutyCyclePeriod:      The period used to calculate duty cycles. Higher
                          values make it take longer to respond to changes in
                          boost or synPerConnectedCell. Shorter values make it
                          more unstable and likely to oscillate.
    maxBoost:            The maximum overlap boost factor. Each column's
                          overlap gets multiplied by a boost factor
                          before it gets considered for inhibition.
                          The actual boost factor for a column is number
                          between 1.0 and maxBoost. A boost factor of 1.0 is
                          used if the duty cycle is >= minOverlapDutyCycle,
                          maxBoost is used if the duty cycle is 0, and any duty
                          cycle in between is linearly extrapolated from these
                          2 endpoints.
    """
    
    self._parent=SP
    self._minPctOverlapDutyCycles = minPctOverlapDutyCycle
    self._minPctActiveDutyCycles = minPctActiveDutyCycle
    self._dutyCyclePeriod = dutyCyclePeriod
    self._maxBoost = maxBoost
    numColumns=self._parent.getNumColumns()    
    self._overlapDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._activeDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._minOverlapDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._minActiveDutyCycles = numpy.zeros(numColumns, dtype=realDType)
    self._boostFactors = numpy.ones(numColumns, dtype=realDType)
    
  
  def updateBoostFactors(self):
    """
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
      self._minActiveDutyCycles[mask] * self._activeDutyCycles[mask]).astype(realDType) + self._maxBoost

    self._boostFactors[self._activeDutyCycles > self._minActiveDutyCycles] = 1.0


  
  def _updateMinDutyCycles(self):
    """
    Updates the minimum duty cycles defining normal activity for a column. A
    column with activity duty cycle below this minimum threshold is boosted.
    """
    if self._parent.getGlobalInhibition():
      self._updateMinDutyCyclesGlobal()
    else:
      self._updateMinDutyCyclesLocal()


  def _updateMinDutyCyclesGlobal(self):
    """
    Updates the minimum duty cycles in a global fashion. Sets the minimum duty
    cycles for the overlap and activation of all columns to be a percent of the
    maximum in the region, specified by minPctOverlapDutyCycle and
    minPctActiveDutyCycle respectively. Functionaly it is equivalent to
    _updateMinDutyCyclesLocal, but this function exploits the globalilty of the
    compuation to perform it in a straightforward, and more efficient manner.
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
    for i in xrange(self._numColumns):
      maskNeighbors = numpy.append(i,
        self._parent._getNeighborsND(i, self._parent._columnDimensions,
        self._parent._inhibitionRadius))
      self._minOverlapDutyCycles[i] = (
        self._overlapDutyCycles[maskNeighbors].max() *
        self._minPctOverlapDutyCycles
      )
      self._minActiveDutyCycles[i] = (
        self._activeDutyCycles[maskNeighbors].max() *
        self._minPctActiveDutyCycles
      )


  def _updateDutyCycles(self, overlaps, activeColumns):
    """
    Updates the duty cycles for each column. The OVERLAP duty cycle is a moving
    average of the number of inputs which overlapped with the each column. The
    ACTIVITY duty cycles is a moving average of the frequency of activation for
    each column.

    Parameters:
    ----------------------------
    overlaps:       an array containing the overlap score for each column.
                    The overlap score for a column is defined as the number
                    of synapses in a "connected state" (connected synapses)
                    that are connected to input bits which are turned on.
    activeColumns:  An array containing the indices of the active columns,
                    the sprase set of columns which survived inhibition
    """
    overlapArray = numpy.zeros(self._parent.getNumColumns())
    activeArray = numpy.zeros(self._parent.getNumColumns())
    overlapArray[overlaps > 0] = 1
    if activeColumns.size > 0:
      activeArray[activeColumns] = 1

    period = self._dutyCyclePeriod
    if (period > self._parent.getIterationNum()):
      period = self._parent.getIterationNum()

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
    dutyCycles:     An array containing one or more duty cycle values that need
                    to be updated
    newInput:       A new numerical value used to update the duty cycle
    period:         The period of the duty cycle
    """
    assert(period >= 1)
    return (dutyCycles * (period -1.0) + newInput) / period


  def doBoosting(self, overlaps):
    """apply boosing to the columns"""
    return self._boostFactors * overlaps


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

  def setMinOverlapDutyCyclesFill(self,fillValue):
    """fills the array with given value"""
    self._minOverlapDutyCycles.fill(fillValue)
    
  def setMinActiveDutyCyclesFill(self,fillValue):
    """fills the array with given value"""
    self._minActiveDutyCycles.fill(fillValue)
  
  def getMinActiveDutyCycles(self, minActiveDutyCycles):
    """Returns the minimum activity duty cycles for all columns.
    '_minActiveDutyCycles' size must match the number of columns"""
    minActiveDutyCycles[:] = self._minActiveDutyCycles[:]


  def setMinActiveDutyCycles(self, minActiveDutyCycles):
    """Sets the minimum activity duty cycles for all columns.
    '_minActiveDutyCycles' size must match the number of columns"""
    self._minActiveDutyCycles = minActiveDutyCycles
