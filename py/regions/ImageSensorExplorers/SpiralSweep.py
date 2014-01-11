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

class SpiralSweep(BaseExplorer):

  """
  This explorer moves the image a certain number of pixels in a spiral.

  The default arguments (radius=1, stepsize=1) generates movements that include
  the 8 pixels around the center
     x  x  x
     x  0  x
     x  x  x

  if radius is 2, then the movements include another circle of pixels around the first set:
     x  x  x  x  x
     x  x  x  x  x
     x  x  0  x  x
     x  x  x  x  x
     x  x  x  x  x

   and larger radius' grow the movements accordingly.

   If the stepsize is greater than 1, then each 'x' in the diagrams above will be
   separated by 'stepsize' pixels. The 'radius' must always be a multiple of 'stepsize'

   if sweepOffObject is False, the explorer will not include any translations
   that clip the object, as specified by the bounding box. If True (default)
   then clipping is permitted.

   By default, the inner circle starts at a radius of stepsize. If minradius is set,
   it defines the smallest circle radius. 'minradius' must also be a multiple of 'stepsize'

   If includeCenter is True, the center location will be included. By default it is not.
  """

  def __init__(self, radius=1, stepsize=1, minradius=None, includeCenter=False,
               sweepOffObject=True, randomSelections=0,
               *args, **kwargs):
    """
    radius - the radius of the spiral sweep
    """

    if minradius is None:
      minradius = stepsize
    assert(radius >= 1)
    if not ((radius >= stepsize) and (radius % stepsize == 0)):
      raise RuntimeError("radius must be a multiple of stepsize")
    if not ((minradius >= stepsize) and (minradius % stepsize == 0)):
      raise RuntimeError("minradius must be a multiple of stepsize")
    if type(sweepOffObject) not in (bool, int):
      raise RuntimeError("'sweepOffObject' should be a boolean")
    BaseExplorer.__init__(self, *args, **kwargs)

    self.sweepOffObject = sweepOffObject

    # Generate a list of possible offsets for this stepsize and radius
    self.offsets = []
    if includeCenter:
      self.offsets += [(0,0)]
    for i in range(minradius, radius+1, stepsize):
      # Generate top row (not including sides)
      self.offsets += [(x, -i) for x in range(-i+stepsize, i, stepsize)]

      # Generate right edge (including top row, but not bottom row)
      self.offsets += [(i, y) for y in range(-i, i, stepsize)]

      # Generate bottom edge (not including left edge, including right edge)
      self.offsets += [(x, i) for x in range(i, -i, -stepsize)]

      # Generate left edge (including top and bottom row)
      self.offsets += [(-i, y) for y in range(i, -i-stepsize, -stepsize)]

    self.index = 0

    # User-set parameters to control random selection.
    self.randomSelections = randomSelections
    # The cache of randomly selected offsets for the current image/filter.
    self._selectedOffsets = None

  def _getCurrentOffsets(self):
    """
    Gets the set of offsets, after applying optional random selection.
    Call this function instead of directly accessing 'offsets' whenever
    the offsets for the current image/filter are needed.
    Use the 'offsets' member if you want to know the full set of offsets,
    regardless of random selection.

    If random selection is off, returns the default set of offsets.
    If random selection is on, and there is already a randomly-selected set,
    returns the generated set.
    If random selection of on, but we need to generate a randomly-selected set,
    takes the original set of offsets, selects some members at random,
    makes sure the selected members are in the original order, stores this
    selection and returns the selection.
    If the number of requested randomly selected offsets exceeds the number of
    available offsets, then the original offsets will be returned.
    """
    if self._selectedOffsets is None:
      sequence = tuple(self.offsets) # Shallow immutable copy.
      n = len(sequence)
      numToSelect = self.randomSelections
      if (numToSelect > 0) and (numToSelect < n):
        order = range(n)
        self.random.shuffle(order)
        # Select from the shuffled originals, but
        # sort so that the original order is restored,
        # just with fewer entries.
        selected = sorted(order[0:numToSelect])
        # Immutable set.
        self._selectedOffsets = tuple(sequence[i] for i in selected)
        return self._selectedOffsets
      else:
        return sequence
    else:
      return self._selectedOffsets

  def _resetIndex(self):
    """
    Resets the current random selection and the index into the
    current set of offsets. Use this instead of directly setting
    self.index=0.

    Do not call from the constructor just to set self.index=0,
    as this function could be overridden
    (it is not a double-underscore function).
    """
    self._selectedOffsets = None
    self.index = 0

  def first(self, center=True):
    """
    Set up the position.

    BaseExplorer picks image 0, offset (0,0), etc., but explorers that wish
    to set a different first position should extend this method. Such explorers
    may wish to call BaseExplorer.first(center=False), which initializes the
    position tuple but does not call centerImage() (which could cause
    unnecessary filtering to occur).
    """

    BaseExplorer.first(self, center)
    self._resetIndex()

    offsets = self._getCurrentOffsets()
    # Set the 2 dimensions of the position.
    for i in (0,1):
      self.position['offset'][i] = offsets[self.index][i]

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    # Loop until we find an image which is not clipped
    # when self.sweepOffObject==False We assume there is at least one image for
    # which there is one un-clipped position!  (Otherwise getNumIterations
    # should have returned zero.)
    self.position['reset'] = False
    while True:
      # Next offset
      self.index += 1

      offsets = self._getCurrentOffsets()

      # If we have reached the end of the current run of offsets,
      # reset the index into the list of offsets and select a new
      # set of offsets (if we are doing random selection).
      if self.index == len(offsets):
        self.position['reset'] = True
        self._resetIndex()
        offsets = self._getCurrentOffsets()

      # Set the 2 dimensions of the position.
      for i in (0,1):
        self.position['offset'][i] = offsets[self.index][i]

      # Time to move to the next filter?
      if self.index == 0:
        # Iterate through the filters
        for i in xrange(self.numFilters):
          self.position['filters'][i] += 1
          if self.position['filters'][i] < self.numFilterOutputs[i]:
            return
          self.position['filters'][i] = 0

        # Go to the next image
        self.position['image'] += 1
        if self.position['image'] == self.numImages:
          self.position['image'] = 0

      # Get bounding box around current image
      # If alpha channel is completely empty, we will end up
      # with a bbox of 'None'.  Nothing much we can do - treat
      # this as an empty bounding box
      bbox = self.getFilteredImages()[0].split()[1].getbbox()
      if bbox is None:
        bbox = (0, 0, 1, 1)
        print 'WARNING: empty alpha channel'

      # Check for clipping if self.sweepOffObject==False, otherwise break
      if self.sweepOffObject or not (\
          (bbox[0]-self.position['offset'][0] < 0) or \
          (bbox[2]-self.position['offset'][0] > self.enabledWidth) or \
          (bbox[1]-self.position['offset'][1] < 0) or \
          (bbox[3]-self.position['offset'][1] > self.enabledHeight) \
          ):
        break

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if self.sweepOffObject:
      offsetsPerImage = len(self._getCurrentOffsets())
      iterationsPerImage = offsetsPerImage * self.numFilteredVersionsPerImage
      if image:
        return iterationsPerImage
      else:
        return iterationsPerImage * self.numImages
    else:
      if image is None:
        filteredImages = []
        for i in xrange(self.numImages):
          filteredImages.extend(self.getAllFilteredVersionsOfImage(i))
      else:
        filteredImages = self.getAllFilteredVersionsOfImage(image)
      return sum([self._getNumIterationsForImage(x[0]) for x in filteredImages])


  def _getNumIterationsForImage(self, image):
    """
    Return the number of iterations for the image, given the current parameters.

    'image' is a PIL image instance
    """

    if self.sweepOffObject:
      offsetsPerImage = self._getNumOffsets()
      iterationsPerImage = offsetsPerImage * self.numFilteredVersionsPerImage
      return iterationsPerImage
    else:
      # Count how many offsets don't lead to clipping based on the alpha channel
      # bounding box
      numIterations = 0
      bbox = image.split()[1].getbbox()
      # If alpha channel is completely empty, we will end up
      # with a bbox of 'None'.  Nothing much we can do - treat
      # this as an empty bounding box
      if bbox is None:
        bbox = (0, 0, 1, 1)
        print 'WARNING: empty alpha channel'

      offsets = self._getCurrentOffsets()

      # Count the offsets which don't cause clipping
      for offset in offsets:
        if not (\
            (bbox[0]-offset[0] < 0) or \
            (bbox[2]-offset[0] > self.enabledWidth) or \
            (bbox[1]-offset[1] < 0) or \
            (bbox[3]-offset[1] > self.enabledHeight) \
            ):
          numIterations += 1

      return numIterations * self.numFilteredVersionsPerImage
