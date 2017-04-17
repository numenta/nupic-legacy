# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2015, Numenta, Inc.  Unless you have an agreement
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

import math
import numbers

import numpy

from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.data.fieldmeta import FieldMetaType
from nupic.bindings.math import SM32, GetNTAReal
from nupic.encoders.base import Encoder, EncoderResult

from nupic.research.spatial_pooler import SpatialPooler


DEFAULT_RADIUS = 0
DEFAULT_RESOLUTION = 0



class SpatialPoolerEncoder(Encoder):
  """
  w=inputDimensions
  """

  def __init__(self,
               w,
               minval=0,
               maxval=0,
               periodic=False,
               n=0,
               radius=DEFAULT_RADIUS,
               resolution=DEFAULT_RESOLUTION,
               name=None,
               verbosity=0,
               clipInput=False,
               forced=False):
    """
    w -- number of bits to set in output
    """

    assert isinstance(w, numbers.Integral)
    self.encoders = None
    self.verbosity = verbosity
    self.w = w
    #if (w % 2 == 0):
    #  raise Exception("Width must be an odd number (%f)" % w)

    self.n=n
    self._initEncoder(w, n)

    self.type_skip=True

    # Our name
    if name is not None:
      self.name = name
    else:
      self.name = "[%s:%s]" % (self.minval, self.maxval)
    if self.verbosity >= 2:
      print "SP encoder initialized",self.name


  def _initEncoder(self, w,n):
    self._SpatialPooler=SpatialPooler( [w],[n] , 403,0.8,1,-1.0,40.0,0)


  def getDescription(self):
    return [(self.name, 0)]
  def getWidth(self):
    return self.n
  def getDecoderOutputFieldTypes(self):
    """ [Encoder class virtual method override]
    """
    #return (FieldMetaType.float, )
    return (FieldMetaType.string, )

  def getScalars(self, inpt):
    return None

  def encodeIntoArray(self, input, output, learn=True):
    """ See method description in base.py """

    __IsValid=False
    if input is not None:
      input=eval(input)

      if type(input)==list or type_skip:
        __IsValid=True
      if __IsValid==False:

        if input == None:
          return None

        if self.verbosity >= 2:
            print "Example:"
            print 'input="[0,0,0,1,0]"'
        raise TypeError(
            "Expected a string input but got input of type %s" % type(input))
    else:
      return None

    if type(input)==list:
      inputVector = numpy.array( input )

      output[:self.n] = 0
      self._SpatialPooler.compute(inputVector=inputVector, learn=1, activeArray=output[:self.n] )
    else:
      #input as numpy array
      output[:self.n] = 0
      self._SpatialPooler.compute(inputVector=input, learn=1, activeArray=output[:self.n] )


    if self.verbosity >= 2:
      print
      print "input:", input
      print "n:", self.n, "w:", self.w
      print "output:",
      self.pprint(output)
      print "input desc:", self.decodedToStr(self.decode(output))


  def dump(self):
    ToImplement()
    print "ScalarEncoder:"
    print "  min: %f" % self.minval
    print "  max: %f" % self.maxval
    print "  w:   %d" % self.w
    print "  n:   %d" % self.n
    print "  resolution: %f" % self.resolution
    print "  radius:     %f" % self.radius
    print "  periodic: %s" % self.periodic
    print "  nInternal: %d" % self.nInternal
    print "  rangeInternal: %f" % self.rangeInternal
    print "  padding: %d" % self.padding


  @classmethod
  def read(cls, proto):
    ToImplement()
    if proto.n is not None:
      radius = DEFAULT_RADIUS
      resolution = DEFAULT_RESOLUTION
    else:
      radius = proto.radius
      resolution = proto.resolution

    return cls(w=proto.w,
               minval=proto.minval,
               maxval=proto.maxval,
               periodic=proto.periodic,
               n=proto.n,
               name=proto.name,
               verbosity=proto.verbosity,
               clipInput=proto.clipInput,
               forced=True)

  def write(self, proto):
    ToImplement()
    proto.w = self.w
    proto.minval = self.minval
    proto.maxval = self.maxval
    proto.periodic = self.periodic
    # Radius and resolution can be recalculated based on n
    proto.n = self.n
    proto.name = self.name
    proto.verbosity = self.verbosity
    proto.clipInput = self.clipInput
