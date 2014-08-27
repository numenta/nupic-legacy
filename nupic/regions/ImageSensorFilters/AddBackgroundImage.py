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

import os
import random

from nupic.image import (createMask, isSimpleBBox)
from nupic.frameworks.vision2 import VisionUtils
from PIL import (Image,
                 ImageChops)
from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class AddBackgroundImage(BaseFilter):

  """
  Fill in the background (around the mask or around the bounding box).
  """

  def __init__(self, img=None, threshold=10, maskScale=1.0, blurRadius=0.0):
    """
    @param img -- path to background image(s) to use
    """

    BaseFilter.__init__(self)

    self.bgPath = img
    self.bgImgs = None
    self._rng = random.Random()
    self._rng.seed(42)
    self._threshold = threshold
    self._maskScale = maskScale
    self._blurRadius = blurRadius


  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)


    # If no background image, just return the input image as-is
    if self.bgPath is None:
      return image

    # ---------------------------------------------------------------------------
    # Open the background image(s) if we haven't done so already
    if self.bgImgs is None:

      # If given a relative path, make it relative to the vision data directory
      if not os.path.isabs(self.bgPath):
        basePath = os.path.abspath(os.curdir)
        basePath = os.path.split(basePath)
        while(basePath[0]):
          if basePath[1] == 'vision':
            break
          basePath = os.path.split(basePath[0])

        # Did we find the vision directory?
        if basePath[1] == 'vision':
          fullPath = VisionUtils.findData(os.path.join(basePath[0], 'vision'),
                        self.bgPath, 'backgound', 'background images', True)
          #basePath = os.path.join(basePath[0], 'vision', 'data')
        else:
          fullPath = self.bgPath
      else:
        fullPath = self.bgPath


      # If given a filename, we only have 1 image
      if os.path.isfile(fullPath):
        self.bgImgs = [Image.open(fullPath).convert('LA')]

      # Else, open up all images in this directory
      else:
        self.bgImgs = []
        w = os.walk(fullPath)
        while True:
          try:
            dirpath, dirnames, filenames = w.next()
          except StopIteration:
            break

          # Don't enter directories that begin with '.'
          for d in dirnames[:]:
            if d.startswith('.'):
              dirnames.remove(d)
          dirnames.sort()

          # Ignore files that begin with '.'
          filenames = [f for f in filenames if not f.startswith('.')]
          filenames.sort()
          imageFilenames = [os.path.join(dirpath, f) for f in filenames]

          # Process each image
          for filename in imageFilenames:
            self.bgImgs.append(Image.open(filename).convert('L'))

      # Keep a cache of all images, scaled to the input image size
      self.scaledBGImgs = [x.copy() for x in self.bgImgs]


    # Pick a background at random.
    idx = self._rng.randint(0, len(self.bgImgs)-1)
    bgImg = self.scaledBGImgs[idx]

    # ---------------------------------------------------------------------------
    # re-scale the background to the source image if necessary
    if bgImg.size != image.size:
      bgImg = self.scaledBGImgs[idx] = self.bgImgs[idx].resize(image.size, Image.ANTIALIAS)

    # ---------------------------------------------------------------------------
    # Create the mask around the source image
    mask = image.split()[-1]
    if image.mode[-1] != 'A' or isSimpleBBox(mask):
      mask = createMask(image, threshold=self._threshold, fillHoles=True,
                        backgroundColor=self.background, blurRadius=self._blurRadius,
                        maskScale=self._maskScale)

    # ---------------------------------------------------------------------------
    # Paste the image onto the background
    newImage = bgImg.copy()
    newImage.paste(image, (0,0), mask)

    # Put an "all-on" alpha channel because we now want the network to consider the entire
    #  image
    newImage.putalpha(ImageChops.constant(newImage, 255))

    return newImage
