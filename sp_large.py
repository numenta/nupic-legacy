#! /usr/bin/env python
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

# Disable since test code accesses private members in the class to be tested
# pylint: disable=W0212

#from mock import Mock
import numpy
#import unittest2 as unittest

from nupic.support.unittesthelpers.algorithm_test_helpers import (
  getNumpyRandomGenerator, getSeed )
from nupic.bindings.math import (SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix,
                                 GetNTAReal)
#from nupic.research.spatial_pooler import SpatialPooler
from nupic.bindings.algorithms import SpatialPooler 


realDType = GetNTAReal()

class SpatialPoolerTest(object):
  """Unit Tests for SpatialPooler class."""


  def testCompute1(self):
    """Checks that feeding in the same input vector leads to polarized
    permanence values: either zeros or ones, but no fractions"""

    inDim = [10000,10,10]
    colDim = [2048, 1, 1]


    sp = SpatialPooler(
        inputDimensions=inDim,
        columnDimensions=colDim,
        potentialRadius=3,
        potentialPct=0.5,
        globalInhibition=False,
        localAreaDensity=-1.0,
        numActiveColumnsPerInhArea=3,
        stimulusThreshold=1,
        synPermInactiveDec=0.01,
        synPermActiveInc=0.1,
        synPermConnected=0.10,
        minPctOverlapDutyCycle=0.1,
        minPctActiveDutyCycle=0.1,
        dutyCyclePeriod=10,
        maxBoost=10.0,
        seed=getSeed(),
        spVerbosity=0)

    inputVector = numpy.random.randint(0, 2, inDim)
    activeArray = numpy.zeros(colDim)

    for i in xrange(10000):
      sp.compute(inputVector, True, activeArray)


if __name__ == "__main__":
  ex = SpatialPoolerTest()
  ex.testCompute1()
