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
      output[e*self._w:(e+1)*self._w]=tmp
    return output
  

  def decode(self, encoded, parentFieldName=''):
    ret = []
    w = self._w
    for i in xrange(self._len):
      tmp = self._enc.decode(encoded[i*w:(i+1)*w])[0].values()[0] # dict.values().first_element
      ret.append(tmp)
    return ret
 
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
    super(VectorEncoderOPF, self).__init__(length, sc)


