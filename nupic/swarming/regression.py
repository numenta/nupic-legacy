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

from collections import deque
import math

""" This file contains some utility classes for computing linear and exponential
regressions. It is primarily used by the maturity checking logic in the
ModelRunner to see whether or not the model should be marked as mature. """

class LinearRegression(object):
    """ Helper class to compute the slope of a best-fit line given a set of (x,y)
    points. This is an object that keeps track of some extra state in order to compute
    the slope efficiently
    """

    def __init__(self, windowSize = None):
      self._sum_xy = 0
      self._sum_x = 0
      self._sum_y = 0
      self._sum_x_sq = 0
      self._n = 0

      if windowSize is not None:
        self._windowSize = windowSize
        self._window = deque(maxlen=windowSize)


    def addPoint(self, x, y):
      self._sum_x += x
      self._sum_y += y
      self._sum_xy += x*y
      self._sum_x_sq += x*x
      self._n += 1

      if self._window is not None:
        if len(self._window) == self._windowSize:
          self.removePoint(*self._window.popleft())

        self._window.append((x,y))

    def removePoint(self, x, y):
      self._sum_x -= x
      self._sum_y -= y
      self._sum_xy -= x*y
      self._sum_x_sq -= x*x
      self._n -=1

    def getSlope(self):
      if self._n < 2:
        return None

      if self._window is not None and \
      len(self._window) < self._windowSize:
        return None

      den = self._sum_x_sq - self._sum_x**2 / float(self._n)
      if den == 0:
        return None

      num = self._sum_xy - self._sum_x * self._sum_y / float(self._n)
      return num/den


class ExponentialRegression(object):
  """ Helper class for computing the average percent change for a best-fit
  exponential function given a set of (x,y) points. This class tries to fit
  a function of the form  y(x) = a e^(bx) to the data. The function getPctChange()
  returns the value of e^(b)-1, where e^(b) is the ratio y(x+1)/y(x) for the
  best-fit curve. """

  def __init__(self, windowSize=None):
    self._linReg = LinearRegression(windowSize)

  def addPoint(self, x, y):
    self._linReg.addPoint(x, math.log(y))

  def removePoint(self, x, y):
    self._linReg.removePoint(x, math.log(y))

  def getPctChange(self):
    slope = self._linReg.getSlope()
    if slope is None:
      return None

    return math.exp(slope) - 1


class AveragePctChange(object):
  def __init__(self, windowSize=None):
    self._sum_pct_change = 0
    self._sum_pct_change_abs = 0
    self._n = 0

    self._last = None
    if windowSize is not None:
      self._windowSize = windowSize
      self._window = deque(maxlen=windowSize)

  def addPoint(self, x, y):
    if self._n > 0:
      if self._last != 0:
        pctChange = (y-self._last)/self._last
      else:
        pctChange = 0

      self._sum_pct_change += pctChange
      self._sum_pct_change_abs += abs(pctChange)
      self._window.append((x, pctChange))

    self._n += 1
    self._last = y
    if len(self._window) == self._windowSize:
      self.removePoint(*self._window.popleft())

  def removePoint(self, x, pctChange):
    self._sum_pct_change -= pctChange
    self._sum_pct_change_abs -= abs(pctChange)
    self._n -= 1

  def getPctChanges(self):
    if self._n < self._windowSize:
      return None,None


    return (self._sum_pct_change/self._n,
            self._sum_pct_change_abs/self._n)
