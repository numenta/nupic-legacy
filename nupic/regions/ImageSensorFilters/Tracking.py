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
import random

import numpy
from PIL import Image
from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class Tracking(BaseFilter):

  """
  Create resized versions of the original image, using various methods of
  padding and stretching.
  """

  def __init__(self,
               targetDims,
               padding=0,
               scales=None,
               fillValue=0,
               fillFromImageWherePossible=True,
               preservationMode=None,
               qualityLevel='antialias',
               dumpDebugImages=False,
               applyAlpha=True):
    """
    @param qualityLevel -- specifies the quality of the filter to be used
          for resizing image patches; must be one of:
            'nearest', 'bilinear', 'bicubic', 'antialias'
          (in increasing order of quality)
    @param applyAlpha -- if True, we'll "apply" the alpha channel to the image
          before flattening it (from 'LA' to 'L').  This allows you to pass in
          images that are non-rectangular.  If False, the alpha channel will
          just be used to figure out the bounding box of the object (unless
          a tracking box is passed in, in which case alpha is ignored).
          Note: this is only useful if fillFromImageWherePossible=False
    """

    BaseFilter.__init__(self)

    # Apply default for scales
    if scales is None:
      scales = [1.0]

    if type(scales) not in (list, tuple):
      raise ValueError("'scales' must be a list or tuple")
    if type(scales) is tuple:
      scales = list(scales)

    self._applyAlpha = applyAlpha
    self._targetDims = targetDims
    self._padding = padding
    self._scales = scales
    self._fillValue = fillValue
    self._fillFromImageWherePossible = fillFromImageWherePossible
    self._preservationMode = preservationMode
    self._resizingFilter = eval("Image.%s" % qualityLevel.upper())
    self._dumpDebugImages = dumpDebugImages
    if fillValue is None:
      self._histWeights = numpy.array(range(256), dtype='float')

  def process(self, image):
    """
    Performs the following operations:
    1. Locates the original bounding box of the image as defined by the
       image's alpha mask.  It is assumed that the alpha mask will consist
       of a single rectangular, in which case the resulting bbox will
       be exactly equivalent to the mask representation.  However, if for
       some reason the positive regions of the alpha mask is not a single
       rectangle, things will still work.
    2. Fit the bounding box to the target dimensions, scaling as needed,
       and filling in padding regions if needed (if the aspect ratio of
       the bounding box does not match that of the target dimensions
       which, in general, will be True.)  If padding is needed, we fill
       from the original image pixels around the bounding box if
       fillFromImageWherePossible is True and we're not outside the original
       image bounds, otherwise, we use 'fillValue'.
    3. Apply each scale in 'scales' to the resulting cropped image, and
       pad each side by 'padding' (pulling from the real image pixels
       when possible, and filling with 'fillValue' where not.)
    4. Return the list of cropped images.
    """

    BaseFilter.process(self, image)

    assert image.mode == "LA"

    # Pull bbox of the alpha mask
    if 'tracking' in image.info:
      bbox = image.info['tracking']
      if type(bbox) == type(""):
        bbox = eval(bbox)
    else:
      bbox = image.split()[1].getbbox()
    # If alpha channel is completely empty, we will end up
    # with a bbox of 'None'.  Nothing much we can do
    if bbox is None:
      bbox = (0, 0, image.size[0], image.size[1])
      print 'WARNING: empty alpha channel'

    # Check for malformed box
    elif bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
      bbox = (0, 0, image.size[0], image.size[1])
      print 'WARNING: malformed box'

    # Ascertain the original raw size of the tracking box
    width  = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]

    if self._fillValue is None:
      [gray, alpha] = image.split()
      hist = numpy.array(gray.histogram(alpha), dtype='float')
      mean = (hist * self._histWeights).sum() / hist.sum()
      if mean < 127.5:
        fillValue = 255
      else:
        fillValue = 0
    elif isinstance(self._fillValue, int):
      fillValue = self._fillValue
    else:
      fillValue = self._fillValue[random.randint(0, len(self._fillValue)-1)]

    # If we're not going to fill from the rest of the image, we should
    # apply the alpha from the original image directly.  If the original alpha
    # was a square bounding box, this won't hurt (since we're not filling from
    # the image).  If it was a tight mask, this will prevent it from reverting
    # back to a square mask.
    if (self._applyAlpha) and (not self._fillFromImageWherePossible):
      grayImage, alphaImage = image.split()
      image = Image.new('L', size=image.size, color=fillValue)
      image.paste(grayImage, alphaImage)

    newImages = []
    for scaleIdx, scale in enumerate(self._scales):

      # Target dimensions depend on the scale at which we're operating
      targetDims = (self._targetDims[0] * scale,
                    self._targetDims[1] * scale)

      scaleFactorX = float(targetDims[0]) / float(width)
      scaleFactorY = float(targetDims[1]) / float(height)

      # Determine the scaling factors needed to map the
      # bounding box to the target dimensions (prior to
      # padding be accounted for)
      if self._preservationMode is None:
        pass
      elif self._preservationMode == "aspect":
        scaleFactor = min(scaleFactorX, scaleFactorY)
        scaleFactorX = scaleFactor
        scaleFactorY = scaleFactor
      else:
        assert self._preservationMode == "size"
        scaleFactorX = scale
        scaleFactorY = scale

      # Now, holding the scaling factor constant, compute the
      # size of the src box in the original image that will
      # produce the correctly padded target size
      targetWidth  = int(round(targetDims[0])) + 2*self._padding
      targetHeight = int(round(targetDims[1])) + 2*self._padding
      srcWidth  = float(targetWidth)  / scaleFactorX
      srcHeight = float(targetHeight) / scaleFactorY

      # Compute the exact coordinates of the source box
      if self._fillFromImageWherePossible:
        origCenterX = float(bbox[0] + bbox[2]) * 0.5
        origCenterY = float(bbox[1] + bbox[3]) * 0.5
        halfWidth  = srcWidth  * 0.5
        halfHeight = srcHeight * 0.5
        srcBox = (int(round(origCenterX - halfWidth)),
                  int(round(origCenterY - halfHeight)),
                  int(round(origCenterX + halfWidth)),
                  int(round(origCenterY + halfHeight)))

        # take into account clipping off the image boundary
        clipBox = (max(srcBox[0], 0),
                   max(srcBox[1], 0),
                   min(srcBox[2], image.size[0]),
                   min(srcBox[3], image.size[1]))
        #clipOffset = (clipBox[0] - srcBox[0],
        #              clipBox[1] - srcBox[1])

      else:
        # extend the bbox to include padding pixels on all sides
        paddedBBox = (int(bbox[0] - self._padding/scaleFactorX),
                      int(bbox[1] - self._padding/scaleFactorY),
                      int(bbox[2] + self._padding/scaleFactorX),
                      int(bbox[3] + self._padding/scaleFactorY))

        # take into account clipping off the image boundary
        clipBox = (max(paddedBBox[0], 0),
                   max(paddedBBox[1], 0),
                   min(paddedBBox[2], image.size[0]),
                   min(paddedBBox[3], image.size[1]))

        # The srcBox is the correct aspect ratio, and either taller or wider than the
        # bbox, but not both.
        srcBox = (0, 0, srcWidth, srcHeight)
        clipBoxWidth = clipBox[2] - clipBox[0]
        clipBoxHeight = clipBox[3] - clipBox[1]
        #clipOffset = (int((srcWidth - clipBoxWidth)/2),
        #              int((srcHeight - clipBoxHeight)/2))

      # Copy the source rect
      croppedImage = image.crop(clipBox)
      croppedImage.load()

      # New development
      croppedImage.putalpha(Image.new(mode='L', size=croppedImage.size, color=255))

      # Scale the cropped image.  At last one dimension of this cropped image
      # should be the target size.
      xFactor = float(targetWidth) / croppedImage.size[0]
      yFactor = float(targetHeight) / croppedImage.size[1]
      scaleFactor = min(xFactor, yFactor)
      if scaleFactor >= 1:
        resizingFilter = Image.BICUBIC
      else:
        resizingFilter = Image.ANTIALIAS
      scaledImage = croppedImage.resize((int(round(scaleFactor * croppedImage.size[0])),
                                         int(round(scaleFactor * croppedImage.size[1]))),
                                        resizingFilter)
      clipOffset = (int((targetWidth - scaledImage.size[0]) / 2),
                    int((targetHeight - scaledImage.size[1]) / 2))



      # Paste into a new image
      newImage = Image.new(mode='LA', size=(targetWidth, targetHeight), color=fillValue)
      newImage.paste(scaledImage, clipOffset)

      # Resize the cropped image to the (padded) target size

      # Convert and save the scaled image as the output
      assert newImage.mode == 'LA'
      newImages += [newImage]

      # Dump debugging images to disk
      if self._dumpDebugImages:
        self._handleDebug(newImage, scaleIdx)

    return [newImages]


  def _handleDebug(self, image, scaleIdx, debugDir="tracking.d"):
    """
    Dump tracking boxes to disk for offline analysis
    """
    if not hasattr(self, "_debugIndex"):
      self._debugIndex = 0
    if not os.path.isdir(debugDir):
      os.mkdir(debugDir)
    debugPath = os.path.join(debugDir, "tracking.%06d.%02d.png" % \
                (self._debugIndex, scaleIdx))
    image.save(debugPath)
    self._debugIndex += 1


  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (outputCount, simultaneousOutputCount).
    """
    return 1, len(self._scales)
