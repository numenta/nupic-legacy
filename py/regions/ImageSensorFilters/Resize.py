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

from PIL import Image

from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Resize(BaseFilter):

  """
  Create resized versions of the original image, using various methods of
  padding and stretching.
  """

  def __init__(self,
               size=None,
               sizes=None,
               method='fit',
               simultaneous=False,
               highQuality=False):
    """
    size -- Target size. Either a tuple (width, height), specifying an
      absolute size in pixels, or a single value, specifying a scale factor
      to apply to the current size.
    sizes -- List of target sizes, for creating multiple output images
      for each input image. Each entry in the list must satisfy the
      requirements for the 'size' parameter, above. 'size' and 'sizes'
      may not be used together.
    method -- Method to use for generating new images, one of:
      'fit'     : scale and pad to match new size, preserving aspect ratio
      'crop'    : scale and crop the image to fill the new size
      'stretch' : stretch the image to fill new size, ignoring aspect ratio
      'center'  : center the original image in the new size without scaling
    simultaneous -- Whether the images should be sent out of the sensor
      simultaneously.
    highQuality -- Whether to use high-quality sampling for resizing
      instead of nearest neighbor. If highQuality is True, antialiasing is
      used for downsampling and bicubic interpolation is used for
      upsampling.

    Example usage:

    Resize the incoming image to fit within (320, 240) by scaling so that
    the image fits exactly within (320, 240) but the aspect ratio is
    maintained, and padding with the sensor's background color:
      Resize(size=(320, 240))

    Scale the image to three different sizes: 100% of the original size,
    50% of the original size, and 25% of the original size, and send the
    three images out of the sensor simultaneously as multiple scales:
      Resize(sizes=(1.0, 0.5, 0.25), simultaneous=True)

    Pad the image to fit in a larger image of size (640, 480), centering it
    in the new image:
      Resize(size=(640, 480), method='center')
    """

    BaseFilter.__init__(self)

    if (not size and not sizes) or (size and sizes):
      raise RuntimeError("Must specify either 'size' or 'sizes'")

    if size:
      sizes = [size]

    if type(sizes) not in (list, tuple):
      raise ValueError("Sizes must be a list or tuple")

    if type(sizes) is tuple:
      sizes = list(sizes)

    for i, size in enumerate(sizes):
      if type(size) in (list, tuple):
        if len(size) > 2:
          raise ValueError("Size is too long (must be a scalar or 2-tuple)")
      elif type(size) in (int, float):
        if size <= 0:
          raise ValueError("Sizes must be positive numbers")
        sizes[i] = [size]
      else:
        raise TypeError("Sizes must be positive numbers")

    if method not in ('fit', 'crop', 'stretch', 'center'):
      raise ValueError("Unknown method "
                       "(options are 'fit', 'crop', 'stretch', and 'center')")

    self.sizes = sizes
    self.method = method
    self.simultaneous = simultaneous
    self.highQuality = highQuality

  def process(self, image):
    """
    @param image -- The image to process.

    Returns a single image, or a list containing one or more images.
    """

    BaseFilter.process(self, image)

    sizes = []
    for i, size in enumerate(self.sizes):
      if len(size) == 1:
        # Convert scalar sizes to absolute sizes in pixels
        sizes.append((int(round(image.size[0]*float(size[0]))),
                      int(round(image.size[1]*float(size[0])))))
      else:
        sizes.append((int(size[0]), int(size[1])))

    newImages = []
    for size in sizes:
      if image.size == size:
        newImage = image

      elif self.method == 'fit':
        # Resize the image to fit in the target size, preserving aspect ratio
        targetRatio = size[0] / float(size[1])
        imageRatio = image.size[0] / float(image.size[1])
        if imageRatio > targetRatio:
          xSize = size[0]
          scale = size[0] / float(image.size[0])
          ySize = int(scale * image.size[1])
        else:
          ySize = size[1]
          scale = size[1] / float(image.size[1])
          xSize = int(scale * image.size[0])
        newImage = self._resize(image, (xSize, ySize))
        # Pad with the background color if necessary
        if newImage.size != size:
          paddedImage = Image.new('LA', size, self.background)
          paddedImage.paste(newImage,
                           ((size[0] - newImage.size[0])/2,
                            (size[1] - newImage.size[1])/2))
          newImage = paddedImage

      elif self.method == 'crop':
        # Resize the image to fill the new size
        targetRatio = size[0] / float(size[1])
        imageRatio = image.size[0] / float(image.size[1])
        if imageRatio > targetRatio:
          # Original image is too wide
          scale = size[1] / float(image.size[1])
          newSize = (int(scale * image.size[0]), size[1])
          cropStart = ((newSize[0] - size[0]) / 2, 0)
        else:
          # Original image is too tall
          scale = size[0] / float(image.size[0])
          newSize = (size[0], int(scale * image.size[1]))
          cropStart = (0, (newSize[1] - size[1]) / 2)

        newImage = self._resize(image, newSize)
        # Crop if necessary
        if newSize != size:
          newImage = newImage.crop((cropStart[0], cropStart[1],
            cropStart[0] + size[0], cropStart[1] + size[1]))

      elif self.method == 'stretch':
        # Resize the image to each target size, ignoring aspect ratio
        newImage = self._resize(image, size)

      elif self.method == 'center':
        # Center the original image in the new image without rescaling it
        newImage = Image.new('LA', size, self.background)
        x = (size[0] - image.size[0]) / 2
        y = (size[1] - image.size[1]) / 2
        newImage.paste(image, (x, y))

      newImages.append(newImage)

    if not self.simultaneous:
      if len(newImages) == 1:
        return newImages[0]
      else:
        return newImages
    else:
      return [newImages]

  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (outputCount, simultaneousOutputCount).
    """

    if not self.simultaneous:
      return len(self.sizes)
    else:
      return 1, len(self.sizes)

  def _resize(self, image, size):
    """
    Resize the image with the appropriate sampling method.
    """

    if self.highQuality:
      if size < image.size:
        return image.resize(size, Image.ANTIALIAS)
      else:
        return image.resize(size, Image.BICUBIC)
    else:
      return image.resize(size)
