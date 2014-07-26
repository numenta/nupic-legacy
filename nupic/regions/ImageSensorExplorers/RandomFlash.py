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


class RandomFlash(BaseExplorer):

  """
  This explorer flashes each filtered image without sweeping, selecting images
  randomly.

  It centers each image, but does not resize them. If an image is larger
  than the sensor's size, only the center portion of it will be visible.

  Use this explorer for flash inference or any other time you want your
  images to be shown in random order with no sweeping.

  This explorer does not use reset signals.
  """

  def __init__(self, replacement=True, start=0,
                     equalizeCategories=False,
                      *args, **kwargs):
    """
    replacement -- Whether the same image can be picked multiple times.
    start -- Number of random choices to skip at the beginning, useful
      when seeding the random number generator.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    if type(replacement) not in (bool, int):
      raise RuntimeError("'replacement' should be a boolean")
    if type(start) is not int:
      raise RuntimeError("'start' should be an integer")

    self.replacement = replacement
    self.start = start
    self.equalizeCategories = equalizeCategories
    self.imagesByCat = None

    if not self.replacement:
      self.history = []

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

    # Zero out the history when seeking to iteration 0. This so we can replicate
    #  how random explorers behave in the vision framework and NVT.
    if iteration is not None and iteration == 0:
      if not self.replacement:
        self.history = []
    BaseExplorer.seek(self, iteration=iteration, position=position)


  def first(self, seeking=False):
    """
    Set up the position.

    BaseExplorer picks image 0, offset (0,0), etc., but explorers that wish
    to set a different first position should extend this method. Such explorers
    may wish to call BaseExplorer.first(center=False), which initializes the
    position tuple but does not call centerImage() (which could cause
    unnecessary filtering to occur).

    seeking -- Passed from seek() through next() to avoid loading images
      unnecessarily when seeking.
    """

    BaseExplorer.first(self, center=False)

    if not self.numImages:
      return

    if not self.replacement \
        and len(self.history) == self.getNumIterations(None):
      # All images have been visited
      self.history = []

    if self.equalizeCategories:
      # Breakdown the images by category
      if self.imagesByCat is None:
        categoryIndex = []
        for k in range(self.numImages):
          categoryIndex += [self.getImageInfo(k)['categoryIndex']]
        categories = list(set(categoryIndex))
        numCats = len(categories)

        catPopulation = {}
        imagesByCat = {}
        for catIndex in categories:
          #catPopulation[catIndex] = len([c for c in categoryIndex if c == catIndex])
          imagesByCat[catIndex] = [k for k, c in enumerate(categoryIndex) if c == catIndex]
          catPopulation[catIndex] = len(imagesByCat[catIndex])
        minNumSamples = min([pop for (cat, pop) in catPopulation.items()])
        totalNumSamples = minNumSamples * numCats
        # Store
        self.imagesByCat = imagesByCat
        self.categories = categories
        self.numCategories = numCats
        self.nextCatIndex = 0

      # Pick random image from next category
      thisCat = self.imagesByCat[self.nextCatIndex]
      #randomImageIndex = random.randint(0, len(thisCat))
      self.position['image'] = self.random.choice(thisCat)
      self.position['filters'] = self.pickRandomFilters(self.random)
      self.nextCatIndex = (self.nextCatIndex + 1) % self.numCategories

    else:
      # Pick a random image and set of filters
      while self.start >= 0:

        finished = False
        while not finished:
          # Pick a position randomly
          self.position['image'] = self.pickRandomImage(self.random)
          self.position['filters'] = self.pickRandomFilters(self.random)
          # Pick again if not replacing and this position has been visited
          if self.replacement or (self.position['image'],
              self.position['filters']) not in self.history:
            finished = True

        if not self.replacement:
          # Remember this position
          self.history.append(
            (self.position['image'], self.position['filters'][:]))

        self.start -= 1

      self.start = 0

    if not seeking:
      self.centerImage()

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    self.first(seeking)

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if self.replacement:
      raise RuntimeError("RandomFlash only supports getNumIterations() when "
        "'replacement' is False.")
    else:
      if image is None:
        return self.numFilteredVersionsPerImage * self.numImages
      else:
        return self.numFilteredVersionsPerImage
