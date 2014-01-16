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
This file defines the 'starBlock' explorer.

"""

from nupic.regions.PictureSensor import PictureSensor
from nupic.math.cross import cross

#+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# BlockSpreadPictureExplorer

class BlockSpreadPictureExplorer(PictureSensor.PictureExplorer):
  """
  This explorer walks through each position within a 2-D block (called the
  "center-points"), and then for each center-point, explores a set of offsets
  around it.

  Generally, when using this explorer, you will want to issue a reset when, and only
  when, you visit the next center-point. This makes it compatible with using the "star"
  training mode of FDRTemporal. This will cause the FDRTemporal to learn that the
  center-point "spreads" to all positions within an area around it.

  Since the generation of resets is controlled outside the explorer, you have
  to be carefull how you set the 'sequenceLength' parameter relative to the
  other parameters. Here's a description of the parameters and how to use them:

  spaceShape: The (height, width) of the 2-D space to explore. This sets the
              number of center-points.
  spreadShape: The shape (height, width) of the area around each center-point
              to explore. .
  stepSize:   The step size. How big each step is, in pixels. This controls
              *both* the spacing of the center-points within the block and the
              points we explore around each center-point

  To issue a reset at the start of each center-point, sequenceLength should be
  set to: spreadShape[0] * spreadShape[1]

  The total number of iterations should be set to:
    numCategories * blockShape[0] * blockShape[1] * spreadShape[0] * spreadShape[1]

  """

  ########################################################################
  @classmethod
  def queryRelevantParams(klass):
    """
    Returns a sequence of parameter names that are relevant to
    the operation of the explorer.

    May be extended or overridden by sub-classes as appropriate.
    """
    return ( 'spaceShape', 'spreadShape', 'stepSize', )

  ########################################################################
  def initSequence(self, state, params):

    # =================================================================
    # If necessary, create intial state
    if self._getIterCount() == 0:

      stepSize = params['stepSize']

      # What is the range on the X and Y offsets of the center points?
      shape = params['spaceShape']
      xMin = -1 * (shape[1] // 2)
      xMax = xMin + shape[1] - 1
      xPositions = range(stepSize * xMin, stepSize * xMax + 1, stepSize)

      yMin = -1 * (shape[0] // 2)
      yMax = yMin + shape[0] - 1
      yPositions = range(stepSize * yMin, stepSize * yMax + 1, stepSize)

      self._centerOffsets = list(cross(yPositions, xPositions))
      self._numCenterOffsets = len(self._centerOffsets)


      # What is the range on the X and Y offsets of the spread points?
      shape = params['spreadShape']
      xMin = -1 * (shape[1] // 2)
      xMax = xMin + shape[1] - 1
      xPositions = range(stepSize * xMin, stepSize * xMax + 1, stepSize)

      yMin = -1 * (shape[0] // 2)
      yMax = yMin + shape[0] - 1
      yPositions = range(stepSize * yMin, stepSize * yMax + 1, stepSize)

      self._spreadOffsets = list(cross(yPositions, xPositions))
      # Put the (0,0) entry first
      self._spreadOffsets.remove((0,0))
      self._spreadOffsets.insert(0, (0,0))
      self._numSpreadOffsets = len(self._spreadOffsets)


      # Set start position
      self._catIdx = 0
      self._centerPosIdx = 0       # Which center point
      self._spreadPosIdx = 0       # radial position around the center point
      self._numCats = self._getNumCategories()

    # =================================================================
    # Present it
    self._presentNextPosn(state, params)


  ########################################################################
  def updateSequence(self, state, params):
    self._presentNextPosn(state, params)


  ########################################################################
  def _presentNextPosn(self, state, params):
    """
    Compute the appropriate category and block position
    deterministically based on the current iteration count.

    This method uses self._getIterCount() to get the current iteration counter
    and from that infers the image category and position of the image.
    """

    centerOffset = self._centerOffsets[self._centerPosIdx]
    spreadOffset = self._spreadOffsets[self._spreadPosIdx]

    state['posnY'] = centerOffset[0] + spreadOffset[0]
    state['posnX'] = centerOffset[1] + spreadOffset[1]
    state['velocityX'] = 0
    state['velocityY'] = 0
    state['angularPosn'] = 0
    state['angularVelocity'] = 0
    state['catIndex'] = self._catIdx

    # Print current state
    if False:
      print "_catIdx:", self._catIdx, "_centerPosIdx", self._centerPosIdx, \
          "_spreadPosIdx:", self._spreadPosIdx, "centerOffset:", centerOffset, \
          "spreadOffset:", spreadOffset, "yPos:", state['posnY'], \
          "xPos:", state['posnX']

    # Update to next position
    self._spreadPosIdx += 1
    if self._spreadPosIdx == self._numSpreadOffsets:
      self._spreadPosIdx = 0
      self._centerPosIdx += 1
      if self._centerPosIdx == self._numCenterOffsets:
        self._centerPosIdx = 0
        self._catIdx += 1
        if self._catIdx == self._numCats:
          self._catIdx = 0
