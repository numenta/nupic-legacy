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
import sys
import random

sys_maxint = sys.maxint

def uint(i):
  """Helper function to convert values to accepted range for PIL

  See: http://www.joachimschipper.nl/SystemError%20when%20using%20PIL

  I modified the function a little to be more efficient and use
  a sys_maxint global variable instead of looking up sys.maxint
  every time.
  """
  i = int(i)
  if sys_maxint < i <= 2 * sys_maxint + 1:
    return int((i & sys_maxint) - sys_maxint - 1)
  else:
    return i


class BaseFilter(object):
  # Save the lookup on the sys.maxint because it will be called a LOT

  def __init__(self, seed=None, reproducible=False):
    """
    seed -- Seed for the random number generator. A specific random number
      generator instance is always created for each filter, so that they do
      not affect each other.
    reproducible -- Seed the random number generator with a hash of the image
      pixels on each call to process(), in order to ensure that the filter
      always generates the same output for a particular input image.
    """

    if seed is not None and reproducible:
      raise RuntimeError("Cannot use 'seed' and 'reproducible' together")

    self.random = random.Random()
    if seed is not None:
      self.random.seed(seed)

    self.reproducible = reproducible

    self.mode = 'gray'
    self.background = 0

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    Post filtersIt can also return an additional raw output numpy array
    that will be used as the output of the ImageSensor
    """

    if self.reproducible:
      # Seed the random instance with a hash of the image pixels
      self.random.seed(hash(image.tostring()))

  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (outputCount, simultaneousOutputCount).
    """

    return 1

  def update(self, mode=None, background=None):
    """
    Accept new parameters from ImageSensor and update state.
    """

    if mode is not None:
      self.mode = mode

    if background is not None:
      self.background = background
