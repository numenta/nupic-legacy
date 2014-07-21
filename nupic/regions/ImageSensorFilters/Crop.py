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

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Crop(BaseFilter):

  """
  Crop the image.
  """

  def __init__(self, box):
    """
    @param box -- 4-tuple specifying the left, top, right, and bottom coords.
    """

    BaseFilter.__init__(self)

    if box[2] <= box[0] or box[3] <= box[1]:
      raise RuntimeError('Specified box has zero width or height')

    self.box = box

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    if self.box[2] > image.size[0] or self.box[3] > image.size[1]:
      raise RuntimeError('Crop coordinates exceed image bounds')

    return image.crop(self.box)
