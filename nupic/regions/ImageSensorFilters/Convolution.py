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

"""
## @file
"""
import os
import ctypes
import imp
import platform

import numpy
from PIL import Image
from nupic.regions.ImageSensorFilters.BaseFilter import BaseFilter, uint


# Global counter used for some debugging operations
id = 0

class Convolution(BaseFilter):
  """Base class for filters that perform a 2D convolution on the iamge
  """

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  # Class constants
  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  # The minimum filter size dimension (3x3)
  minFilterDim = 3

  ## The minimum filter size dimension (3x3)
  #minNumOrients = 0 # GABOR ONLY

  # List of filter dimensions supported by the optimized
  # C library
  _optimizedFilterDims = [5, 7, 9, 11, 13] # BC


  # Valid parameter values
  _validValues = {
      'boundaryMode':         ['constrained', 'sweepOff'],
      'normalizationMethod':  ['fixed', 'max', 'mean'],
      'postProcessingMethod': ['raw', 'sigmoid', 'threshold'],
      }

  # Our C implementation performs the 2D convolution using
  # integer math, but scales the operands to preserve
  # precision.  The scaling is done by left shifting the Gabor
  # filter coefficients by a fixed number of bits:
  _integerMathShifts = 12     # 2^12 = 4096
  _integerMathScale  = 1 << _integerMathShifts

  def __init__(self,
               scaleDecimation=[1],
               filterDim=9,
               gainConstant=1.0,
               normalizationMethod='fixed',
               perPlaneNormalization=False,
               perPhaseNormalization=True,
               postProcessingMethod='raw',
               postProcessingSlope=1.0,
               postProcessingCenter=0.5,
               postProcessingMin=0.0,
               postProcessingMax=1.0,
               zeroThresholdOut=0.0,
               boundaryMode='constrained',
               offImagePixelValue=0,
               suppressOutsideBox=True,
               forceBoxContraction=False,
               aspectRatio=0.3,
               effectiveWidth=4.5):
    """Initialize the the convolution filter

    @param inputDims: a list of input image sizes in the
          form of 2-tuples (width, height)

    """

    BaseFilter.__init__(self)

    self._scaleDecimation = scaleDecimation
    self._filterDim = filterDim
    self._gainConstant = gainConstant
    self._normalizationMethod = normalizationMethod
    self._perPlaneNormalization = perPlaneNormalization
    self._perPhaseNormalization = perPhaseNormalization
    self._postProcessingMethod = postProcessingMethod
    self._postProcessingSlope = postProcessingSlope
    self._postProcessingCenter = postProcessingCenter
    self._postProcessingMin = postProcessingMin
    self._postProcessingMax = postProcessingMax
    self._zeroThresholdOut = zeroThresholdOut
    self._boundaryMode = boundaryMode
    self._offImagePixelValue = offImagePixelValue
    self._suppressOutsideBox = suppressOutsideBox
    self._forceBoxContraction = forceBoxContraction
    self._aspectRatio = aspectRatio
    self._effectiveWidth = effectiveWidth

    self._filterBank = None
    self._outputPlaneCount = self._calcPlaneCount()

    self._cache = {}
    self._bbox_cache = {}

    # Load the _algorithms C library that contains the fast convolution code
    libAlgorithms = self._loadLibrary("_algorithms")

    # Prepare the C calls
    self._convolutionProc = libAlgorithms.gaborCompute

    # Generate post-processing lookup-tables (LUTs) that will be
    # used by the C implementation
    self._makeLUTs()

  def _getBBox(self, image_size):
    if image_size in self._bbox_cache:
      return self._bbox_cache[image_size]

    width, height = image_size
    validRegionIn = (0, 0, width, height)
    validPyramid = validRegionIn / numpy.array([width,
                                               height,
                                               width,
                                               height],
                                               dtype=numpy.float32)

    bbox = self._computeBBox(validPyramid, width, height)
    self._bbox_cache[image_size] = bbox
    return bbox

  def process(self, image):
    images = []
    factor = 1.0

    # Extract the bounding box from the image
    full_bbox = self._getBBox(image.size)
    bbox = numpy.array(full_bbox)
    image_size = image.size
    for s in self._scaleDecimation:
      factor /= s
      new_size = [int(round(x * factor)) for x in image_size]
      resized_image = image.resize(new_size, Image.ANTIALIAS)
      bbox = bbox.astype(float)
      bbox *= factor
      bbox = bbox.astype(int)
      images.append(self._processImage(resized_image, bbox))

    raw_output = numpy.concatenate([x[1] for x in images])
    images = [x[0] for x in images]

    return ([images], raw_output)

  def _processImage(self, image, bbox):
    """Return a single image, or a list containing one or more images.

    @param image -- The image to process.
    """
    BaseFilter.process(self, image)

    inWidth, inHeight = image.size

    # Get output dims and buffers (cached)
    outWidth, outHeight, inBuffer, outBuffer, mask = self._prepare(image.size)

    # Ask the sub-class the build the filter bank
    self._buildFilterBank()

    inputOffset  = 0
    outputOffset = 0

    data = image.split()[0]
    inputVector = numpy.asarray(data, dtype=numpy.float32)

    inputVector.shape = (inHeight, inWidth)

    # If we are using "color-key" mode, then detect the value of
    # the upper-left pixel and use it as the value of
    # 'offImagePixelValue'
    if self._offImagePixelValue in ('colorKey', u'colorKey'):
      offImagePixelValue = inputVector[0, 0]
    else:
      offImagePixelValue = self._offImagePixelValue

    result = []

    # Compute the convolution responses

    # Determine proper input/output dimensions
    outputSize = outHeight * outWidth * self._outputPlaneCount

    # Locate correct portion of output
    outputVector = numpy.zeros((outHeight,
                                outWidth,
                                self._outputPlaneCount),
                                dtype=numpy.float32)
    outputVector.shape = (self._outputPlaneCount, outHeight, outWidth)


    # Compute the bounding box to use for our C implementation
    imageBox = numpy.array([0, 0, inWidth, inHeight], dtype=numpy.int32)

    ## --- DEBUG CODE ----
    #global id
    #o = inputVector
    #f = os.path.abspath('convolution_input_%d.txt' % id)
    #print f
    #numpy.savetxt(f, o)
    #id += 1
    ##from dbgp.client import brk; brk(port=9019)
    ## --- DEBUG CODE END ----

    # Call the fast convolution C code
    self._convolve(inputVector,
                   bbox,
                   imageBox,
                   outputVector,
                   offImagePixelValue,
                   inBuffer,
                   outBuffer)

    outputVector = numpy.rollaxis(outputVector, 0, 3)
    outputVector = outputVector.reshape(outWidth * outHeight,
                                        self._outputPlaneCount).flatten()
    assert outputVector.dtype == numpy.float32

    locationCount = len(outputVector) / self._outputPlaneCount
    response = outputVector.reshape(locationCount, self._outputPlaneCount)

    ## --- DEBUG CODE ----
    #global id
    #o = outputVector.flatten()
    ##print outputVector.shape, len(o)
    #f = os.path.abspath('convolution_output_%d.txt' % id)
    #print f
    #numpy.savetxt(f, o)
    #id += 1
    ##from dbgp.client import brk; brk(port=9019)
    ## --- DEBUG CODE END ----

    # Convert the reponses to images
    result = []
    for i in range(response.shape[1]):
      newImage = Image.new('L', (outWidth, outHeight))
      #data = (self._gainConstant * 255.0 * response[:,i]).clip(min=0.0, max=255.0).astype(numpy.uint8)
      data = (255.0 * response[:,i]).clip(min=0.0, max=255.0).astype(numpy.uint8)
      newImage.putdata([uint(p) for p in data])
      newImage.putalpha(mask)
      result.append(newImage)

    return (result, outputVector)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def getOutputCount(self):
    """
    Return the number of images returned by each call to process().

    If the filter creates multiple simultaneous outputs, return a tuple:
    (numOutputs, numSimultaneousOutputs).
    """

    return (1, len(self._scaleDecimation) * self._calcPlaneCount())

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+


  def _getNeededBufferCount(self):
    """Compute the number of allocated buffers to hold the responses.

    Must be implemented by sub-class
    """
    raise NotImplementedError()

  def _calcPlaneCount(self):
    """ Compute the number of responses planes for a particular configuration.

    Must be implemented by sub-class
    """
    raise NotImplementedError()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _buildFilterBank(self):
    """Return the the 2D filters that will convolve with the original image

    MUST override in sub-class
    """
    raise NotImplementedError()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  class ARRAY(ctypes.Structure):
    _fields_ = [
          ("nd",          ctypes.c_int),
          ("dimensions",  ctypes.c_void_p),
          ("strides",     ctypes.c_void_p),
          ("data",        ctypes.c_void_p),
          ]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _wrapArray(self, array):
    """
    Helper function that takes a numpy array and returns
    a 4-tuple consisting of ctypes references to the
    following:
      (nd, dimensions, strides, data)
    """
    if array is None:
      return None
    else:
      return ctypes.byref(self.ARRAY(len(array.ctypes.shape),
                   ctypes.cast(array.ctypes.shape, ctypes.c_void_p),
                   ctypes.cast(array.ctypes.strides, ctypes.c_void_p),
                   array.ctypes.data))

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _prepare(self, inputDims):
    """Perform one-time preparations needed for convolution processing of
    images of a particular size.

    Compute the output dims correponding to the input dims and allocate
    input and output buffers (used later by the C implementation). Cache the
    output dims and the buffers

    @param inputDims: width and height of image
    @return outWidth, outHeight, inBuffer, outBuffer
    """

    # If already cached  just bail out
    if not inputDims in self._cache:
      # Compute output dims
      outputDims = self.getOutputDims(inputDims)
      outWidth, outHeight = outputDims

      # Allocate working buffers to be used by the C implementation
      #self._buffers = [numpy.zeros(inputDim, dtype=numpy.int32) for inputDim in inputDims]
      inBuffer, outBuffer = self._allocBuffers(inputDims, outputDims)

      # Prepare the mask
      mask_box = (0, 0, outWidth, outHeight)
      mask = Image.new('L', outputDims, 255)



      self._cache[inputDims] = (outWidth, outHeight, inBuffer, outBuffer, mask)

    return self._cache[inputDims]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def getOutputDims(self, inputDim):
    """Compute the output dimensions in form (height, width)
    """
    if self._boundaryMode == 'sweepOff':
      shrinkage = 0
    else:
      assert self._boundaryMode == 'constrained'
      shrinkage = self._filterDim - 1
    return tuple([dim - shrinkage for dim in inputDim])

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _alignToFour(self, val):
    """
    Utility macro that increases a value 'val' to ensure
    that it is evenly divisible by four (e.g., for
    purposes of memory alignment, etc.)
    """
    return (((val - 1) / 4) + 1) * 4

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _makeLUTs(self):
    """
    Generate post-processing lookup-tables (LUTs) that will be
    used by the C implementation
    """

    # --------------------------------------------------
    # Define LUT parameters
    # For 'normalizationMethod' of 'mean', this internal parameter
    # controls the trade-off between how finely we can discretize our
    # LUT bins vs. how often a raw response value "overflows" the
    # maximum LUT bin and has to be clamped.  In essence, any raw
    # response value greater than 'meanLutCushionFactor' times the
    # mean response for the image will "overflow" and be clamped
    # to the response value of the largest bin in the LUT.
    meanLutCushionFactor = 4.0

    # We'll use a LUT large enough to give us decent precision
    # but not so large that it causes cache problems.
    # A total of 1024 bins seems reasonable:
    numLutShifts = 10
    numLutBins = (1 << numLutShifts)

    # --------------------------------------------------
    # Build LUT

    # Build the filter bank if it doesn't already exist
    #self._buildGaborBankIfNeeded(self._useNumpy())
    if self._filterBank is None:
      self._buildFilterBank()

    # Empirically compute the maximum possible response value
    # given our current parameter settings.  We do this by
    # generating a fake image of size (filterDim X filterDim)
    # that has a pure vertical edge and then convolving it with
    # the first gabor filter (which is always vertically oriented)
    # and measuring the response.
    testImage = numpy.ones((self._filterDim, self._filterDim), dtype=numpy.float32) * 255.0
    #testImage[:, :(self._filterDim/2)] = 0
    testImage[numpy.where(self._filterBank[0] < 0.0)] *= -1.0
    maxRawResponse = (testImage * self._filterBank[0]).sum()
    # At run time our Gabor responses will be scaled (via
    # bit shifting) so that we can do integer match instead of
    # floating point match, but still have high precision.
    # So we'll simulate that in order to get a comparable result.
    maxShiftedResponse = maxRawResponse / (255.0 * float(self._integerMathScale))

    # Depending on our normalization method, our LUT will have a
    # different scaling factor (for pre-scaling values prior
    # to discretizing them into LUT bins)
    if self._normalizationMethod == 'fixed':
      postProcScalar = float(numLutBins - 1) / maxShiftedResponse
    elif self._normalizationMethod == 'max':
      postProcScalar = float(numLutBins - 1)
    elif self._normalizationMethod == 'mean':
      postProcScalar = float(numLutBins - 1) / meanLutCushionFactor
    else:
      assert False

    # Build LUT
    lutInputs = numpy.array(range(numLutBins), dtype=numpy.float32) / postProcScalar

    # Sigmoid: output = 1 / (1 + exp(input))
    if self._postProcessingMethod == 'sigmoid':
      offset = 1.0 / (1.0 + numpy.exp(self._postProcessingSlope * self._postProcessingCenter))
      scaleFactor = 1.0 / (1.0 - offset)
      postProcLUT = ((1.0 / (numpy.exp(numpy.clip(self._postProcessingSlope \
                    * (self._postProcessingCenter - lutInputs), \
                    -40.0, 40.0)) + 1.0)) - offset) * scaleFactor
      # For some parameter choices, it is possible that numerical precision
      # issues will result in the 'offset' being ever so slightly larger
      # than the value of postProcLUT[0].  This will result in a very
      # tiny negative value in the postProcLUT[0] slot, which is
      # undesireable because the output of a sigmoid should always
      # be bound between (0.0, 1.0).
      # So we clip the LUT values to this range just to keep
      # things clean.
      postProcLUT = numpy.clip(postProcLUT, 0.0, 1.0)

    # Threshold: Need piecewise linear LUT
    elif self._postProcessingMethod == "threshold":
      postProcLUT = lutInputs
      postProcLUT[lutInputs < self._postProcessingMin] = 0.0
      postProcLUT[lutInputs > self._postProcessingMax] = 1.0

    # Raw: no LUT needed at all
    else:
      assert self._postProcessingMethod == "raw"
      postProcLUT = None

    # If we are in 'dual' phase mode, then we'll reflect
    # the LUT on the negative side of zero to speed up
    # processing inside the C function.
    if False:
      if postProcLUT is not None and self._phaseMode == 'dual':
        # Make a reflected LUT
        comboLut = numpy.concatenate((numpy.fliplr(postProcLUT[numpy.newaxis,:]),
                                                   postProcLUT[numpy.newaxis,:]),
                                                   axis=1)
        # Now clone the reflected LUT and clip it's responses
        # for positive and negative phases
        postProcLUT = numpy.concatenate((comboLut, comboLut), axis=1).reshape(4*numLutBins)
        # First half of it is for positive phase
        postProcLUT[:numLutBins] = 0.0
        # Second half of it is for negative phase
        postProcLUT[-numLutBins:] = 0.0

    # Store our LUT and it's pre-scaling factor
    self._postProcLUT = postProcLUT
    self._postProcLutScalar = postProcScalar

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _allocBuffers(self, inputDims, outputDims):
    """
    Allocate some working buffers that are required
    by the C implementation.
    """

    # Compute how much "padding" ou input buffers
    # we will need due to boundary effects
    if self._boundaryMode == 'sweepOff':
      padding = self._filterDim - 1
    else:
      padding = 0

    inWidth, inHeight = inputDims
    inBuffer = numpy.zeros((inHeight + padding,
                            self._alignToFour(inWidth + padding)),
                            dtype=numpy.int32)

    outWidth, outHeight = outputDims
    neededBufferCount = self._getNeededBufferCount()
    outBuffer = numpy.zeros((neededBufferCount,
                             outHeight,
                             self._alignToFour(outWidth)),
                             dtype=numpy.int32)

    return inBuffer, outBuffer

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _loadLibrary(self, libraryName, libSubDir='bindings'):
    """
    Utility method for portably loading a NuPIC shared library.
    Note: we assume the library lives in the NuPIC "lib" directory.

    @param: libraryName - the name of the library (sans extension)
    @returns: reference to the loaded library; otherwise raises
          a runtime exception.
    """

    # Locate the file system path to algorithms bindings.
    nupicRoot = imp.find_module("nupic")[1]

    # Choose correct extension:
    systemID = platform.system()
    extension = {
        "Darwin":  "so",
        "Linux":   "so",
        "Windows": "pyd",
        }.get(systemID)
    if not extension:
      raise RuntimeError, "Unknown platform: %s" % systemID

    # Generate the library path
    libPath = os.path.join(nupicRoot, libSubDir, "%s.%s" % (libraryName, extension))

    # Attempt to load the library
    try:
      return ctypes.cdll.LoadLibrary(libPath)
    except:
      print "Warning: Could not load shared library: %s" % libraryName
      return None


  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _computeBBox(self, validPyramid, inWidth, inHeight):
    """
    Compute a bounding box given the validPyramid (a fraction
    of the valid input region as provided by the sensor) and
    the output dimensions for a particular current scale.
    """
    # Assemble the bounding box by converting 'validPyramid' from float (0,1) to integer (O,N)
    if self._suppressOutsideBox:
      halfFilterDim = (self._filterDim - 1) / 2
      bbox = numpy.round((validPyramid * numpy.array([inWidth, inHeight, inWidth, inHeight],
              dtype=validPyramid.dtype))).astype(numpy.int32)

      # Subtract enough padding for our filter on all four edges
      # We'll only subtract enough padding if we have a non-trivlal bounding box.
      # In other words, if our validRegionIn is [0, 25, 200, 175] for input image
      # dimensions of [0, 0, 200, 200], then we will assume that two horizontal strips
      # of filler pixels were artificially added at the top and bottom, but no
      # such artificial vertical strips were added.  So we don't need to erode the
      # bounding box horizontally, only vertically.
      if self._forceBoxContraction or bbox[0] > 0:
        bbox[0] += halfFilterDim
      if self._forceBoxContraction or bbox[1] > 0:
        bbox[1] += halfFilterDim
      if self._forceBoxContraction or bbox[2] < inWidth:
        bbox[2] -= halfFilterDim
      if self._forceBoxContraction or bbox[3] < inHeight:
        bbox[3] -= halfFilterDim

      # Clip the bounding box to the size of the image
      bbox[0] = max(bbox[0], 0)
      bbox[1] = max(bbox[1], 0)
      bbox[2] = min(bbox[2], inWidth)
      bbox[3] = min(bbox[3], inHeight)
      # Make sure the bounding box didn't become negative width/height
      bbox[0] = min(bbox[0], bbox[2])
      bbox[1] = min(bbox[1], bbox[3])

    # If absolutely no suppression is requested under any
    # circumstances, then force the bbox to be the entire image
    else:
      bbox = numpy.array([0, 0, inWidth, inHeight], dtype=numpy.int32)

    # Check in case bbox is non-existent or mal-formed
    if bbox[0] < 0 or bbox[1] < 0 or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
      print "WARNING: empty or malformed bounding box:", bbox
      # Fix bbox so that it is a null box but at least not malformed
      if bbox[0] < 0:
        bbox[0] = 0
      if bbox[1] < 0:
        bbox[1] = 0
      if bbox[2] < bbox[0]:
        bbox[2] = bbox[0]
      if bbox[3] < bbox[1]:
        bbox[3] = bbox[1]

    return bbox

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _convolve(self,
                inputVector,
                bbox,
                imageBox,
                outputVector,
                offImagePixelValue,
                inBuffer,
                outBuffer):
    """
    Prepare arguments and invoke C function for
    performing actual 2D convolution, rectification,
    normalization, and post-processing.
    """
    if offImagePixelValue is None:
      assert type(offImagePixelValue) in [type(0), type(0.0)]
      offImagePixelValue = self._offImagePixelValue

    # No alpha mask
    validAlpha = None

    # Invoke C function
    #self._postProcLutScalar = 141.38911437988281
    self._convolutionProc(
              self._wrapArray(self._filterBank),
              self._wrapArray(inputVector),
              self._wrapArray(validAlpha),
              self._wrapArray(bbox),
              self._wrapArray(imageBox),
              self._wrapArray(outputVector),
              ctypes.c_float(self._gainConstant),
              self._mapParamFromPythonToC('boundaryMode'),
              ctypes.c_float(offImagePixelValue),
              self._mapParamFromPythonToC('phaseMode'),
              self._mapParamFromPythonToC('normalizationMethod'),
              self._mapParamFromPythonToC('perPlaneNormalization'),
              self._mapParamFromPythonToC('perPhaseNormalization'),
              self._mapParamFromPythonToC('postProcessingMethod'),
              ctypes.c_float(self._postProcessingSlope),
              ctypes.c_float(self._postProcessingCenter),
              ctypes.c_float(self._postProcessingMin),
              ctypes.c_float(self._postProcessingMax),
              self._wrapArray(inBuffer),
              self._wrapArray(outBuffer),
              self._wrapArray(self._postProcLUT),
              ctypes.c_float(self._postProcLutScalar),
              )

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _convertEnumValue(self, enumValue):
    """
    Convert a Python integer object into a ctypes integer
    that can be passed to a C function and seen as an
    int on the C side.
    """
    return ctypes.c_int(enumValue)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  # THINK OF A SAFE WAY TO MAKE SURE C ENUMS ARE SYNCHED WITH PYTHON SYMBOLIC NAMES (UNIT TEST, AUTP PARSING,...)
  def _mapParamFromPythonToC(self, paramName):
    """
    Map Python object values to equivalent enumerated C values.
    """
    # boundaryMode
    if paramName == "boundaryMode":
      if self._boundaryMode == 'constrained':
        enumValue = 0
      elif self._boundaryMode == 'sweepOff':
        enumValue = 1
      return self._convertEnumValue(enumValue)

    # phaseMode
    elif paramName == "phaseMode":
      if self._phaseMode == 'single':
        enumValue = 0
      elif self._phaseMode == 'dual':
        enumValue = 1
      return self._convertEnumValue(enumValue)

    # normalizationMethod
    elif paramName == "normalizationMethod":
      if self._normalizationMethod == 'fixed':
        enumValue = 0
      elif self._normalizationMethod == 'max':
        enumValue = 1
      elif self._normalizationMethod == 'mean':
        enumValue = 2
      #elif self._normalizationMethod == 'maxPower':
      #  enumValue = 3
      #elif self._normalizationMethod == 'meanPower':
      #  enumValue = 4
      return self._convertEnumValue(enumValue)

    # perPlaneNormalization
    elif paramName == "perPlaneNormalization":
      if not self._perPlaneNormalization:
        enumValue = 0
      else:
        enumValue = 1
      return self._convertEnumValue(enumValue)

    # perPhaseNormalization
    elif paramName == "perPhaseNormalization":
      if not self._perPhaseNormalization:
        enumValue = 0
      else:
        enumValue = 1
      return self._convertEnumValue(enumValue)

    # postProcessingMethod
    elif paramName == "postProcessingMethod":
      if self._postProcessingMethod == 'raw':
        enumValue = 0
      elif self._postProcessingMethod == 'sigmoid':
        enumValue = 1
      elif self._postProcessingMethod == 'threshold':
        enumValue = 2
      return self._convertEnumValue(enumValue)

    # Invalid parameter
    else:
      assert False

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
