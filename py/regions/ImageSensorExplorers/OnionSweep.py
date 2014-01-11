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


class OnionSweep(BaseExplorer):

  """
  This explorer moves the image a certain number of pixels in each direction
  from the initial starting point.
  """

  def __init__(self, numSteps, diagonals=False, jitterSize=0, *args, **kwargs):
    """
    numSteps --
    diagonals -- Whether to step along the diagonal
    jitterSize -- How much to jitter around each step of the onion trajectories.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    self.numSteps = numSteps
    self.diagonals = diagonals
    if self.diagonals:
      self.offsetDelta = [[-1,-1],[-1,1],[1,1],[1,-1]]
    else:
      self.offsetDelta = [[-numSteps,-numSteps],[-numSteps,numSteps], \
                          [numSteps,numSteps],[numSteps,-numSteps]]
    if jitterSize == 0:
      self.jitter = [[0,0]]
      self.jitterLength = 1
    else:
      # eg. jitterSize = 2 ->
      #         self.jitter = [[-2,0],[-1,0],[1,0],[2,0],
      #                        [0,2],[0,1],[0,-1],[0,-2],
      #                        [0,0]]
      self.jitter = []
      listi = range(-jitterSize,0) + range(1,jitterSize+1)
      for i in listi:
        self.jitter.append([i,0])
      for i in listi:
        self.jitter.append([0,i])
      self.jitter.append([0,0])
      self.jitterLength = len(self.jitter)
      assert(self.jitterLength == 4*jitterSize+1)

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

    self.diagdiri = 0
    self.diagi = 0
    self.position['offset'][0] += self.numSteps
    self.cent = list(self.position['offset'])
    self.jitteri = 0

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    jitter = self.jitter[self.jitteri]
    self.position['offset'][0] = self.cent[0] + jitter[0]
    self.position['offset'][1] = self.cent[1] + jitter[1]
    # Verbose:
    # print self.position['offset']
    self.jitteri += 1
    if self.jitteri == self.jitterLength:
      self.jitteri = 0
      offsetDelta = self.offsetDelta[self.diagdiri]
      self.cent[0] += offsetDelta[0]
      self.cent[1] += offsetDelta[1]
      self.diagi += 1
      if not self.diagonals or self.diagi == self.numSteps:
        self.diagi = 0
        self.diagdiri += 1
    if self.diagdiri == len(self.offsetDelta) or self.numSteps == 0:
      self.diagdiri = 0
      # Iterate through the filters
      for i in xrange(self.numFilters):
        self.position['filters'][i] += 1
        if self.position['filters'][i] < self.numFilterOutputs[i]:
          self.centerImage()
          return
        self.position['filters'][i] = 0
      # Go to the next image
      self.position['image'] += 1
      if self.position['image'] == self.numImages:
        self.position['image'] = 0
      self.centerImage()

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if self.numSteps ==0:
      itersPer = self.jitterLength
    elif self.diagonals:
      itersPer = self.jitterLength*4*self.numSteps
    else:
      itersPer = self.jitterLength*4
    if image is None:
      return itersPer * self.numFilteredVersionsPerImage * self.numImages
    else:
      return itersPer * self.numFilteredVersionsPerImage
