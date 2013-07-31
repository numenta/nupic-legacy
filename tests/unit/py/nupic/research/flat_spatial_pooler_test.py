#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import numpy
from mock import Mock, patch, ANY, call
import unittest2 as unittest
from nupic.bindings.math import SM32 as SparseMatrix, \
                                SM_01_32_32 as SparseBinaryMatrix, \
                                count_gte, GetNTAReal
from nupic.research.flat_spatial_pooler import FlatSpatialPooler

class FlatSpatialPoolerTest(unittest.TestCase):

	def setUp(self):
		self._sp = FlatSpatialPooler(
			   numInputs = 5,
               numColumns = 5,
               localAreaDensity = 0.1,
               numActiveColumnsPerInhArea=-1,
               stimulusThreshold=1,
               minDistance = 0.0,
               seed=-1,
               spVerbosity=0,
			)

	def testSelectVIPColumns(self):
		sp = self._sp
		sp._numColumns = 7
		sp._minDistance = 0.0
		sp._overlapsPct = numpy.array([1.0, 0.7, 0.8, 0.1, 1.0, 0.3, 0.1])
		vipColumns = sp._selectVIPColumns(sp._overlapsPct)
		trueVIPColumns = [0, 4]
		self.assertListEqual(trueVIPColumns, list(vipColumns))

		sp._numColumns = 7
		sp._minDistance = 0.1
		sp._overlapsPct = numpy.array([0.0, 0.9, 0.85, 0.91, 1.0, 0.3, 0.89])
		vipColumns = sp._selectVIPColumns(sp._overlapsPct)
		trueVIPColumns = [1, 3, 4]
		self.assertListEqual(trueVIPColumns, list(vipColumns))

		sp._numColumns = 7
		sp._minDistance = 0.15
		sp._overlapsPct = numpy.array([0.0, 0.9, 0.85, 0.91, 1.0, 0.3, 0.89])
		vipColumns = sp._selectVIPColumns(sp._overlapsPct)
		trueVIPColumns = [1, 2, 3, 4, 6]
		self.assertListEqual(trueVIPColumns, list(vipColumns))

		sp._numColumns = 7
		sp._minDistance = 1.0
		sp._overlapsPct = numpy.array([0.0, 0.9, 0.85, 0.91, 1.0, 0.3, 0.89])
		vipColumns = sp._selectVIPColumns(sp._overlapsPct)
		trueVIPColumns = range(7)
		self.assertListEqual(trueVIPColumns, list(vipColumns))

		sp._numColumns = 7
		sp._minDistance = 0.99
		sp._overlapsPct = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
		vipColumns = sp._selectVIPColumns(sp._overlapsPct)
		trueVIPColumns = []
		self.assertListEqual(trueVIPColumns, list(vipColumns))


if __name__ == "__main__":
  unittest.main()