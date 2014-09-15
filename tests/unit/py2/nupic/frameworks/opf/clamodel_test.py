#!/usr/bin/env python
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

"""Unit tests for the clamodel module."""

import unittest2 as unittest

from nupic.frameworks.opf.clamodel import CLAModel



class CLAModelTest(unittest.TestCase):
  """CLAModel unit tests."""


  def testRemoveUnlikelyPredictionsEmpty(self):
    result = CLAModel._removeUnlikelyPredictions({}, 0.01, 3)
    self.assertDictEqual(result, {})


  def testRemoveUnlikelyPredictionsSingleValues(self):
    result = CLAModel._removeUnlikelyPredictions({1: 0.1}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1})
    result = CLAModel._removeUnlikelyPredictions({1: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.001})


  def testRemoveUnlikelyPredictionsLikelihoodThresholds(self):
    result = CLAModel._removeUnlikelyPredictions({1: 0.1, 2: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1})
    result = CLAModel._removeUnlikelyPredictions({1: 0.001, 2: 0.002}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.002})
    result = CLAModel._removeUnlikelyPredictions({1: 0.002, 2: 0.001}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.002})


  def testRemoveUnlikelyPredictionsMaxPredictions(self):
    result = CLAModel._removeUnlikelyPredictions({1: 0.1, 2: 0.2, 3: 0.3},
                                                 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.2, 3: 0.3, 4: 0.4})


  def testRemoveUnlikelyPredictionsComplex(self):
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.004}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.005}, 0.01, 3)
    self.assertDictEqual(result, {2: 0.2, 3: 0.3, 4: 0.4})
    result = CLAModel._removeUnlikelyPredictions(
        {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.004, 5: 0.005}, 0.01, 3)
    self.assertDictEqual(result, {1: 0.1, 2: 0.2, 3: 0.3})


  def testInitBasicCLAModel(self):
    #TODO enable this test
    #self.assertTrue(CLAModel(), CLAModel)
    pass

if __name__ == "__main__":
  unittest.main()
