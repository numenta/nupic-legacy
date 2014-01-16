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

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class ScaleToFit(BaseFilter):

  """
  ** DEPRECATED ** Scale the image to fit the specified size.
  """

  def __init__(self, width, height, scaleHeightTo=None, scaleWidthTo=None, pad=False):
    """
    ** DEPRECATED **
    @param width -- Target width, in pixels.
    @param height -- Target height, in pixels.
    @param pad -- Whether to pad the image with the background color in order
      to fit the specified size exactly.
    """

    BaseFilter.__init__(self)

    self.width = width
    self.height = height
    self.pad = pad
    self.scaleHeightTo = scaleHeightTo
    self.scaleWidthTo = scaleWidthTo

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    if image.size == (self.width, self.height):
      return image

    # Resize the image
    targetRatio = self.width / float(self.height)
    imageRatio = image.size[0] / float(image.size[1])
    if self.scaleHeightTo:
      ySize = self.scaleHeightTo
      scaleFactor = self.scaleHeightTo / float(image.size[1])
      xSize = int(scaleFactor * image.size[0])
    elif self.scaleWidthTo:
      xSize = self.scaleWidthTo
      scaleFactor = self.scaleWidthTo / float(image.size[0])
      ySize = int(scaleFactor * image.size[1])
    else:
      if imageRatio > targetRatio:
        xSize = self.width
        scaleFactor = self.width / float(image.size[0])
        ySize = int(scaleFactor * image.size[1])
      else:
        ySize = self.height
        scaleFactor = self.height / float(image.size[1])
        xSize = int(scaleFactor * image.size[0])

    if (xSize, ySize) < image.size:
      image = image.resize((xSize, ySize),Image.ANTIALIAS)
    else:
      image = image.resize((xSize, ySize),Image.BICUBIC)

    # Pad the image if necessary
    if self.pad and image.size != (self.width, self.height):
      paddedImage = Image.new('L', (self.width, self.height),
        self.background)
      alpha = Image.new('L', (self.width, self.height))
      paddedImage.putalpha(alpha)
      paddedImage.paste(image,
        ((self.width - image.size[0])/2, (self.height - image.size[1])/2))
      image = paddedImage

    return image
