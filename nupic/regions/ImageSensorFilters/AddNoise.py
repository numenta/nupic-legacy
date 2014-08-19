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

import numpy
from PIL import Image

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class AddNoise(BaseFilter):

  """
  Add noise to the image.
  """

  def __init__(self, noiseLevel=0.0, doForeground=True, doBackground=False,
               dynamic=True, noiseThickness=1):
    """
    noiseLevel -- Amount of noise to add, from 0 to 1.0. For black and white
      images, this means the values of noiseLevel fraction of the pixels will
      be flipped (e.g. noiseLevel of 0.2 flips 20 percent of the pixels). For
      grayscale images, each pixel will be modified by up to 255 * noiseLevel
      (either upwards or downwards).
    doForeground -- Whether to add noise to the foreground. For black and white
      images, black pixels are foreground and white pixels are background. For
      grayscale images, any pixel which does not equal the background color
      (the ImageSensor 'background' parameter) is foreground, and the rest is
      background.
    doBackground -- Whether to add noise to the background (see above).
    """

    BaseFilter.__init__(self)

    self.noiseLevel = noiseLevel
    self.doForeground = doForeground
    self.doBackground = doBackground
    self.dynamic = dynamic
    self.noiseThickness = noiseThickness

    # Generate and save our random state
    saveState = numpy.random.get_state()
    numpy.random.seed(0)
    self._randomState = numpy.random.get_state()
    numpy.random.set_state(saveState)

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """
    # Get our random state back
    saveState = numpy.random.get_state()
    numpy.random.set_state(self._randomState)

    # Send through parent class first
    BaseFilter.process(self, image)

    alpha = image.split()[1]
    # -----------------------------------------------------------------------
    # black and white
    if self.mode == 'bw':
      # For black and white images, our doBackground pixels are 255 and our figure pixels
      #  are 0.
      assert self.noiseThickness != 0, "ImageSensor parameter noiseThickness cannot be 0"
      pixels = numpy.array(image.split()[0].getdata(), dtype=int)
      (imgWidth,imgHeight) = image.size
      pixels2d = (numpy.array(pixels)).reshape(imgHeight, imgWidth)
      noiseArrayW = numpy.floor(imgWidth/float(self.noiseThickness))
      noiseArrayH = numpy.floor(imgHeight/float(self.noiseThickness))
      thickNoise = numpy.random.random((noiseArrayH, noiseArrayW))
      thickNoise = 255*(thickNoise < self.noiseLevel)
      idxW = numpy.array([int(self.noiseThickness*i) for i in xrange(noiseArrayW)])
      idxH = numpy.array([int(self.noiseThickness*i) for i in xrange(noiseArrayH)])
      for nt1 in xrange(self.noiseThickness):
        for nt2 in xrange(self.noiseThickness):
          submatIdx = numpy.ix_(idxH + nt1, idxW + nt2)
          if self.doForeground and self.doBackground:
            pixels2d[submatIdx] ^= thickNoise
          elif self.doForeground:
            pixels2d[submatIdx] = (pixels2d[submatIdx]^thickNoise) | pixels2d[submatIdx]
          elif self.doBackground:
            pixels2d[submatIdx] = (pixels2d[submatIdx]^thickNoise) & pixels2d[submatIdx]
        pixels2d = numpy.abs(pixels2d)
        pixels = pixels2d.reshape(1,imgWidth*imgHeight)[0]

    # -----------------------------------------------------------------------
    # gray-scale
    elif self.mode == 'gray':
      pixels = numpy.array(image.split()[0].getdata(), dtype=int)
      noise = numpy.random.random(len(pixels))  # get array of floats from 0 to 1

      # Add +/- self.noiseLevel to each pixel
      noise = (noise - 0.5) * 2 * self.noiseLevel * 255
      mask = numpy.array(alpha.getdata(), dtype=int) != self.background
      if self.doForeground and self.doBackground:
        pixels += noise
      elif self.doForeground:
        pixels[mask!=0] += noise[mask!=0]
      elif self.doBackground:
        pixels[mask==0] += noise[mask==0]
      pixels = pixels.clip(min=0, max=255)

    else:
      raise ValueError("This image mode not supported")

    # write out the new pixels
    #from dbgp.client import brk; brk(port=9049)
    newimage = Image.new(image.mode, image.size)

    #newimage.putdata([uint(p) for p in pixels])
    newimage.putdata(pixels.tolist())
    newimage.putalpha(alpha)

    # If generating dynamic noise, change our random state each time.
    if self.dynamic:
      self._randomState = numpy.random.get_state()

    # Restore random state
    numpy.random.set_state(saveState)

    return newimage
