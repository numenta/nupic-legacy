# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

"""
utils.py are a collection of methods that can be reused by different classes
in our codebase.
"""

class MovingAverage(object):
  """Helper class for computing moving average and sliding window"""

  def __init__(self, windowSize, existingHistoricalValues=None):
    """
    new instance of MovingAverage, so method .next() can be used
    @param windowSize - length of sliding window
    @param existingHistoricalValues - construct the object with already
    	some values in it.
    """
    try:
      int(windowSize)
    except:
      raise TypeError("MovingAverage - windowSize must be integer type")
    if  windowSize <= 0:
      raise ValueError("MovingAverage - windowSize must be >0")

    self.windowSize=windowSize
    if existingHistoricalValues is not None:
      self.slidingWindow=\
        existingHistoricalValues[len(existingHistoricalValues)-windowSize:]
    else:
      self.slidingWindow=[]
    self.total=sum(self.slidingWindow)
    
  
  @staticmethod
  def compute(historicalValues, total, newVal, windowSize):
    """
    Routine for computing a moving average. Given 
    @param historicalValues - a list of historical numbers
    @param total -  a running total of those values
    @param newVal - a new number compute the new windowed average
    @param windowSize - length of sliding window used

    @returns an updated windowed average, the new list of ``historicalValues``,
        and the new running total. Ensures the list of ``historicalValues`` is
        at most ``windowSize``.
    """
    while len(historicalValues) >= windowSize:
      total -= historicalValues[0]
      historicalValues.pop(0)
    historicalValues.append(newVal)
    total += newVal
    newAverage = float(total) / len(historicalValues)

    return newAverage, historicalValues, total


  def next(self, newValue):
    """
    update moving average with the new value added
    @param newValue - integer value to be added
    @return an updated windowed average, the new list of ``historicalValues``,
        and the new running total. Ensures the list of ``historicalValues`` is
        at most ``windowSize``.
    """
    newAverage, self.slidingWindow, self.total = (MovingAverage.compute(
							self.slidingWindow,
							self.total,
							newValue,
							self.windowSize) )
    return newAverage, self.slidingWindow, self.total
