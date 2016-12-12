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

import time
import numpy
import unittest2 as unittest

from nupic.support.unittesthelpers.algorithm_test_helpers \
     import getNumpyRandomGenerator, convertSP, CreateSP
from nupic.bindings.math import (count_gte,
                                 GetNTAReal,
                                 SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix)
from nupic.research.spatial_pooler import SpatialPooler

uintType = "uint32"


class SpatialPoolerComputeTest(unittest.TestCase):
  """
  End to end tests of the compute function for the SpatialPooler class with no
  mocking anywhere. 
  """


  def basicComputeLoop(self, imp, params, inputSize, columnDimensions,
                       seed = None):
    """
    Feed in some vectors and retrieve outputs. Ensure the right number of
    columns win, that we always get binary outputs, and that nothing crashes.
    """
    sp = CreateSP(imp,params)

    # Create a set of input vectors as well as various numpy vectors we will
    # need to retrieve data from the SP
    numRecords = 100
    randomState = getNumpyRandomGenerator(seed)
    inputMatrix = (
      randomState.rand(numRecords,inputSize) > 0.8).astype(uintType)

    y = numpy.zeros(columnDimensions, dtype = uintType)
    dutyCycles = numpy.zeros(columnDimensions, dtype = uintType)

    # With learning on we should get the requested number of winners
    for v in inputMatrix:
      y.fill(0)
      sp.compute(v, True, y)
      self.assertEqual(sp.getNumActiveColumnsPerInhArea(),y.sum())
      self.assertEqual(0,y.min())
      self.assertEqual(1,y.max())

    # With learning off and some prior training we should get the requested
    # number of winners
    for v in inputMatrix:
      y.fill(0)
      sp.compute(v, False, y)
      self.assertEqual(sp.getNumActiveColumnsPerInhArea(),y.sum())
      self.assertEqual(0,y.min())
      self.assertEqual(1,y.max())


  def testBasicCompute1(self):
    """
    Run basicComputeLoop with mostly default parameters
    """
    # Size of each input vector
    inputSize = 30
    
    # Size of each output SDR vector
    columnDimensions = 50

    params = {
      "inputDimensions": [inputSize],
      "columnDimensions": [columnDimensions],
      "potentialRadius": inputSize,
      'globalInhibition': True,
      "seed": int((time.time()%10000)*10),
    }
    print "testBasicCompute1, SP seed set to:",params['seed']
    self.basicComputeLoop('py', params, inputSize, columnDimensions)
    self.basicComputeLoop('cpp', params, inputSize, columnDimensions)


  def testBasicCompute2(self):
    """
    Run basicComputeLoop with learning turned off.
    """

    # Size of each input vector
    inputSize = 100
    
    # Size of each output SDR vector
    columnDimensions = 100

    params = {
      "inputDimensions": [inputSize],
      "columnDimensions": [columnDimensions],
      "potentialRadius": inputSize,
      'globalInhibition': True,
      "synPermActiveInc": 0.0,
      "synPermInactiveDec": 0.0,
      "seed": int((time.time()%10000)*10),
    }
    print "testBasicCompute2, SP seed set to:",params['seed']
    self.basicComputeLoop('py', params, inputSize, columnDimensions)
    self.basicComputeLoop('cpp', params, inputSize, columnDimensions)


if __name__ == "__main__":
  unittest.main()
