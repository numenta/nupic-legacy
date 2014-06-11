# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import math

import numpy

from nupic.encoders.coordinate import CoordinateEncoder



EARTH_CIRCUMFERENCE = 40075000  # in meters



class GeospatialCoordinateEncoder(CoordinateEncoder):
  """
  Given a GPS coordinate and a speed reading, the
  Geospatial Coordinate Encoder returns an SDR representation
  of that position.
  """

  def __init__(self,
               scale,
               timestep,
               w=21,
               n=1000,
               name=None,
               verbosity=0):
    """
    See `nupic.encoders.base.Encoder` for more information.

    @param scale (int) Scale of the map, as measured by
                       distance between two coordinates
                       (in meters per dimensional unit)
    @param timestep (int) Time between readings (in seconds)
    """
    super(GeospatialCoordinateEncoder, self).__init__(w=w,
                                                      n=n,
                                                      name=name,
                                                      verbosity=verbosity)

    self.scale = scale
    self.timestep = timestep


  def getDescription(self):
    """See `nupic.encoders.base.Encoder` for more information."""
    return [('longitude', 0), ('latitude', 1), ('speed', 2)]


  def encodeIntoArray(self, inputData, output):
    """
    See `nupic.encoders.base.Encoder` for more information.

    @param inputData (tuple) Contains longitude (float),
                             latitude (float), speed (float)
    @param output (numpy.array) Stores encoded SDR in this numpy array
    """
    (longitude, latitude, speed) = inputData
    coordinate = self.coordinateForPosition(longitude, latitude)
    radius = self.radiusForSpeed(speed)
    super(GeospatialCoordinateEncoder, self).encodeIntoArray(
     (coordinate, radius), output)


  def coordinateForPosition(self, longitude, latitude):
    """
    Returns coordinate for given GPS position.

    Uses an [Equirectangular Projection]
    (http://en.wikipedia.org/wiki/Equirectangular_projection).

    @param longitude (float) Longitude of position
    @param latitude (float) Latitude of position
    @return (numpy.array) Coordinate that the given GPS position
                          maps to
    """
    position = numpy.array([longitude, latitude])
    normalizer = numpy.array([90., 180.])
    normalized = position / normalizer
    multiplier = numpy.array([EARTH_CIRCUMFERENCE / 2, EARTH_CIRCUMFERENCE])
    coordinate = normalized * multiplier / self.scale
    return coordinate.astype(int)


  def radiusForSpeed(self, speed):
    """
    Returns radius for given speed.

    Tries to get the encodings of consecutive readings to be
    right next to each other.

    @param speed (float) Speed (in meters per second)
    @return (int) Radius for given spede
    """
    coordinatesPerTimestep = speed * self.timestep / self.scale
    radius = int(round(float(coordinatesPerTimestep) / 2))
    minRadius = int(math.ceil((math.sqrt(self.w) - 1) / 2))
    return max(radius, minRadius)


  def dump(self):
    print "GeospatialCoordinateEncoder:"
    print "  w:   %d" % self.w
    print "  n:   %d" % self.n
