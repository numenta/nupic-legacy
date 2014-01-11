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

from nupic.regions.ImageSensorExplorers.BaseExplorer import BaseExplorer


class RandomJump(BaseExplorer):

  """
  This explorer randomly selects positions. It does not do any sweeping.
  """

  ############################################################################
  def __init__(self, jumpOffObject=False, numJumpsPerImage=None,
               numVisitsPerImage=None, spaceShape=None, *args, **kwargs):
    """
    Parameters:
    -----------------------------------------------------------------
    jumpOffObject:      Whether the sensor can only include a part of the object,
                        as specified by the bounding box. If False, it will only
                        move to positions that include as much of the object as
                        possible.
    numJumpsPerImage:   The number of iterations for which RandomJump
                        should dwell on one image before moving on to the next one.
    numVisitsPerImage:  The number of times RandomJump should visit each
                        image (and do numJumpsPerImage jumps on it).
    spaceShape:         The (height, width) of the 2-D space to explore. This
                        constrains how far away from the center point an image
                        is allowed to be presented.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    if type(jumpOffObject) not in (bool, int):
      raise RuntimeError("'jumpOffObject' should be a boolean")
    if numJumpsPerImage is not None and type(numJumpsPerImage) is not int:
      raise RuntimeError("'numJumpsPerImage' should be an integer")
    if numVisitsPerImage is not None and type(numVisitsPerImage) is not int:
      raise RuntimeError("'numVisitsPerImage' should be an integer")
    if numVisitsPerImage is not None and numJumpsPerImage is None:
      raise RuntimeError("Must specify 'numJumpsPerImage'"
        " when using 'numVisitsPerImage'")
    if spaceShape is not None and \
       (len(spaceShape) != 2 or spaceShape[0] < 1 or spaceShape[1] < 1):
      raise RuntimeError("'spaceShape' should be a 2-item tuple specifying the"
            "(height, width) of the overall space to explore.")


    self.jumpOffObject = jumpOffObject
    self.numJumpsPerImage = numJumpsPerImage
    self.numVisitsPerImage = numVisitsPerImage
    self.spaceShape = spaceShape

    # Keeps track of how many jumps on this image
    self.numJumpsThisImage = 0
    self.lastImageIndex = None

  ############################################################################
  def first(self):
    """
    Set up the position.

    BaseExplorer picks image 0, offset (0,0), etc., but explorers that wish
    to set a different first position should extend this method. Such explorers
    may wish to call BaseExplorer.first(center=False), which initializes the
    position tuple but does not call centerImage() (which could cause
    unnecessary filtering to occur).
    """

    BaseExplorer.first(self, center=False)

    if not self.numImages:
      return

    isBlank = True
    while isBlank:

      # Pick a random position
      if not self.numJumpsPerImage or self.lastImageIndex is None or \
          (self.numJumpsThisImage % self.numJumpsPerImage == 0):
        # Pick new image
        image = self.pickRandomImage(self.random)
        self.lastImageIndex = image
        self.numJumpsThisImage = 0
      else:
        image = self.lastImageIndex
      self.position['image'] = image
      self.position['filters'] = self.pickRandomFilters(self.random)
      filteredImages = self.getFilteredImages()

      # Pick a random offset
      if self.spaceShape is not None:
        self.centerImage()
        # NOTE: self.position['offset'] is (x, y), whereas our spaceShape is
        #  (height, width). Also note that the self.position['offset']
        #  direction is counter-intuitive: negative numbers move us to the RIGHT
        #  and DOWN instead of LEFT and UP.
        xOffset = self.random.randint(-(self.spaceShape[1]//2), self.spaceShape[1]//2)
        yOffset = self.random.randint(-(self.spaceShape[0]//2), self.spaceShape[0]//2)
        #print "(yOffset, xOffset) = ", yOffset, xOffset
        self.position['offset'][0] += xOffset
        self.position['offset'][1] += yOffset

      else:
        ebbox = self._getEffectiveBoundingBox(filteredImages[0])
        self.position['offset'] = [
          self.random.randint(ebbox[0], ebbox[2]-1),
          self.random.randint(ebbox[1], ebbox[3]-1)
        ]

      # Check if the position is blank
      isBlank = self.isBlank(self.jumpOffObject)

    self.position['reset'] = True
    self.numJumpsThisImage += 1

  ############################################################################
  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    self.first()

  ############################################################################
  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if self.numVisitsPerImage is None:
      return -1

    totalPerImage = self.numFilteredVersionsPerImage * self.numJumpsPerImage \
      * self.numVisitsPerImage

    if image is None:
      return totalPerImage * self.numImages
    else:
      return totalPerImage

  ############################################################################
  def _getEffectiveBoundingBox(self, image):
    """
    Calculate the 'effective' bounding box from the image's bounding box,
    taking into account the jumpOffObject parameter.

    The effective bounding box determines which offsets the explorer should
    consider. If 'ebbox' is the bounding box returned from this method, valid
    offsets [x,y] are bounded by:
      ebbox[0] <= x < ebbox[2]
      ebbox[1] <= y < ebbox[3].
    """

    bbox = image.split()[1].getbbox()
    if self.jumpOffObject:
      startX = bbox[0] - self.enabledWidth + 1
      startY = bbox[1] - self.enabledHeight + 1
      endX = bbox[2]
      endY = bbox[3]
    else:
      startX = min(bbox[0], bbox[2] - self.enabledWidth)
      startY = min(bbox[1], bbox[3] - self.enabledHeight)
      endX = max(bbox[0], bbox[2] - self.enabledWidth) + 1
      endY = max(bbox[1], bbox[3] - self.enabledHeight) + 1
    return (startX, startY, endX, endY)
