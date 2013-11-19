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
from nupic.encoders.utility import UtilityEncoder

class UtilityEncoderTest(unittest.TestCase):
  """testing Utility encoder"""

  def setUp(self):
    self.data = [-1,0,10]

    # encoder for score: 0..100, fine-grained to 0.5
    self.scoreEnc = ScalarEncoder(3, 0, 100, resolution=0.5, name='score')

    # encoder for the input (data) part
    elem = ScalarEncoder(5,-5,50,resolution=1)
    self.dataEnc = VectorEncoder(len(self.data), elem, typeCastFn=float, name='data')

    # utility encoder
    def sumAll(list):
      return sum(list)

    self.fn = sumAll

    self.utilityEnc = UtilityEncoder(self.dataEnc, self.scoreEnc, feval=self.fn, name='sum-er')

  def testInitialization(self):
    """creating a utility encoder"""
    util = UtilityEncoder(self.dataEnc, self.scoreEnc, feval=self.fn, name='starter')
    assert True==isinstance(util, UtilityEncoder)

  def testEncoding(self):
    """check encoding.."""
    sc = self.fn(self.data) # expected
    score = self.utilityEnc.getScoreIN(self.data)
    assert sc == score

    enc = self.utilityEnc.encode(self.data)
    print "encoded=", enc

  def testDecoding(self):
    """decoding.."""
    enc = self.utilityEnc.encode(self.data)
    sc = self.fn(self.data) # expected
    score = self.utilityEnc.getScoreOUT(enc) #real
    print "score", score
    assert sc == score[0]

    dec = self.utilityEnc.decode(enc)
    print "decoded=", dec

    res = self.utilityEnc.getData(dec)
    assert res==self.data

  def testDemo1(self):
    """Alife: agent perceives its inner and outer environment and reacts;
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
       feval function's score cleverly."""

    dimX=5
    dimY=5
    from collections import namedtuple
    Point = namedtuple('Point', 'x y')
    pos = Point(3,3)
    target = Point(1,4)
    #action 1==walk 0==noop, 2==eat
    Agent = namedtuple('Agent', 'hunger hostile pos action target')
    bot = Agent(hunger=0, hostile=0, pos=pos, action=0, target=target, _visited=[])

    def _thinkRules(ag):
      sc = 50

      # dont die
      if(ag.hunger>=8 and ag.action!=2):
        return 0 # worst possible score
      if(ag.hunger>=8 and ag.action==2):
        return 100 # best idea to eat, when dying!

      # effects of actions
      if(ag.action==1): #walk
        sc += 10 # better to do sth than just sit
        _walk(ag, dimX, dimY)
      elif(ag.action==2): #eat
        _eat(ag)
      # else: noop



##########################################################
if __name__ == '__main__':
  unittest.main()
