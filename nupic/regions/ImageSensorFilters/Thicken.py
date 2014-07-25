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

from PIL import ImageChops

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Thicken(BaseFilter):

  """
  Thicken lines by shifting the image around and returning the brightest
  image.
  """

  def __init__(self, shiftSize=1):
    """
    @param stepSize -- number of pixels to shift
    """

    BaseFilter.__init__(self)

    self.shiftSize = shiftSize

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image
    """

    BaseFilter.process(self, image)

    newImage = image

    # Shifting by more than one pixel can cause problems, so even if
    # stepSize > 1, get there by thickening by one shift at a time
    for x in xrange(-self.shiftSize,self.shiftSize+1):
      for y in xrange(-self.shiftSize,self.shiftSize+1):
        offsetImage = ImageChops.offset(image,x,y)
        newImage = ImageChops.lighter(newImage,offsetImage)
    return newImage
