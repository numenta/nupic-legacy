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


class MultipleScales(BaseFilter):

  """
  ** DEPRECATED ** Create scaled versions of the original image.
  """

  def __init__(self, scales=[1], simultaneous=False):
    """
    ** DEPRECATED **
    @param scales -- List of factors used for scaling. scales = [.5, 1] returns
      two images, one half the size of the original in each dimension, and one
      which is the original image.
    @param simultaneous -- Whether the images should be sent out of the sensor
      simultaneously.
    """

    BaseFilter.__init__(self)

    self.scales = scales
    self.simultaneous = simultaneous

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    sizes = [(int(round(image.size[0]*s)), int(round(image.size[1]*s)))
      for s in self.scales]

    resizedImages = []
    for size in sizes:
      if size < image.size:
        resizedImages.append(image.resize(size,Image.ANTIALIAS))
      else:
        resizedImages.append(image.resize(size,Image.BICUBIC))

    if not self.simultaneous:
      return resizedImages
    else:
      return [resizedImages]

  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (outputCount, simultaneousOutputCount).
    """

    if not self.simultaneous:
      return len(self.scales)
    else:
      return (1, len(self.scales))
