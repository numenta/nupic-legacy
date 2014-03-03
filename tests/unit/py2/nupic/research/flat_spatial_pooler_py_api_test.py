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


import unittest2 as unittest

from nupic.bindings.algorithms import FlatSpatialPooler as FlatSpatialPooler

import  spatial_pooler_py_api_test

spatial_pooler_py_api_test.SpatialPooler = FlatSpatialPooler
FlatSpatialPoolerBaseAPITest = spatial_pooler_py_api_test.SpatialPoolerAPITest


def flatSetUp(self):
  self.sp = FlatSpatialPooler(inputShape=[5], coincidencesShape=[5])


spatial_pooler_py_api_test.SpatialPoolerAPITest.setUp = flatSetUp



class FlatSpatialPoolerAPITest(unittest.TestCase):


  def testGetMinDistance(self):
    sp = FlatSpatialPooler()
    inParam = 0.2 
    sp.setMinDistance(inParam)
    outParam = sp.getMinDistance()
    self.assertAlmostEqual(inParam, outParam)


  def testGetRandomSP(self):
    sp = FlatSpatialPooler()
    inParam = True 
    sp.setRandomSP(inParam)
    outParam = sp.getRandomSP()
    self.assertEqual(inParam, outParam)


    inParam = False
    sp.setRandomSP(inParam)
    outParam = sp.getRandomSP()
    self.assertEqual(inParam, outParam)



if __name__ == "__main__":
  unittest.main()
