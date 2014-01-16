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

from PIL import (Image,
                 ImageChops)

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter
from nupic.image import (createMask, isSimpleBBox)


class FillBackground(BaseFilter):

  """
  Fill in the background (around the mask or around the bounding box).
  """

  def __init__(self, value=None, threshold=10, maskScale=1.0, blurRadius=0.0):
    """
    @param value -- If None, the background is filled in with the background
      color. Otherwise, it is filled with value. If value is a list, then
      this filter will return multiple images, one for each value
    """

    BaseFilter.__init__(self)

    if hasattr(value, '__len__'):
      self._values = value
    else:
      self._values = [value]
    self._threshold = threshold
    self._maskScale = maskScale
    self._blurRadius = blurRadius

  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (outputCount, simultaneousOutputCount).
    """
    return len(self._values)

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    # ---------------------------------------------------------------------------
    # Create the mask around the source image
    mask = image.split()[-1]
    if image.mode[-1] != 'A' or isSimpleBBox(mask):
      mask = createMask(image, threshold=self._threshold, fillHoles=True,
                        backgroundColor=self.background, blurRadius=self._blurRadius,
                        maskScale=self._maskScale)


    # ---------------------------------------------------------------------------
    # Process each value
    newImages = []
    for value in self._values:
      if value is None:
        value = self.background

      bg = ImageChops.constant(image, value)
      newImage = Image.composite(image.split()[0], bg, mask)
      newImage.putalpha(image.split()[-1])
      newImages.append(newImage)

    if len(newImages) == 1:
      return newImages[0]
    else:
      return newImages
