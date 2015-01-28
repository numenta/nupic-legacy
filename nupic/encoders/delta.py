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


  def __init__(self, w, n, minval=None, maxval=None, 
                name=None, verbosity=0, clipInput=True, forced=False):
    """[AdaptiveScalarEncoder class method override]"""
    
    # periodic must be False for Delta encoders
    super(DeltaEncoder,  self).__init__(w=w, n=n, minval=minval, maxval=maxval,
             name=name, verbosity=verbosity, forced=forced)
    
    self._learningEnabled = True
    self._stateLock = False
    self._init = True
    assert n>0           #An adaptive encoder can only be intialized using n

    self._prevAbsolute = None    #how many inputs have been sent to the encoder?

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
      if self._prevAbsolute is None:
        self._prevAbsolute = input
      delta = input - self._prevAbsolute
      super(DeltaEncoder, self).encodeIntoArray(delta, output, learn)
      if not self._stateLock:
        self._prevAbsolute = input
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
  def topDownCompute(self, encoded):
    """[ScalarEncoder class method override]"""

    #Decode to delta scalar
    if self._prevAbsolute is None:
      return [EncoderResult(value=0, scalar=0, encoding=numpy.zeros(self.n))]
    ret = super(DeltaEncoder, self).topDownCompute(encoded)
    val = float(super(DeltaEncoder, self).decode(encoded)[0].values()[0][1])
    print ret
    diff = self._prevAbsolute
    if self._stateLock or self._init: 
      diff = 0
      self._init = False
    print "abs",self._prevAbsolute," diff",diff," val",val," ",self._init
    ret = [EncoderResult(value=val-diff,
                          scalar=val-diff,
                          encoding=ret[0].encoding)]
    print "pos",ret[0]
    return ret
