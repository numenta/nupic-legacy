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

from PIL import (ImageEnhance,
                 ImageMath,)

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Contrast(BaseFilter):

  """
  Modify the contrast of the image.
  """

  def __init__(self, factor=1.0, scaleTowardCenter=False):
    """
    Parameters
    ----------
    factor: float
      How much contrast to produce in the output image relative
      to the input image. A factor of 0 returns a solid gray image,
      a factor of 1.0 returns the original image, and higher values
      return higher-contrast images.

    scaleTowardCenter: bool
      If False (the default), uses PIL.ImageEnhance.Contrast.
      If True, scales the pixel values toward 0.5.
    """

    BaseFilter.__init__(self)

    if factor < 0:
      raise ValueError("'factor' must be nonnegative")

    self.factor = factor
    self.scaleTowardCenter = scaleTowardCenter
    if scaleTowardCenter and not (0.0 <= factor <= 1.0):
      raise ValueError("scaleTowardCenter only supports contrast factors "
          "between 0 and 1, inclusive.")

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """
    BaseFilter.process(self, image)

    base, alpha = image.split()

    if self.scaleTowardCenter:
      scale = float(self.factor)
      assert base.mode == "L"
      maxValue = 255 # TODO: Determine how to get maximum value __allowed__.
      offset = ((1.0 - self.factor) / 2.0) * maxValue
      newImage = ImageMath.eval(
          "convert(convert(gray, 'F') * scale + offset, mode)",
          gray=base,
          scale=scale,
          offset=offset,
          mode=base.mode,
        )
    else:
      contrastEnhancer = ImageEnhance.Contrast(image.split()[0])
      newImage = contrastEnhancer.enhance(self.factor)

    newImage.putalpha(alpha)

    return newImage
