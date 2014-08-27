# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

"""
## @file
"""

import math

import numpy
from PIL import Image
from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter, uint

class Gradient(BaseFilter):
  """
  Adds brightness using one of three gradient types (horizontal, vertical, and circular) with random intensity controlled by difficulty.
  """
  def __init__(self, difficulty = 0.5, seed=None, reproducible=False):
    """
    @param difficulty -- Value between 0.0 and 1.0 that controls the intensity of the gradient applied.
    @param seed -- Seed value for random number generator, to produce
      reproducible results.
    @param reproducible -- Whether to seed the random number generator based
      on a hash of the image pixels upon each call to process().
    'seed' and 'reproducible' cannot be used together.
    """
    BaseFilter.__init__(self, seed, reproducible)
    self.difficulty = difficulty
    self.types = ('horizontal', 'vertical', 'circular')
    self.gradientImages = {}

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """
    BaseFilter.process(self, image)
    #Type of gradient?
    type = self.random.choice(self.types)

    gradientImage = self.gradientImages.get((image.size, type))

    if not gradientImage:
        #Gradient image, used as mask
        gradientImage = Image.new("L", image.size)
        gradientArray = numpy.array(gradientImage.split()[0].getdata())
        gradientArray.resize(image.size[1], image.size[0])

        #Calculate gradient
        opacity = self.difficulty - self.difficulty*.2 + self.random.random()*self.difficulty*.2
        for i in xrange(image.size[1]):
            for j in xrange(image.size[0]):
                if type == 'horizontal':
                    gradientArray[i][j] = int(float(j)/image.size[0]*255/opacity)
                elif type == 'vertical':
                    gradientArray[i][j] = int(float(i)/image.size[1]*255/opacity)
                elif type == 'circular':
                    gradientArray[i][j] = int(math.sqrt((i - image.size[1]/2)**2 + (j - image.size[0]/2)**2)/math.sqrt((image.size[1]/2)**2 + (image.size[0]/2)**2)*255/opacity)

        gradientImage.putdata([uint(p) for p in gradientArray.flatten()])
        #Add gradient image to dictionary
        self.gradientImages[(image.size, type)] = gradientImage

    #Image to composite with for brightness
    whiteImage = Image.new("LA", image.size)
    whiteArray = numpy.array(whiteImage.split()[0].getdata())
    whiteArray += 255
    whiteImage.putdata([uint(p) for p in whiteArray])
    newImage = Image.composite(image, whiteImage, gradientImage)
    return newImage
