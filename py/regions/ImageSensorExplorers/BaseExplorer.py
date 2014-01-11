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


class BaseExplorer(object):

  """
  BaseExplorer is the base class for all ImageSensor explorers. An explorer is
  a plugin to ImageSensor that defines how the sensor moves through the "input
  space" of images, filtered images, and positions of the sensor "window" on
  the image.

  The basic job of the explorer is to take the current sensor position (image
  number, filtered version, (x,y) offset) and move to the next position. For
  example, the ExhaustiveSweep filter with default parameters shifts the
  offset one pixel to the right on each iteration, and then moves the offset
  down and back to the left side of the image when it falls off the edge of the
  bounding box. When it is done sweeping left-to-right, it sweeps
  top-to-bottom, and then moves on to the next image. The RandomSweep explorer
  works similarly, but after completely one sweep across the image, it randomly
  chooses a new image and a place to start the sweep. The Flash explorer is the
  simplest explorer; it just shows each image once and then moves to the next
  one.

  Explorers do a lot of ImageSensor's work. They maintain the sensor's position
  and increment it. They know how to seek to a certain image, iteration, and
  filtered version. They decide when to send a reset signal (end of a temporal
  sequence). Some of them can report how many iterations are necessary to
  explore all the inputs (though some cannot, like RandomSweep).

  All other ImageSensor explorers should subclass BaseExplorer and implement
  at least next(), and probably __init__(), first(), and seek() as well.
  Deterministic explorers that can calculate a total number of iterations
  should override the getNumIterations() method.
  """

  def __init__(self, getOriginalImage, getFilteredImages, getImageInfo,
               seed=None, holdFor=1):
    """
    getOriginalImage -- ImageSensor method to get an original image.
    getFilteredImages -- ImageSensor method to get filtered images.
    getImageInfo -- ImageSensor method to get imageInfo.
    seed -- Seed for the random number generator. A specific random number
      generator instance is always created for each explorer, so that they do
      not affect each other.
    holdFor -- how many iterations to hold each output image for. Default is 1.
      The sensor will take care of dealing with this - nothing special needs to be
      done by the explorer.
    """

    self.getOriginalImage = getOriginalImage
    self.getFilteredImages = getFilteredImages
    self.getImageInfo = getImageInfo
    self.position = None
    self.holdFor = holdFor

    self.random = random.Random()
    if seed is not None:
      self.random.seed(seed)
    self.initialRandomState = self.random.getstate()

  def first(self, center=True):
    """
    Set up the position.

    BaseExplorer picks image 0, offset (0,0), etc., but explorers that wish
    to set a different first position should extend this method. Such explorers
    may wish to call BaseExplorer.first(center=False), which initializes the
    position tuple but does not call centerImage() (which could cause
    unnecessary filtering to occur).
    """

    self.position = {
      'image': 0,
      'filters': [0] * self.numFilters,
      'offset': [0,0],
      'reset': False
    }
    if self.numImages and center:
      self.centerImage()

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    pass

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

    if iteration is not None:
      self.restoreRandomState()
      self.first()
      if iteration > 0:
        for i in xrange(iteration-1):
          self.next(seeking=True)
        self.next()
    else:
      if position['image'] is not None:
        self.position['image'] = position['image']
      if position['filters'] is not None:
        self.position['filters'] = position['filters']
      if position['offset'] is not None:
        self.position['offset'] = position['offset']
      if position['reset'] is not None:
        self.position['reset'] = position['reset']

  def update(self, **kwargs):
    """
    Update state with new parameters from ImageSensor and call first().
    """

    for key in kwargs:
      if kwargs[key] is not None:
        setattr(self, key, kwargs[key])

    self.first()

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    return -1

  def restoreRandomState(self):
    """
    Restore the initial random state of the explorer.
    """

    self.random.setstate(self.initialRandomState)

  def isBlank(self, fallOffObject, position=None):
    """
    Return True if the enabled region of the image specified by the current
    position is blank.

    fallOffObject -- If True, the image is considered blank only if the mask
      is entirely black. Otherwise, it is considered blank if any of mask is
      black.
    position -- Position to use. Uses current position if not specified.
    """

    if not position:
      position = self.position

    x1, y1 = position['offset']
    x2 = x1 + self.enabledWidth
    y2 = y1 + self.enabledHeight
    mask = self.getFilteredImages(position)[0].split()[1]
    extrema = mask.crop((max(x1, 0), max(y1, 0),
      min(x2, mask.size[0]), min(y2, mask.size[1]))).getextrema()
    if (fallOffObject and extrema[1] == 0) \
        or (not fallOffObject and extrema[0] == 0):
      if not fallOffObject:
        # The non-fallOffObject case is tricky - devious masks can make it hang
        # Test 1: If the window contains the entire mask, it's not a blank
        bbox = mask.getbbox()
        if bbox[0] >= x1 and bbox[1] >= y1 and bbox[2] <= x2 and bbox[3] <= y2:
          return False
        # Need to add more tests
      return True
    else:
      return False

  def isValid(self, position=None):
    """
    Return True if the current position and enabled size contains at least
    some of the region specified by the bounding box.

    position -- Position to use. Uses current position if not specified.
    """

    if not position:
      position = self.position

    x, y = position['offset']
    bbox = self.getFilteredImages(position)[0].split()[1].getbbox()
    if (bbox[0] - self.enabledWidth >= x) or \
       (bbox[1] - self.enabledHeight >= y) or \
       (bbox[2] + self.enabledWidth <= x) or \
       (bbox[3] + self.enabledHeight <= y):
      return False
    return True

  def getAllFilteredVersionsOfImage(self, image=None):
    """
    Get all the filtered versions of the image, as a flat list.

    Each item in the list is a list of images, containing an image for each
    simultaneous response.

    image -- Image index to use. Uses current position if not specified.
    """

    if not image:
      image = self.position['image']

    filteredImages = []
    filterPosition = [0] * self.numFilters
    position = {'image': image, 'filters': filterPosition}
    while True:
      filteredImages.append(self.getFilteredImages(position))
      for i in xrange(self.numFilters-1, -1, -1):
        filterPosition[i] += 1
        if filterPosition[i] == self.numFilterOutputs[i]:
          filterPosition[i] = 0
        else:
          break
      if filterPosition == [0] * self.numFilters:
        break
    return filteredImages

  def pickRandomImage(self, random):
    """
    Pick a random image from a uniform distribution.

    random -- Instance of random.Random.
    """

    return random.randint(0, self.numImages - 1)

  def pickRandomFilters(self, random):
    """
    Pick a random position for each filter from uniform distributions.

    random -- Instance of random.Random.
    """

    return [random.randint(0, self.numFilterOutputs[i] - 1)
      for i in xrange(self.numFilters)]

  def centerImage(self):
    """
    Update the offset to center the current image.
    """

    image = self.getFilteredImages()[0]
    self.position['offset'] = [(image.size[0] - self.enabledWidth)  / 2,
                               (image.size[1] - self.enabledHeight) / 2]

  def _getNumFilteredVersionsPerImage(self):
    """
    Get the number of filtered versions for each original image.
    """

    numFilteredVersions = 1
    for i in xrange(self.numFilters):
      numFilteredVersions *= self.numFilterOutputs[i]
    return numFilteredVersions

  numFilteredVersionsPerImage = property(_getNumFilteredVersionsPerImage)
