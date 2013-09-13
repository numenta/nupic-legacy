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

from base import *
from nupic.data.fieldmeta import FieldMetaType

############################################################################
class PassThruEncoder(Encoder):
  """Pass an encoded SDR straight to the model

  Each encoding is an SDR in which w out of n bits are turned on.
  The input should be a 1-D array or numpy.ndarray of length n

  """

  ############################################################################
  def __init__(self, n, w, name="passthru", verbosity=0):
    """
    n is the total bits in input/output
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
    if type(input) == numpy.ndarray:
      numpy.copyto(output, input)
    else:
      for i, v in enumerate(input):
        output[i] = v

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
    return ({fieldName: ([[0, 0]], 'input')}, [fieldName])


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

############################################################################
def testPassThruEncoder():
  print "Testing PassThruEncoder...",

  fieldWidth = 9
  bitsOn = 3

  s = PassThruEncoder(n=fieldWidth, w=bitsOn, name="foo")

  sdr = [0,0,0,1,1,1,0,0,0]
  out = s.encode(sdr)
  assert out.sum() == bitsOn

  sdr = numpy.zeros(fieldWidth, dtype=defaultDtype)
  sdr[0:bitsOn] = 1
  out = s.encode(sdr)
  assert (out == sdr).all()
  #print out

  x = s.decode(out)
  print x
  assert isinstance(x[0], dict)
  assert "foo" in x[0]

  print "passed"


################################################################################
if __name__=='__main__':

  # Run all tests
  testPassThruEncoder()
