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

"""Unit tests for scalar space encoder"""

import unittest2 as unittest

from nupic.encoders.scalarspace import ScalarSpaceEncoder


#########################################################################
class ScalarSpaceEncoderTest(unittest.TestCase):
  '''Unit tests for ScalarSpaceEncoder class'''


  def testScalarSpaceEncoder(self):
    """scalar space encoder"""
    # use of forced=True is not recommended, but used in the example for readibility, see scalar.py
    sse = ScalarSpaceEncoder(w=21,minval=1,maxval=2,n=100,radius=1,
            resolution=1,name="SP1",verbosity=0,clipInput=False,space="delta")
    self.assertTrue(sse.isDelta())
    sse = ScalarSpaceEncoder(w=21,minval=1,maxval=2,n=100,radius=1,
            resolution=1,name="sp2",verbosity=0,clipInput=False,space="absolute")
    self.assertFalse(sse.isDelta())

     
###########################################
if __name__ == '__main__':
  unittest.main()
