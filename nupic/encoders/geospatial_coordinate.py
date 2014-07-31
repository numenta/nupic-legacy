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
from pyproj import Proj
from nupic.encoders.coordinate import CoordinateEncoder



PROJ = Proj(init="epsg:3785")  # Spherical Mercator
# From http://spatialreference.org/ref/epsg/popular-visualisation-crs-mercator/
PROJ_RANGE=(20037508.3428, 19971868.8804)  # in meters



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

    @param longitude (float) Longitude of position
    @param latitude (float) Latitude of position
    @return (numpy.array) Coordinate that the given GPS position
                          maps to
    """
    coordinate = numpy.array(PROJ(longitude, latitude))
    coordinate = coordinate / self.scale
    return coordinate.astype(int)


  def radiusForSpeed(self, speed):
    """
    Returns radius for given speed.

    Tries to get the encodings of consecutive readings to be
    adjacent with some overlap.

    @param speed (float) Speed (in meters per second)
    @return (int) Radius for given speed
    """
    overlap = 1.5
    coordinatesPerTimestep = speed * self.timestep / self.scale
    radius = int(round(float(coordinatesPerTimestep) / 2 * overlap))
    minRadius = int(math.ceil((math.sqrt(self.w) - 1) / 2))
    return max(radius, minRadius)


  def dump(self):
    print "GeospatialCoordinateEncoder:"
    print "  w:   %d" % self.w
    print "  n:   %d" % self.n
