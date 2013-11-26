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

import numpy

from nupic.encoders.base import Encoder
from nupic.encoders.scalar import ScalarEncoder
from nupic.data.fieldmeta import FieldMetaType


class VectorEncoder(Encoder):
  """represents an array/vector of values of the same type (scalars, or date, ..);"""

  def __init__(self, length, encoder, name='vector', typeCastFn=None):
    """param length: size of the vector, number of elements
       param encoder: instance of encoder used for coding of the elements
       param typeCastFn: function to convert decoded output (as string) back to original values
       NOTE: this constructor cannot be used in description.py, as it depands passing of an object!
    """

    if not (isinstance(length, int) and length > 0):
      raise Exception("Length must be int > 0")
    if not isinstance(encoder, Encoder):
      raise Exception("Must provide an encoder")
    if typeCastFn is not None and not isinstance(typeCastFn, type):
      raise Exception("if typeCastFn is provided, it must be a function")

    self._len = length
    self._enc = encoder
    self._w = encoder.getWidth()
    self._name = name
    self._typeCastFn = typeCastFn
    self.encoders = None

  def encodeIntoArray(self, input, output):
    if not (isinstance(input, list) and len(input)==self._len):
      raise Exception("input must be list if size %d (it is %d)" % (self._len, len(input)))
    for e in range(self._len):
      tmp = self._enc.encode(input[e])
      output[e*self._w:(e+1)*self._w]=tmp
  

  def decode(self, encoded, parentFieldName=''):
    ret = []
    w = self._w
    for i in xrange(self._len):
      tmp = self._enc.decode(encoded[i*w:(i+1)*w])[0].values()[0][1] # dict.values().first_element.scalar_value
      if self._typeCastFn is not None:
        tmp = self._typeCastFn(tmp)
      ret.append(tmp)
    
    # Return result as EncoderResult
    if parentFieldName != '':
      fieldName = "%s.%s" % (parentFieldName, self._name)
    else:
      fieldName = self._name
    ranges = ret
    desc = ret
    return ({fieldName: (ranges, desc)}, [fieldName])

  def getData(self, decoded):
    """get the data part (vector) from the decode() output format; 
       use when you want to work with the data manually"""
    fieldname = decoded[1][0]
    return decoded[0][fieldname][0]
       
  ########################################################
  # the boring stuff

  def getDescription(self):
    return [(self._name, 0),]

  def getBucketValues(self):
    #TODO
    pass

  def getWidth(self):
    return self._len * self._enc.getWidth()

  def getDecoderOutputFieldTypes(self):
    return [FieldMetaType.list]

  def getBucketIndices(self, input):
    if not (isinstance(input, list) and len(input)==self._len):
      raise Exception("Input must be a list of size %d" % self._len) 
    return [0]



###############################################################################################
class VectorEncoderOPF(VectorEncoder):
  """Vector encoder using ScalarEncoder; 
     usecase: in OPF description.py files, see above why VectorEncoder 
     cannot be used there directly. """

  def __init__(self, length, w, minval, maxval, periodic=False, n=0, radius=0,
                resolution=0, name=None, verbosity=0, clipInput=False):
    """instance of VectorEncoder using ScalarEncoder as base, 
       use-case: in OPF description.py files, where you cannot use VectorEncoder directly (see above);
       param length: #elements in the vector, 
       param: rest of params is from ScalarEncoder, see scalar.py for details"""

    sc = ScalarEncoder(w, minval, maxval, periodic=periodic, n=n, radius=radius, resolution=resolution, 
                       name=name, verbosity=verbosity, clipInput=clipInput)
    super(VectorEncoderOPF, self).__init__(length, sc, typeCastFn=float)


#################################################################################################
class SimpleVectorEncoder(VectorEncoder):
  """Vector encoder for beginners, easy to create and play with;
     by default encodes list of 5 elements, numbers 0-100"""

  def __init__(self, length=5, minval=0, maxval=100, resolution=1, name='vect'):
    sc = ScalarEncoder(5, minval, maxval, resolution=resolution, name='idx')
    super(SimpleVectorEncoder, self).__init__(length, sc, typeCastFn=float)


