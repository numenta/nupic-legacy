#!/usr/bin/env python
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

"""Unit tests for array algorithms."""

import unittest2 as unittest

import numpy

from nupic.bindings.math import nearlyZeroRange



class TestArrayAlgos(unittest.TestCase):


  def setUp(self):
    self.x = numpy.zeros((10))


  def testNearlyZeroRange1(self):
    self.assertTrue(nearlyZeroRange(self.x))


  def testNearlyZeroRange2(self):
    self.assertTrue(nearlyZeroRange(self.x, 1e-8))


  def testNearlyZeroRange3(self):
    self.assertTrue(nearlyZeroRange(self.x, 2))



if __name__ == '__main__':
  unittest.main()
