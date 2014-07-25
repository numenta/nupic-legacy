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

from PIL import ImageEnhance

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Brightness(BaseFilter):

  """
  Modify the brightness of the image.
  """

  def __init__(self, factor=1.0):
    """
    @param factor -- Factor by which to brighten the image, a nonnegative
      number. 0.0 returns a black image, 1.0 returns the original image, and
      higher values return brighter images.
    """

    BaseFilter.__init__(self)

    if factor < 0:
      raise ValueError("'factor' must be a nonnegative number")

    self.factor = factor

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    brightnessEnhancer = ImageEnhance.Brightness(image.split()[0])
    newImage = brightnessEnhancer.enhance(self.factor)
    newImage.putalpha(image.split()[1])
    return newImage
