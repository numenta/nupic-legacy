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
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders import *

from base import *
import numpy as np


class DeltaEncoder(AdaptiveScalarEncoder):
  """
  This is an implementation of a delta encoder. The delta encoder encodes differences between
  successive scalar values instead of encoding the actual values. It returns an actual value when
  decoding and not a delta.
  """

  ############################################################################
  def __init__(self, w, minval=None, maxval=None, periodic=False, n=0, radius=0,
                resolution=0, name=None, verbosity=0, clipInput=True):
    """[ScalarEncoder class method override]"""
    self._learningEnabled = True
    self._stateLock = False
    self.width = 0
    self.encoders = None
    self.description = []
    self.name = name
    if periodic:
      #Delta scalar encoders take non-periodic inputs only
      raise Exception('Delta encoder does not encode periodic inputs')
    assert n!=0           #An adaptive encoder can only be intialized using n

    self._adaptiveScalarEnc = AdaptiveScalarEncoder(w=w, n=n, minval=minval,
                   maxval=maxval, clipInput=True, name=name, verbosity=verbosity)
    self.width+=self._adaptiveScalarEnc.getWidth()
    self.n = self._adaptiveScalarEnc.n
    self._prevAbsolute = None    #how many inputs have been sent to the encoder?
    self._prevDelta = None

  def encodeIntoArray(self, input, output, learn=None):

    if learn is None:
      learn =  self._learningEnabled
    if input == SENTINEL_VALUE_FOR_MISSING_DATA:
      output[0:self.n] = 0
    else:
      #make the first delta zero so that the delta ranges are not messed up.
      if self._prevAbsolute==None:
        self._prevAbsolute= input
      delta = input - self._prevAbsolute
      self._adaptiveScalarEnc.encodeIntoArray(delta, output, learn)
      if not self._stateLock:
        self._prevAbsolute = input
        self._prevDelta = delta
      return output

  ############################################################################
  def setStateLock(self, lock):
    self._stateLock = lock
  ############################################################################
  def setFieldStats(self, fieldName, fieldStatistics):
    pass
  ############################################################################
  def isDelta(self):
    return True
  ############################################################################
  def getBucketIndices(self, input, learn=None):
    return self._adaptiveScalarEnc.getBucketIndices(input, learn)
  ############################################################################
  def getBucketInfo(self, buckets):
    return self._adaptiveScalarEnc.getBucketInfo(buckets)
  ############################################################################
  def topDownCompute(self, encoded):
    """[ScalarEncoder class method override]"""

    #Decode to delta scalar
    if self._prevAbsolute==None or self._prevDelta==None:
      return [EncoderResult(value=0, scalar=0,
                             encoding=numpy.zeros(self.n))]
    ret = self._adaptiveScalarEnc.topDownCompute(encoded)
    if self._prevAbsolute != None:
      ret = [EncoderResult(value=ret[0].value+self._prevAbsolute,
                          scalar=ret[0].scalar+self._prevAbsolute,
                          encoding=ret[0].encoding)]
#      ret[0].value+=self._prevAbsolute
#      ret[0].scalar+=self._prevAbsolute
    return ret




def testDeltaEncoder():
  print "testing delta encoder"
  dencoder = DeltaEncoder(w=21, n=100)
  adaptscalar = AdaptiveScalarEncoder(w=21, n=100)

  for i in range(5):
    encarr =  dencoder.encodeIntoArray(i, np.zeros(100), learn=True)
  dencoder.setStateLock(True)
  for i in range(5, 7):
    encarr =  dencoder.encodeIntoArray(i, np.zeros(100), learn=True)
  res = dencoder.topDownCompute(encarr)
  assert res[0].value == 6
  assert dencoder.topDownCompute(encarr)[0].value == res[0].value
  assert dencoder.topDownCompute(encarr)[0].scalar == res[0].scalar
  assert (dencoder.topDownCompute(encarr)[0].encoding == res[0].encoding).all()

  print "simple delta reconstruction test passed"

  feedIn  = [1, 10, 4, 7, 9, 6, 3, 1]
  expectedOut = [0, 9, -6, 3, 2, -3, -3, -2]
  dencoder.setStateLock(False)
  #Check that the deltas are being returned correctly.
  for i in range(len(feedIn)):
    aseencode = np.zeros(100)
    adaptscalar.encodeIntoArray(expectedOut[i], aseencode, learn=True)
    delencode = np.zeros(100)
    dencoder.encodeIntoArray(feedIn[i], delencode, learn=True)
    assert  (delencode[0] == aseencode[0]).all()

  print "encoding verification test passed"

  feedIn  = [1, 10, 9, 7, 9, 6, 3, 1]
  expectedOut = [0, 9, -6, 3, 2, -3, -3, -2]
  #Check that locking the state works correctly.
  for i in range(len(feedIn)):
    if i == 3:
      dencoder.setStateLock(True)

    aseencode = np.zeros(100)
    adaptscalar.encodeIntoArray(expectedOut[i], aseencode, learn=True)
    delencode = np.zeros(100)
    if i>=3:
      dencoder.encodeIntoArray(feedIn[i]-feedIn[2], delencode, learn=True)
    else:
      dencoder.encodeIntoArray(expectedOut[i], delencode, learn=True)

    assert  (delencode[0] == aseencode[0]).all()

  print "state locking test passed"

if __name__ == "__main__":
  testDeltaEncoder()
