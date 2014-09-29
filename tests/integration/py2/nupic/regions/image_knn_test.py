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



class ImageKNNTest(unittest.TestCase):
  """
  This test is a simple end to end test. It creates a simple network with an
  ImageSensor and a KNNClassifier region. It creates a 'dataset' with two random
  images, trains the network and then runs inference to ensures we can correctly
  classify them.  This tests that the plumbing is working well.
  """



  def testSimpleImageNetwork(self):

    # Create the network and get region instances
    net = Network()
    net.addRegion("sensor", "py.ImageSensor", "{width: 32, height: 32}")
    net.addRegion("classifier","py.KNNClassifierRegion",
                  "{distThreshold: 0.01, maxCategoryCount: 2}")
    net.link("sensor", "classifier", "UniformLink", "",
             srcOutput = "dataOut", destInput = "bottomUpIn")
    net.link("sensor", "classifier", "UniformLink", "",
             srcOutput = "categoryOut", destInput = "categoryIn")
    net.initialize()
    sensor = net.regions['sensor']
    classifier = net.regions['classifier']

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

    # Load the dataset
    sensor.executeCommand(["loadMultipleImages", tmpDir])
    numImages = sensor.getParameter('numImages')
    self.assertEqual(numImages, 2)

    # Ensure learning is turned ON
    self.assertEqual(classifier.getParameter('learningMode'), 1)

    # Train the network (by default learning is ON in the classifier)
    # and then turn off learning and turn on inference mode
    net.run(2)
    classifier.setParameter('inferenceMode', 1)
    classifier.setParameter('learningMode', 0)

    # Check to make sure learning is turned OFF and that the classifier learned
    # something
    self.assertEqual(classifier.getParameter('learningMode'), 0)
    self.assertEqual(classifier.getParameter('inferenceMode'), 1)
    self.assertEqual(classifier.getParameter('categoryCount'),2)
    self.assertEqual(classifier.getParameter('patternCount'),2)

    # Now test the network to make sure it categories the images correctly
    numCorrect = 0
    for i in range(2):
      net.run(1)
      inferredCategory = classifier.getOutputData('categoriesOut').argmax()
      if sensor.getOutputData('categoryOut') == inferredCategory:
        numCorrect += 1

    self.assertEqual(numCorrect,2)

    # Cleanup the temp files
    os.unlink(os.path.join(tmpDir,'0','im0.png'))
    os.unlink(os.path.join(tmpDir,'1','im1.png'))
    os.removedirs(os.path.join(tmpDir,'0'))
    os.removedirs(os.path.join(tmpDir,'1'))

if __name__ == "__main__":
  unittest.main()
