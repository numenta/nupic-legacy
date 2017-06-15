# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

"""
utils.py are a collection of methods that can be reused by different classes
in our codebase.
"""

import numbers

from nupic.serializable import Serializable
try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.movingaverage_capnp import MovingAverageProto


class MovingAverage(Serializable):
  """Helper class for computing moving average and sliding window"""


  def __init__(self, windowSize, existingHistoricalValues=None):
    """
    new instance of MovingAverage, so method .next() can be used
    @param windowSize - length of sliding window
    @param existingHistoricalValues - construct the object with already
        some values in it.
    """
    if not isinstance(windowSize, numbers.Integral):
      raise TypeError("MovingAverage - windowSize must be integer type")
    if  windowSize <= 0:
      raise ValueError("MovingAverage - windowSize must be >0")

    self.windowSize = windowSize
    if existingHistoricalValues is not None:
      self.slidingWindow = existingHistoricalValues[
                              len(existingHistoricalValues)-windowSize:]
    else:
      self.slidingWindow = []
    self.total = float(sum(self.slidingWindow))


  @staticmethod
  def compute(slidingWindow, total, newVal, windowSize):
    """Routine for computing a moving average.

    @param slidingWindow a list of previous values to use in computation that
        will be modified and returned
    @param total the sum of the values in slidingWindow to be used in the
        calculation of the moving average
    @param newVal a new number compute the new windowed average
    @param windowSize how many values to use in the moving window

    @returns an updated windowed average, the modified input slidingWindow list,
        and the new total sum of the sliding window
    """
    if len(slidingWindow) == windowSize:
      total -= slidingWindow.pop(0)

    slidingWindow.append(newVal)
    total += newVal
    return float(total) / len(slidingWindow), slidingWindow, total


  def next(self, newValue):
    """Instance method wrapper around compute."""
    newAverage, self.slidingWindow, self.total = self.compute(
        self.slidingWindow, self.total, newValue, self.windowSize)
    return newAverage


  def getSlidingWindow(self):
    return self.slidingWindow


  def getCurrentAvg(self):
    """get current average"""
    return float(self.total) / len(self.slidingWindow)

  # TODO obsoleted by capnp, will be removed in future
  def __setstate__(self, state):
    """ for loading this object"""
    self.__dict__.update(state)

    if not hasattr(self, "slidingWindow"):
      self.slidingWindow = []

    if not hasattr(self, "total"):
      self.total = 0
      self.slidingWindow = sum(self.slidingWindow)


  def __eq__(self, o):
    return (isinstance(o, MovingAverage) and
            o.slidingWindow == self.slidingWindow and
            o.total == self.total and
            o.windowSize == self.windowSize)


  def __call__(self, value):
    return self.next(value)


  @classmethod
  def read(cls, proto):
    movingAverage = object.__new__(cls)
    movingAverage.windowSize = proto.windowSize
    movingAverage.slidingWindow = list(proto.slidingWindow)
    movingAverage.total = proto.total
    return movingAverage


  def write(self, proto):
    proto.windowSize = self.windowSize
    proto.slidingWindow = self.slidingWindow
    proto.total = self.total


  @classmethod
  def getSchema(cls):
    return MovingAverageProto

