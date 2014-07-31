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

import random

import numpy
from PIL import Image
from PIL import ImageDraw
from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter, uint

class Lines(BaseFilter):
  """
  Adds a random number of dark lines to the image.
  """
  def __init__(self, difficulty = 0.5, seed=None, reproducible=False):
    """
    @param difficulty -- Value between 0.0 and 1.0 that controls how many lines to add in image.
    @param seed -- Seed value for random number generator, to produce
      reproducible results.
    @param reproducible -- Whether to seed the random number generator based
      on a hash of the image pixels upon each call to process().
    'seed' and 'reproducible' cannot be used together.
    """
    BaseFilter.__init__(self, seed, reproducible)
    self.difficulty = difficulty
    #Maximum number of lines to add
    self.maxLines = 10

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """
    BaseFilter.process(self, image)
    s = min(image.size)
    sizeRange = [0, s]

    imageArray = numpy.array(image.split()[0].getdata())
    newImage = Image.new("LA", image.size)
    newImage.putdata([uint(p) for p in imageArray])
    newImage.putalpha(image.split()[1])
    for i in xrange(int(self.difficulty*self.maxLines)):
      # Generate random line
      start = (random.randint(sizeRange[0], sizeRange[1]),
        random.randint(sizeRange[0], sizeRange[1]))
      end = (random.randint(sizeRange[0], sizeRange[1]),
        random.randint(sizeRange[0], sizeRange[1]))

      # Generate random color
      color = random.randint(0,255)

      # Add the line to the image
      draw = ImageDraw.Draw(newImage)
      draw.line((start, end), fill=color)

    return newImage
