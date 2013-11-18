from nupic.encoders.base import Encoder
from nupic.encoders.scalar import ScalarEncoder
from nupic.data.fieldmeta import FieldMetaType
import numpy

class VectorEncoder(Encoder):
  """represents an array of values of the same type"""

  def __init__(self, length, encoder, name='vector'):
    """param length: size of the vector, number of elements
       param encoder: instance of encoder used for coding of the elements
       NOTE: this constructor cannot be used in description.py, as it depands passing of an object!
    """

    if not (isinstance(length, int) and length > 0):
      raise Exception("Length must be int > 0")
    if not isinstance(encoder, Encoder):
      raise Exception("Must provide an encoder")

    self._len = length
    self._enc = encoder
    self._w = encoder.getWidth()
    self._name = name


  def encodeIntoArray(self, input, output):
    if not isinstance(input, list) and len(input)==self._len:
      raise Exception("input must be list if size %d" % self._len)
    for e in range(self._len):
      tmp = self._enc.encode(input[e])
      print "out", output, "tt", tmp
      numpy.concatenate((output,tmp))
    return output
  

  def decode(self, encoded, parentFieldName=''):
    ret = []
    w = self._w
    for i in xrange(self._len):
      ret[i*w:(i+1)*w-1]=self._enc.decode(encoded[i*w:(i+1)*w-1]) 
 
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


