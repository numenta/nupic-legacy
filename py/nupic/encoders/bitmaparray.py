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

import random

from nupic.data.fieldmeta import FieldMetaType
from nupic.encoders.base import *


############################################################################
class BitmapArrayEncoder(Encoder):
  """Convert a bitmap encoded as array indicies to an SDR

  Each encoding is an SDR in which w out of n bits are turned on.
  The input should be an array or string of indicies to turn on
  Note: the value for n must equal input length * w
  i.e. for n=8 w=1 [0,2,5] => 101001000
    or for n=8 w=1 "0,2,5" => 101001000

  i.e. for n=24 w=3 [0,2,5] => 111000111000000111000000000
    or for n=24 w=3 "0,2,5" => 111000111000000111000000000
  """

  ############################################################################
  def __init__(self, n, w, onbits=0, name="bitmaparray", verbosity=0):
    """
    n is the total bits in input
    w is the number of bits used to encode each input bit
    """

    self.n = n
    self.w = w
    self.onbits = onbits
    self.verbosity = verbosity
    self.description = [(name, 0)]
    self.name = name

  ############################################################################
  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override]
    """
    return (FieldMetaType.string,)

  ############################################################################
  def getWidth(self):
    return self.n

  ############################################################################
  def getDescription(self):
    return self.description

  ############################################################################
  def getScalars(self, input):
    """ See method description in base.py """
    return numpy.array([0])

  ############################################################################
  def getBucketIndices(self, input):
    """ See method description in base.py """
    return [0]

  ############################################################################
  def encodeIntoArray(self, input, output):
    """ See method description in base.py """
    if type(input) == str:
      input = input.split(',')

    for i in input:
      for j in xrange(0,self.w):
        output[(int(i)*self.w)+j] = 1

    if self.onbits > 0:
      random.seed(hash(str(output)))
      t = self.onbits - output.sum()
      while t > 0:
        """ turn on more bits to normalize """
        i = random.randint(0,self.n-1)
        if output[i] == 0:
          output[i] = 1
          t -= 1

      while t < 0:
        """ turn off some bits to normalize """
        i = random.randint(0,self.n-1)
        if output[i] == 1:
          output[i] = 0
          t += 1

    if self.verbosity >= 2:
      print "input:", input, "index:", index, "output:", output
      print "decoded:", self.decodedToStr(self.decode(output))


  ############################################################################
  def decode(self, encoded, parentFieldName=''):
    """ See the function description in base.py
    """

    if parentFieldName != '':
      fieldName = "%s.%s" % (parentFieldName, self.name)
    else:
      fieldName = self.name
    return ({fieldName: ([[0, 0]], 'bitmap')}, [fieldName])


  ############################################################################
  def getBucketInfo(self, buckets):
    """ See the function description in base.py
    """

    return [EncoderResult(value=0, scalar=0,
                         encoding=numpy.zeros(self.n * self.w))]

  ############################################################################
  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    return EncoderResult(value=0, scalar=0,
                         encoding=numpy.zeros(self.n * self.w))

  ############################################################################
  def closenessScores(self, expValues, actValues, **kwargs):
    """ Does a bitwise compare of the two bitmaps and returns a fractonal 
    value between 0 and 1 of how similar they are. 
    1 => identical
    0 => no overlaping bits

    kwargs will have the keyword "fractional", which is assumed by this encoder
    """

    ratio = 1.0
    esum = int(expValues.sum())
    asum = int(actValues.sum())
    if asum > esum:
      diff = asum - esum
      if diff < esum:
        ratio = 1 - diff/float(esum)
      else:
        ratio = 1/float(diff)

    olap = expValues & actValues
    osum = int(olap.sum())
    if esum == 0:
      r = 0.0
    else:
      r = osum/float(esum)
    r = r * ratio

    return numpy.array([r])

