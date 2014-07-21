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

import numpy
from PIL import Image

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter, uint

class HistogramShift(BaseFilter):
  """
  Shifts the image histogram randomly in any direction, given a difficulty level.
  """
  def __init__(self, difficulty = 0.5, seed=None, reproducible=False):
    """
    @param difficulty -- Value between 0.0 and 1.0 that dictates how far
      to shift the image histogram. The direction will be random, and a random offset will be added.
    @param seed -- Seed value for random number generator, to produce
      reproducible results.
    @param reproducible -- Whether to seed the random number generator based
      on a hash of the image pixels upon each call to process().
    'seed' and 'reproducible' cannot be used together.
    """
    BaseFilter.__init__(self, seed, reproducible)

    if difficulty < 0.0 or difficulty > 1.0:
        raise RuntimeError("difficulty must be between 0.0 and 1.0")
    self.difficulty = difficulty
    #Maximum histogram shift - half the grayscale band (0-255)
    self.maxOffset = 128

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """
    BaseFilter.process(self, image)
    #Create numpy array from image grayscale data and resize to image dimensions
    imageArray = numpy.array(image.split()[0].getdata())
    imageArray.resize(image.size[1], image.size[0])
    #Calculate offset from difficulty level
    offset = self.difficulty*(self.maxOffset)
    #Add random change to offset within window size
    halfWindowSize = 0.1*offset
    offset = (offset - halfWindowSize) + halfWindowSize*self.random.random()*((-1)**self.random.randint(1, 2))
    #Apply random direction
    offset *= ((-1)**self.random.randint(1, 2))
    imageArray += offset
    #Recreate PIL image
    newImage = Image.new("L", image.size)
    newImage.putdata([uint(p) for p in imageArray.flatten()])
    newImage.putalpha(image.split()[1])
    return newImage
