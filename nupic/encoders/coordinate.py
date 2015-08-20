# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import hashlib
import itertools

import numpy
from nupic.bindings.math import Random
from nupic.encoders.base import Encoder



class CoordinateEncoder(Encoder):
  """
  Given a coordinate in an N-dimensional space, and a radius around
  that coordinate, the Coordinate Encoder returns an SDR representation
  of that position.

  The Coordinate Encoder uses an N-dimensional integer coordinate space.
  For example, a valid coordinate in this space is (150, -49, 58), whereas
  an invalid coordinate would be (55.4, -5, 85.8475).

  It uses the following algorithm:

  1. Find all the coordinates around the input coordinate, within the
  specified radius.
  2. For each coordinate, use a uniform hash function to
  deterministically map it to a real number between 0 and 1. This is the
  "order" of the coordinate.
  3. Of these coordinates, pick the top W by order, where W is the
  number of active bits desired in the SDR.
  4. For each of these W coordinates, use a uniform hash function to
  deterministically map it to one of the bits in the SDR. Make this bit active.
  5. This results in a final SDR with exactly W bits active
  (barring chance hash collisions).
  """

  def __init__(self,
               w=21,
               n=1000,
               name=None,
               verbosity=0):
    """
    See `nupic.encoders.base.Encoder` for more information.

    @param name An optional string which will become part of the description
    """
    # Validate inputs
    if (w <= 0) or (w % 2 == 0):
      raise ValueError("w must be an odd positive integer")

    if (n <= 6 * w) or (not isinstance(n, int)):
      raise ValueError("n must be an int strictly greater than 6*w. For "
                       "good results we recommend n be strictly greater "
                       "than 11*w")

    self.w = w
    self.n = n
    self.verbosity = verbosity
    self.encoders = None

    if name is None:
      name = "[%s:%s]" % (self.n, self.w)
    self.name = name


  def getWidth(self):
    """See `nupic.encoders.base.Encoder` for more information."""
    return self.n


  def getDescription(self):
    """See `nupic.encoders.base.Encoder` for more information."""
    return [('coordinate', 0), ('radius', 1)]


  def getScalars(self, inputData):
    """See `nupic.encoders.base.Encoder` for more information."""
    return numpy.array([0]*len(inputData))


  def encodeIntoArray(self, inputData, output):
    """
    See `nupic.encoders.base.Encoder` for more information.

    @param inputData (tuple) Contains coordinate (numpy.array)
                             and radius (float)
    @param output (numpy.array) Stores encoded SDR in this numpy array
    """
    (coordinate, radius) = inputData
    neighbors = self._neighbors(coordinate, radius)
    winners = self._topWCoordinates(neighbors, self.w)

    bitFn = lambda coordinate: self._bitForCoordinate(coordinate, self.n)
    indices = numpy.array([bitFn(w) for w in winners])

    output[:] = 0
    output[indices] = 1


  @staticmethod
  def _neighbors(coordinate, radius):
    """
    Returns coordinates around given coordinate, within given radius.
    Includes given coordinate.

    @param coordinate (numpy.array) Coordinate whose neighbors to find
    @param radius (float) Radius around `coordinate`

    @return (numpy.array) List of coordinates
    """
    ranges = [range(n-radius, n+radius+1) for n in coordinate.tolist()]
    return numpy.array(list(itertools.product(*ranges)))


  @classmethod
  def _topWCoordinates(cls, coordinates, w):
    """
    Returns the top W coordinates by order.

    @param coordinates (numpy.array) A 2D numpy array, where each element
                                     is a coordinate
    @param w (int) Number of top coordinates to return
    @return (numpy.array) A subset of `coordinates`, containing only the
                          top ones by order
    """
    orders = numpy.array([cls._orderForCoordinate(c)
                          for c in coordinates.tolist()])
    indices = numpy.argsort(orders)[-w:]
    return coordinates[indices]


  @staticmethod
  def _hashCoordinate(coordinate):
    """Hash a coordinate to a 64 bit integer."""
    coordinateStr = ",".join(str(v) for v in coordinate)
    # Compute the hash and convert to 64 bit int.
    hash = int(int(hashlib.md5(coordinateStr).hexdigest(), 16) % (2 ** 64))
    return hash


  @classmethod
  def _orderForCoordinate(cls, coordinate):
    """
    Returns the order for a coordinate.

    @param coordinate (numpy.array) Coordinate
    @return (float) A value in the interval [0, 1), representing the
                    order of the coordinate
    """
    seed = cls._hashCoordinate(coordinate)
    rng = Random(seed)
    return rng.getReal64()


  @classmethod
  def _bitForCoordinate(cls, coordinate, n):
    """
    Maps the coordinate to a bit in the SDR.

    @param coordinate (numpy.array) Coordinate
    @param n (int) The number of available bits in the SDR
    @return (int) The index to a bit in the SDR
    """
    seed = cls._hashCoordinate(coordinate)
    rng = Random(seed)
    return rng.getUInt32(n)


  def dump(self):
    print "CoordinateEncoder:"
    print "  w:   %d" % self.w
    print "  n:   %d" % self.n


  @classmethod
  def read(cls, proto):
    encoder = object.__new__(cls)
    encoder.w = proto.w
    encoder.n = proto.n
    encoder.verbosity = proto.verbosity
    encoder.name = proto.name
    return encoder


  def write(self, proto):
    proto.w = self.w
    proto.n = self.n
    proto.verbosity = self.verbosity
    proto.name = self.name
