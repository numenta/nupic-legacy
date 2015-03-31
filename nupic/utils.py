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

import numbers
from collections import MutableMapping
import logging

class MovingAverage(object):
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


  def __setstate__(self, state):
    """ for loading this object"""
    self.__dict__.update(state)

    if not hasattr(self, "slidingWindow"):
      self.slidingWindow = []

    if not hasattr(self, "total"):
      self.total = 0
      self.slidingWindow = sum(self.slidingWindow)


  def __call__(self, value):
    return self.next(value)

#######################################################################
class GlobalDict(MutableMapping):
  """
  a dict{} storing its content globally. 

  GlobalDict class serves as a global look-up table addressed by names, 
  for storing and accessing objects globally.
  """

  # global variable
  store = {}

  logging.basicConfig()
  logger = logging.getLogger(__name__)

  def __init__(self, *args, **kwargs):
    self.update(dict(*args, **kwargs))
  def __getitem__(self, key):
    return GlobalDict.get(key)
  def __setitem__(self, key, value):
    """if the key is in use, generate a unique one"""
    self.__class__.set(key, value)
  def __delitem__(self, key):
    del GlobalDict.store[key]
  def __iter__(self):
    return iter(GlobalDict.store)
  def __len__(self):
    return len(GlobalDict.store)
  @classmethod
  def set(cls, key, value):
    if key is None:
      key = str(id(value)) # generate uniq name
    if key in cls.store: # replacing existing item
      cls.logger.error("replacing item '%s' named '%s' with new '%s'." % (cls.get(key), key, value))
      raise ValueError("GlobalDict: key %s already exists! " %(key))
    cls.store[key] = value
    cls.logger.warn("Globally stored item '%s' named '%s' " % (value, key))
  @classmethod
  def get(cls, key):
    return cls.store.get(key, None)

  def __str__(self):
    return str(GlobalDict.store)
