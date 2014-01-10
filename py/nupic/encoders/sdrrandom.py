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
from nupic.encoders.base import Encoder


############################################################################
class SDRRandomEncoder(Encoder):
  """Generate a random encoding

  Each  encoding is an SDR in which w out of n bits are turned on.

  """

  ############################################################################
  def __init__(self, n, w, name="random", verbosity=0):
    """
    n is  total bits in output
    w is the number of bits that are turned on for each rep
    """

    self.n = n
    self.w = w
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
    output[0:self.n] = 0
    output[0:self.n][random.sample(xrange(self.n), self.w)] = 1

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
    return ({fieldName: ([[0, 0]], 'rand')}, [fieldName])


  ############################################################################
  def getBucketInfo(self, buckets):
    """ See the function description in base.py
    """

    return [EncoderResult(value=0, scalar=0,
                         encoding=numpy.zeros(self.n))]

  ############################################################################
  def topDownCompute(self, encoded):
    """ See the function description in base.py
    """

    return EncoderResult(value=0, scalar=0,
                         encoding=numpy.zeros(self.n))

  ############################################################################
  def closenessScores(self, expValues, actValues, **kwargs):
    """ See the function description in base.py

    kwargs will have the keyword "fractional", which is ignored by this encoder
    """

    return numpy.array([0])
