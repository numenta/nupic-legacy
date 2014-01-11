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

import math

from nupic.regions.ImageSensorExplorers.BaseExplorer import BaseExplorer


class ExhaustiveSweep(BaseExplorer):

  """
  This explorer performs an exhaustive raster scan through the input space.

  By default, it iterates through images, filters, and sweep positions, with
  sweep positions as the inner loop.
  """

  def __init__(self, sweepDirections=["right", "down"], shiftDuringSweep=1,
      shiftBetweenSweeps=1, sweepOffObject=False, order=None, *args, **kwargs):
    """
    sweepDirections -- Directions for sweeping (a list containing one or
      more of 'left', 'right', 'up', and 'down').
    shiftDuringSweep -- Number of pixels to jump with each step (during a
      sweep).
    shiftBetweenSweeps -- Number of pixels to jump in between sweeps
      (for example, when moving down a line after sweeping across).
    sweepOffObject -- Whether the sensor can only include a part of the
      object, as specified by the bounding box. If False, it will only move to
      positions that include as much of the object as possible. If True, it
      will sweep until all of the object moves off the sensor. If set to a floating
      point number between 0 and 1, then it will sweep until that fraction of the
      object moves off the sensor.
    order -- Order in which to iterate (outer to inner). Default progresses
      through switching images, filters, and sweeping, where switching images
      is the outer loop and sweeping is the inner loop. Should be a list
      containing 'image', 'sweep', and 0, 1, ... numFilters-1.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    for direction in sweepDirections:
      if direction not in ('left', 'right', 'up', 'down'):
        raise RuntimeError("Unknown sweep direction: '%s'" % direction)
    if type(shiftDuringSweep) is not int:
      raise RuntimeError("'shiftDuringSweep' must be an integer")
    if type(shiftBetweenSweeps) is not int:
      raise RuntimeError("'shiftBetweenSweeps' must be an integer")
    if float(sweepOffObject) < 0 or float(sweepOffObject) > 1.0:
      raise RuntimeError("'sweepOffObject' should be a boolean, or floating point"
                          " number between 0 and 1")
    if order is not None:
      if 'image' not in order or 'sweep' not in order:
        raise RuntimeError("'order' must contain both 'image' and 'sweep'")
      if len([x for x in order if type(x) == str]) > 2:
        raise RuntimeError("'order' must contain no other strings besides "
          "'image' and 'sweep'")
      self.customOrder = True
    else:
      self.customOrder = False

    self.sweepDirections = sweepDirections
    self.shiftDuringSweep = shiftDuringSweep
    self.shiftBetweenSweeps = shiftBetweenSweeps
    self.sweepOffObject = sweepOffObject
    self.order = order

  def first(self):
    """
    Set up the position.

    BaseExplorer picks image 0, offset (0,0), etc., but explorers that wish
    to set a different first position should extend this method. Such explorers
    may wish to call BaseExplorer.first(center=False), which initializes the
    position tuple but does not call centerImage() (which could cause
    unnecessary filtering to occur).
    """

    BaseExplorer.first(self)

    self.directionIndex = 0
    if self.numImages:
      self._firstSweepPosition()

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    BaseExplorer.next(self)

    # If filters were changed, order may be invalid
    if self.order is None or \
        len([x for x in self.order if type(x) == int]) != self.numFilters:
      # If user did not set a custom order, just create new one automatically
      if not self.customOrder:
        self.order = ["image"]
        self.order.extend(range(self.numFilters))
        self.order += ["sweep"]
      # Otherwise, user needs to recreate the explorer with a new order
      else:
        raise RuntimeError("'order' is invalid. Must recreate explorer with "
          "valid order after changing filters.")

    if self.position['reset'] and self.blankWithReset:
      # Last iteration was a blank, so don't increment the position
      self.position['reset'] = False
    else:
      self.position['reset'] = False
      for x in reversed(self.order):
        if x == 'image':  # Iterate the image
          self.position['image'] += 1
          if self.position['image'] == self.numImages:
            self.position['image'] = 0
            self.position['reset'] = True
          else:
            break
        elif x == 'sweep':  # Iterate the sweep position
          nextImage = self._nextSweepPosition()
          if not nextImage:
            break
        else:  # Iterate the filter with index x
          self.position['filters'][x] += 1
          if self.position['filters'][x] == self.numFilterOutputs[x]:
            self.position['filters'][x] = 0
            self.position['reset'] = True
          else:
            break
      if nextImage:
        self._firstSweepPosition()

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if image is None:
      filteredImages = []
      for i in xrange(self.numImages):
        filteredImages.extend(self.getAllFilteredVersionsOfImage(i))
    else:
      filteredImages = self.getAllFilteredVersionsOfImage(image)
    return sum([self._getNumIterationsForImage(x[0]) for x in filteredImages])

  def _firstSweepPosition(self):
    """
    Go to the first sweep position for the current image and sweep direction.
    """

    sbbox = self._getSweepBoundingBox(self.getFilteredImages()[0])
    direction = self.sweepDirections[self.directionIndex]
    if direction in ('right', 'down'):
      self.position['offset'][0] = sbbox[0]
      self.position['offset'][1] = sbbox[1]
    elif direction == 'left':
      self.position['offset'][0] = sbbox[2] - 1
      self.position['offset'][1] = sbbox[1]
    elif direction == 'up':
      self.position['offset'][0] = sbbox[0]
      self.position['offset'][1] = sbbox[3] - 1

  def _nextSweepPosition(self):
    """
    Increment the sweep position.

    Return True (nextImage) if we exhausted all sweeps.
    """

    sbbox = self._getSweepBoundingBox(self.getFilteredImages()[0])
    direction = self.sweepDirections[self.directionIndex]
    nextDirection = False

    if direction == 'right':
      self.position['offset'][0] += self.shiftDuringSweep
      if self.position['offset'][0] >= sbbox[2]:
        self.position['reset'] = True
        self.position['offset'][0] = sbbox[0]
        self.position['offset'][1] += self.shiftBetweenSweeps
        if self.position['offset'][1] >= sbbox[3]:
          nextDirection = True
    elif direction == 'left':
      self.position['offset'][0] -= self.shiftDuringSweep
      if self.position['offset'][0] < sbbox[0]:
        self.position['reset'] = True
        self.position['offset'][0] = sbbox[2] - 1
        self.position['offset'][1] += self.shiftBetweenSweeps
        if self.position['offset'][1] >= sbbox[3]:
          nextDirection = True
    elif direction == 'down':
      self.position['offset'][1] += self.shiftDuringSweep
      if self.position['offset'][1] >= sbbox[3]:
        self.position['reset'] = True
        self.position['offset'][1] = sbbox[1]
        self.position['offset'][0] += self.shiftBetweenSweeps
        if self.position['offset'][0] >= sbbox[2]:
          nextDirection = True
    elif direction == 'up':
      self.position['offset'][1] -= self.shiftDuringSweep
      if self.position['offset'][1] < sbbox[1]:
        self.position['reset'] = True
        self.position['offset'][1] = sbbox[3] - 1
        self.position['offset'][0] += self.shiftBetweenSweeps
        if self.position['offset'][0] >= sbbox[2]:
          nextDirection = True

    if nextDirection:
      self.directionIndex += 1
      if self.directionIndex == len(self.sweepDirections):
        self.directionIndex = 0
        return True  # Go to next image
      self._firstSweepPosition()

    return False

  def _getSweepBoundingBox(self, image):
    """
    Calculate a 'sweep bounding box' from the image's bounding box.

    If 'sbbox' is the bounding box returned from this method, valid sweep
    positions [x,y] are bounded by sbbox[0] <= x < sbbox[2] and
    sbbox[1] <= y < sbbox[3].
    """

    bbox = image.split()[1].getbbox()
    # If alpha channel is completely empty, we will end up
    # with a bbox of 'None'.  Nothing much we can do
    if bbox is None:
      bbox = (0, 0, 1, 1)
      #bbox = (0, 0, image.size[0], image.size[1])
      print 'WARNING: empty alpha channel'
    if float(self.sweepOffObject) == 1.0:
      startX = bbox[0] - self.enabledWidth + 1
      startY = bbox[1] - self.enabledHeight + 1
      endX = bbox[2]
      endY = bbox[3]
    else:
      # Shrink the bbox based on the amount of the object we want to sweep off
      width = bbox[2] - bbox[0]
      height = bbox[3] - bbox[1]
      bbox = [int(round(bbox[0] + width*self.sweepOffObject)),
              int(round(bbox[1] + height*self.sweepOffObject)),
              int(round(bbox[2] - width*self.sweepOffObject)),
              int(round(bbox[3] - height*self.sweepOffObject))]
      startX = min(bbox[0], bbox[2] - self.enabledWidth)
      startY = min(bbox[1], bbox[3] - self.enabledHeight)
      endX = max(bbox[0], bbox[2] - self.enabledWidth) + 1
      endY = max(bbox[1], bbox[3] - self.enabledHeight) + 1
    return (startX, startY, endX, endY)

  def _getNumIterationsForImage(self, image):
    """
    Return the number of iterations for the image, given the current parameters.
    """

    sbbox = self._getSweepBoundingBox(image)
    stepsX = sbbox[2] - sbbox[0]
    stepsY = sbbox[3] - sbbox[1]
    numIterations = 0
    for direction in self.sweepDirections:
      if direction in ('left', 'right'):
        across = int(math.ceil(stepsX / float(self.shiftDuringSweep)))
        down = int(math.ceil(stepsY / float(self.shiftBetweenSweeps)))
        if self.blankWithReset:
          across += 1
      elif direction in ('up', 'down'):
        across = int(math.ceil(stepsX / float(self.shiftBetweenSweeps)))
        down = int(math.ceil(stepsY / float(self.shiftDuringSweep)))
        if self.blankWithReset:
          down += 1
      numIterations += across*down
    return numIterations
