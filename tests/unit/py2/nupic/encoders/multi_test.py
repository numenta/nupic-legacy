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

"""Unit tests for multi- encoder"""

import numpy
import unittest2 as unittest

from nupic.encoders.multi import MultiEncoder as ME
from nupic.encoders import *
from nupic.data.dictutils import DictObj

#########################################################################
class MultiEncoderTest(unittest.TestCase):
  '''Unit tests for MultiEncoder class'''


##########################################################################
  def testMultiEncoder(self):
      """Testing MultiEncoder..."""

      e = MultiEncoder()

      # should be 7 bits wide
      e.addEncoder("dow", ScalarEncoder(w=3, resolution=1, minval=1, maxval=8,
                    periodic=True, name="day of week"))
      # sould be 14 bits wide
      e.addEncoder("myval", ScalarEncoder(w=5, resolution=1, minval=1, maxval=10,
                    periodic=False, name="aux"))
      self.assertEqual(e.getWidth(), 21)
      self.assertEqual(e.getDescription(), [("day of week", 0), ("aux", 7)])

      d = DictObj(dow=3, myval=10)
      expected=numpy.array([0,1,1,1,0,0,0] + [0,0,0,0,0,0,0,0,0,1,1,1,1,1], dtype='uint8')
      output = e.encode(d)
      assert(expected == output).all()


      e.pprintHeader()
      e.pprint(output)

      # Check decoding
      decoded = e.decode(output)
      #print decoded
      self.assertEqual(len(decoded), 2)
      (ranges, desc) = decoded[0]['aux']
      self.assertTrue(len(ranges) == 1 and numpy.array_equal(ranges[0], [10, 10]))
      (ranges, desc) = decoded[0]['day of week']
      self.assertTrue(len(ranges) == 1 and numpy.array_equal(ranges[0], [3, 3]))
      print "decodedToStr=>", e.decodedToStr(decoded)

      e.addEncoder("myCat", SDRCategoryEncoder(n=7, w=3,
                                               categoryList=["run", "pass","kick"]))

      print "\nTesting mixed multi-encoder"
      d = DictObj(dow=4, myval=6, myCat="pass")
      output = e.encode(d)
      topDownOut = e.topDownCompute(output)
      self.assertEqual(topDownOut[0].value, 4)
      self.assertEqual(topDownOut[1].value, 6)
      self.assertEqual(topDownOut[2].value, "pass")
      self.assertEqual(topDownOut[2].scalar, 2)
      self.assertEqual(topDownOut[2].encoding.sum(), 3)

############################################################################
  def testMultiEncoder_overloaded(self):
    """testing overloaded encode/decode functions..."""
    e = ME()
  
    e.addEncoder("age", ScalarEncoder(w=3, resolution=1, minval=1, maxval=120, periodic=False, name="age"))
    e.addEncoder("firstname", SDRCategoryEncoder(n=10, w=5, categoryList=["Mark", "Anna", "John", "Eve"]))

    #DictObj
    d = DictObj(age=18, firstname="Eve")
    res_Dict = e.encode(d)
  
    #List
    res_List = e.encode([18, "Eve"])
  
    #Array
    res_NpyArr = e.encode(numpy.array([18, "Eve"]))

    #check encodings
    assert( (res_Dict == res_List).all() and (res_List == res_NpyArr).all() )

    #decode
    l = [21, "Mark"]
    le = e.encode(l)
    #outputMode='Dict' (default)
    res = e.decode(le)
    assert( isinstance(res, DictObj) and res['age'] == 21 and res['firstname'] == "Mark")

    #'List'
    e.outputMode = 'List'
    res = e.decode(le)
    assert( isinstance(res, list) and res[0] == 21 and res[1] == "Mark")

    #'NumpyArray'
    e.outputMode = 'NumpyArray'
    res = e.decode(le)
    assert( isinstance(res, numpy.ndarray) and res[0] == 21 and res[1] == "Mark")
  
  ################################################################################
  def testSimpleVector(self):
    """testing SimpleVector..."""
    from nupic.encoders.multi import SimpleVector as Vec
    v = Vec(5, 0, 10, outputMode='List')
    data = [1, 2, 3, 4, 5]
    enc = v.encode(data)
    dec = v.decode(enc)
    assert (data == dec).all()

###########################################
if __name__ == '__main__':
  unittest.main()
