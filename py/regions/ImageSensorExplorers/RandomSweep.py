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


class RandomSweep(BaseExplorer):

  """
  This explorer performs randomly-selected horizontal or vertical sweeps, and
  it switches to a randomly-selected image in between each sweep.
  """

  def __init__(self, sweepDirections=['left', 'right', 'up', 'down'],
               shiftDuringSweep=1, sweepOffObject=False, *args, **kwargs):
    """
    sweepDirections -- Directions for sweeping. Must be a list containing
      one or more of 'left', 'right', 'up', and 'down' for horizontal and
      vertical sweeps, or 'leftup', 'leftdown', 'rightup', and 'rightdown'
      for diagonal sweeps (or 'upleft, 'downleft', 'upright', and
      'downright'). Can also be the string 'all', for all eight directions.
    shiftDuringSweep -- Number of pixels to jump with each step (during
      a sweep).
    sweepOffObject -- Whether the sensor can only include a part of the
      object, as specified by the bounding box. If False, it will only move
      to positions that include as much of the object as possible.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    if sweepDirections == 'all':
      sweepDirections = ['left', 'right', 'up', 'down',
        'leftdown', 'leftup', 'rightdown', 'rightup']
    else:
      for direction in sweepDirections:
        if direction not in ('left', 'right', 'up', 'down',
            'leftup', 'upleft', 'leftdown', 'downleft',
            'rightup', 'upright', 'rightdown', 'downright'):
          raise RuntimeError('Unknown sweep direction: %s' % direction)
    if type(shiftDuringSweep) is not int:
      raise RuntimeError("'shiftDuringSweep' should be an integer")
    if type(sweepOffObject) not in (bool, int):
      raise RuntimeError("'sweepOffObject' should be a boolean")

    self.sweepDirections = sweepDirections
    self.shiftDuringSweep = shiftDuringSweep
    self.sweepOffObject = sweepOffObject

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

    # Pick a random direction and filtered image
    self.direction = self.random.choice(self.sweepDirections)
    self.position['image'] = self.random.randint(0, self.numImages - 1)
    for i in xrange(self.numFilters):
      self.position['filters'][i] = self.random.randint(0,
        self.numFilterOutputs[i] - 1)
    filteredImages = self.getFilteredImages()

    # Pick a random starting position on the appropriate edge of the image
    sbbox = self._getSweepBoundingBox(filteredImages[0])

    if self.direction == 'left':
      self.position['offset'][0] = sbbox[2] - 1
      self.position['offset'][1] = self.random.randint(sbbox[1], sbbox[3] - 1)
    elif self.direction == 'right':
      self.position['offset'][0] = sbbox[0]
      self.position['offset'][1] = self.random.randint(sbbox[1], sbbox[3] - 1)
    elif self.direction == 'up':
      self.position['offset'][0] = self.random.randint(sbbox[0], sbbox[2] - 1)
      self.position['offset'][1] = sbbox[3] - 1
    elif self.direction == 'down':
      self.position['offset'][0] = self.random.randint(sbbox[0], sbbox[2] - 1)
      self.position['offset'][1] = sbbox[1]
    elif self.direction in ('leftup', 'upleft'):
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(sbbox[0] + (sbbox[2] - sbbox[0])/2, sbbox[2] - 1)
        self.position['offset'][1] = sbbox[3] - 1
      else:
        self.position['offset'][0] = sbbox[2] - 1
        self.position['offset'][1] = \
          self.random.randint(sbbox[1] + (sbbox[3] - sbbox[1])/2, sbbox[3] - 1)
    elif self.direction in ('leftdown', 'downleft'):
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(sbbox[0] + (sbbox[2] - sbbox[0])/2, sbbox[2] - 1)
        self.position['offset'][1] = sbbox[1]
      else:
        self.position['offset'][0] = sbbox[2] - 1
        self.position['offset'][1] = \
          self.random.randint(sbbox[1], sbbox[3] - 1 - (sbbox[3] - sbbox[1])/2)
    elif self.direction in ('rightup', 'upright'):
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(sbbox[0], sbbox[2] - 1 - (sbbox[2] - sbbox[0])/2)
        self.position['offset'][1] = sbbox[3] - 1
      else:
        self.position['offset'][0] = sbbox[0]
        self.position['offset'][1] = \
          self.random.randint(sbbox[1] + (sbbox[3] - sbbox[1])/2, sbbox[3] - 1)
    elif self.direction in ('rightdown', 'downright'):
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(sbbox[0], sbbox[2] - 1 - (sbbox[2] - sbbox[0])/2)
        self.position['offset'][1] = sbbox[1]
      else:
        self.position['offset'][0] = sbbox[0]
        self.position['offset'][1] = \
          self.random.randint(sbbox[1], sbbox[3] - 1 - (sbbox[3] - sbbox[1])/2)

    # Increment the position by a random amount in the range
    # [0, shiftDuringSweep)
    if self.shiftDuringSweep > 1:
      prevShiftDuringSweep = self.shiftDuringSweep
      self.shiftDuringSweep = self.random.randint(0, self.shiftDuringSweep)
      self._nextSweepPosition()
      self.shiftDuringSweep = prevShiftDuringSweep
      if self.position['reset']:
        self.first()

    self.position['reset'] = True

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    BaseExplorer.next(self)

    if self.position['reset'] and self.blankWithReset:
      # Last iteration was a blank, so don't increment the position
      self.position['reset'] = False
    else:
      self.position['reset'] = False
      self._nextSweepPosition()
      # Begin a new sweep if necessary
      if self.position['reset']:
        self.first()

  def _nextSweepPosition(self):
    """
    Go to the next position in the current sweep.
    """

    filteredImages = self.getFilteredImages()
    sbbox = self._getSweepBoundingBox(filteredImages[0])

    if self.direction == 'left':
      self.position['offset'][0] -= self.shiftDuringSweep
      if self.position['offset'][0] < sbbox[0]:
        self.position['reset'] = True
    elif self.direction == 'right':
      self.position['offset'][0] += self.shiftDuringSweep
      if self.position['offset'][0] >= sbbox[2]:
        self.position['reset'] = True
    elif self.direction == 'up':
      self.position['offset'][1] -= self.shiftDuringSweep
      if self.position['offset'][1] < sbbox[1]:
        self.position['reset'] = True
    elif self.direction == 'down':
      self.position['offset'][1] += self.shiftDuringSweep
      if self.position['offset'][1] >= sbbox[3]:
        self.position['reset'] = True
    elif self.direction in ('leftup', 'upleft'):
      self.position['offset'][0] -= self.shiftDuringSweep
      self.position['offset'][1] -= self.shiftDuringSweep
      if self.position['offset'][0] < sbbox[0] \
          or self.position['offset'][1] < sbbox[1]:
        self.position['reset'] = True
    elif self.direction in ('leftdown', 'downleft'):
      self.position['offset'][0] -= self.shiftDuringSweep
      self.position['offset'][1] += self.shiftDuringSweep
      if self.position['offset'][0] < sbbox[0] \
          or self.position['offset'][1] >= sbbox[3]:
        self.position['reset'] = True
    elif self.direction in ('rightup', 'upright'):
      self.position['offset'][0] += self.shiftDuringSweep
      self.position['offset'][1] -= self.shiftDuringSweep
      if self.position['offset'][0] >= sbbox[2] \
          or self.position['offset'][1] < sbbox[1]:
        self.position['reset'] = True
    elif self.direction in ('rightdown', 'downright'):
      self.position['offset'][0] += self.shiftDuringSweep
      self.position['offset'][1] += self.shiftDuringSweep
      if self.position['offset'][0] >= sbbox[2] \
          or self.position['offset'][1] >= sbbox[3]:
        self.position['reset'] = True

  def _getSweepBoundingBox(self, image):
    """
    Calculate a 'sweep bounding box' from the image's bounding box.

    If 'sbbox' is the bounding box returned from this method, valid sweep
    positions [x,y] are bounded by sbbox[0] <= x < sbbox[2] and
    sbbox[1] <= y < sbbox[3].
    """

    bbox = image.split()[1].getbbox()
    if bbox is None:
      bbox = (0,0,1,1)
    if self.sweepOffObject:
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
