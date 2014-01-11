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

import os
import copy
import re

from nupic.regions.ImageSensorExplorers.BaseExplorer import BaseExplorer


class MultiSweep(BaseExplorer):

  """
  This explorer performs randomly-selected sweeps through all dimensions
  (translation, images, and filters). Additionally, a pattern can be matched
  against filenames in order to extract extra dimensions for sweeping.
  """

  def __init__(self, dimensions=None, sweepOffObject=False,
               crossDirectories=False, minSweepLength=0, pattern=None,
               *args, **kwargs):
    """
    dimensions -- List of dimensions through which to sweep. Each
      element is a string with the name of a dimension, or a dictionary with
      more options (see below). 'translation', is normal translation sweeping,
      and 'image' holds the position constant as it moves across images.
      Include an integer from [0, numFilters-1] to specifying sweeping across
      the outputs of a certain filter while holding the rest of the position
      constant. If None, all dimensions are used, with default options.
    sweepOffObject -- Whether the sensor can only include a part of the
      object, as specified by the bounding box. If False, it will only move to
      positions that include as much of the object as possible.
    crossDirectories -- ** DEPRECATED ** If False and sweeping through
      images, the explorer looks at the filename of the images and stops
      sweeping when it would go to an image whose enclosing directory is
      different than the current image.
    minSweepLength -- Minimum length for each sweep. If a sweep is too
      short, image and filter sweeps continue smoothly if 'wraparound' is True,
      and otherwise they switch directions. Translation sweeps bounce into a
      new direction, excluding the opposite direction of the current sweep.
    pattern -- Pattern to use for extracting extra dimensions from
      image filenames. If you use the 'dimensions' argument, make sure to list
      these extra dimensions or they won't be used.
      Sweeps will hold all other dimensions constant while going through the
      selected dimension in sorted order.
      Can either be a tuple: (separator, dimensionName, dimensionName, ...),
      or a regular expression that extracts named dimensions.
      Example:
        If the filenames look like this: "Apple_1 50 90 foo.png", where
        "Apple_1" is the name of the object, "50" is the vertical angle, "90"
        is the horizontal angle, and "foo" is extra text to ignore, MultiSweep
        will sweep through the vertical and horizontal dimensions with either
        of these values for 'pattern' (and ['vertical', 'horizontal'] as the
        value for 'dimensions'):
          Tuple:
            (" ", "object", "vertical", "horizontal", None)
            The separator tells MultiSweep to split up the name on spaces, and
            the None argument specifies that the "foo" part of the name is not
            a dimension and should be ignored.
          Regular expression:
            "^(?P<object>\w+)\s(?P<vertical>\d+)\s(?P<horizontal>\d+)\s\w+$"
            "(?P<NAME>PATTERN)" is a Python-specific syntax for extracting
            named groups.
      Note that "object" is extracted as its own dimension even though it could
      have been ignored. This allows for multiple objects (such as "Apple_1"
      and "Apple_2") to appear in the same directory without MultiSweep
      generating sweeps across objects.
      After the dimensions are extracted, they are converted to ints or floats
      if possible. Then they are sorted using Python's list.sort() method.

    Dictionaries for dimensions take the following keywords:
    name           : Name of the dimension, one of:
                       - 'translation' (translation sweeping)
                       - 'image' (cycle through images)
                       - the name of a dimension extracted via 'pattern'
                       - an integer specifying the index of a filter
    shift          : Number of steps to jump on each iteration.
                     For example, 2 means to jump by 2 pixels or 2 images.
    probability    : Probability of randomly selecting this dimension.
    wraparound     : Whether to 'wrap around' from one end of the dimension to
                     the other, rather than stopping the sweep (or changing
                     directions, if minSweepLength has not been met).
                     ** ONLY IMPLEMENTED FOR SWEEPING THROUGH FILTER OUTPUTS
                     WITH SHIFT == 1 **
    sweepOffObject : Overrides the main 'sweepOffObject' parameter.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    if type(sweepOffObject) not in (bool, int):
      raise RuntimeError("'sweepOffObject' should be a boolean")
    if type(crossDirectories) not in (bool, int):
      raise RuntimeError("'crossDirectories' should be a boolean")
    if type(minSweepLength) is not int:
      raise RuntimeError("'minSweepLength' should be an integer")

    self.sweepOffObject = sweepOffObject
    self.crossDirectories = crossDirectories
    self.minSweepLength = minSweepLength

    # Get dimensions to be parsed from filenames
    self.pattern = pattern
    self.parsedDimensions = []
    if pattern:
      if type(pattern) in (list, tuple):
        if type(pattern) is tuple:
          pattern = list(pattern)
        self.parsedDimensions = pattern[1:]
        while None in self.parsedDimensions:
          self.parsedDimensions.remove(None)
      elif isinstance(pattern, basestring):
        self.parsedDimensions = re.findall("\(\?P<([^>]+)>", pattern)
      else:
        raise ValueError("'pattern' should be a list/tuple or string")
      # Extra instance variables for parsed dimensions
      self.parsedIndices = []
      self.parsedIndex = 0

    # Figure out all the dimensions
    if not dimensions:
      self.allDimensions = True
      self.dimensions = ['translation']
      if not self.parsedDimensions:
        self.dimensions.append('image')
    else:
      self.allDimensions = False
      if type(dimensions) in (str, int):
        dimensions = [dimensions]
      self.dimensions = list(dimensions)
      # Add the dimensions to be parsed from filenames
      self.dimensions += self.parsedDimensions
    for i, d in enumerate(self.dimensions):
      if type(d) in (str, int):
        self.dimensions[i] = self._newSweepDictionary(name=d)
      else:
        self.dimensions[i] = self._newSweepDictionary(**d)

    self._calculateProbabilities()

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

    # Pick a random dimension (exclude filters without multiple outputs)
    filters = []
    for i in xrange(self.numFilters):
      if self.numFilterOutputs[i] > 1:
        filters.append(i)
    legalDimensions = self.dimensions[:]
    for d in self.dimensions:
      if type(d['name']) is int and d['name'] not in filters:
        legalDimensions.remove(d)
    # Choice is weighted by probabilities
    r = self.random.uniform(0, sum([d['probability'] for d in legalDimensions]))
    for i, d in enumerate(legalDimensions):
      if r <= d['probability']:
        self.dimension = d
        break
      r -= d['probability']

    self.start = None
    restart = True
    while restart:

      self.position['reset'] = False
      restart = False

      # Translation sweep
      if self.dimension['name'] == 'translation':

        # Pick a random direction, image, and set of filters
        self.direction = self.random.choice(('left', 'right', 'up', 'down',
          'leftdown', 'leftup', 'rightdown', 'rightup'))
        self.position['image'] = self.pickRandomImage(self.random)
        self.position['filters'] = self.pickRandomFilters(self.random)
        filteredImages = self.getFilteredImages()
        ebbox = self._getEffectiveBoundingBox(filteredImages[0])

        # Align starting position at zero offset position.
        forceAlignment = self.dimension.get('forceAlignment')
        if forceAlignment is not None and forceAlignment:
          self.position['offset'] = [0,0]
        # Pick a random starting position on the appropriate edge of the image
        else:
          self._firstTranslationPosition(ebbox, filteredImages[0])

        # Increment the start position until it is not blank
        while self.isBlank(self.dimension['sweepOffObject']):
          self._nextTranslationPosition(shift=1)
          if self.position['reset'] or not self.isValid():
            restart = True
            break
        if restart:
          continue

        # Increment the position by a random amount in the range [0, shift)
        if not forceAlignment:
          self._nextTranslationPosition(randomShift=True)

      # Image sweep
      elif self.dimension['name'] == 'image':

        # Pick a random direction
        self.direction = self.random.choice(('up', 'down'))

        # Pick a random image and find the first or last image in the category
        image = self.pickRandomImage(self.random)
        startCategory = self.getImageInfo(image)['categoryIndex']
        if self.direction == 'up':
          while image > 0 and \
              self.getImageInfo(image-1)['categoryIndex'] == startCategory:
            image -= 1
        else:
          while image < self.numImages - 1 and \
              self.getImageInfo(image+1)['categoryIndex'] == startCategory:
            image += 1
        self.position['image'] = image

        # Pick the filters
        self.position['filters'] = self.pickRandomFilters(self.random)
        filteredImages = self.getFilteredImages()

        # Pick a random position within the bounding box
        ebbox = self._getEffectiveBoundingBox(filteredImages[0])
        self.position['offset'] = [
          self.random.randint(ebbox[0], ebbox[2]-1),
          self.random.randint(ebbox[1], ebbox[3]-1)
        ]

        # Increment the start position until it is not blank
        while self.isBlank(self.dimension['sweepOffObject']):
          self._nextImagePosition(shift=1)
          if self.position['reset'] or not self.isValid():
            restart = True
            break
        if restart:
          continue

        # Increment the position by a random amount in the range [0, shift)
        self._nextImagePosition(randomShift=True)

      # Parsed dimension sweep
      elif self.dimension['name'] in self.parsedDimensions:

        # Pick a random direction
        self.direction = self.random.choice(('up', 'down'))

        # Pick a random image
        image = self.pickRandomImage(self.random)

        # Create a list of filenames that will be included in this sweep
        self._createParsedDimension(image)

        # Find the first or last image
        if self.direction == 'up':
          self.parsedIndex = 0
        else:
          self.parsedIndex = len(self.parsedIndices) - 1
        self.position['image'] = self.parsedIndices[self.parsedIndex]

        # Pick the filters
        self.position['filters'] = self.pickRandomFilters(self.random)
        filteredImages = self.getFilteredImages()

        # Pick a random position within the bounding box
        ebbox = self._getEffectiveBoundingBox(filteredImages[0])
        self.position['offset'] = [
          self.random.randint(ebbox[0], ebbox[2]-1),
          self.random.randint(ebbox[1], ebbox[3]-1)
        ]

        # Increment the start position until it is not blank
        while self.isBlank(self.dimension['sweepOffObject']):
          self._nextParsedPosition(shift=1)
          if self.position['reset'] or not self.isValid():
            restart = True
            break
        if restart:
          continue

        # Increment the position by a random amount in the range [0, shift)
        self._nextParsedPosition(randomShift=True)

      # Filter sweep
      else:

        # Pick a random direction, image, and set of filters
        self.direction = self.random.choice(('up', 'down'))
        self.position['image'] = self.pickRandomImage(self.random)
        self.position['filters'] = self.pickRandomFilters(self.random)
        filteredImages = self.getFilteredImages()

        # Go to one end of the selected filter
        if self.direction == 'up':
          self.position['filters'][self.dimension['name']] = 0
        else:
          self.position['filters'][self.dimension['name']] = \
            self.numFilterOutputs[self.dimension['name']] - 1

        # Pick a random position within the bounding box
        filteredImages = self.getFilteredImages()
        ebbox = self._getEffectiveBoundingBox(filteredImages[0])
        self.position['offset'] = [
          self.random.randint(ebbox[0], ebbox[2]-1),
          self.random.randint(ebbox[1], ebbox[3]-1)
        ]
        self.prevImageSize = filteredImages[0].size

        # Increment the start position until it is not blank
        while self.isBlank(self.dimension['sweepOffObject']):
          self._nextFilterPosition(shift=1)
          if self.position['reset'] or not self.isValid():
            restart = True
            break
        if restart:
          continue

        # Increment the position by a random amount in the range [0, shift)
        self._nextFilterPosition(randomShift=True)

    self.start = self._copyPosition(self.position)
    self.position['reset'] = True
    self.length = 1

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
      return
    self.position['reset'] = False

    prevPosition = self._copyPosition(self.position)

    # Translation sweep
    if self.dimension['name'] == 'translation':
      self._nextTranslationPosition()
      bounceDirections = self._getBounceDirections()
      while self.position['reset'] and self.length < self.minSweepLength and \
          bounceDirections:
        # Sweep is too short - bounce and continue
        self.position = self._copyPosition(prevPosition)
        self.direction = bounceDirections.pop(0)
        self._nextTranslationPosition()

    # Image sweep
    elif self.dimension['name'] == 'image':
      self._nextImagePosition()
      if self.position['reset'] and self.length < self.minSweepLength:
        # Sweep is too short - bounce and continue
        self.position = prevPosition
        if self.direction == 'up':
          self.direction = 'down'
        else:
          self.direction = 'up'
        self._nextImagePosition()

    # Parsed dimension sweep
    elif self.dimension['name'] in self.parsedDimensions:
      self._nextParsedPosition()
      if self.position['reset'] and self.length < self.minSweepLength:
        # Sweep is too short - bounce and continue
        self.position = prevPosition
        if self.direction == 'up':
          self.direction = 'down'
        else:
          self.direction = 'up'
        self._nextParsedPosition()

    # Filter sweep
    else:
      self._nextFilterPosition()
      if self.position['reset'] and self.length < self.minSweepLength:
        # Sweep is too short - bounce and continue
        self.position = prevPosition
        if self.direction == 'up':
          self.direction = 'down'
        else:
          self.direction = 'up'
        self._nextFilterPosition()

    # Stop the sweep if it has fallen off the object
    if not self.position['reset'] \
        and self.isBlank(self.dimension['sweepOffObject']):
      self.position['reset'] = True

    # Begin a new sweep if necessary
    if self.position['reset']:
      self.first()
    else:
      self.length += 1

  def update(self, **kwargs):
    """
    Update state with new parameters from ImageSensor and call first().
    """

    numFilters = kwargs.get('numFilters', None)
    if numFilters is not None and self.allDimensions:
      # Remove existing filter dimensions
      for dimension in self.dimensions[:]:
        if type(dimension['name']) is int:
          self.dimensions.remove(dimension)
      # Reset the probabilities from the existing dimensions
      for d in self.dimensions:
        d['probability'] = None
      # Add the new filter dimensions
      self.dimensions += \
        [self._newSweepDictionary(name=name) for name in range(numFilters)]

    numImages = kwargs.get('numImages', None)
    if numImages is not None and self.pattern:
      # Parse all the filenames
      self._parseFilenames(numImages)

    self._calculateProbabilities()

    BaseExplorer.update(self, **kwargs)

  def _newSweepDictionary(self, name, shift=1, probability=None,
      wraparound=False, sweepOffObject=None, forceAlignment=False, **kwds):
    """
    Create and return a new dictionary for a sweep dimension.
    """

    if kwds:
      raise RuntimeError('Invalid key(s) in sweep dimension: '
        + str(keywds.keys()))

    if name not in ('translation', 'image') \
        and name not in self.parsedDimensions \
        and type(name) is not int:
      raise RuntimeError('Invalid dimension: ' + str(name))

    if sweepOffObject is None:
      sweepOffObject = self.sweepOffObject

    if wraparound and not (isinstance(name, int) and shift == 1):
      raise RuntimeError("'wraparound' is currently only supported when "
                         "sweeping through a filter dimension "
                         "with 'shift' == 1")

    return {'name': name, 'shift': shift, 'probability': probability,
      'wraparound': wraparound, 'sweepOffObject': sweepOffObject,
      'forceAlignment': forceAlignment}

  def _firstTranslationPosition(self, ebbox, image):
    """
    Pick a starting position for a translation sweep on the edge of the image.
    """

    if self.direction == 'left':
      self.position['offset'][0] = ebbox[2] - 1
      self.position['offset'][1] = self.random.randint(ebbox[1], ebbox[3] - 1)
    elif self.direction == 'right':
      self.position['offset'][0] = ebbox[0]
      self.position['offset'][1] = self.random.randint(ebbox[1], ebbox[3] - 1)
    elif self.direction == 'up':
      self.position['offset'][0] = self.random.randint(ebbox[0], ebbox[2] - 1)
      self.position['offset'][1] = ebbox[3] - 1
    elif self.direction == 'down':
      self.position['offset'][0] = self.random.randint(ebbox[0], ebbox[2] - 1)
      self.position['offset'][1] = ebbox[1]
    elif self.direction == 'leftup':
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(ebbox[0] + (ebbox[2] - ebbox[0])/2, ebbox[2] - 1)
        self.position['offset'][1] = ebbox[3] - 1
      else:
        self.position['offset'][0] = ebbox[2] - 1
        self.position['offset'][1] = \
          self.random.randint(ebbox[1] + (ebbox[3] - ebbox[1])/2, ebbox[3] - 1)
    elif self.direction == 'leftdown':
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(ebbox[0] + (ebbox[2] - ebbox[0])/2, ebbox[2] - 1)
        self.position['offset'][1] = ebbox[1]
      else:
        self.position['offset'][0] = ebbox[2] - 1
        self.position['offset'][1] = \
          self.random.randint(ebbox[1], ebbox[3] - 1 - (ebbox[3] - ebbox[1])/2)
    elif self.direction == 'rightup':
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(ebbox[0], ebbox[2] - 1 - (ebbox[2] - ebbox[0])/2)
        self.position['offset'][1] = ebbox[3] - 1
      else:
        self.position['offset'][0] = ebbox[0]
        self.position['offset'][1] = \
          self.random.randint(ebbox[1] + (ebbox[3] - ebbox[1])/2, ebbox[3] - 1)
    elif self.direction == 'rightdown':
      if self.random.randint(0,1):
        self.position['offset'][0] = \
          self.random.randint(ebbox[0], ebbox[2] - 1 - (ebbox[2] - ebbox[0])/2)
        self.position['offset'][1] = ebbox[1]
      else:
        self.position['offset'][0] = ebbox[0]
        self.position['offset'][1] = \
          self.random.randint(ebbox[1], ebbox[3] - 1 - (ebbox[3] - ebbox[1])/2)

  def _nextTranslationPosition(self, randomShift=False, shift=None):
    """
    Go to the next position in the current translation sweep.
    """

    filteredImages = self.getFilteredImages()
    ebbox = self._getEffectiveBoundingBox(filteredImages[0])

    if shift is None:
      shift = self.dimension['shift']
    if randomShift:
      shift = self.random.randint(0, shift-1)

    if self.direction == 'left':
      self.position['offset'][0] -= shift
      if self.position['offset'][0] < ebbox[0]:
        self.position['reset'] = True
    elif self.direction == 'right':
      self.position['offset'][0] += shift
      if self.position['offset'][0] >= ebbox[2]:
        self.position['reset'] = True
    elif self.direction == 'up':
      self.position['offset'][1] -= shift
      if self.position['offset'][1] < ebbox[1]:
        self.position['reset'] = True
    elif self.direction == 'down':
      self.position['offset'][1] += shift
      if self.position['offset'][1] >= ebbox[3]:
        self.position['reset'] = True
    elif self.direction in ('leftup', 'upleft'):
      self.position['offset'][0] -= shift
      self.position['offset'][1] -= shift
      if self.position['offset'][0] < ebbox[0] \
          or self.position['offset'][1] < ebbox[1]:
        self.position['reset'] = True
    elif self.direction in ('leftdown', 'downleft'):
      self.position['offset'][0] -= shift
      self.position['offset'][1] += shift
      if self.position['offset'][0] < ebbox[0] \
          or self.position['offset'][1] >= ebbox[3]:
        self.position['reset'] = True
    elif self.direction in ('rightup', 'upright'):
      self.position['offset'][0] += shift
      self.position['offset'][1] -= shift
      if self.position['offset'][0] >= ebbox[2] \
          or self.position['offset'][1] < ebbox[1]:
        self.position['reset'] = True
    elif self.direction in ('rightdown', 'downright'):
      self.position['offset'][0] += shift
      self.position['offset'][1] += shift
      if self.position['offset'][0] >= ebbox[2] \
          or self.position['offset'][1] >= ebbox[3]:
        self.position['reset'] = True

    if not self.position['reset'] \
        and self.isBlank(self.dimension['sweepOffObject']):
      self.position['reset'] = True

  def _getBounceDirections(self):
    """
    Return a randomly-ordered set of directions in which to 'bounce'.

    The opposite of the current direction is included and is always in the
    last position.
    """

    if self.direction == 'left':
      directions = ['up', 'rightup', 'rightdown', 'down']
    elif self.direction == 'up':
      directions = ['right', 'rightdown', 'leftdown', 'left']
    elif self.direction == 'right':
      directions = ['down', 'leftdown', 'leftup', 'up']
    elif self.direction == 'down':
      directions = ['left', 'leftup', 'rightup', 'right']
    elif self.direction == 'leftup':
      directions = ['up', 'rightup', 'right', 'down', 'leftdown', 'left']
    elif self.direction == 'rightup':
      directions = ['right', 'rightdown', 'down', 'left', 'leftup', 'up']
    elif self.direction == 'rightdown':
      directions = ['down', 'leftdown', 'left', 'up', 'rightup', 'right']
    elif self.direction == 'leftdown':
      directions = ['left', 'leftup', 'up', 'right', 'rightdown', 'down']
    self.random.shuffle(directions)
    opposites = {'left': 'right', 'leftup': 'rightdown', 'up': 'down',
      'rightup': 'leftdown', 'right': 'left', 'rightdown': 'leftup',
      'down': 'up', 'leftdown': 'rightup'}
    return directions + [opposites[self.direction]]

  def _parseFilenames(self, numImages):
    """
    Parse all image filenames and store as a list of dictionaries.
    """

    self.parsedFilenames = []
    for i in xrange(numImages):
      filename = os.path.split(self.getImageInfo(i)['imagePath'])[1]
      if isinstance(self.pattern, basestring):
        # Regular expression
        match = re.search(self.pattern, filename)
        if not match:
          raise RuntimeError("Failed to match 'pattern' argument to MultiSweep "
            "(regular expression) against imagePath %s " % filename
            + "(image index: %d)" % i)
        self.parsedFilenames.append(match.groupdict())
      else:
        # List: (separator, dimensionName, dimensionName, dimensionName, ...)
        filename = os.path.splitext(filename)[0]
        # Split on separator
        separator = self.pattern[0]
        indices = filename.split(separator)
        if len(indices) != len(self.pattern) - 1:
          raise RuntimeError("Splitting filename '%s' " % filename
            + "on separator '%s' " % separator
            + "returned %d elements " % len(indices)
            + "instead of %d " % (len(self.pattern) - 1)
            + "(as specified by the 'pattern' argument to MultiSweep)")
        self.parsedFilenames.append(dict(zip(self.pattern[1:], indices)))
        # Remove entry for None if it exists, which corresponds to one or
        # more parts of the filename that should be ignored
        self.parsedFilenames[-1].pop(None, None)

    # Convert to ints or floats if possible
    for key in self.parsedFilenames[0]:
      indices = [f[key] for f in self.parsedFilenames]
      for func in (int, float):
        try:
          [func(i) for i in indices]
        except ValueError:
          pass
        else:
          for p in self.parsedFilenames:
            p[key] = func(p[key])
          break

  def _createParsedDimension(self, image):
    """
    Create a list of filenames that will be included in the current sweep.
    """

    indices = self.parsedFilenames[image]
    # Look backwards to find the first image in the same directory
    path = os.path.split(self.getImageInfo(image)['imagePath'])[0]
    startImage = image
    while startImage > 0:
      if os.path.split(self.getImageInfo(startImage-1)['imagePath'])[0] != path:
        break
      startImage -= 1
    # Get other images with the same index in the other parsed dimensions
    imageIndices = []
    for i in xrange(startImage, len(self.parsedFilenames)):
      if os.path.split(self.getImageInfo(i)['imagePath'])[0] != path:
        break
      for key, value in indices.iteritems():
        if key == self.dimension['name']:
          continue
        if self.parsedFilenames[i][key] != value:
          break
      else:
        imageIndices.append(i)
    # Sort the images by their index along the current dimension
    imageIndices.sort(
      key=lambda i: self.parsedFilenames[i][self.dimension['name']])
    self.parsedIndices = imageIndices

  def _nextImagePosition(self, randomShift=False, shift=None):
    """
    Go to the next position in the current image sweep.
    """

    if shift is None:
      shift = self.dimension['shift']
    if randomShift:
      shift = self.random.randint(0, shift-1)
    if not shift:
      return

    prevImage = self.position['image']
    if self.direction == 'up':
      image = prevImage + shift
    else:
      image = prevImage - shift
    self.position['image'] = image
    # Check if we've changed categories or run past the end
    if image >= self.numImages or image < 0 \
        or self.getImageInfo(image)['categoryIndex'] \
        != self.getImageInfo(prevImage)['categoryIndex']:
      self.position['reset'] = True
    else:
      if not self.crossDirectories and self.getImageInfo(image)['imagePath']:
        # Check if we have moved to an image from a different directory
        if not self.getImageInfo(prevImage)['imagePath'] or \
            (os.path.split(self.getImageInfo(image)['imagePath'])[0] !=
            os.path.split(self.getImageInfo(prevImage)['imagePath'])[0]):
          self.position['reset'] = True

    if not self.position['reset'] \
        and self.isBlank(self.dimension['sweepOffObject']):
      self.position['reset'] = True

  def _nextParsedPosition(self, randomShift=False, shift=None):
    """
    Go to the next position in the current parsed dimension sweep.
    """

    if shift is None:
      shift = self.dimension['shift']
    if randomShift:
      shift = self.random.randint(0, shift-1)
    if not shift:
      return

    if self.direction == 'up':
      parsedIndex = self.parsedIndex + shift
    else:
      parsedIndex = self.parsedIndex - shift

    # Check if we've changed categories or run past the end
    if parsedIndex >= len(self.parsedIndices) or parsedIndex < 0:
      self.position['reset'] = True
    else:
      self.parsedIndex = parsedIndex
      self.position['image'] = self.parsedIndices[parsedIndex]
      if self.isBlank(self.dimension['sweepOffObject']):
        self.position['reset'] = True

  def _nextFilterPosition(self, randomShift=False, shift=None):
    """
    Go to the next position in the current filter sweep.
    """

    if shift is None:
      shift = self.dimension['shift']
    if randomShift:
      shift = self.random.randint(0, shift-1)
    if not shift:
      return

    if self.direction == 'up':
      self.position['filters'][self.dimension['name']] += shift
    else:
      self.position['filters'][self.dimension['name']] -= shift

    # Check if we've run past the end
    if self.position['filters'][self.dimension['name']] < 0 \
        or self.position['filters'][self.dimension['name']] >= \
        self.numFilterOutputs[self.dimension['name']]:
      if self.dimension['wraparound']:
        # Wrap around
        if self.position['filters'][self.dimension['name']] < 0:
          self.position['filters'][self.dimension['name']] = \
            self.numFilterOutputs[self.dimension['name']] - 1
        else:
          self.position['filters'][self.dimension['name']] = 0
      else:
        # End the sweep
        self.position['reset'] = True

    # Check if we've reached the start position
    if not self.position['reset'] and self.dimension['wraparound'] and \
        self.start and self.position == self.start:
      self.position['reset'] = True

    if not self.position['reset']:
      # Move the offset if the image changed size
      newImageSize = self.getFilteredImages()[0].size
      if newImageSize != self.prevImageSize:
        x, y = self.position['offset']
        x += self.enabledWidth / 2
        y += self.enabledHeight / 2
        x = int(x * newImageSize[0] / float(self.prevImageSize[0]))
        y = int(y * newImageSize[1] / float(self.prevImageSize[1]))
        x -= self.enabledWidth / 2
        y -= self.enabledHeight / 2
        self.position['offset'] = [x,y]
        self.prevImageSize = newImageSize

    if not self.position['reset'] \
        and self.isBlank(self.dimension['sweepOffObject']):
      self.position['reset'] = True

  def _getEffectiveBoundingBox(self, image):
    """
    Calculate the 'effective' bounding box from the image's bounding box,
    taking into account the sweepOffObject parameter.

    The effective bounding box determines which offsets the explorer should
    consider. If 'ebbox' is the bounding box returned from this method, valid
    offsets [x,y] are bounded by:
      ebbox[0] <= x < ebbox[2]
      ebbox[1] <= y < ebbox[3].
    """

    bbox = image.split()[1].getbbox()
    if self.dimension['sweepOffObject']:
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

  def _calculateProbabilities(self):
    """
    Update the probabilities for each dimension.
    """

    cumulativeProbability = 0.0
    numWithoutProbability = 0
    for d in self.dimensions:
      if d['probability'] is not None:
        cumulativeProbability += d['probability']
      else:
        numWithoutProbability += 1
    if numWithoutProbability:
      if cumulativeProbability >= 1:
        raise RuntimeError('Sum of probabilities >= 1, but some dimensions '
          'have not been assigned a probability')
      # Assign remaining probability among other dimensions
      for d in self.dimensions:
        if d['probability'] is None:
          d['probability'] = \
            max(0.0, 1 - cumulativeProbability) / numWithoutProbability

  def _copyPosition(self, position):
    """
    Return a copy of the current position. Faster than copy.deepcopy.
    """

    return {
      'image': position['image'],
      'filters': copy.copy(position['filters']),
      'offset': copy.copy(position['offset']),
      'reset': position['reset']
    }
