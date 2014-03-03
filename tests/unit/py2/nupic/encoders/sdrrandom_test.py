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

"""Unit tests for SDRRandom encoder"""

import unittest2 as unittest
from nupic.encoders.sdrrandom import SDRRandomEncoder


#########################################################################
class SDRRandomEncoderTest(unittest.TestCase):
  '''Unit tests for SDRRandomEncoder class'''

  def testSDRRandomEncoder(self):
      print "Testing RandomEncoder...",

      fieldWidth = 25
      bitsOn = 10

      s = SDRRandomEncoder(n=fieldWidth, w=bitsOn, name="foo")

      for _ in range(100):
        out = s.encode(0)
        self.assertEqual(out.shape, (fieldWidth,))
        self.assertEqual(out.sum(), bitsOn)
        #print out

      x = s.decode(out)
      print x
      self.assertIsInstance(x[0], dict)
      self.assertTrue("foo" in x[0])

###########################################
if __name__ == '__main__':
  unittest.main()
