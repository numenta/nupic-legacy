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
import tempfile
import os

from PIL import Image, ImageDraw

from nupic.engine import Network
from nupic.regions.ImageSensor import ImageSensor



class ImageSensorTest(unittest.TestCase):


  def testGetSelf(self):
    # Create network
    net = Network()

    # Add sensor
    sensor = net.addRegion("sensor", "py.ImageSensor",
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


  def testParameters(self):
    # Test setting and getting parameters
    net = Network()

    # Add sensor to the network
    sensor = net.addRegion("sensor", "py.ImageSensor",
        "{width: 100, height: 50}")

    # Verify get parameters
    self.assertEqual(sensor.getParameter('height'), 50)
    self.assertEqual(sensor.getParameter('width'), 100)

    # Verify set parameters
    sensor.setParameter('width', 42)
    self.assertEqual(sensor.getParameter('width'), 42)


  def testLoadImages(self):
    # Create a simple network with an ImageSensor. You can't actually run
    # the network because the region isn't connected to anything
    net = Network()
    net.addRegion("sensor", "py.ImageSensor", "{width: 32, height: 32}")
    sensor = net.regions['sensor']

    # Create a dataset with two categories, one image in each category
    # Each image consists of a unique rectangle
    tmpDir = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmpDir,'0'))
    os.makedirs(os.path.join(tmpDir,'1'))

    im0 = Image.new("L",(32,32))
    draw = ImageDraw.Draw(im0)
    draw.rectangle((10,10,20,20), outline=255)
    im0.save(os.path.join(tmpDir,'0','im0.png'))

    im1 = Image.new("L",(32,32))
    draw = ImageDraw.Draw(im1)
    draw.rectangle((15,15,25,25), outline=255)
    im1.save(os.path.join(tmpDir,'1','im1.png'))

    # Load the dataset and check we loaded the correct number
    sensor.executeCommand(["loadMultipleImages", tmpDir])
    numImages = sensor.getParameter('numImages')
    self.assertEqual(numImages, 2)

    # Load a single image (this will replace the previous images)
    sensor.executeCommand(["loadSingleImage",
                           os.path.join(tmpDir,'1','im1.png')])
    numImages = sensor.getParameter('numImages')
    self.assertEqual(numImages, 1)

    # Cleanup the temp files
    os.unlink(os.path.join(tmpDir,'0','im0.png'))
    os.unlink(os.path.join(tmpDir,'1','im1.png'))
    os.removedirs(os.path.join(tmpDir,'0'))
    os.removedirs(os.path.join(tmpDir,'1'))

if __name__ == "__main__":
  unittest.main()
