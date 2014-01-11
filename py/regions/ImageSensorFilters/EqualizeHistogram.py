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
                 ImageOps)
import numpy

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter, uint


class EqualizeHistogram(BaseFilter):

  """
  Equalize the image's histogram.
  """

  def __init__(self, region='all', mode=None):
    """
    @param region -- Options are 'all' (equalize the entire image), 'bbox'
      (equalize just the portion of the image within the bounding box), and
      'mask' (equalize just the portion of the image within the mask).
    @param mode -- ** DEPRECATED ** Alias for 'region'.
    """

    BaseFilter.__init__(self)

    if mode is not None:
      region = mode

    if region not in ('all', 'bbox', 'mask'):
      raise RuntimeError(
        "Not a supported region (options are 'all', 'bbox', and 'mask')")

    self.region = region

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    if self.mode != 'gray':
      raise RuntimeError("EqualizeHistogram only supports grayscale images.")

    if self.region == 'bbox':
      bbox = image.split()[1].getbbox()
      croppedImage = image.crop(bbox)
      croppedImage.load()
      alpha = croppedImage.split()[1]
      croppedImage = ImageOps.equalize(croppedImage.split()[0])
      croppedImage.putalpha(alpha)
      image.paste(croppedImage, bbox)
    elif self.region == 'mask':
      bbox = image.split()[1].getbbox()
      croppedImage = image.crop(bbox)
      croppedImage.load()
      alpha = croppedImage.split()[1]
      # Fill in the part of the cropped image outside the bounding box with
      # uniformly-distributed noise
      noiseArray = \
        numpy.random.randint(0, 255, croppedImage.size[0]*croppedImage.size[1])
      noiseImage = Image.new('L', croppedImage.size)
      noiseImage.putdata([uint(p) for p in noiseArray])
      compositeImage = Image.composite(croppedImage, noiseImage, alpha)
      # Equalize the composite image
      compositeImage = ImageOps.equalize(compositeImage.split()[0])
      # Paste the part of the equalized image within the mask back
      # into the cropped image
      croppedImage = Image.composite(compositeImage, croppedImage, alpha)
      croppedImage.putalpha(alpha)
      # Paste the cropped image back into the full image
      image.paste(croppedImage, bbox)
    elif self.region == 'all':
      alpha = image.split()[1]
      image = ImageOps.equalize(image.split()[0])
      image.putalpha(alpha)
    return image
