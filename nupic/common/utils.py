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
  """
  computes moving average;
  @method compute() - static, requires all parameters set
  @method next() - from an instance of MovingAverage object, does the bookkeeping
	for you.
  """
  
  @staticmethod
  def compute(historicalValues, total, newVal, windowSize):
    """
    Routine for computing a moving average. Given 
    @param historicalValues - a list of historical numbers
    @param total -  a running total of those values
    @param newVal - a new number compute the new windowed average
    @param windowSize - length of sliding window used

    @returns an updated windowed average, the new list of ``historicalValues``,
        and the new running total. Ensures the list of ``historicalValues`` is at
        most ``windowSize``.
    """
    while len(historicalValues) >= windowSize:
      total -= historicalValues[0]
      historicalValues.pop(0)
    historicalValues.append(newVal)
    total += newVal
    newAverage = float(total) / len(historicalValues)

    return newAverage, historicalValues, total

