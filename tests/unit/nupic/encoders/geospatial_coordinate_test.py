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

import numpy as np
import tempfile
import unittest

from nupic.encoders.base import defaultDtype
from nupic.encoders.geospatial_coordinate import GeospatialCoordinateEncoder

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.encoders.geospatial_coordinate_capnp import (
    GeospatialCoordinateEncoderProto
  )

# Disable warnings about accessing protected members
# pylint: disable=W0212



class GeospatialCoordinateEncoderTest(unittest.TestCase):
  """Unit tests for GeospatialCoordinateEncoder class"""

  def testCoordinateForPosition(self):
    scale = 30  # meters
    encoder = GeospatialCoordinateEncoder(scale, 60)
    coordinate = encoder.coordinateForPosition(
      -122.229194, 37.486782
    )
    self.assertEqual(coordinate.tolist(), [-453549, 150239])


  def testCoordinateForPosition3D(self):
    scale = 30 # meters
    encoder = GeospatialCoordinateEncoder(scale, 60)
    coordinate = encoder.coordinateForPosition(
      -122.229194, 37.486782, 1500
    )
    self.assertEqual(coordinate.tolist(), [-90102, -142918, 128710])


  def testCoordinateForPositionOrigin3D(self):
    scale = 1 # meters
    encoder = GeospatialCoordinateEncoder(scale, 60)
    coordinate = encoder.coordinateForPosition(0,0,0)

    # see WGS80 defining parameters (semi-major axis) on
    # http://en.wikipedia.org/wiki/Geodetic_datum#Parameters_for_some_geodetic_systems
    self.assertEqual(coordinate.tolist(), [6378137, 0, 0])


  def testCoordinateForPositionOrigin(self):
    scale = 30  # meters
    encoder = GeospatialCoordinateEncoder(scale, 60)
    coordinate = encoder.coordinateForPosition(0, 0)
    self.assertEqual(coordinate.tolist(), [0, 0])


  def testRadiusForSpeed(self):
    scale = 30  # meters
    timestep = 60  #seconds
    speed = 50  # meters per second
    encoder = GeospatialCoordinateEncoder(scale, timestep)
    radius = encoder.radiusForSpeed(speed)
    self.assertEqual(radius, 75)


  def testRadiusForSpeed0(self):
    scale = 30  # meters
    timestep = 60  #seconds
    speed = 0  # meters per second
    n = 999
    w = 27
    encoder = GeospatialCoordinateEncoder(scale, timestep, n=n, w=w)
    radius = encoder.radiusForSpeed(speed)
    self.assertEqual(radius, 3)


  def testRadiusForSpeedInt(self):
    """Test that radius will round to the nearest integer"""
    scale = 30  # meters
    timestep = 62  #seconds
    speed = 25  # meters per second
    encoder = GeospatialCoordinateEncoder(scale, timestep)
    radius = encoder.radiusForSpeed(speed)
    self.assertEqual(radius, 38)


  def testEncodeIntoArray(self):
    scale = 30  # meters
    timestep = 60  #seconds
    speed = 2.5  # meters per second
    encoder = GeospatialCoordinateEncoder(scale, timestep,
                                          n=999,
                                          w=25)
    encoding1 = encode(encoder, speed, -122.229194, 37.486782)
    encoding2 = encode(encoder, speed, -122.229294, 37.486882)
    encoding3 = encode(encoder, speed, -122.229294, 37.486982)

    overlap1 = overlap(encoding1, encoding2)
    overlap2 = overlap(encoding1, encoding3)

    self.assertTrue(overlap1 > overlap2)


  def testEncodeIntoArrayAltitude(self):
    scale = 30 # meters
    timestep = 60 # seconds
    speed = 2.5 # meters per second
    longitude, latitude = -122.229294, 37.486782
    encoder = GeospatialCoordinateEncoder(scale, timestep,
                                          n=999,
                                          w=25)
    encoding1 = encode(encoder, speed, longitude, latitude, 0)
    encoding2 = encode(encoder, speed, longitude, latitude, 100)
    encoding3 = encode(encoder, speed, longitude, latitude, 1000)

    overlap1 = overlap(encoding1, encoding2)
    overlap2 = overlap(encoding1, encoding3)

    self.assertGreater(overlap1, overlap2)


  def testEncodeIntoArray3D(self):
    scale = 30 # meters
    timestep = 60 # seconds
    speed = 2.5 # meters per second
    encoder = GeospatialCoordinateEncoder(scale, timestep,
                                          n=999,
                                          w=25)
    encoding1 = encode(encoder, speed, -122.229194, 37.486782, 0)
    encoding2 = encode(encoder, speed, -122.229294, 37.486882, 100)
    encoding3 = encode(encoder, speed, -122.229294, 37.486982, 1000)

    overlap1 = overlap(encoding1, encoding2)
    overlap2 = overlap(encoding1, encoding3)

    self.assertGreater(overlap1, overlap2)


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testReadWrite(self):
    scale = 30 # meters
    timestep = 60 # seconds
    speed = 2.5 # meters per second
    original = GeospatialCoordinateEncoder(scale, timestep, n=999, w=25)
    encode(original, speed, -122.229194, 37.486782, 0)
    encode(original, speed, -122.229294, 37.486882, 100)

    proto1 = GeospatialCoordinateEncoderProto.new_message()
    original.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = GeospatialCoordinateEncoderProto.read(f)

    encoder = GeospatialCoordinateEncoder.read(proto2)

    self.assertIsInstance(encoder, GeospatialCoordinateEncoder)
    self.assertEqual(encoder.w, original.w)
    self.assertEqual(encoder.n, original.n)
    self.assertEqual(encoder.name, original.name)
    self.assertEqual(encoder.verbosity, original.verbosity)

    # Compare a new value with the original and deserialized.
    encoding3 = encode(original, speed, -122.229294, 37.486982, 1000)
    encoding4 = encode(encoder, speed, -122.229294, 37.486982, 1000)
    self.assertTrue(np.array_equal(encoding3, encoding4))


def encode(encoder, speed, longitude, latitude, altitude=None):
  output = np.zeros(encoder.getWidth(), dtype=defaultDtype)
  encoder.encodeIntoArray((speed, longitude, latitude, altitude), output)
  return output


def overlap(sdr1, sdr2):
  assert sdr1.size == sdr2.size
  return float((sdr1 & sdr2).sum()) / sdr1.sum()



if __name__ == "__main__":
  unittest.main()
