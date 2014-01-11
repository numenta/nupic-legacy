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

from PIL import Image

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Rotation2D(BaseFilter):

  """
  Created rotated versions of the image.
  """

  def __init__(self, angles=[0], expand=False, targetRatio=None,
               highQuality=True):
    """
    angles -- List of angles by which to rotate, in degrees.
    expand -- Whether to expand the output image to contain the entire
      rotated image. If False, the output image will match the dimensions of
      the input image, but cropping may occur.
    targetRatio -- Ratio of the sensor. If specified, used if expand == False
      to grow the image to the target ratio to avoid unnecessary clipping.
    highQuality -- Whether to use bicubic interpolation for rotating.
      instead of nearest neighbor.
    """

    BaseFilter.__init__(self)

    self.angles = angles
    self.expand = expand
    self.targetRatio = targetRatio
    self.highQuality = highQuality
    if not expand:
      for i, angle in enumerate(angles):
        if angle != 0 and angle % 90 == 0:
          angles[i] -= .01  # Oh, PIL...

  def process(self, image):
    """
    image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    if not self.expand and self.targetRatio:
      # Pad the image to the aspect ratio of the sensor
      # This allows us to rotate in expand=False without cutting off parts
      # of the image unnecessarily
      # Unlike expand=True, the object doesn't get smaller
      ratio = (image.size[0] / float(image.size[1]))
      if ratio < self.targetRatio:
        # Make image wider
        size = (int(image.size[0] * self.targetRatio / ratio), image.size[1])
        newImage = Image.new('LA', size, (self.background, 0))
        newImage.paste(image, ((newImage.size[0] - image.size[0])/2, 0))
        image = newImage
      elif ratio > self.targetRatio:
        # Make image taller
        size = (image.size[0], int(image.size[1] * ratio / self.targetRatio))
        newImage = Image.new('LA', size, (self.background, 0))
        newImage.paste(image, (0, (newImage.size[1] - image.size[1])/2))
        image = newImage

    if self.highQuality:
      resample = Image.BICUBIC
    else:
      resample = Image.NEAREST
    outputs = []
    for angle in self.angles:
      # Rotate the image, which expands it and pads it with black and a 0
      # alpha value
      rotatedImage = image.rotate(angle,
                                  resample=resample,
                                  expand=self.expand)

      # Create a new larger image to hold the rotated image
      # It is filled with the background color and an alpha value of 0
      outputImage = Image.new('LA', rotatedImage.size, (self.background, 0))
      # Paste the rotated image into the new image, using the rotated image's
      # alpha channel as a mask
      # This effectively just fills the area around the rotation with the
      # background color, and imports the alpha channel from the rotated image
      outputImage.paste(rotatedImage, None, rotatedImage.split()[1])
      outputs.append(outputImage)
    return outputs

  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (outputCount, simultaneousOutputCount).
    """

    return len(self.angles)
