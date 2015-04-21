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

## run python -m cProfile --sort cumTime tp_large.py 

#from mock import Mock
import numpy
#import unittest2 as unittest

from nupic.support.unittesthelpers.algorithm_test_helpers import (
  getNumpyRandomGenerator, getSeed )
from nupic.bindings.math import (SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix,
                                 GetNTAReal)
from nupic.research.TP10X2 import TP10X2 as TP 


realDType = GetNTAReal()

class SpatialPoolerTest(object):
  """Unit Tests for SpatialPooler class."""


  def testCompute1(self):
    """Checks that feeding in the same input vector leads to polarized
    permanence values: either zeros or ones, but no fractions"""

    tpDim = 2048
    
    tp = TP(numberOfCols=tpDim)

    tpArray = numpy.random.randint(0, 2, tpDim).astype('float32')

    for i in xrange(10000):
      tp.compute(tpArray, True)



if __name__ == "__main__":
  ex = SpatialPoolerTest()
  ex.testCompute1()
