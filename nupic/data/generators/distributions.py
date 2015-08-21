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
# Author: Surabhi Gupta

from math import *
from random import *

import numpy as np


class Distributions():


  def __init__(self):
    """A distribution is a set of values with certain statistical properties

    Methods/properties that must be implemented by subclasses
    - getNext() -- Returns the next value for the distribution
    - getData(n) -- Returns n values for the distribution
    - getDescription() -- Returns a dict of parameters pertinent to the
      distribution, if any as well as state variables.
    """


  def getNext(self):
    """ Returns the next value of the disribution using knowledge about the
    current state of the distribution as stored in numValues.
    """
    raise Exception("getNext must be implemented by all subclasses")


  def getData(self, n):
    """Returns the next n values for the distribution as a list."""

    records = [self.getNext() for x in range(n)]
    return records


  def getDescription(self):
    """Returns a dict of parameters pertinent to the distribution (if any) as
    well as state variables such as numValues."""

    raise Exception("getDescription must be implemented by all subclasses")



class SineWave(Distributions):
  """Generates a sinewave of a given period, amplitude and phase shift"""


  def __init__(self, params={}):

    if 'period' in params: self.period=params.pop('period')
    else: self.period=pi
    if 'amplitude' in params:
      self.amplitude=params.pop('amplitude')
    else: self.amplitude=1
    if 'phaseShift' in params: self.phaseShift = params.pop('phaseShift')
    else: self.phaseShift=0
    self.valueNum=0


  def getNext(self):
    nextVal = self.amplitude*np.sin(2*pi*(self.period)*self.valueNum*(pi/180) - \
      self.phaseShift)
    self.valueNum+=1

    return nextVal


  def getData(self, numOfValues):
    return Distributions.getData(self, numOfValues)


  def getDescription(self):
    description = dict(name='SineWave', period=self.period, amplitude=self.amplitude, \
                         phaseShift=self.phaseShift, numOfValues=self.valueNum)

    return description



class RandomCategories(Distributions):
  """Generates random categories"""


  def __init__(self, params={}):
    self.valueNum=0
    self.alphabet = 'abcdefghijklmnopqrstuvwxyz'


  def getNext(self):
    self.valueNum+=1

    return ''.join(x for x in sample(self.alphabet, randint(3,15)))


  def getData(self, numOfValues):
    return Distributions.getData(self, numOfValues)


  def getDescription(self):
    description = dict(name='Random Categories', numOfValues=self.valueNum)

    return description



class GaussianDistribution(Distributions):
  """Generates a gaussian distribution"""


  def __init__(self, params={}):

    self.valueNum=0
    assert 'numOfValues' in params
    self.numOfValues = params.pop('numOfValues')

    if 'mean' in params: self.mean = params.pop('mean')
    else: self.mean = 0

    if 'std' in params: self.std=params.pop('std')
    else: self.std = 0.6

    self.records = np.random.normal(self.mean, self.std, self.numOfValues)


  def getNext(self):

    assert (self.numOfValues>self.valueNum)
    nextValue = self.records[self.valueNum]
    self.valueNum+=1

    return nextValue


  def getData(self):
    return Distributions.getData(self, self.numOfValues)


  def getDescription(self):
    description = dict(name='GaussianDistribution', mean=self.mean,
            standardDeviation=self.std, numOfValues=self.valueNum)
