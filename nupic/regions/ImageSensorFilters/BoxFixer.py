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

import numpy
from PIL import Image
from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter


class BoxFixer(BaseFilter):

  """
  Does not modify any image pixels, just adjusts the
  tracking box to defeat hard shadows, etc., and in
  general to normalize the box with respect to the
  SMotion map between truth and tracker-generated boxes.
  """

  def __init__(self,
          #--------------------------------------------------
          # General parameters
          #
          # Width (in pixels) of smooth window for horizontal
          # SMotion strength histogram
          windowX=9,
          # Height (in pixels) of smooth window for vertical
          # SMotion strength histogram
          windowY=9,
          # Smooth window type; must be one of: 'flat', 'hanning',
          # 'hamming', 'bartlett', 'blackman'
          windowType='hanning',

          #--------------------------------------------------
          # Horizontal tightening/splitting parameters
          #
          # Minimum smoothed SMotion strength (summed vertically)
          # for an X position to be considered "strong" (expressed as
          # a fraction of the maximum vertically-summed SMotion)
          heightThresh=0.1,
          # Minimum peak SMotion strength for a secondary lobe
          # (i.e., not the strongest "primary" lobe) to avoid
          # being culled
          secondaryHeightThresh=0.5,
          # Minimum absolute horizontal length (in pixels) that a
          # horizontal strong zone must extend to avoid being
          # culled
          minAbsZoneLenX=5,
          # Minimum relative horizontal length (expressed as a
          # fraction of the total original box width) that a
          # horizontal strong zone must extend to avoid being
          # culled
          minRelZoneLenX=0.15,
          # Minimum horizontal "gap" width (in terms of absolute
          # pixels) which a weak zone must extend to avoid
          # being filled in (if it lies between two strong zones)
          minAbsWeakLenX=5,
          # Minimum horizontal "gap" width (as percentage of the
          # image width) which a weak zone must extend to avoid
          # being filled in (if it lies between two strong zones)
          minRelWeakLenX=0.10,
          # The number of pixels to expand our accepted zones
          # horizontally prior to tightening/splitting
          zonePreExpansionX=16, #8, #0, #8,
          # The number of pixels to expand our accepted zones
          # norizontally following tightening/splitting
          zonePostExpansionX=4, #0, #4,

          #--------------------------------------------------
          # Vertical tightening/splitting parameters
          #
          # Minimum smoothed SMotion strength (summed horizontally)
          # for a Y position to be considered "strong" (expressed as
          # a fraction of the maximum horizontally-summed SMotion)
          widthThresh=0.1,
          # Minimum peak SMotion strength for a secondary lobe
          # (i.e., not the strongest "primary" lobe) to avoid
          # being culled
          secondaryWidthThresh=0.20,
          # Minimum absolute vertical length (in pixels) that a
          # vertical strong zone must extend to avoid being
          # culled
          minAbsZoneLenY=5,
          # Minimum relative vertical length (expressed as a
          # fraction of the total original box height) that a
          # vertical strong zone must extend to avoid being
          # culled
          minRelZoneLenY=0.15,
          # Minimum vertical "gap" width (in terms of absolute
          # pixels) which a weak zone must extend to avoid
          # being filled in (if it lies between two strong zones)
          minAbsWeakLenY=5,
          # Minimum vertical "gap" width (as percentage of the
          # image height) which a weak zone must extend to avoid
          # being filled in (if it lies between two strong zones)
          minRelWeakLenY=0.30,
          # The number of pixels to expand our accepted zones
          # vertically (not yet implemented)
          zonePreExpansionY=16, #8, #0, #8,
          # The number of pixels to expand our accepted zones
          # vertically following tightening/splitting
          zonePostExpansionY=4, #0, #4,

          #---------------------------------
          # Splitting policy
          # Controls what to do if our algorithm wants to split
          # a box.  Valid values are 'union' (take the union of
          # the split pieces) or 'biggest' (use the biggest
          # split box.)
          splitPolicy='biggest',

          #---------------------------------
          # Debugging
          debugMode=False,
          ):
    """
    """

    BaseFilter.__init__(self)

    self._windowX = windowX
    self._windowY = windowY
    self._windowType = windowType
    self._heightThresh = heightThresh
    self._secondaryHeightThresh = secondaryHeightThresh
    self._minAbsZoneLenX = minAbsZoneLenX
    self._minRelZoneLenX = minRelZoneLenX
    self._minAbsWeakLenX = minAbsWeakLenX
    self._minRelWeakLenX = minRelWeakLenX
    self._zonePreExpansionX = zonePreExpansionX
    self._zonePostExpansionX = zonePostExpansionX
    self._widthThresh = widthThresh
    self._secondaryWidthThresh = secondaryWidthThresh
    self._minAbsZoneLenY = minAbsZoneLenY
    self._minRelZoneLenY = minRelZoneLenY
    self._minAbsWeakLenY = minAbsWeakLenY
    self._minRelWeakLenY = minRelWeakLenY
    self._zonePreExpansionY = zonePreExpansionY
    self._zonePostExpansionY = zonePostExpansionY
    self._splitPolicy = splitPolicy
    self._debugMode = debugMode

    # Counts how many images we've processed
    self._imgCounter = 0

    # @todo -- perform parameter validation


  def process(self, image):
    """
    """

    assert image.mode == 'LA'
    smotion, mask = image.split()

    # Try to get box from info, otherwise from alpha channel
    origBox = image.info.get('tracking')
    if not origBox:
      origBox = mask.getbbox()

    expandedBox = (max(0, origBox[0] - self._zonePreExpansionX),
                   max(0, origBox[1] - self._zonePreExpansionY),
                   min(image.size[0], origBox[2] + self._zonePreExpansionX),
                   min(image.size[1], origBox[3] + self._zonePreExpansionY))

    imgbox = smotion.crop(expandedBox)
    #imgbox = smotion.crop(origBox)
    w, h = imgbox.size
    imgdata = numpy.array(imgbox.getdata())
    imgdata.shape = (h, w)

    # Create binary image indicating whether non-zero
    # S-Motion exists
    salpha = (imgdata > 0).astype(int)
    histX = salpha.mean(axis=0)
    smoothX = self._smooth(histX, window_len=self._windowX,
                                  window=self._windowType)

    #-----------------------------------------------------------------------
    # Apply tightening/splitting in horizontal direction

    # Pre-compute the minimum length of a strong
    # zone that we'll accept.
    # This is the max of an absolute length and a
    # minimum fraction of the original box.
    minZoneLen = max(self._minAbsZoneLenX,
                     int(round(self._minRelZoneLenX \
                           * float(len(smoothX)))))
    # Minimum length for a weak gap
    minWeakLen = max(self._minAbsWeakLenX,
                     int(round(self._minRelWeakLenX \
                           * float(len(smoothX)))))

    maxX = smoothX.max()
    # For now, simple threshold
    threshX = self._heightThresh * maxX
    strongX = (smoothX >= threshX).astype(int)

    # Pre-calculate the minimum peak strength for
    # each lobe to avoid being culled
    minStrength = maxX * self._secondaryHeightThresh

    # Find changes:
    # If deltas[k] == 1, then strongX[k+1] is the
    #       beginning of a new strong block;
    # If deltas[k] == -1, then strongX[k+1] is the
    #       beginning of a new weak block
    deltas = strongX[1:] - strongX[:-1]
    changes = numpy.where(deltas)[0]
    # Form our block lists
    strongZonesX = []
    if strongX[0]:
      curZoneStart = 0
    else:
      curZoneStart = None
    for changeIdx in changes:
      strongIdx = changeIdx + 1
      changeDir = deltas[changeIdx]
      # Start of new strong zone
      if changeDir == 1:
        assert curZoneStart is None
        curZoneStart = strongIdx
      # End of existing strong zone
      else:
        assert changeDir == -1
        assert curZoneStart is not None
        strongZone = (curZoneStart, strongIdx)
        self._acceptOrCull(smoothX, strongZonesX, strongZone, minZoneLen, minStrength)
        curZoneStart = None
    # Last one
    if curZoneStart is not None:
      strongZone = (curZoneStart, len(strongX))
      self._acceptOrCull(smoothX, strongZonesX, strongZone, minZoneLen, minStrength)

    # Remove tiny/thin weak gaps
    if len(strongZonesX) > 1:
      tempZones = []
      lastZone = strongZonesX[0]
      for startIdx, endIdx in strongZonesX[1:]:
        if startIdx - lastZone[1] >= minWeakLen:
          tempZones += [lastZone]
          lastZone = (startIdx, endIdx)
        else:
          lastZone = (lastZone[0], endIdx)
      tempZones += [lastZone]
      strongZonesX = tempZones

    #-----------------------------------------------------------------------
    # Apply tightening/splitting in vertical direction (to each strong zone)

    strongZonesAll = []
    for strongZoneX in strongZonesX:

      #histY = salpha.mean(axis=1)
      histY = salpha[:,strongZoneX[0]:strongZoneX[1]].mean(axis=1)
      smoothY = self._smooth(histY, window_len=self._windowY,
                                    window=self._windowType)

      # Pre-compute the minimum length of a strong
      # zone that we'll accept.
      # This is the max of an absolute length and a
      # minimum fraction of the original box.
      minZoneLen = max(self._minAbsZoneLenY,
                       int(round(self._minRelZoneLenY \
                             * float(len(smoothY)))))
      # Minimum length for a weak gap
      minWeakLen = max(self._minAbsWeakLenY,
                       int(round(self._minRelWeakLenY \
                             * float(len(smoothY)))))

      maxY = smoothY.max()
      # For now, simple threshold
      threshY = self._widthThresh * maxY
      strongY = (smoothY >= threshY).astype(int)

      # Pre-calculate the minimum peak strength for
      # each lobe to avoid being culled
      minStrength = maxY * self._secondaryWidthThresh

      # Find changes:
      deltas = strongY[1:] - strongY[:-1]
      changes = numpy.where(deltas)[0]
      # Form our block lists
      strongZonesY = []
      if strongY[0]:
        curZoneStart = 0
      else:
        curZoneStart = None
      for changeIdx in changes:
        strongIdx = changeIdx + 1
        changeDir = deltas[changeIdx]
        # Start of new strong zone
        if changeDir == 1:
          assert curZoneStart is None
          curZoneStart = strongIdx
        # End of existing strong zone
        else:
          assert changeDir == -1
          assert curZoneStart is not None
          strongZoneY = (curZoneStart, strongIdx)
          self._acceptOrCull(smoothY, strongZonesY, strongZoneY, minZoneLen, minStrength)
          curZoneStart = None
      # Last one
      if curZoneStart is not None:
        strongZoneY = (curZoneStart, len(strongY))
        self._acceptOrCull(smoothY, strongZonesY, strongZoneY, minZoneLen, minStrength)

      # Remove tiny/thin weak gaps
      if len(strongZonesY) > 1:
        tempZones = []
        lastZone = strongZonesY[0]
        for startIdx, endIdx in strongZonesY[1:]:
          if startIdx - lastZone[1] >= minWeakLen:
            tempZones += [lastZone]
            lastZone = (startIdx, endIdx)
          else:
            lastZone = (lastZone[0], endIdx)
        tempZones += [lastZone]
        strongZonesY = tempZones

      left, right = strongZoneX
      #strongZonesAll.extend([(left, top, right, bottom) for (top, bottom) in strongZonesY])
      for (top, bottom) in strongZonesY:
        expandedZone = (max(0, left - self._zonePostExpansionX),
                        max(0, top - self._zonePostExpansionY),
                        min(image.size[0], right + self._zonePostExpansionX),
                        min(image.size[1], bottom + self._zonePostExpansionY))
        if expandedZone[2] < expandedZone[0]:
          expandedZone[2] = expandedZone[0]
        if expandedZone[3] < expandedZone[1]:
          expandedZone[3] = expandedZone[1]
        strongZonesAll += [expandedZone]

    if False:
        # Obtain the videoID and sequenceID
        imgDir, imgName = os.path.split(imagePath)
        imgPrefix = os.path.split(imgDir)[1]
        # Example:
        # overlap.0550_sequence10067
        match = re.match(r"^(?P<mnemonic>[a-z]+)\.(?P<videoID>[0-9]{4})_sequence(?P<seqID>\-?[0-9]{1,5})$", imgPrefix)
        if not match:
          match = re.match(r"^vid(?P<videoID>[0-9]{4})_seq(?P<seqID>\-?[0-9]{3,4})$", imgPrefix)
        assert match
        d = match.groupdict()
        videoID = int(d['videoID'])
        seqID = int(d['seqID'])
        key = (videoID, seqID)

    numZones = len(strongZonesAll)

    # Debugging (and inefficient)
    if self._debugMode:
      # Mark up the img box
      blank = Image.new('L', image.size, 0)
      base = smotion.convert('RGB')
      alphaNew = blank.copy()
      alphaOrig = blank.copy()
      alphaOrig.paste(255, origBox)
      #for zoneStart, zoneEnd in strongZones:
      for (left, top, right, bottom) in strongZonesAll:
        zoneBox = (expandedBox[0] + left, expandedBox[1] + top,
                   expandedBox[0] + right, expandedBox[1] + bottom)
        #zoneBox = (origBox[0] + left, origBox[1] + top,
        #           origBox[0] + right, origBox[1] + bottom)
        alphaNew.paste(255, zoneBox)
      blender = Image.merge('RGB', (alphaOrig, alphaNew, blank))
      #blender = Image.merge('RGB', (alphaOrig, blank, alphaNew))
      blendFraction = 0.5
      resultImg = Image.blend(base, blender, blendFraction)

      # Dump marked-up images to disk
      #imgDir, imgName = os.path.split(imagePath)
      #imgPrefix = os.path.split(imgDir)[1]
      dstPath = "%06d.png" % self._imgCounter
      dstName, dstExt = os.path.splitext(dstPath)
      dstName += "__Z%d" % numZones
      dstPath = dstName + dstExt
      resultImg.save(dstPath)

    # Print stats
    #(left, top, right, bottom) = strongZonesAll[0]
    #print "ORIG (%3d, %3d, %3d, %3d) [%3dx%3d] ==> (%3d, %3d, %3d, %3d) [%3dx%3d]" % \
    #       (origBox[0], origBox[1], origBox[2], origBox[3],
    #        origBox[2]-origBox[0], origBox[3]-origBox[1],
    #        left, top, right, bottom, right-left, bottom-top)

    # If there is more than one box, use the biggest
    # (this is just a hack heuristic)
    tightenedZone = None
    if len(strongZonesAll) > 1:
      # Take biggest
      if self._splitPolicy == 'biggest':
        #print "WARNING: multiple (%d) split boxes...choosing biggest one..." % len(strongZonesAll)
        bigBoxIdx = None
        bigBoxArea = -1
        for boxIdx, subBox in enumerate(strongZonesAll):
          area = (subBox[2] - subBox[0]) * (subBox[3] - subBox[1])
          if area > bigBoxArea:
            bigBoxArea = area
            bigBoxIdx = boxIdx
        tightenedZone = strongZonesAll[bigBoxIdx]

      # Take biggest
      elif self._splitPolicy == 'union':
        #print "WARNING: multiple (%d) split boxes...taking union..." % len(strongZonesAll)
        left, top, right, bottom = strongZonesAll[0]
        for boxIdx, subBox in enumerate(strongZonesAll[1:]):
          left   = min(left,   subBox[0])
          top    = min(top,    subBox[1])
          right  = max(right,  subBox[2])
          bottom = max(bottom, subBox[3])
        tightenedZone = (left, top, right, bottom)

    elif not strongZonesAll:
      #print "WARNING: dissipated box...reverting to original..."
      box = origBox

    else:
      assert len(strongZonesAll) == 1
      tightenedZone = strongZonesAll[0]

    if strongZonesAll:
      subBox = tightenedZone
      # 'inference' may be None if box was culled
      box = (expandedBox[0] + subBox[0],
             expandedBox[1] + subBox[1],
             expandedBox[0] + subBox[2],
             expandedBox[1] + subBox[3])

    # Print stats
    (left, top, right, bottom) = box
    #print "%06d: (%3d, %3d, %3d, %3d) [%3dx%3d] ==> (%3d, %3d, %3d, %3d) [%3dx%3d]" % \
    #       (self._imgCounter,
    #        origBox[0], origBox[1], origBox[2], origBox[3],
    #        origBox[2]-origBox[0], origBox[3]-origBox[1],
    #        left, top, right, bottom, right-left, bottom-top)

    alphaNew = Image.new('L', smotion.size, 0)
    alphaNew.paste(255, box)
    dstImage = Image.merge('LA', (smotion, alphaNew))

    dstImage.info['tracking'] = box

    # TEMP TEMP TEMP - dump box dims (pre and post fix)
    if self._debugMode:
      if self._imgCounter == 0:
        mode = 'w'
        self._logBox = open("LOGBOX.txt", mode)
      print >>self._logBox, "%d    %d %d %d %d    %d %d %d %d" % \
                      (self._imgCounter,
                       origBox[0], origBox[1], origBox[2], origBox[3],
                       box[0], box[1], box[2], box[3])

    self._imgCounter += 1

    return dstImage

  #-----------------------------------------------------------------------
  def _acceptOrCull(self, strength, strongZones, candidateZone, minZoneLen, minStrength):
    """
    Utility method that will append a candidate strong zone to
    an existing list of strong zones if and only if it's length
    meets the minimum zone length requirement.
    """
    (startIdx, stopIdx) = candidateZone
    zoneLen = stopIdx - startIdx
    assert zoneLen > 0
    peakStrength = strength[startIdx:stopIdx].max()
    if zoneLen >= minZoneLen and \
       peakStrength >= minStrength:
      strongZones += [candidateZone]


  #-----------------------------------------------------------------------
  def _smooth(self, x, window_len=10, window=None):
      """smooth the data using a window with requested size.

      This method is based on the convolution of a scaled window with the signal.
      The signal is prepared by introducing reflected copies of the signal
      (with the window size) in both ends so that transient parts are minimized
      in the begining and end part of the output signal.

      input:
          x: the input signal
          window_len: the dimension of the smoothing window
          window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
              flat window will produce a moving average smoothing.

      output:
          the smoothed signal

      example:

      t=linspace(-2,2,0.1)
      x=sin(t)+randn(len(t))*0.1
      y=smooth(x)

      see also:

      numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
      scipy.signal.lfilter

      TODO: the window parameter could be the window itself if an array instead of a string
      """

      if x.ndim != 1:
          raise ValueError, "smooth only accepts 1 dimension arrays."

      if x.size < window_len:
          window_len = x.size

      if window_len<3:
          return x

      if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
          raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


      s=numpy.r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]
      if window == 'flat': #moving average
          w=ones(window_len,'d')
      else:
          w=eval('numpy.'+window+'(window_len)')

      y=numpy.convolve(w/w.sum(),s,mode='same')
      return y[window_len-1:-window_len+1]



  if False:
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
        else:
          bbox = image.split()[1].getbbox()
        # If alpha channel is completely empty, we will end up
        # with a bbox of 'None'.  Nothing much we can do
        if bbox is None:
          bbox = (0, 0, image.size[0], image.size[1])
          print 'WARNING: empty alpha channel'

        # Ascertain the original raw size of the tracking box
        width  = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]

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
            clipOffset = (clipBox[0] - srcBox[0],
                          clipBox[1] - srcBox[1])

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
            clipOffset = (int((srcWidth - clipBoxWidth)/2),
                          int((srcHeight - clipBoxHeight)/2))


          # Copy the source rect
          croppedImage = image.crop(clipBox)
          croppedImage.load()

          # New development
          croppedImage.putalpha(Image.new(mode='L', size=croppedImage.size, color=255))

          if self._fillValue is None:
            [gray, alpha] = image.split()
            hist = numpy.array(gray.histogram(alpha), dtype='float')
            mean = (hist * self._histWeights).sum() / hist.sum()
            if mean < 127.5:
              fillValue = 255
            else:
              fillValue = 0
          else:
            fillValue = self._fillValue

          # Paste into a new image
          newImage = Image.new(mode='LA', size=(srcBox[2]-srcBox[0],
                                               srcBox[3]-srcBox[1]), color=fillValue)
          newImage.paste(croppedImage, clipOffset)

          # Resize the cropped image to the (padded) target size
          scaledImage = newImage.resize((targetWidth, targetHeight), self._resizingFilter)

          # Convert and save the scaled image as the output
          assert scaledImage.mode == 'LA'
          newImages += [scaledImage]

          # Dump debugging images to disk
          if self._dumpDebugImages:
            self._handleDebug(scaledImage, scaleIdx)

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
    return 1
    #return 1, len(self._scales)
