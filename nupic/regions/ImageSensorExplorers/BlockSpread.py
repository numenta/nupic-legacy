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
from nupic.math.cross import cross


class BlockSpread(BaseExplorer):

  """
  This explorer walks through each position within a 2-D block (the
  "center-points"), and then for each center-point, explores a set of offsets
  around it.

  This explorer issues a reset when, and only when, it visits the next
  center-point. This makes it compatible with using the "star" training mode of
  FDRTemporal. This will cause the FDRTemporal to learn that the center-point
  "spreads" to all positions within the area around it.

  """

  def __init__(self, spaceShape=(5,5), spreadShape=None, spreadRadius=None,
                  stepSize=1, resetEveryPos=False, verbosity=0, *args, **kwargs):
    """
    spaceShape:   The (height, width) of the 2-D space to explore. This
                  sets the number of center-points.
    spreadShape:  The shape (height, width) of the area around each center-point
                  to explore if you want to spread in a square area. If this is
                  specified, then radius must be None.
    spreadRadius: The radius of the spread if you want to spread in a circular
                  area. If this is specified, then spreadShape must be None.
                  When set to R, this explorer will visit all positions where:
                      int(round(sqrt(dx*dx + dy*dy))) <= radius
    stepSize:     The step size. How big each step is, in pixels. This controls
                  *both* the spacing of the center-points within the block and the
                  points we explore around each center-point.

                  When spreadRadius is used to define the spread shape, then it will
                  only visit points within stepSize*spreadRadius of the center
                  point and insure that no two points it visits within this
                  area are closer than stepSize from each other, where distance
                  is defined as: int(round(sqrt(dx*dx + dy*dy)))

                  This euclidean distance is NOT used to determine where the
                  center points are - they are always laid out in a grid with x
                  spacing and y spacing of stepSize.

    resetEveryPos: If False (the default), output a reset only when we first
                  visit a new center point. This is what is normally used for
                  training.
                  If True, then output a reset on every iteration. This is
                  often used for flash inference testing.

    """
    BaseExplorer.__init__(self, *args, **kwargs)

    # Parameter checking
    if type(stepSize) is not int or stepSize < 1:
      raise RuntimeError("'stepSize' should be a positive integer")

    if len(spaceShape) != 2 or spaceShape[0] < 1 or spaceShape[1] < 1:
      raise RuntimeError("'spaceShape' should be a 2-item tuple specifying the"
            "(height, width) of the overall space to explore.")

    if spreadShape is not None:
      if spreadRadius is not None:
        raise RuntimeError ("When spreadShape is used, spreadRadius must be set to None")
      if len(spreadShape) != 2 or spreadShape[0] < 1 or spreadShape[1] < 1:
        raise RuntimeError("'spreadShape' should be a 2-item tuple specifying the"
              "(height, width) of the of the area round each center point to"
              "explore.")

    if spreadRadius is None and spreadShape is None:
      raise RuntimeError ("Either spreadRadius or spreadShape must be defined")


    # Parameters
    self._spaceShape = spaceShape
    self._spreadShape = spreadShape
    self._spreadRadius = spreadRadius
    self._stepSize = stepSize
    self._verbosity = verbosity
    self._resetEveryPos = resetEveryPos

    # =====================================================================
    # Init data structures
    # What is the range on the X and Y offsets of the center points?
    shape = self._spaceShape
    # If the shape is (1,1), special case of just 1 center point
    if shape[0] == 1 and shape[1] == 1:
      self._centerOffsets = [(0,0)]
    else:
      xMin = -1 * (shape[1] // 2)
      xMax = xMin + shape[1] - 1
      xPositions = range(stepSize * xMin, stepSize * xMax + 1, stepSize)

      yMin = -1 * (shape[0] // 2)
      yMax = yMin + shape[0] - 1
      yPositions = range(stepSize * yMin, stepSize * yMax + 1, stepSize)

      self._centerOffsets = list(cross(yPositions, xPositions))

    self._numCenterOffsets = len(self._centerOffsets)


    # ----------------------------------------------------------------
    # Figure out the spread points based on spreadShape:
    if self._spreadShape is not None:
      # What is the range on the X and Y offsets of the spread points?
      shape = self._spreadShape
      # If the shape is (1,1), special case of no spreading around each center
      #  point
      if shape[0] == 1 and shape[1] == 1:
        self._spreadOffsets = [(0,0)]
      else:
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

    # ---------------------------------------------------------------------
    # Figure out the spread points based on spreadRadius
    else:
      # Special case of spreadRadius = 0:, no spreading around each center point
      if spreadRadius == 0:
        self._spreadOffsets = [(0,0)]

      # Build up a list of all offsets within spreadRadius * stepSize
      else:
        self._spreadOffsets = []
        for y in range(-spreadRadius*stepSize, spreadRadius*stepSize+1):
          for x in range(-spreadRadius*stepSize, spreadRadius*stepSize+1):
            distance = int(round(math.sqrt(x*x + y*y)))
            if distance > spreadRadius*stepSize:
              continue
            # Make sure it's not closer than stepSize to another point within
            #  the spread
            if not (x==0 and y==0) and stepSize > 1:
              tooClose = False
              for (otherY, otherX) in self._spreadOffsets:
                dx = x - otherX
                dy = y - otherY
                distance = int(round(math.sqrt(dx*dx + dy*dy)))
                if distance < stepSize:
                  tooClose = True
                  break
              if tooClose:
                continue
            self._spreadOffsets.append((y,x))

        # Put the (0,0) entry first
        self._spreadOffsets.remove((0,0))
        self._spreadOffsets.insert(0, (0,0))

        if self._verbosity >= 1:
          print "Visiting spread positions:", self._spreadOffsets

    self._numSpreadOffsets = len(self._spreadOffsets)

    # Set start position
    self._centerPosIdx = 0       # Which center point
    self._spreadPosIdx = 0       # radial position around the center point


  ###########################################################################
  def _getHomePosition(self):
    """
    Get the home position for the current image and save it in self._home
    """

    if self.numImages > 0:
      savePosition = self.position['offset'][:]
      self.centerImage()
      self._home = self.position['offset'][:]
      self.position['offset'][:] = savePosition[:]
    else:
      self._home = (0,0)


  ###########################################################################
  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if self._verbosity >= 1:
      print "BlockSpread: getNumIterations():"

    if image is None:
      filteredImages = []
      for i in xrange(self.numImages):
        filteredImages.extend(self.getAllFilteredVersionsOfImage(i))
    else:
      filteredImages = self.getAllFilteredVersionsOfImage(image)

    result = len(filteredImages) * self._numCenterOffsets * self._numSpreadOffsets

    if self._verbosity >= 1:
      print "BlockSpread: getNumIterations() returned %d" % result

    return result

  ###########################################################################
  def first(self):
    """
    Set up the position.

    BaseExplorer picks image 0, offset (0,0), etc., but explorers that wish
    to set a different first position should extend this method. Such explorers
    may wish to call BaseExplorer.first(center=False), which initializes the
    position tuple but does not call centerImage() (which could cause
    unnecessary filtering to occur).
    """

    BaseExplorer.first(self, center=True)

    # Update the "home" position for the current image
    self._getHomePosition()

    if self._verbosity >= 1:
      print "BlockSpread: first():"

    # Set start position
    self._centerPosIdx = 0       # Which center point
    self._spreadPosIdx = 0       # radial position around the center point

    # Convert to X and Y offsets
    self._getPosition()


  ###########################################################################
  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """
    BaseExplorer.next(self)

    if self._verbosity >= 1:
      print "BlockSpread: next():"

    # ========================================================================
    # Update to next position
    self._spreadPosIdx += 1
    if self._spreadPosIdx == self._numSpreadOffsets:
      self._spreadPosIdx = 0
      self._centerPosIdx += 1

      # If we've run through all the center positions, advance to the next
      #  filtered image
      if self._centerPosIdx == self._numCenterOffsets:
        self._centerPosIdx = 0

        # --------------------------------------------------------------------
        # Go to next filter for this image, or next image
        # Iterate through the filters first
        needNewImage = True
        for i in xrange(self.numFilters):
          self.position['filters'][i] += 1
          if self.position['filters'][i] < self.numFilterOutputs[i]:
            needNewImage = False
            break
          else:
            self.position['filters'][i] = 0

        # Go to the next image if ready
        if needNewImage:
          self.position['image'] += 1
          if self.position['image'] == self.numImages:
            self.position['image'] = 0

        # -----------------------------------------------------------------
        # Get the home position for this new filtered image
        self._getHomePosition()

    # ========================================================================
    # Get the X,Y corrdinates and reset signal
    if not seeking:
      self._getPosition()



  ###########################################################################
  def _getPosition(self):
    """
    Given the current center position index (self._centerPosIdx) and
    spread position index (self._spreadPosIdx), update self.position
    with the x and y coordinates of our current position and the status of
    the reset signal.

    """

    if self._verbosity >= 1:
      print "BlockSpread: _getPosition():"

    # Get the X and Y offsets
    centerOffset = self._centerOffsets[self._centerPosIdx]
    spreadOffset = self._spreadOffsets[self._spreadPosIdx]

    # NOTE: self.position['offset'] is (x, y), whereas our internal
    #  coordinates are all (y,x). Also note that the self.position['offset']
    #  direction is counter-intuitive: negative numbers move us to the RIGHT
    #  and DOWN instead of LEFT and UP.
    self.position['offset'][1] = self._home[1] - (centerOffset[0] + spreadOffset[0])
    self.position['offset'][0] = self._home[0] - (centerOffset[1] + spreadOffset[1])

    # If we are at the start of a new center point, issue a reset
    if self._resetEveryPos or self._spreadPosIdx == 0:
      self.position['reset'] = True
    else:
      self.position['reset'] = False


    # Print current state
    if self._verbosity >= 2:
      print "_home", self._home, "_centerPosIdx", self._centerPosIdx, \
          "_spreadPosIdx:", self._spreadPosIdx, "centerOffset:", centerOffset, \
          "spreadOffset:", spreadOffset, "yPos:", self.position['offset'][1], \
          "xPos:", self.position['offset'][0], "reset:", self.position['reset']
