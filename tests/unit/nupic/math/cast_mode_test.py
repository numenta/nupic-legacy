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

"""Cast mode test."""

import sys

import numpy
import unittest2 as unittest

from nupic.bindings.math import SM32



class TestCastMode(unittest.TestCase):


  @unittest.skipIf(sys.platform == "linux2",
                   "Castmode test disabled on linux -- fails")
  def testCastMode(self):
    """Test for an obscure error that is fixed by the -castmode flag to swig.

    This code will throw an exception if the error exists.
    """
    hist = SM32(5, 10)
    t = numpy.array([0, 0, 1, 0, 1, 0, 0, 1, 0, 1], dtype='float32')

    hist.setRowFromDense(0, t)
    hist.setRowFromDense(1, t)
    self.assertSequenceEqual(tuple(hist.getRow(1)),
                             (0, 0, 1, 0, 1, 0, 0, 1, 0, 1))



if __name__ == "__main__":
  unittest.main()
