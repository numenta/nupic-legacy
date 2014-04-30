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


import unittest2 as unittest


from nupic.encoders.scalar import ScalarEncoder
from nupic.encoders.vector import VectorEncoder
from nupic.encoders.extras.utility import UtilityEncoder, SimpleUtilityEncoder, UtilityEncoderOPF

class UtilityEncoderTest(unittest.TestCase):
  """testing Utility encoder"""

  def setUp(self):
    self.data = [-1,0,10]

    # encoder for score: 0..100, fine-grained to 0.5
    self.scoreEnc = ScalarEncoder(21, 0, 100, resolution=0.5, name='score')

    # encoder for the input (data) part
    elem = ScalarEncoder(21,-5,50,resolution=1)
    self.dataEnc = VectorEncoder(len(self.data), elem, typeCastFn=float, name='data')

    # utility encoder
    def sumAll(list):
      return sum(list)

    self.fn = sumAll

    self.utilityEnc = UtilityEncoder(self.dataEnc, self.scoreEnc, feval=self.fn, name='sum-er')

  def testInitialization(self):
    """creating a utility encoder"""
    util = UtilityEncoder(self.dataEnc, self.scoreEnc, feval=self.fn, name='starter')
    self.assertTrue(isinstance(util, UtilityEncoder),"failed to initialize UtilityEncoder")

  def testEncoding(self):
    """check encoding.."""
    sc = self.fn(self.data) # expected
    score = self.utilityEnc.getScoreIN(self.data)
    self.assertEqual(sc,score,"encoding: score is not the same")

    enc = self.utilityEnc.encode(self.data)
#    print "encoded=", enc

  def testDecoding(self):
    """decoding.."""
    enc = self.utilityEnc.encode(self.data)
    sc = self.fn(self.data) # expected
    score = self.utilityEnc.getScoreOUT(enc) #real
#    print "score", score
    self.assertEqual(sc, score,"decoding: score not equal")

    dec = self.utilityEnc.decode(enc)
#    print "decoded=", dec

    res = self.utilityEnc.getData(dec, int)
#    print "res=", res
    self.assertEqual(res, self.data, "decoded data not equal to original") 
    sc2 = self.utilityEnc.getScoreOUT(enc)
    self.assertAlmostEqual(sc, sc2, 0.01, "decoded score is not equal to original") # almostEqual because 9 (int) != 9.0 (float)

  def testDemo1(self):
    """
    Alife: agent perceives its inner and outer environment and reacts;
       states:
         hunger(0=full, 10=starving);
         hostile env (0=lovely place, 3=hell);
         pos_x, pos_y coordinates in the world;
       actions:
         walk (random direction, for simplicity)
         eat  (reduce hunger)
         noop (idle)
       external states:
         target (x,y) -- desired position
       goal: 
         "Stay alive and explore to find the target." 

       We can achieve the goal by encoding "rules"/physics laws/ground truths on the
       feval function's score cleverly.
    """
    pass

  def testSimpleUtilityEncoder(self):
    """making it simple.."""
    ut = SimpleUtilityEncoder()
    self.assertTrue(isinstance(ut, SimpleUtilityEncoder))
    def scoring(listA):
      """average value"""
      return sum(listA)/float(len(listA))
    ut.setEvaluationFn(scoring)
    data = [1,2,3,4,5]
    score=scoring(data) # 3.0
    self.assertEqual(ut.getScoreIN(data),score)
    enc = ut.encode(data)
    dec = ut.decode(enc)
    self.assertEqual(data, ut.getData(dec))
    self.assertEqual(score, ut.getScoreOUT(enc))

  def testUtilityEncoderOPF(self):
    """UtilityEncoder in OPF.."""
    # prepare /tmp/myfun.py as feval function to load
    with open("/tmp/myfun.py", "w") as text_file:
      text_file.write("def feval(self, listData):\n  # compute avg\n  return sum(listData)/size(listData)\n")
    # test OPF
    utOPF = UtilityEncoderOPF("/tmp/myfun.py", length=3)
    self.assertIsInstance(utOPF, UtilityEncoderOPF, "failed to create UtilityEncoderOPF with file /tmp/myfun.py") 

##########################################################
if __name__ == '__main__':
  unittest.main()
