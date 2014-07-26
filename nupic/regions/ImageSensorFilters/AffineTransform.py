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

from PIL import Image
from PIL import ImageChops

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter

class AffineTransform(BaseFilter):
  """
  Applies a random combination of stretch and shear to the image, controlled by difficulty.
  """
  def __init__(self, difficulty = 0.5, seed=None, reproducible=False):
    """
    @param difficulty -- Controls the amount of stretch and shear applied to the image.
    @param seed -- Seed value for random number generator, to produce
      reproducible results.
    @param reproducible -- Whether to seed the random number generator based
      on a hash of the image pixels upon each call to process().
    'seed' and 'reproducible' cannot be used together.
    """
    BaseFilter.__init__(self, seed, reproducible)
    self.difficulty = difficulty
    self.maxShear = 1.0
    self.maxSqueeze = 0.1
    self.minSqueeze = 1.0
    self.types = ('shear_x', 'shear_y', 'squeeze_x', 'squeeze_y')
  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """
    BaseFilter.process(self, image)
    type = self.random.choice(self.types)
    #Default matrix
    matrix = (1, 0, 0, 0, 1, 0)
    size = list(image.size)
    newImage = Image.new('LA', size)
    if type == 'shear_x':
        shear = self.difficulty*self.maxShear - self.difficulty*0.3 + self.difficulty*0.3*self.random.random()
        matrix = (1, shear, -shear*size[1], 0, 1, 0)
        size[0] += int(shear*size[0])
        newImage = image.transform(tuple(size), Image.AFFINE, matrix)
        bbox = list(newImage.split()[1].getbbox())
        bbox[1] = 0
        bbox[3] = size[1]
        newImage = newImage.crop(bbox)
    elif type == 'shear_y':
        shear = self.difficulty*self.maxShear - self.difficulty*0.3 + self.difficulty*0.3*self.random.random()
        matrix = (1, 0, 0, shear, 1, -shear*size[0])
        size[1] += int(shear*size[1])
        newImage = image.transform(tuple(size), Image.AFFINE, matrix)
        bbox = list(newImage.split()[1].getbbox())
        bbox[0] = 0
        bbox[2] = size[0]
        newImage = newImage.crop(bbox)
    elif type == 'squeeze_x':
        squeeze = self.minSqueeze - (self.minSqueeze - self.maxSqueeze)*(self.difficulty - self.difficulty*0.3 + self.difficulty*0.3*self.random.random())
        matrix = (1/squeeze, 0, 0, 0, 1, 0)
        newImage = ImageChops.offset(image.transform(tuple(size), Image.AFFINE, matrix), int((size[0] - squeeze*size[0])/2), 0)
    elif type == 'squeeze_y':
        squeeze = self.minSqueeze - (self.minSqueeze - self.maxSqueeze)*(self.difficulty - self.difficulty*0.3 + self.difficulty*0.3*self.random.random())
        matrix = (1, 0, 0, 0, 1/squeeze, 0)
        newImage = ImageChops.offset(image.transform(tuple(size), Image.AFFINE, matrix), 0, int((size[1] - squeeze*size[1])/2))
    #Appropriate sizing
    if newImage.size[0] > image.size[0] or newImage.size[1] > image.size[1]:
        newImage = newImage.resize(image.size)
    elif newImage.size[1] < image.size[1]:
        retImage = Image.new('LA', image.size)
        retImage.paste(newImage, (0, int((image.size[1] - newImage.size[1])/2.0)))
        newImage = retImage
    elif newImage.size[0] < image.size[0]:
        retImage = Image.new('LA', image.size)
        retImage.paste(newImage, (0, int((image.size[0] - newImage.size[0])/2.0)))
    return newImage
