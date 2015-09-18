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

import numbers

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.encoders.adaptivescalar import AdaptiveScalarEncoder
from nupic.encoders.base import EncoderResult


class DeltaEncoder(AdaptiveScalarEncoder):
  """
  This is an implementation of a delta encoder. The delta encoder encodes differences between
  successive scalar values instead of encoding the actual values. It returns an actual value when
  decoding and not a delta.
  """


  def __init__(self, w, minval=None, maxval=None, periodic=False, n=0, radius=0,
                resolution=0, name=None, verbosity=0, clipInput=True, forced=False):
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
                   maxval=maxval, clipInput=True, name=name, verbosity=verbosity, forced=forced)
    self.width+=self._adaptiveScalarEnc.getWidth()
    self.n = self._adaptiveScalarEnc.n
    self._prevAbsolute = None    #how many inputs have been sent to the encoder?
    self._prevDelta = None

  def encodeIntoArray(self, input, output, learn=None):
    if not isinstance(input, numbers.Number):
      raise TypeError(
          "Expected a scalar input but got input of type %s" % type(input))

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


  def setStateLock(self, lock):
    self._stateLock = lock


  def setFieldStats(self, fieldName, fieldStatistics):
    pass


  def getBucketIndices(self, input, learn=None):
    return self._adaptiveScalarEnc.getBucketIndices(input, learn)


  def getBucketInfo(self, buckets):
    return self._adaptiveScalarEnc.getBucketInfo(buckets)


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


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)
    encoder.width = proto.width
    encoder.name = proto.name or None
    encoder.n = proto.n
    encoder._adaptiveScalarEnc = (
      AdaptiveScalarEncoder.read(proto.adaptiveScalarEnc)
    )
    encoder._prevAbsolute = proto.prevAbsolute
    encoder._prevDelta = proto.prevDelta
    encoder._stateLock = proto.stateLock
    return encoder


  def write(self, proto):
    proto.width = self.width
    proto.name = self.name or ""
    proto.n = self.n
    self._adaptiveScalarEnc.write(proto.adaptiveScalarEnc)
    proto.prevAbsolute = self._prevAbsolute
    proto.prevDelta = self._prevDelta
    proto.stateLock = self._stateLock
