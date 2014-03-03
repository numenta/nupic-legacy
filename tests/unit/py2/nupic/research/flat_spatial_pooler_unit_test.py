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

from mock import Mock, patch, ANY, call
import numpy
import unittest2 as unittest
from copy import copy

from nupic.bindings.math import (count_gte,
                                 GetNTAReal,
                                 SM_01_32_32 as SparseBinaryMatrix,
                                 SM32 as SparseMatrix)
from nupic.research.flat_spatial_pooler import FlatSpatialPooler

# Globals
realType = GetNTAReal()
uintType = "uint32"

class FlatSpatialPoolerTest(unittest.TestCase):


  def setUp(self):
    self._sp = FlatSpatialPooler(
        inputShape=(5, 1),
        coincidencesShape=(10, 1))


  def testSelectVirginColumns(self):
    sp = self._sp
    sp._numColumns = 6
    sp._activeDutyCycles = numpy.zeros(sp._numColumns)
    virgins = list(sp._selectVirginColumns())
    trueVirgins = range(sp._numColumns)
    self.assertListEqual(trueVirgins,virgins)

    sp._activeDutyCycles = numpy.zeros(sp._numColumns)
    sp._activeDutyCycles[[3,4]] = 0.2
    virgins = list(sp._selectVirginColumns())
    trueVirgins = [0,1,2,5]
    self.assertListEqual(trueVirgins,virgins)


  def testSelectHighTierColumns(self):
    sp = self._sp
    sp._numColumns = 7
    sp._minDistance = 0.0
    sp._overlapsPct = numpy.array([1.0, 0.7, 0.8, 0.1, 1.0, 0.3, 0.1])
    vipColumns = sp._selectHighTierColumns(sp._overlapsPct)
    trueVIPColumns = [0, 4]
    self.assertListEqual(trueVIPColumns, list(vipColumns))

    sp._numColumns = 7
    sp._minDistance = 0.1
    sp._overlapsPct = numpy.array([0.0, 0.9, 0.85, 0.91, 1.0, 0.3, 0.89])
    vipColumns = sp._selectHighTierColumns(sp._overlapsPct)
    trueVIPColumns = [1, 3, 4]
    self.assertListEqual(trueVIPColumns, list(vipColumns))

    sp._numColumns = 7
    sp._minDistance = 0.15
    sp._overlapsPct = numpy.array([0.0, 0.9, 0.85, 0.91, 1.0, 0.3, 0.89])
    vipColumns = sp._selectHighTierColumns(sp._overlapsPct)
    trueVIPColumns = [1, 2, 3, 4, 6]
    self.assertListEqual(trueVIPColumns, list(vipColumns))

    sp._numColumns = 7
    sp._minDistance = 1.0
    sp._overlapsPct = numpy.array([0.0, 0.9, 0.85, 0.91, 1.0, 0.3, 0.89])
    vipColumns = sp._selectHighTierColumns(sp._overlapsPct)
    trueVIPColumns = range(7)
    self.assertListEqual(trueVIPColumns, list(vipColumns))

    sp._numColumns = 7
    sp._minDistance = 0.99
    sp._overlapsPct = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    vipColumns = sp._selectHighTierColumns(sp._overlapsPct)
    trueVIPColumns = []
    self.assertListEqual(trueVIPColumns, list(vipColumns))

  def testRandomSPDoesNotLearn(self):
    
    sp = FlatSpatialPooler(inputShape=5,
                           coincidencesShape=10,
                           randomSP=True)
    inputArray = (numpy.random.rand(5) > 0.5).astype(uintType)
    activeArray = numpy.zeros(sp._numColumns).astype(realType)
    # Should start off at 0
    self.assertEqual(sp._iterationNum, 0)
    self.assertEqual(sp._iterationLearnNum, 0)
    
    # Store the initialized state
    initialPerms = copy(sp._permanences)
    
    sp.compute(inputArray, False, activeArray)
    # Should have incremented general counter but not learning counter
    self.assertEqual(sp._iterationNum, 1)
    self.assertEqual(sp._iterationLearnNum, 0)
    
    # Should not learn even if learning set to True
    sp.compute(inputArray, True, activeArray)
    self.assertEqual(sp._iterationNum, 2)
    self.assertEqual(sp._iterationLearnNum, 0)
    
    # Check the initial perm state was not modified either
    self.assertEqual(sp._permanences, initialPerms)

  def testActiveColumnsEqualNumActive(self):
    '''
    After feeding in a record the number of active columns should
    always be equal to numActivePerInhArea
    '''

    for i in [1, 10, 50]:
      numActive = i
      inputShape = 10
      sp = FlatSpatialPooler(inputShape=inputShape,
                             coincidencesShape=100,
                             numActivePerInhArea=numActive)
      inputArray = (numpy.random.rand(inputShape) > 0.5).astype(uintType)
      inputArray2 = (numpy.random.rand(inputShape) > 0.8).astype(uintType)
      activeArray = numpy.zeros(sp._numColumns).astype(realType)
  
      # Random SP
      sp._randomSP = True
      sp.compute(inputArray, False, activeArray)
      sp.compute(inputArray2, False, activeArray)
      self.assertEqual(sum(activeArray), numActive)
      
      # Default, learning on
      sp._randomSP = False
      sp.compute(inputArray, True, activeArray)
      sp.compute(inputArray2, True, activeArray)
      self.assertEqual(sum(activeArray), numActive)
    
    

if __name__ == "__main__":
  unittest.main()
