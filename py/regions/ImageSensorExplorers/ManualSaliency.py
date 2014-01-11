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
import cPickle as pickle

from nupic.regions.ImageSensorExplorers.BaseExplorer import BaseExplorer


class ManualSaliency(BaseExplorer):

  """
  The ManualSaliency explorer loads manually created fixation points from a
  file and moves the sensor to those locations.
  """

  def __init__(self, filename, *args, **kwargs):
    """
    filename -- Path to the file with the pickled dictionary mapping image
      filenames to fixation points.
    """

    BaseExplorer.__init__(self, *args, **kwargs)

    # Load the fixation points
    self.points = pickle.load(open(filename))
    self.pointIndex = None
    self.currentPoints = None

    # Retain just the enclosing directory and filename, not the full path
    self.doSaliencySize = True
    keys = self.points.keys()
    for key in keys:
      path, filename = os.path.split(key)
      key2 = os.path.join(os.path.split(path)[1], filename)
      if key2 != key:
        self.points[key2] = self.points[key]
        self.points.pop(key)
      if 'saliencySize' not in self.points[key2]:
        self.doSaliencySize = False

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

    # Set up the list of filenames
    self.names = []
    for i in xrange(self.numImages):
      path, filename = os.path.split(self.getImageInfo(i)['imagePath'])
      name = os.path.join(os.path.split(path)[1], filename)
      self.names.append(name)

    # Find the first image with some fixation points
    image = 0
    while not self.names[image] in self.points:
      # No fixation points for this image
      image += 1
      if image >= self.numImages:
        raise RuntimeError("No fixation points for any loaded images")
    self.position['image'] = image
    self._firstPoint()
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

    if self.pointIndex is None:
      self.first()

    self.pointIndex += 1
    if self.pointIndex < len(self.currentPoints):
      # Next fixation point for this image
      self._setOffset()
    else:
      # Ran out of points for this image
      image = self.position['image'] + 1
      if image >= self.numImages:
        self.first()
        return
      while not self.names[image] in self.points:
        image += 1
        if image >= self.numImages:
          self.first()
          return
      self.position['image'] = image
      self._firstPoint()

  def getNumIterations(self, image):
    """
    Get the number of iterations required to completely explore the input space.

    Explorers that do not wish to support this method should not override it.

    image -- If None, returns the sum of the iterations for all the loaded
      images. Otherwise, image should be an integer specifying the image for
      which to calculate iterations.

    ImageSensor takes care of the input validation.
    """

    if image is None:
      if self.doSaliencySize:
        return sum([len(self.points[p]['saliencyPoints']) for p in self.points])
      else:
        return sum([len(self.points[p]['points']) for p in self.points])
    else:
      if self.names[image] in self.points:
        return len(self.points[self.names[image]])
      else:
        return 0

  def _firstPoint(self):
    """Go to the first fixation point for the current image."""

    self.pointIndex = 0
    if self.doSaliencySize:
      self.currentPoints = \
        self.points[self.names[self.position['image']]]['saliencyPoints']
      self.currentSaliencySizes = \
        self.points[self.names[self.position['image']]]['saliencySize']
    else:
      self.currentPoints = \
        self.points[self.names[self.position['image']]]['points']
    self.currentImageSize = \
      self.points[self.names[self.position['image']]]['imageSize']
    currImg = self.getFilteredImages()[0]
    self.bbox = currImg.split()[1].getbbox()
    self._setOffset()

  def _setOffset(self):
    """
    Set the offset based on the current fixation point, accounting for the
    sensor's enabled size.
    """

    width = self.bbox[2] - self.bbox[0]
    height = self.bbox[3] - self.bbox[1]
    # This option is for backward compatibility
    self.scale = not self.doSaliencySize
    if self.scale:
      xOffset = self.bbox[0] + self.currentPoints[self.pointIndex][0] \
                  * width/self.currentImageSize[0] - self.enabledWidth / 2
      yOffset = self.bbox[1] + self.currentPoints[self.pointIndex][1] \
                  * height/self.currentImageSize[1] - self.enabledHeight / 2
      if self.doSaliencySize:
        self.position['saliencySize'] = (self.currentSaliencySizes[self.pointIndex][0] \
                                              * width/self.currentImageSize[0],
                                      self.currentSaliencySizes[self.pointIndex][1] \
                                              * height/self.currentImageSize[1])
        # from dbgp.client import brk ; brk()
    else:
      xOffset = self.bbox[0] + self.currentPoints[self.pointIndex][0] \
                  - self.currentSaliencySizes[self.pointIndex][0]
      yOffset = self.bbox[1] + self.currentPoints[self.pointIndex][1] \
                  - self.currentSaliencySizes[self.pointIndex][1]
      if self.doSaliencySize:
        self.position['saliencySize'] = self.currentSaliencySizes[self.pointIndex]
    self.position['offset'] = [xOffset, yOffset]
