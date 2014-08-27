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

import random

from nupic.regions.ImageSensorExplorers.BaseExplorer import BaseExplorer


class RepetitiveSweep(BaseExplorer):

  """
  This explorer performs random sweeps that are of specified length, and
  are repeated identically a specified number of times.
  """

  def __init__(self, sweepLength=4,
                     numRepetitions=1,
                     sweepOffMode=False,
                     maxOffset=None,
                     minVelocity=1,
                     maxVelocity=3,
                     seed=42,
                     *args, **kwargs):
    """
    @param sweepLen: number of presentations per sweep sequence.
    @param numRepetitions: number of times to present each inward sweep.
    """
    BaseExplorer.__init__(self, *args, **kwargs)
    # Parameter checking
    if type(sweepLength) is not int or sweepLength < 1:
      raise RuntimeError("'sweepLength' should be a positive integer")
    if type(numRepetitions) is not int or numRepetitions < 1:
      raise RuntimeError("'numRepetitions' should be a positive integer")
    # Parameters
    self._sweepLength = sweepLength
    self._numRepetitions = numRepetitions
    self._minVelocity = minVelocity
    self._maxVelocity = maxVelocity
    self._sweepOffMode = sweepOffMode
    self._maxOffset = maxOffset
    # Internal state
    self._seqIndex = 0
    self._repIndex = 0
    self._state = None
    self._repMemory = None
    # Prepare PRNG
    self._rng = random.Random()
    self._rng.seed(seed)


  def _initSequence(self):

    bbox = self.getOriginalImage().getbbox()
    patternWidth = bbox[2] - bbox[0]
    patternHeight = bbox[3] - bbox[1]

    slopX = (self.enabledWidth  - patternWidth) // 2
    slopY = (self.enabledHeight - patternHeight) // 2
    if self._sweepOffMode:
      slopX = abs(slopX)
      slopY = abs(slopY)
    if self._maxOffset is not None:
      slopX = min(abs(slopX), self._maxOffset)
      slopY = min(abs(slopY), self._maxOffset)
    posnX = self._rng.choice(xrange(-slopX, slopX + 1))
    posnY = self._rng.choice(xrange(-slopY, slopY + 1))
    velocityX = self._rng.choice([-1, +1]) \
              * self._rng.choice(xrange(self._minVelocity, self._maxVelocity + 1))
    velocityY = self._rng.choice([-1, +1]) \
              * self._rng.choice(xrange(self._minVelocity, self._maxVelocity + 1))
    # Choose a category random
    catIndex = self._rng.choice(range(self.numImages))

    # Make sure we don't allow stationary (no velocity)
    if self._maxVelocity > 0:
      if velocityX == 0 and velocityY == 0:
        velocityX, velocityY = self._rng.choice([(-1, -1), (-1, 1), (1, -1), (1, 1)])

    self.position['reset'] = True
    self.position['image'] = catIndex
    self.position['offset'] = [posnX, posnY]
    # Store internal state
    self._state = dict(posnX=posnX, posnY=posnY,
                       velocityX=velocityX, velocityY=velocityY,
                       catIndex=catIndex)


  def _updateSequence(self):
    posnX = self._state['posnX']
    posnY = self._state['posnY']
    posnX += self._state['velocityX']
    posnY += self._state['velocityY']
    self._state['posnX'] = posnX
    self._state['posnY'] = posnY
    self.position['offset'] = [posnX, posnY]
    self.position['reset'] = False
    self.position['image'] = self._state['catIndex']


  def _computeNextPosn(self):
    """
    Helper method that deterministically computes the next
    inward sweep position.
    """

    # Start new pattern to be repeated
    if not self._repIndex:
      if self._seqIndex == 0:
        self._repMemory = []
        self._initSequence()
      else:
        self._updateSequence()
      self._repMemory += [self.position.copy()]
    else:
      self.position = self._repMemory[self._seqIndex]

    # Debugging output to console
    if False:
      print "[%04d] %d: (%d, %d) %s" % ( \
            self._seqIndex,
            self.position['image'],
            self.position['offset'][0],
            self.position['offset'][1],
            "RESET" if self.position['reset'] else "")

    # Update count
    self._seqIndex += 1
    if self._seqIndex == self._sweepLength:
      self._seqIndex = 0
      self._repIndex = (self._repIndex + 1) % self._numRepetitions



  def seek(self, iteration=None, position=None):
    """
    Seek to the specified position or iteration.

    iteration -- Target iteration number (or None).
    position -- Target position (or None).

    ImageSensor checks validity of inputs, checks that one (but not both) of
    position and iteration are None, and checks that if position is not None,
    at least one of its values is not None.

    Updates value of position.
    """
    self.first()


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
    self._computeNextPosn()


  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """
    self._computeNextPosn()
