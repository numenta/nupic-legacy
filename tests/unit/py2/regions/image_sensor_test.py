#!/usr/bin/env python
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

import unittest2 as unittest

from nupic.engine import Network
from nupic.regions.ImageSensor import ImageSensor



class ImageSensorTest(unittest.TestCase):


  def testGetSelf(self):
    # Create network
    net = Network()

    # Add sensor
    sensor = net.addRegion("sensor", "py.ImageSensor", \
      "{width: 100, height: 50}")
    pysensor = sensor.getSelf()

    # Verify set parameters
    self.assertEqual(type(pysensor), ImageSensor)
    self.assertEqual(pysensor.height, 50)
    self.assertEqual(pysensor.width, 100)

    self.assertEqual(pysensor.width, sensor.getParameter('width'))
    self.assertEqual(pysensor.height, sensor.getParameter('height'))

    sensor.setParameter('width', 444)
    sensor.setParameter('height', 444)
    self.assertEqual(pysensor.width, 444)
    self.assertEqual(pysensor.height, 444)

    # Verify py object is not a copy
    sensor.getSelf().height = 100
    sensor.getSelf().width = 200
    self.assertEqual(pysensor.height, 100)
    self.assertEqual(pysensor.width, 200)

    pysensor.height = 50
    pysensor.width = 100
    self.assertEqual(sensor.getSelf().height, 50)
    self.assertEqual(sensor.getSelf().width, 100)



if __name__ == '__main__':
  unittest.main()
