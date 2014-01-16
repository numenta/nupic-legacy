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


class RandomEyeMovements(BaseExplorer):

  """
  This explorer flashes each image nine times, shifted by one pixel each time,
  simulating "eye movements". On each iteration, it randomly picks an image,
  randomly picks a filtered version of the image, and then randomly picks one
  of the nine positions.
  """

  def __init__(self, shift=1, replacement=True, *args, **kwargs):
    """
    shift -- Number of pixels to move from the center ("radius" of the eye
      movement square).
    replacement -- Whether the same image/position can be picked twice.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    self.shift = shift
    self.replacement = replacement

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

    if not self.numImages:
      return

    if not self.replacement \
        and len(self.history) == self.getNumIterations(None):
      # All images have been visited
      self.history = []

    while True:
      self.position['image'] = self.pickRandomImage(self.random)
      self.position['filters'] = self.pickRandomFilters(self.random)
      index = self.random.randint(0, 8)
      historyItem = (self.position['image'], self.position['filters'][:], index)
      if self.replacement or historyItem not in self.history:
        # Use this position
        if not self.replacement:
          # Add to the history
          self.history.append(historyItem)
        # Calculate the offset from the eye movement index
        if index in (1, 2, 3):
          self.position['offset'][1] -= self.shift
        elif index in (5, 6, 7):
          self.position['offset'][1] += self.shift
        if index in (1, 7, 8):
          self.position['offset'][0] -= self.shift
        elif index in (3, 4, 5):
          self.position['offset'][0] += self.shift
        break

    self.position['reset'] = True

  def next(self, seeking=False):
    """
    Go to the next position (next iteration).

    seeking -- Boolean that indicates whether the explorer is calling next()
      from seek(). If True, the explorer should avoid unnecessary computation
      that would not affect the seek command. The last call to next() from
      seek() will be with seeking=False.
    """

    self.first()

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    image -- If None, returns the sum of the iterations for all the
      loaded images. Otherwise, image should be an integer specifying the
      image for which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if self.replacement:
      raise RuntimeError("RandomEyeMovements only supports getNumIterations() "
        "when 'replacement' is False.")
    else:
      if image is not None:
        return self.numFilteredVersionsPerImage * 9
      else:
        return self.numFilteredVersionsPerImage * 9 * self.numImages
