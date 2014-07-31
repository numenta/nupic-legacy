#!/usr/bin/env python

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

import ctypes

import numpy

try:
  # Not normally needed. Not available in demo app.
  import hotshot
except:
  pass

# Attempt to import OpenCV's ctypes-based bindings
try:
  from opencv.cvtypes import cv
except:
  cv = None

from StringIO import StringIO
from PIL import (Image,
                 ImageChops)

from nupic.regions.PyRegion import PyRegion, RealNumpyDType
from nupic.regions.Spec import *

# Global counter used for some debugging operations
id = 0
#+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
# GaborNode
#+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
class GaborNode2(PyRegion):
  """
  Performs dense Gabor filtering upon a multi-resolution grid.
  """

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  # Class constants
  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  # The minimum filter size dimension (3x3)
  minFilterDim = 3

  # The minimum filter size dimension (3x3)
  minNumOrients = 0

  # List of filter dimensions supported by the optimized
  # C library
  _optimizedFilterDims = [5, 7, 9, 11, 13]

  # Valid parameter values
  _validValues = {
      'phaseMode':            ('single', 'dual'),
      'targetType':           ('edge', 'line'),
      'boundaryMode':         ('constrained', 'sweepOff'),
      'normalizationMethod':  ('fixed', 'max', 'mean'),
      'postProcessingMethod': ('raw', 'sigmoid', 'threshold'),
      'nta_morphologyMethod': ('best', 'opencv', 'nta'),
      }

  # Default parameter values
  _defaults = {
    # Documented parameters:
    'filterDim':                          9,
    'numOrientations':                    4,
    'phaseMode':                   'single',
    'centerSurround':                 False,
    'targetType':                    'edge',
    'gainConstant':                     1.0,
    'normalizationMethod':          'fixed',
    'perPlaneNormalization':          False,
    'perPhaseNormalization':           True,
    'postProcessingMethod':           'raw',
    'postProcessingSlope':              1.0,
    'postProcessingCenter':             0.5,
    'postProcessingMin':                0.0,
    'postProcessingMax':                1.0,
    'zeroThresholdOut':                 0.0,
    'boundaryMode':           'constrained',
    'offImagePixelValue':                 0,
    'suppressOutsideBox':              True,
    'forceBoxContraction':            False,
    'suppressByAlpha':                False,
    'logPrefix':                       None,
    # Undocumented parameters:
    'nta_aspectRatio':                  0.3,
    'nta_effectiveWidth':               4.5,
    'nta_wavelength':                   5.6,
    'nta_lobeSuppression':             True,
    'nta_debugLogBuffers':            False,
    'nta_morphologyMethod':          'best',
    }

  # Our C implementation performs the 2D convolution using
  # integer math, but scales the operands to preserve
  # precision.  The scaling is done by left shifting the Gabor
  # filter coefficients by a fixed number of bits:
  _integerMathShifts = 12     # 2^12 = 4096
  _integerMathScale  = 1 << _integerMathShifts


  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  # Public API calls
  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def __init__(self,
               # Filter size:
               filterDim=None,
               # Filter responses:
               numOrientations=None,
               phaseMode=None,
               centerSurround=None,
               targetType=None,
               # Normalization:
               gainConstant=None,
               normalizationMethod=None,
               perPlaneNormalization=None,
               perPhaseNormalization=None,
               # Post-processing:
               postProcessingMethod=None,
               postProcessingSlope=None,
               postProcessingCenter=None,
               postProcessingMin=None,
               postProcessingMax=None,
               zeroThresholdOut=None,
               # Bounding effects:
               boundaryMode=None,
               offImagePixelValue=None,
               suppressOutsideBox=None,
               forceBoxContraction=None,
               suppressByAlpha=None,
               # Logging
               logPrefix=None,
               # Additional keywords
               **keywds
               ):
    """
    @param filterDim -- The size (in pixels) of both the width and height of the
            gabor filters.  Defaults to 9x9.

    @param numOrientations -- The number of gabor filter orientations to produce.
            The half-circle (180 degrees) of rotational angle will be evenly partitioned.
            Defaults to 4, which produces a gabor bank containing filters oriented
            at 0, 45, 90, and 135 degrees.

    @param phaseMode -- The number of separate phases to compute per orientation.
            Valid values are: 'single' or 'dual'.  In 'single', responses to each such
            orientation are rectified by absolutizing them; i.e., a 90-degree edge
            will produce the same responses as a 270-degree edge, and the two
            responses will be indistinguishable.  In "dual" mode, the responses to
            each orientation are rectified by clipping at zero, and then creating
            a second output response by inverting the raw response and again clipping
            at zero; i.e., a 90-degree edge will produce a response only in the
            90-degree-oriented plane, and a 270-degree edge will produce a response
            only the dual phase plane associated with the 90-degree plane (an
            implicit 270-degree plane.)  Default is 'single'.

    @param centerSurround -- Controls whether an additional filter corresponding to
            a non-oriented "center surround" response is applied to the image.
            If phaseMode is "dual", then a second "center surround" response plane
            is added as well (the inverted version of the center-surround response.)
            Defaults to False.

    @param targetType -- The preferred "target" of the gabor filters.  A value of
            'line' specifies that line detectors (peaks in the center and troughs
            on either side) are to be used.  A value of 'edge' specifies that edge
            detectors (with a peak on one side and a trough on the other) are to
            be used.  Default is 'edge'.

    @param gainConstant -- A multiplicative amplifier that is applied to the gabor
            responses after any normalization.  Defaults to 1.0; larger values
            increase the sensitivity to edges.

    @param normalizationMethod -- Controls the method by which responses are
            normalized on a per image (and per scale) basis.  Accepts the following
            three legal values:
              "fixed": No response normalization;
              "max":   Applies a global gain value to the responses so that the
                       max response equals the value of 'gainConstant'
              "mean":  Applies a global gain value to the responses so that the
                       mean response equals the value of 'gainConstant'
            Default is 'fixed'.

    @param perPlaneNormalization -- Controls whether normalization (as specified by
            'normalizationMethod') is applied globally across all response planes
            (for a given scale), or individually to each response plane.  Default
            is False.  Note: this parameter is ignored if normalizationMethod is "fixed".

    @param perPhaseNormalization -- Controls whether normalization (as specified by
            'normalizationMethod') is applied globally across both phases for a
            particular response orientation and scale, or individually to each
            phase of the response.  Default is True.  Note: this parameter is
            ignored if normalizationMethod is "fixed".

    @param postProcessingMethod -- Controls what type of post-processing (if any)
            is to be performed on the normalized responses. Valid value are:
              "raw":       No post-processing is performed; final output values are
                           unmodified after normalization
              "sigmoid":   Passes normalized output values through a sigmoid function
                           parameterized by 'postProcessingSlope' and 'postProcessingCenter'.
              "threshold": Passes normalized output values through a piecewise linear
                           thresholding function parameterized by 'postProcessingMin'
                           and 'postProcessingMax'.

    @param postProcessingSlope -- Controls the slope (steepness) of the sigmoid
            function used when 'postProcessingMethod' is set to 'sigmoid'.

    @param postProcessingCenter -- Controls the center point of the sigmoid function
            used when 'postProcessingMethod' is set to 'sigmoid'.

    @param postProcessingMin -- If 'postProcessingMethod' is set to 'threshold', all
            normalized response values less than 'postProcessingMin' are suppressed to zero.

    @param postProcessingMax -- If 'postProcessingMethod' is set to 'threshold', all
            normalized response values greater than 'postProcessingMax' are clamped to one.

    @param zeroThresholdOut -- if all outputs of a gabor node are below this threshold,
            they will all be driven to absolute 0. This is useful in conjunction with
            using the product mode/don't care spatial pooler which needs to know when
            an input should be treated as 0 vs being normalized to sum to 1.

    @param boundaryMode -- Controls how GaborNode deals with boundary effects.  Accepts
            two valid parameters:
                'constrained' -- Gabor responses are normally only computed for image locations
                        that are far enough from the edge of the input image so that the entire
                        filter mask fits within the input image.  Thus, the spatial dimensions of
                        the output gabor maps will be smaller than the input image layers.
                'sweepOff' -- Gabor responses will be generated at every location within
                        the input image layer.  Thus, the spatial dimensions of the output gabor
                        maps will be identical to the spatial dimensions of the input image.
                        For input image locations that are near the edge (i.e., a portion of
                        the gabor filter extends off the edge of the input image), the values
                        of pixels that are off the edge of the image are taken to be as specifed
                        by the parameter 'offImagePixelValue'.
             Default is 'constrained'.

    @param offImagePixelValue -- If 'boundaryMode' is set to 'sweepOff', then this
              parameter specifies the value of the input pixel to use for "filling"
              enough image locations outside the bounds of the original image.
              Ignored if 'boundaryMode' is 'constrained'.  Default value is 0.

    @param suppressOutsideBox -- If True, then gabor responses outside of the bounding
              box (provided from the sensor) are suppressed.  Internally, the bounding
              box is actually expanded by half the filter dimension (respecting the edge
              of the image, of course) so that responses can be computed for all image
              locations within the original bounding box.

    @param forceBoxContraction -- Fine-tunes the behavior of bounding box suppression.
              If False (the default), then the bounding box will only be 'contracted'
              (by the half-width of the filter) in the dimenion(s) in which it is not
              the entire span of the image.  If True, then the bounding box will be
              contracted unconditionally.

    @param suppressByAlpha -- A boolean that, if True, instructs GaborNode to use
              the pixel-accurate alpha mask received on the input 'validAlphaIn' for
              the purpose of suppression of responses.

    @param logPrefix -- If non-None, causes the response planes at each scale, and
              for each input image, to be written to disk using the specified prefix
              for the name of the log images.  Default is None (no such logging.)
    """

    #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
    #|  The following parameters are for advanced configuration and unsupported at this time   |
    #|  They may be specified via keyword arguments only.                                      |
    #+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
    #
    # @param nta_aspectRatio -- Controls how "fat" (i.e., how oriented) the Gabor
    #                 filters are.  A value of 1 would produce completely non-oriented
    #                 (circular) filters; smaller values will produce a more oriented
    #                 filter.  Default is 0.3.
    #
    # @param nta_effectiveWidth -- Controls the rate of exponential drop-off in
    #                 the Gaussian component of the Gabor filter.  Default is 4.5.
    #
    # @param nta_wavelength -- Controls the frequency of the sinusoidal component
    #                 of the Gabor filter.  Default is 5.6.
    #
    # @param nta_lobeSuppression -- Controls whether or not the secondary lobes of the
    #                 Gabor filters are suppressed.  The suppression is performed based
    #                 on the radial distance from the oriented edge to which the Gabor
    #                 filter is tuned.  If True, then the secondary lobes produced
    #                 by the pure mathematical Gabor equation will be suppressed
    #                 and have no effect; if False, then the pure mathematical
    #                 Gabor equation (digitized into discrete sampling points, of
    #                 course) will be used.  Default is True.
    #
    # @param nta_debugLogBuffers -- If enabled, causes internal memory buffers used
    #                 C implementation to be dumped to disk after each compute()
    #                 cycle as an aid in the debugging of the C code path.
    #
    # @param nta_morphologyMethod -- Controls the method to use for performing
    #                 morphological operations (erode or dilate) upon the
    #                 valid alpha masks.  Legal values are: 'opencv' (use the
    #                 faster OpenCV routines), 'nta' (use the slower routines,
    #                 or 'best' (use OpenCV if it is available on the platform,
    #                 otherwise use the slower routines.)
    #

    # ------------------------------------------------------
    # Handle hidden/undocumented parameters
    for paramName in [p for p in self._defaults if self._isHiddenParam(p)]:
      exec("%s = keywds.pop('%s', None)" % (paramName, paramName))

    # ------------------------------------------------------
    # Assign default values to missing parameters
    for paramName, paramValue in self._defaults.items():
      if eval(paramName) is None:
        exec("%s = paramValue" % paramName)

    # ------------------------------------------------------
    # Handle deprecated parameters

    # Deprecated: numOrients
    numOrients = keywds.pop('numOrients', None)
    if numOrients:
      print "WARNING: 'numOrients' has been deprecated and replaced with 'numOrientations'"
      if numOrientations is None:
        numOrientations = numOrients
      elif numOrients != numOrientations:
        print "WARNING: 'numOrients' (%s) is inconsistent with 'numOrientations' (%s) and will be ignored" % \
              (str(numOrients), str(numOrientations))

    # Deprecated: filterPhase
    filterPhase = keywds.pop('filterPhase', None)
    if filterPhase:
      print "WARNING: 'filterPhase' has been deprecated and replaced with 'targetType'"
      if targetType is None:
        targetType = filterPhase
      elif filterPhase != targetType:
        print "WARNING: 'filterPhase' (%s) is inconsistent with 'targetType' (%s) and will be ignored" % \
              (str(filterPhase), str(targetType))

    # Deprecated: nta_edgeMode
    nta_edgeMode = keywds.pop('nta_edgeMode', None)
    if nta_edgeMode:
      print "WARNING: 'nta_edgeMode' has been deprecated and replaced with 'edgeMode'"
      if edgeMode is None:
        edgeMode = nta_edgeMode
      elif nta_edgeMode != edgeMode:
        print "WARNING: 'nta_edgeMode' (%s) is inconsistent with 'edgeMode' (%s) and will be ignored" % \
              (str(nta_edgeMode), str(edgeMode))

    # Deprecated: lateralInhibition
    lateralInhibition = keywds.pop('nta_lateralInhibition', None)
    if lateralInhibition:
      print "WARNING: 'lateralInhibition' has been deprecated and will not be supported in future releases"

    # Deprecated: validityShrinkage
    validityShrinkage = keywds.pop('validityShrinkage', None)
    if validityShrinkage:
      print "WARNING: 'validityShrinkage' has been deprecated and replaced with 'suppressOutsideBox'"
      if suppressOutsideBox is None:
        suppressOutsideBox = (validityShrinkage >= 0.0)
      elif suppressOutsideBox != (validityShrinkage >= 0.0):
        print "WARNING: 'validityShrinkage' (%s) is inconsistent with 'suppressOutsideBox' (%s) and will be ignored" % \
              (str(validityShrinkage), str(suppressOutsideBox))

    self._numScales = None

    self.nta_phaseIndex = 0
    self._inputPyramidTopology = None
    self._outputPyramidTopology = None

    self._topDownCombiner = None
    self._tdNumParents = None
    self._enabledNodes = []
    self._nodesWithReceptiveField = None

    # These are cached inputs/outputs used for detecting/skipping either the
    # bottom up or top down compute to improve performance.
    self._cachedRFInput = None
    self._cachedBUInput = None
    self._cachedBUOutput = None
    self._cachedTDInput = None
    self._cachedTDOutput = None
    self._cachedResetIn = None
    self._cachedValidRegionIn = None
    self._cachedValidRegionOut = None

    # Profiling information
    self._profileObj = None
    self._iterations = 0

    # No longer neede for receptivefields_test, but still needed to satisfy
    # an assertion in _checkEphemeralMembers
    if not hasattr(self, "_inputSplitter"):
      self._inputSplitter = None
    self._rfMask = None
    self._rfSize = None
    self._rfInvLenY = None
    self._rfCenterX = None
    self._rfCenterY = None
    self._rfMinX = None
    self._rfMinY = None
    self._rfInvLenX = None
    self._rfMaxX = None
    self._rfMaxY = None

    self._initEphemerals()

    # ------------------------------------------------------
    # Validate each parameter
    for paramName in self._defaults.keys():
      self._validate(paramName, eval(paramName))

    # ------------------------------------------------------
    # Store each parameter value
    for paramName in self._defaults.keys():
      # Hidden parameters have the 'nta_' prefix stripped
      #if self._isHiddenParam(paramName):
      #  internalName = paramName[4:]
      #else:
      #  internalName = paramName
      internalName = self._stripHidingPrefixIfPresent(paramName)
      exec("self._%s = %s" % (internalName, paramName))

    # ------------------------------------------------------
    # Perform additional validations that operate on
    # combinations/interactions of parameters
    self._doHolisticValidation()

    # ------------------------------------------------------
    # Set up internal state

    # This node always get its input as a padded image cube from the ImageSensor
    # It may change in the future when ImageSensor supports packed image pyramids
    self._gaborBank = None

    # Generation of response images must be explicitly enabled
    self.disableResponseImages()

    # This node type is non-learning, and thus begins life in 'infer' mode.
    # This is only needed because our base class requires it.
    self._stage = 'infer'
    # We are always connected to an image sensor with padded pixels
    self._inputPyramidFormat = 'padded'

    # Store the number of output planes we'll produce
    self._numPlanes = self.getNumPlanes()

    # Initially, we do not generate response images
    self._makeResponseImages = False

    # Where we keep the maxTopDownOut for every node
    self._maxTopDownOut = []

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _stripHidingPrefixIfPresent(self, paramName):
    """
    If the named parameter is hidden, strip off the
    leading "nta_" prefix.
    """
    if self._isHiddenParam(paramName):
      return paramName[4:]
    else:
      return paramName

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _isHiddenParam(self, paramName):
    """
    Utility method for returning True if 'paramName' is the name
    of a hidden parameter.
    """
    return paramName.find('nta_') == 0

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def getOutputDims(self, inputDims):
    """
    Instance method version of class method
    """
    return self.calcOutputDims(inputDims,
                               self._filterDim,
                               self._boundaryMode)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def getNumPlanes(self):
    """
    Instance method version of class method
    """
    return self.calcNumPlanes(self._numOrientations,
                              self._phaseMode,
                              self._centerSurround)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  @classmethod
  def calcOutputDims(cls, inputDims,
                          filterDim,
                          boundaryMode,
                          **keywds):
    """
    Public utility method that computes the output dimensions
    in form (height, width), given 'inputDims' (height, width),
    for a particular 'filterDim'.
    """
    # Assign default values to missing parameters
    for paramName in ['filterDim', 'boundaryMode']:
      if eval(paramName) is None:
        defValue = cls._defaults[paramName]
        exec("%s = defValue" % paramName)

    # Validatation
    cls._validate('filterDim', filterDim)
    cls._validate('boundaryMode', boundaryMode)

    # Compute output dimensions
    if boundaryMode == 'sweepOff':
      shrinkage = 0
    elif boundaryMode == 'constrained':
      shrinkage = filterDim - 1
    return tuple([dim - shrinkage for dim in inputDims])

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  @classmethod
  def calcNumPlanes(cls, numOrientations=None,
                         phaseMode=None,
                         centerSurround=None,
                         **keywds):
    """
    Public utility method that computes the number
    of responses planes for a particular Gabor
    configuration.
    """
    # Assign default values to missing parameters
    for paramName in ['numOrientations', 'phaseMode', 'centerSurround']:
      if eval(paramName) is None:
        defValue = cls._defaults[paramName]
        exec("%s = defValue" % paramName)

    # Validatation
    cls._validate('phaseMode', phaseMode)
    cls._validate('numOrientations', numOrientations)
    cls._validate('centerSurround', centerSurround)

    # Compute output planes
    numPlanes = numOrientations
    if centerSurround:
      numPlanes += 1
    if phaseMode == 'dual':
      numPlanes *= 2
    return numPlanes

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _doHolisticValidation(self):
    """
    Perform additional validations that operate on
    combinations/interactions of parameters.
    """
    # We must have at least one response plane
    if self.getNumPlanes() < 1:
      raise RuntimeError("Configuration error: no response planes; " \
                         "either 'numOrientations' must be > 0 or " \
                         "'centerSurround' must be True")

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  @classmethod
  def _validate(cls, name, value):
    """
    Validate a parameter.  Raises a RunTimeError if
    the parameter is invalid.
    """

    # ------------------------------------------------------
    # Filter size:

    # Validation: filterDim
    if name == "filterDim":
      if type(value) != type(0) or \
         value < cls.minFilterDim or \
         value % 2 != 1:
        raise RuntimeError("Value error: '%s' must be an odd integer >= %d; your value: %s" % \
                          (name, cls.minFilterDim, str(value)))

    # ------------------------------------------------------
    # Filter responses:

    # Validation: numOrientations
    elif name == "numOrientations":
      if type(value) != type(0) or \
          value < cls.minNumOrients:
        raise RuntimeError("Value error: '%s' must be an integers >= %d; your value: %s" % \
                          (name, cls.minNumOrients, str(value)))

    # Validation: phaseMode
    elif name == "phaseMode":
      if value not in cls._validValues[name]:
        raise RuntimeError("Value error: '%s' must be one of %s; your value: %s" % \
              (name, str(cls._validValues[name]), value))

    # Validation: centerSurround
    elif name == "centerSurround":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name, str(value)))

    # Validation: targetType
    elif name == "targetType":
      if value not in cls._validValues[name]:
        raise RuntimeError("Value error: '%s' must be one of %; your value: %s" % \
              (name, str(cls._validValues[name]), value))

    # ------------------------------------------------------
    # Normalization:

    elif name == "gainConstant":
      if type(value) not in [type(0), type(0.0)] or float(value) < 0.0:
        raise RuntimeError("Value error: '%s' must be a float or integer >= 0.0; your value: %s" % \
                          (name, str(value)))

    # Validation: targetType
    elif name == "normalizationMethod":
      if not value in cls._validValues[name]:
        raise RuntimeError("Value error: '%s' must be one of %; your value: %s" % \
              (name, str(cls._validValues[name]), value))

    # Validation: perPlaneNormalization
    elif name == "perPlaneNormalization":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name, str(value)))

    # Validation: perPhaseNormalization
    elif name == "perPhaseNormalization":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name, str(value)))

    # ------------------------------------------------------
    # Post-processing:

    # Validation: targetType
    elif name == "postProcessingMethod":
      if not value in cls._validValues[name]:
        raise RuntimeError("Value error: '%s' must be one of %; your value: %s" % \
              (name, str(cls._validValues[name]), value))

    # Validation: postProcessingSlope
    elif name == "postProcessingSlope":
      if type(value) not in [type(0), type(0.0)] or float(value) <= 0.0:
        raise RuntimeError("Value error: '%s' must be a float or integer > 0.0; your value: %s" % \
                          (name, str(value)))

    # Validation: postProcessingCenter
    elif name == "postProcessingCenter":
      if type(value) not in [type(0), type(0.0)]:
        raise RuntimeError("Value error: '%s' must be a float or integer; your value: %s" % \
                          (name, str(value)))

    # Validation: postProcessingMin
    elif name == "postProcessingMin":
      if type(value) not in [type(0), type(0.0)]:
        raise RuntimeError("Value error: '%s' must be a float or integer; your value: %s" % \
                          (name, str(value)))

    # Validation: postProcessingMax
    elif name == "postProcessingMax":
      if type(value) not in [type(0), type(0.0)]:
        raise RuntimeError("Value error: '%s' must be a float or integer; your value: %s" % \
                          (name, str(value)))

    # Validation: zeroThresholdOut
    elif name == "zeroThresholdOut":
      if type(value) not in [type(0), type(0.0)]:
        raise RuntimeError("Value error: '%s' must be a float or integer >= 0.0; your value: %s" % \
                          (name, str(value)))

    # ------------------------------------------------------
    # Boundary effects:

    # Validation: boundaryMode
    elif name == "boundaryMode":
      if not value in cls._validValues[name]:
        raise RuntimeError("Value error: '%s' must be one of %; your value: %s" % \
              (name, str(cls._validValues[name]), str(value)))

    # Validation: offImagePixelValue
    elif name == "offImagePixelValue":
      if value != 'colorKey' and (type(value) not in (int, float) or float(value) < 0.0 or float(value) > 255.0):
        raise RuntimeError("Value error: '%s' must be a float or integer between 0 and 255, or 'colorKey'; your value: %s" % \
                          (name, str(value)))

    # Validation: suppressOutsideBox
    elif name == "suppressOutsideBox":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name, str(value)))

    # Validation: forceBoxContraction
    elif name == "forceBoxContraction":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name, str(value)))

    # Validation: suppressByAlpha
    elif name == "suppressByAlpha":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name, str(value)))

    # ------------------------------------------------------
    # Logging

    # Validation: logPrefix
    elif name == "logPrefix":
      if value is not None and (type(value) != type("") or len(value) == 0):
        raise RuntimeError("Value error: '%s' must be a string; your value: %s" % \
                          (name, str(value)))

    # ------------------------------------------------------
    # Undocumented parameters:

    # Validation: aspectRatio
    elif name == "nta_aspectRatio":
      if type(value) not in [type(0), type(0.)] or value <= 0.0:
        raise RuntimeError("Value error: '%s' must be a float > 0.0; your value: %s" % \
                          (name, str(value)))

    # Validation: effectiveWidth
    elif name == "nta_effectiveWidth":
      if type(value) not in [type(0), type(0.)] or value <= 0.0:
        raise RuntimeError("Value error: '%s' must be a float > 0.0; your value: %s" % \
                          (name, str(value)))

    # Validation: wavelength
    elif name == "nta_wavelength":
      if type(value) not in [type(0), type(0.)] or value <= 0.0:
        raise RuntimeError("Value error: '%s' must be a float > 0.0; your value: %s" % \
                          (name, str(value)))

    # Validation: lobeSuppression
    elif name == "nta_lobeSuppression":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name,  str(value)))

    # Validation: debugLogBuffers
    elif name == "nta_debugLogBuffers":
      if value not in [True, False]:
        raise RuntimeError("Value error: '%s' must be a boolean; your value: %s" % \
                          (name,  str(value)))

    # Validation: morphologyMethod
    elif name == "nta_morphologyMethod":
      if value not in cls._validValues[name]:
        raise RuntimeError("Value error: '%s' must be one of %; your value: %s" % \
              (name, str(cls._validValues[name]), str(value)))
      elif value == "opencv" and cv is None:
        raise RuntimeError(
              "'%s' was explicitly specified as 'opencv' " \
              "but OpenCV is not available on this platform" % name)


    # ------------------------------------------------------
    # Deprecated parameters:

    # Validation: numOrients
    elif name == "numOrients":
      if type(value) != type(0) or \
          value < cls.minNumOrients:
        raise RuntimeError("Value error: '%s' must be an integers >= %d; your value: %s" % \
                          (name, cls.minNumOrients, str(value)))

    # Validation: lateralInhibition
    elif name == "lateralInhibition":
      if type(value) not in [type(0), type(0.0)] or value < 0.0 or value > 1.0:
        raise RuntimeError("Value error: '%s' must be a float >= 0 and <= 1; your value: %s" % \
                          (name, str(value)))

    # Validation: validityShrinkage
    elif name == "validityShrinkage":
      if type(value) not in [type(0), type(0.0)] or float(value) < 0.0 or float(value) > 1.0:
        raise RuntimeError("Value error: '%s' must be a float or integer between 0 and 1; your value: %s" % \
                          (name, str(value)))

    # ------------------------------------------------------
    # Unknown parameter

    else:
      raise RuntimeError("Unknown parameter: %s [%s]" % (name, value))

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def initialize(self, dims, splitterMaps):
    """Build the gaborfilter bank.

    This method is called after construction.
    """
    # Preparations (creation of buffer, etc.)

    # Send the dims as a tuple that contains one pair. This needed to make
    # the node treat its input as a single scale.
    self._prepare((dims,))

    # Determine the number of response planes
    self._numPlanes = self.getNumPlanes()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def getParameter(self, parameterName, nodeSet=""):
    """
    Get the value of an PyMultiNode parameter.

    @param parameterName -- the name of the parameter to retrieve, as defined
            by the Node Spec.
    """
    if parameterName in self._defaults:
      # Hidden "nta_" parameters are internally stored as
      # class attributes without the leading "nta"
      if parameterName.startswith("nta_"):
        parameterName = parameterName[4:]
      return eval("self._%s" % parameterName)

    # Handle standard MRG infrastructure
    elif parameterName == 'nta_width':
      return self._inputPyramidTopology[0]['numNodes'][0]

    elif parameterName == 'nta_height':
      return self._inputPyramidTopology[0]['numNodes'][1]

    # Handle the maxTopDownOut read-only parameter
    elif parameterName == 'maxTopDownOut':
      return self._maxTopDownOut

    # Handle deprecated parameters
    elif parameterName == 'numOrients':
      return self._numPlanes
    elif parameterName == 'filterPhase':
      return self._targetType
    elif parameterName == 'nta_edgeMode':
      return self._boundaryMode
    elif parameterName == 'nta_lateralInhibition':
      return 0.0

    # Unknown parameter (at least by GaborNode)
    else:
      return PyRegion.getParameter(self, parameterName, nodeSet)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def setParameter(self, parameterName, parameterValue, nodeSet=""):
    """
    Set the value of an PyRegion parameter.

    @param parameterName -- the name of the parameter to update, as defined
            by the Node Spec.
    @param parameterValue -- the value to which the parameter is to be set.
    """
    # @todo -- Need to add validation of parameter changes

    settableParams = ["suppressOutsideBox", "forceBoxContraction",
                      "suppressByAlpha", "offImagePixelValue",
                      "perPlaneNormalization", "perPhaseNormalization",
                      "nta_debugLogBuffers", "logPrefix",
                      "zeroThresholdOut"]
    regenParams = ["gainConstant", "normalizationMethod",
                   "postProcessingMethod", "postProcessingSlope",
                   "postProcessingCenter", "postProcessingMin",
                   "postProcessingMax"]

    if parameterName in settableParams + regenParams:
      exec("self._%s = parameterValue" % parameterName)
    elif parameterName == 'nta_morphologyMethod':
      self._morphologyMethod = parameterValue
    # Not one of our parameters
    else:
      return PyRegion.setParameter(self, parameterName, parameterValue, nodeSet)

    # Generate post-processing lookup-tables (LUTs) that will be
    # used by the C implementation
    if parameterName in regenParams:
      self._makeLUTs()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def enableResponseImages(self):
    """
    Enable the generation of PIL Images representing the Gabor reponses.
    """
    self._makeResponseImages = True

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def disableResponseImages(self):
    """
    Disable the generation of PIL Images representing the Gabor reponses.
    """
    self._makeResponseImages = False

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def getResponseImages(self, whichResponse='all',
                              preSuppression=False,
                              whichScale='all',
                              whichPhase=0,
                              whichDirection='bottomUp'):
    """
    Return a list of PIL Images representing the Gabor responses
    computed upon the latest multi-resolution input image pyramid.

    @param whichResponse -- Indicates which Gabor orientation response
            should be returned.  If 'all' (the default), then false
            color composite images will be generated that contains the
            gabor responses for all orientations.  Otherwise, it should
            be an integer index between 0 and numOrients-1, in which
            case grayscale images will be generated.
    @param preSuppression -- Indicates whether the images should be
            generated before bounding box suppression is performed
            (if True), or after suppression (if False, the default.)
    @param whichScale -- Indicates which multi-resolution scale
            should be used to generate the response Images.  If 'all'
            (the default), then images will be generated for each
            scale in the input multi-resolution grid, and will be
            returned in a list.  Otherwise, it should be an integer
            index between 0 and numResolutions-1 (the number of
            layers in the multi-resolution grid), in which case a
            single Image will be returned (not a list).
    @param whichDirection -- Indicates which phase of resonse images should
            be returned ('bottomUp', 'topDown', 'combined').  'bottomUp'
            gets the unaltered bottom-up responses, 'top-down' gets the
            top-down feedback responses, and 'combined'
    @returns -- Either a single PIL Image, or a list of PIL Images
            that correspond to different resolutions.
    """

    # Make sure response images were enabled
    if not self._makeResponseImages:
      # Need to generate images now
      if whichDirection == 'bottomUp':
        if self.response is None:
          return
        response = self.response
      elif whichDirection == 'topDown':
        if self.tdInput is None:
          return
        response = self.tdInput
      elif whichDirection == 'combined':
        if self.selectedBottomUpOut:
          return
        response = self.selectedBottomUpOut
      if response is None:
        # No response to use
        return
      self._genResponseImages(response, preSuppression=preSuppression, phase=whichDirection)

    # Make sure we have images to provide
    if self._responseImages is None:
      return

    # Pull subset of images based on 'preSuppression' setting
    imageSet = self._responseImages.get(self._getResponseKey(preSuppression))

    # Validate format of 'whichScale' arg
    numScales = len(self._inputPyramidTopology)
    if whichScale != 'all' and (type(whichScale) != type(0) or whichScale < 0 or whichScale >= numScales):
      raise RuntimeError, \
              "'whichScale' must be 'all' or an integer between 0 and %d." % self._numScales

    # Validate format of 'whichResponse' arg
    if whichResponse not in ['all', 'centerSurround']:
      if type(whichResponse) != type(0) or whichResponse < 0 or whichResponse >= self._numPlanes:
        raise RuntimeError, \
                "'whichResponse' must be 'all' or an integer between 0 and %d." % self._numPlanes

    # Make sure the requested phase of response exists
    if not imageSet.has_key(whichDirection):
      return

    # Handle "exotic" responses
    if whichResponse != 'all':
      if whichResponse == 'centerSurround':
        whichResponse = self._numOrientations
      assert type(whichResponse) == type(0)
      if whichPhase > 0:
        whichResponse += self._numOrientations
        if self._centerSurround:
          whichResponse += 1

    # Return composite gabor response(s)
    return imageSet[whichDirection][whichResponse][whichScale]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  # Public class methods
  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  @classmethod
  def deserializeImage(cls, serialized):
    """
    Helper function that training/testing scripts can invoke in order
    to deserialize debugging images provided by the getResponseImages()
    method.
    """
    image = Image.open(StringIO(serialized))
    image.load()
    return image


  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  # Private methods - Overriding base class
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
    """
    Perform one-time preparations need for gabor processing.
    """
    #inputDims = [(inputDim['numNodes'][1], inputDim['numNodes'][0]) \
    #             for inputDim in self._inputPyramidTopology]
    self.prepare(inputDims)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def prepare(self, inputDims):
    """
    Perform one-time preparations need for gabor processing.
    Public interface allowing the GaborNode to be tested
    outside of the full RTE.

    @param inputDims: a list of input image sizes in the
          form of 2-tuples (width, height)
    """

    # Reverse the input dims into (height, width) format for internal storage
    self._numScales = len(inputDims)
    self._inputDims = inputDims

    # Compute output dims for each input dim
    self._outputDims = [self.getOutputDims(inputDim) for inputDim in inputDims]

    # Compute the minimum output dimension
    self._minInputDim = min([min(inputDim) for inputDim in self._inputDims])
    self._minOutputDim = min([min(outputDim) for outputDim in self._outputDims])

    # Break out
    self._inHeight, self._inWidth   = [float(x) for x in self._inputDims[0]]
    self._outHeight, self._outWidth = [float(x) for x in self._outputDims[0]]

    # Load the _gaborNode C library
    libGabor = self._loadLibrary("_algorithms")

    # Prepare the C calls
    if libGabor:
      self._gaborComputeProc = libGabor.gaborCompute
    else:
      raise Exception('Unable to load gaborNode C library _algorithms')


      # If we could not load the library, then we'll default to
      # using numpy for our gabor processing.
      self._gaborComputeProc = None

    # Prepare some data structures in advance

    # Allocate working buffers to be used by the C implementation
    #self._buffers = [numpy.zeros(inputDim, dtype=numpy.int32) for inputDim in inputDims]
    self._allocBuffers()

    # Generate post-processing lookup-tables (LUTs) that will be
    # used by the C implementation
    self._makeLUTs()

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

    # Build our Gabor Bank if it doesn't already exist
    self._buildGaborBankIfNeeded()

    # Empirically compute the maximum possible response value
    # given our current parameter settings.  We do this by
    # generating a fake image of size (filterDim X filterDim)
    # that has a pure vertical edge and then convolving it with
    # the first gabor filter (which is always vertically oriented)
    # and measuring the response.
    testImage = numpy.ones((self._filterDim, self._filterDim), dtype=numpy.float32) * 255.0
    #testImage[:, :(self._filterDim/2)] = 0
    testImage[numpy.where(self._gaborBank[0] < 0.0)] *= -1.0
    maxRawResponse = (testImage * self._gaborBank[0]).sum()
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

  def _allocBuffers(self):
    """
    Allocate some working buffers that are required
    by the C implementation.
    """
    # Allocate working buffers to be used by the C implementation
    #self._buffers = [numpy.zeros(inputDim, dtype=numpy.int32) for inputDim in self._inputDims]

    # Compute how much "padding" ou input buffers
    # we will need due to boundary effects
    if self._boundaryMode == 'sweepOff':
      padding = self._filterDim - 1
    else:
      padding = 0

    # For each scale, allocate a set of buffers
    # Allocate a working "input buffer" of unsigned int32
    # We want our buffers to have rows that are aligned on 16-byte boundaries
    #self._bufferSetIn  = []
    #for inHeight, inWidth in self._inputDims:
    #  self._bufferSetIn = numpy.zeros((inHeight + padding,
    #                            _alignToFour(inWidth + padding)),
    #                           dtype=numpy.int32)
    self._bufferSetIn = [numpy.zeros((inHeight + padding,
                                      self._alignToFour(inWidth + padding)),
                                      dtype=numpy.int32) \
                         for inHeight, inWidth in self._inputDims]

    # Allocate a working plane of "output buffers" of unsigned int32
    # We want our buffers to have rows that are aligned on 16-byte boundaries
    #self._bufferSetOut = []
    #for outHeight, outWidth in self._outputDims:
    #  self._bufferSetOut += numpy.zeros((self._numOrientations,
    #                             outHeight,
    #                             _alignToFour(outWith)),
    #                            dtype=numpy.int32)
    numBuffersNeeded = self._numOrientations
    if self._centerSurround:
      numBuffersNeeded += 1
    self._bufferSetOut = [numpy.zeros((numBuffersNeeded,
                                       outHeight,
                                      self._alignToFour(outWidth)),
                                      dtype=numpy.int32) \
                         for outHeight, outWidth in self._outputDims]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _initEphemerals(self):
    self._gaborComputeProc = None
    # For (optional) debug logging, we keep track of the number of
    # images we have seen
    self._imageCounter = 0
    self._bufferSetIn = None
    self._bufferSetOut = None
    self._morphHeader = None
    self._erosion = None
    self._numScales = None
    self._inputDims = None
    self._outputDims = None
    self._minInputDim = None
    self._minOutputDim = None
    self._inHeight = None
    self._inWidth = None
    self._outHeight = None
    self._outWidth = None
    self._postProcLUT = None
    self._postProcLutScalar = None

    self._filterPhase = None
    self.response = None
    self._responseImages = None

    self._makeResponseImages = None
    self.tdInput = None
    self.selectedBottomUpOut = None
    self._tdThreshold = None
    self._morphHeader = None

    if not hasattr(self, '_numPlanes'):
      self._numPlanes = None

    # Assign default values to missing parameters
    for paramName, paramValue in self._defaults.items():
      paramName = self._stripHidingPrefixIfPresent(paramName)
      if not hasattr(self, "_%s" % paramName):
        exec("self._%s = paramValue" % paramName)


  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _getEphemeralMembers(self):
    """
    Callback (to be overridden) allowing the class to publish a list of
    all "ephemeral" members (i.e., data members that should not and/or
    cannot be pickled.)
    """
    # We can't pickle a pointer to a C function
    return [
        '_gaborComputeProc',
        '_bufferSetIn',
        '_bufferSetOut',
        '_imageCounter',
        '_morphHeader',
        '_erosion',
        ]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _loadLibrary(self, libraryName, libSubDir=None):
    """
    Utility method for portably loading a NuPIC shared library.
    Note: we assume the library lives in the NuPIC "lib" directory.

    @param: libraryName - the name of the library (sans extension)
    @returns: reference to the loaded library; otherwise raises
          a runtime exception.
    """

    # By default, we will look for our shared library in our
    # bindings directory.
    if not libSubDir:
      libSubDir = "bindings"

    # Attempt to load the library
    try:
      # All of these shared libraries are python modules.  Let python find them
      # for us.  Once it finds us the path, we'll load it with CDLL.
      dottedPath = ('.'.join(['nupic', libSubDir, libraryName]))
      exec("import %s" % dottedPath)
      libPath = eval("%s.__file__" % dottedPath)

      lib = ctypes.cdll.LoadLibrary(libPath)
      # These calls initialize the logging system inside
      # the loaded library. Disabled for now.
      # See comments at INIT_FROM_PYTHON in gaborNode.cpp
      # pythonSystemRefP = PythonSystem.getInstanceP()
      # lib.initFromPython(ctypes.c_void_p(pythonSystemRefP))
      return lib
    except Exception, e:
      print "Warning: Could not load shared library: %s" % libraryName
      print "Exception: %s" % str(e)
      return None

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  def compute(self, inputs, outputs):
    """
    Run one iteration of fat node, profiling it if requested.

    Derived classes should NOT override this method.

    The guts of the compute are contained in the _compute() call so that
    we can profile it if requested.
    """

    # Modify this line to turn on profiling for a given node. The results file
    #  ('hotshot.stats') will be sensed and printed out by the vision framework's
    #  RunInference.py script and the end of inference.
    # Also uncomment the hotshot import at the top of this file.
    if False:
      if self._profileObj is None:
        self._profileObj = hotshot.Profile("hotshot.stats", 1, 1)
                                          # filename, lineevents, linetimings
      self._profileObj.runcall(self._gaborCompute, *[inputs, outputs])
    else:
      self._gaborCompute(inputs, outputs)

    self._imageCounter += 1

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _getUpperLeftPixelValue(self, inputs, validAlpha=None):
    """
    Extract the intensity value of the upper-left pixel.
    """
    # Obtain raw input pixel data
    #buInputVector = inputs['bottomUpIn'][0].array()
    buInputVector = inputs['bottomUpIn']

    # Respect valid region for selection of
    # color key value
    pixelIndex = 0

    # If we have an alpha channel, then we need to find
    # the first pixel for which the alpha is nonzero
    if validAlpha is not None:
      # Temporarily decode the polarity that is stored
      # in the first alpha element
      indicatorValue = validAlpha[0,0]
      if indicatorValue < 0.0:
        validAlpha[0,0] = -1.0 - indicatorValue
      alphaLocns = numpy.where(validAlpha >= 0.5)[0]
      # Put the indicator back
      validAlpha[0,0] = indicatorValue
      # If there are no positive alpha pixels anywhere, then
      # just use white (255) as the color key (which may not
      # be the "correct" thing to do, but we have no other
      # options really.
      if len(alphaLocns) == 0:
        return 255.0;
      pixelIndex = alphaLocns[0]

    # Otherwise, if we have a bounding box, then we
    # need to find the first (upper-left) pixel in
    # the valid bounding box
    elif 'validRegionIn' in inputs:
      #validRegionIn = inputs['validRegionIn'][0].array()
      validRegionIn = inputs['validRegionIn']
      left = int(validRegionIn[0])
      top  = int(validRegionIn[1])
      if left > 0 or top > 0:
        pixelIndex = left + top * int(self._inWidth)

    return buInputVector[pixelIndex]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _gaborCompute(self, inputs, outputs):
    """
    Run one iteration of multi-node.

    We are taking the unconventional approach of overridding the
    base class compute() method in order to avoid applying the
    splitter map, since this is an expensive process for a densely
    overlapped node such as GaborNode.
    """

    # Build our Gabor Bank (first time only)
    self._buildGaborBankIfNeeded()

    # If we are using "color-key" mode, then detect the value of
    # the upper-left pixel and use it as the value of
    # 'offImagePixelValue'
    if self._offImagePixelValue == "colorKey":
      offImagePixelValue = self._getUpperLeftPixelValue(inputs)
    else:
      offImagePixelValue = float(self._offImagePixelValue)

    # Fast C implementation

    # Get our inputs into numpy arrays
    buInputVector = inputs['bottomUpIn']
    validRegionIn = inputs.get('validRegionIn', None)

    # Obtain access to valid alpha region, if it exists
    # and if we are configured to use the pixel-accurate
    # alpha validity mask (as opposed to using the
    # valid bounding box.)
    if self._suppressByAlpha and 'validAlphaIn' in inputs:
      if self._numScales > 1:
        raise NotImplementedError("Multi-scale GaborNodes cannot currently handle alpha channels")
      # We assume alpha channels are expressed in a format in
      # which '0.0' corresponds to total suppression of
      # responses, and '255.0' corresponds to no suppression
      # whatsoever, and intermediate values apply a linearly
      # proportional degree of suppression (e.g., a value of
      # '127.5' would result in a 50% suppression of the
      # raw responses.)
      #validAlpha = inputs['validAlphaIn'][0].array()[:, numpy.newaxis] * (1.0/255.0)
      validAlpha = inputs['validAlphaIn'][:, numpy.newaxis] * (1.0/255.0)
      # If we are using an alpha channel, then it will take
      # a bit more work to find the correct "upper left"
      # pixel because we can't just look for the first
      # upper-left pixel in the valid bounding box; we have
      # to find the first upper-left pixel in the actual
      # valid alpha zone.
      if self._offImagePixelValue == "colorKey":
        offImagePixelValue = self._getUpperLeftPixelValue(inputs, validAlpha)
    else:
      validAlpha = None

    if self.nta_phaseIndex == 0: # Do bottom-up inference.

      self._computeWithC(buInputVector, validRegionIn,
                         outputs, offImagePixelValue, validAlpha)

      # Cache input. The output is already stored in self.response
      if self._topDownCombiner is not None and self._stage == 'infer':
        self._cachedBUInput = buInputVector
        self._cachedValidRegionIn = validRegionIn

    else: # Try top-down inference.
        cachedBUInput = self._cachedBUInput \
            if self._cachedBUInput is not None else numpy.zeros(0)
        validCachedBUInput = numpy.array_equal(buInputVector, cachedBUInput)
        cachedValidRegionIn = self._cachedValidRegionIn \
            if self._cachedValidRegionIn is not None else numpy.zeros(0)
        validCachedValidRegionIn = ((validRegionIn is None) or
                numpy.array_equal(validRegionIn, cachedValidRegionIn))

        # See if we can use the cached values from the last bottom up compute. For better performance,
        #  we only perform the cache checking when we know we might have top down computes.
        topDownConditionsMet = (self.nta_phaseIndex == 1) and \
            (self._stage == 'infer') and \
            (self._topDownCombiner is not None) and \
            validCachedBUInput and validCachedValidRegionIn

        if not topDownConditionsMet:
          message = (
              ("Top-down conditions were not met for GaborNode:\n") +
              ("  phaseIndex=%s (expected %d)\n" % (self.nta_phaseIndex, 1)) +
              ("  stage='%s' (expected '%s')\n" % (self._stage, "infer")) +
              ("  topDownCombiner is %s (expected not None)\n" %
                ("not None" if (self._topDownCombiner is not None) else "None")) +
              ("  buInputVector %s cache (expected ==)\n" %
                ("==" if validCachedBUInput else "!=")) +
              ("  validRegionIn %s cache (expected ==)\n" %
                ("==" if validCachedValidRegionIn else "!="))
            )
          import warnings
          warnings.warn(message, stacklevel=2)
          return

        # No need to copy to the node outputs, they should be the same as last time.
        # IMPORTANT: When using the pipeline scheduler, you MUST write to the output buffer
        #  each time because there are 2 output buffers.  But, we know that for feedback
        #  networks, the pipleline scheduler cannot and will not be used, so it's OK to
        #  skip the write to the output when we have top down computes.

        # Perform the topDown compute instead
        #print "Gabor topdown"
        buOutput = self.response.reshape(self._inputSplitter.shape[0], self._numPlanes)
        PyRegion._topDownCompute(self, inputs, outputs, buOutput,
                                      buInputVector)

    # DEBUG DEBUG
    #self._logPrefix = "debug"
    #print "WARNING: using a hacked version of GaborNode.py [forced logging]"

    # Write debugging images
    if self._logPrefix is not None:
      self._doDebugLogging()


  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _doDebugLogging(self):
    """
    Dump the most recently computed responses to logging image files.
    """
    preSuppression = False
    # Make the response images if they haven't already been made
    if not self._makeResponseImages:
      self._genResponseImages(self.response, preSuppression=False)
    # Write the response images to disk
    imageSet = self._responseImages[self._getResponseKey(preSuppression=False)]['bottomUp']
    for orient, orientImages in imageSet.items():
      for scale, image in orientImages.items():
        if type(scale) == type(0):
          if type(orient) == type(0):
            orientCode = "%02d" % orient
          else:
            orientCode = "%s" % orient
          debugPath = "%s.img-%04d.scale-%02d.orient-%s.png" % (self._logPrefix,
                                                                self._imageCounter,
                                                                scale, orientCode)
          self.deserializeImage(image).save(debugPath)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def filter(self, image, validRegionIn=None,
                   orientation='all', phase=0,
                   scaleIndex=0,
                   cachedResponse=None,
                   gain=1.0):
    """
    Perform gabor filtering on a PIL image, and return a PIL
    image containing the composite responses.

    @param validRegion: [left, top, right, bottom]
    """

    if validRegionIn is None:
      validRegionIn = (0, 0, image.size[0], image.size[1])

    # Decide whether or not to use numpy
    self._buildGaborBankIfNeeded()

    # Determine proper input/output dimensions
    inHeight,  inWidth  = self._inputDims[scaleIndex]
    outHeight, outWidth = self._outputDims[scaleIndex]
    inputSize  = inHeight * inWidth
    outputSize = outHeight * outWidth * self._numPlanes

    inputVector = numpy.array(image.getdata()).astype(RealNumpyDType)
    inputVector.shape = (inHeight, inWidth)
    assert image.size[1] == inHeight
    assert image.size[0] == inWidth

    # Locate correct portion of output
    outputVector = numpy.zeros((outHeight, outWidth, self._numPlanes), dtype=RealNumpyDType)
    outputVector.shape = (self._numPlanes, outHeight, outWidth)

    inputVector.shape = (inHeight, inWidth)

    # Use a provided responses
    if cachedResponse is not None:
      response = cachedResponse

    # If we need to re-generate the gabor response cache:
    else:

      # If we are using "color-key" mode, then detect the value of
      # the upper-left pixel and use it as the value of
      # 'offImagePixelValue'
      if self._offImagePixelValue == "colorKey":
        # Respect valid region for selection of
        # color key value
        [left, top, right, bottom] = validRegionIn
        offImagePixelValue = inputVector[top, left]
        #offImagePixelValue = inputVector[0, 0]
      else:
        offImagePixelValue = self._offImagePixelValue

      # Extract the bounding box signal (if present).
      validPyramid = validRegionIn / numpy.array([self._inWidth,
                                                 self._inHeight,
                                                 self._inWidth,
                                                 self._inHeight],
                                     dtype=RealNumpyDType)

      # Compute the bounding box to use for our C implementation
      bbox = self._computeBBox(validPyramid, outWidth, outHeight)

      imageBox = numpy.array([0, 0, self._inputDims[scaleIndex][1],
                                    self._inputDims[scaleIndex][0]],
                                    dtype=numpy.int32)

      # Perform gabor processing
      self._doGabor(inputVector, bbox, imageBox, outputVector, scaleIndex, offImagePixelValue)

      outputVector = numpy.rollaxis(outputVector, 0, 3)
      outputVector = outputVector.reshape(outWidth * outHeight, self._numPlanes).flatten()
      assert outputVector.dtype == RealNumpyDType

      numLocns = len(outputVector) / self._numPlanes
      response = outputVector.reshape(numLocns, self._numPlanes)



    nCols, nRows = self._outputPyramidTopology[scaleIndex]['numNodes']
    startNodeIdx, stopNodeIdx = self._getNodeRangeByScale(scaleIndex)

    # Make composite response
    if orientation == 'all':
      # Build all the single-orientation responses
      responseSet = []
      for responseIdx in xrange(self._numPlanes):
        img = Image.new('L', (nCols, nRows))
        img.putdata((gain * 255.0 * response[:stopNodeIdx-startNodeIdx, responseIdx]).astype(numpy.uint8))
        responseSet += [img]
      finalResponse = self._makeCompositeImage(responseSet)
    # Make an individual response
    else:
      img = Image.new('L', (nCols, nRows))
      if orientation == 'centerSurround':
        orientation = self._numOrientations
      if phase > 0:
        orientation += self._numOrientations
        if self._centerSurround:
          orientation += 1
      img.putdata((gain * 255.0 * response[:stopNodeIdx-startNodeIdx, orientation]).astype(numpy.uint8))
      finalResponse = img

    return finalResponse, response

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _buildGaborBankIfNeeded(self):
    """
    Check to see if we have a Gabor Bank, and if not, then build it.
    """
    if self._gaborBank is None:
      self._buildGaborBank()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _doCompute(self, rfInput, rfMask, rfSize, resetSignal, validPyramid):
    """
    Actual compute() implementation.  This is a placeholder that should
    be overridden by derived sub-classes

    @param inputPyramid -- a list of numpy array containing planes of the
                  input pyramid.
    @param rfMask -- a 2-dimensional numpy array (of same shape as 'inputPyramid')
                  that contains a value of 0.0 for every element that corresponds
                  to a padded "dummy" (sentinel) value within 'inputPyramid', and
                  a value of 1.0 for every real input element.
    @param rfSize -- a 1-dimensional numpy array (same number of rows as
                  'inputPyramid') containing the total number of real (non-dummy)
                  elements for each row of 'inputPyramid'.
    @param reset -- boolean indicating whether the current input is the first
                  of a new temporal sequence.
    @param validPyramid -- a 4-element numpy array (vector) that specifies the
                  zone in which the input pyramid is "valid".  A point in the
                  pyramid is "valid" if that point maps to a location in the
                  original image, rather than a "padded" region that was added
                  around the original image in order to scale/fit it into the
                  dimensions of the input pyramid.
                  The 4-element array is in the following format:
                    [left, top, right, bottom]
                  where 'left' is the fraction (between 0 and 1) of the width of
                  the image where the valid zone begins, etc.

    Returns:
      outputPyramid -- a list of numpy arrays containing planes of the
              output pyramid.
    """

    numGaborFilters = self._gaborBank.shape[1]
    numOutputLocns = rfInput.shape[0]

    # ---------------------------------------------------------------
    # Conceptual pipeline:
    #
    # 1. Apply Gabor filtering upon the input pixels X to
    #    generate raw responses Y0  Even in dual-phase mode,
    #    we will only need to perform the actual computations
    #    on a single phase (because the responses can be inverted).
    #
    # 2. Rectify the raw Gabor responses Y0 to produce rectified
    #    responses Y1.
    #
    # 3. Apply an adaptive normalization operation to the
    #    rectified responses Y1 to produce Y2.
    #
    # 4. Amplify the normalized responses Y2 by a fixed gain G
    #    to produce amplified responses Y3.
    #
    # 5. Apply post-processing upon the amplified responses Y3 to
    #    produce final responses Z.
    #

    #----------------------------------
    # Step 1 - Raw Gabor filtering:
    # Convolve each output location against the complete gabor bank.
    responseRaw = numpy.dot(rfInput, self._gaborBank)

    #----------------------------------
    # Step 2 - Rectify responses:
    effectiveInfinity = 1.0e7
    if self._phaseMode == 'single':
      responseRectified = numpy.abs(responseRaw)
    elif self._phaseMode == 'dual':
      responseRectified = numpy.concatenate((responseRaw.clip(min=0.0, max=effectiveInfinity),
                                           (-responseRaw).clip(min=0.0, max=effectiveInfinity)),
                                           axis=1)

    #----------------------------------
    # Step 3 - Adaptive normalization:
    # Step 4 - Amplification

    # If we are not doing any normalization, then it is easy:
    if self._normalizationMethod == 'fixed':
      # In 'fixed' mode, we simply apply a default normalization
      # that takes into account the fact that the input range
      # lies between 0 and 255.
      responseAmplified = responseRectified * (self._gainConstant / 255.0)

    # Otherwise, we have to perform normalization
    else:

      # First we'll apply the power rule, if needed
      if self._normalizationMethod in ['meanPower', 'maxPower']:
        responseToUse = (responseRectified * responseRectified)
      elif self._normalizationMethod in ['mean', 'max']:
        responseToUse = responseRectified

      # At this point, our responseRectified array is of
      # the shape (totNumOutputLocns, numOrients)
      # First, we will perform the max/mean operation over
      # the spatial dimensions; the result will be an
      # intermediate array of the shape:
      # (numScales, numOrients) which will contain the
      # max/mean over the spatial dimensions for each
      # scale and orientation.
      numLayers = len(self._inputPyramidTopology)
      layerOffsets = self._computeLayerOffsets(self._inputPyramidTopology)
      responseStats = []
      for k in xrange(numLayers):
        startOffset = layerOffsets[k]
        stopOffset  = layerOffsets[k+1]
        if self._normalizationMethod in ['max', 'maxPower']:
          responseStats += [responseToUse[startOffset:stopOffset].max(axis=0)[numpy.newaxis, :]]
        elif self._normalizationMethod in ['mean', 'meanPower']:
          responseStats += [responseToUse[startOffset:stopOffset].mean(axis=0)[numpy.newaxis, :]]
      responseStats = numpy.array(responseStats).reshape(numLayers, self._numPlanes)
      # This should be a numpy array containing the desired statistics
      # over the spatial dimensions; one statistic for each tuple
      # of (scale, orientation)

      # If we used a power law, then take the square root of the statistics
      if self._normalizationMethod in ['maxPower', 'meanPower']:
        responseStats = numpy.sqrt(responseStats)

      # Compute statistics over orientation (if needed)
      if not self._perOrientNormalization:
        if self._normalizationMethod in ['max', 'maxPower']:
          responseStats = responseStats.max(axis=1)
        elif self._normalizationMethod in ['mean', 'meanPower']:
          responseStats = responseStats.mean(axis=1)
        responseStats = responseStats[:, numpy.newaxis]
        # At this point, responseStats is of shape: (numLayers, 1)

      # Compute statistics over scale (if needed)
      if not self._perScaleNormalization:
        if self._normalizationMethod in ['max', 'maxPower']:
          responseStats = responseStats.max(axis=0)
        elif self._normalizationMethod in ['mean', 'meanPower']:
          responseStats = responseStats.mean(axis=0)
        # Expand back out for each scale
        responseStats = responseStats[numpy.newaxis, :] * numpy.ones((numLayers, 1))

      # Expand back out for each orientation
      if not self._perOrientNormalization:
        responseStats = responseStats[:, numpy.newaxis] * numpy.ones((1, self._numPlanes))

      # Step 4 - Amplification
      responseStats = responseStats.reshape(numLayers, self._numPlanes)
      gain = self._gainConstant * numpy.ones((numLayers, self._numPlanes), dtype=RealNumpyDType)
      nonZeros = numpy.where(responseStats > 0.0)
      gain[nonZeros] /= responseStats[nonZeros]

      # Fast usage case: neither per-scale nor per-orient normalization
      if not self._perScaleNormalization and not self._perOrientNormalization:
        responseAmplified = responseRectified * gain[0, 0]

      # Somewhat slower: per-orient (but not per-scale) normalization
      elif not self._perScaleNormalization:
        responseAmplified = responseRectified * gain[0, :]

      # Slowest: per-scale normalization
      else:
        responseAmplified = None
        for k in xrange(numLayers):
          startOffset = layerOffsets[k]
          stopOffset  = layerOffsets[k+1]
          if not self._perOrientNormalization:
            gainToUse = gain[k, 0]
          else:
            gainToUse = gain[k, :]
          thisResponse = responseRectified[startOffset:stopOffset, :] * gainToUse
          if responseAmplified is None:
            responseAmplified = thisResponse
          else:
            responseAmplified = numpy.concatenate((responseAmplified, thisResponse), axis=0)

    #----------------------------------
    # Step 5 - Post-processing

    # No post-processing (linear)
    if self._postProcessingMethod == "raw":
      responseFinal = responseAmplified

    # Sigmoidal post-processing
    elif self._postProcessingMethod == "sigmoid":
      offset = 1.0 / (1.0 + numpy.exp(self._postProcessingSlope * self._postProcessingCenter))
      scaleFactor = 1.0 / (1.0 - offset)
      responseFinal = ((1.0 / (numpy.exp(numpy.clip(self._postProcessingSlope \
                    * (self._postProcessingCenter - responseAmplified), \
                    -40.0, 40.0)) + 1.0)) - offset) * scaleFactor

    # Piece-wise linear post-processing
    elif self._postProcessingMethod == "threshold":
      responseFinal = responseAmplified
      responseFinal[responseAmplified < self._postProcessingMin] = 0.0
      responseFinal[responseAmplified > self._postProcessingMax] = 1.0

    #----------------------------------
    # Optional: Dump statistics for comparative purposes
    #self._dumpStats(responseFinal, "gabor.stats.txt")

    # Generate raw response images (prior to suppression)
    if self._makeResponseImages:
      self._genResponseImages(responseFinal, preSuppression=True)

    # Apply suppression to responses outside valid pyramid.
    if self._suppressOutsideBox:
      self._applyValiditySuppression(responseFinal, validPyramid)

    # Perform the zeroOutThreshold clipping now if requested
    if self._zeroThresholdOut > 0.0:
      # Get the max of each node
      nodeMax = responseFinal.max(axis=1).reshape(numOutputLocns)
      # Zero out children where all elements are below the threshold
      responseFinal[nodeMax < self._zeroThresholdOut] = 0

    # Generate final response images (after suppression)
    if self._makeResponseImages:
      self._genResponseImages(responseFinal, preSuppression=False)

    # Store the response so that it can be retrieved later
    self.response = responseFinal
    return responseFinal

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _applyValiditySuppression(self, response, validPyramid):
    """
    Apply suppression to responses outside valid pyramid.
    This overrides the default PyRegion implementation.
    """

    # We compute the valid fraction of each output locations' RF by
    # computing the valid fraction of it's spatial dimension.
    # @todo -- Generalize this to handle more than two spatial dimensions.
    validX = (self._rfMaxX.clip(min=validPyramid[0], max=validPyramid[2]) - \
              self._rfMinX.clip(min=validPyramid[0], max=validPyramid[2])) * \
              self._rfInvLenX
    validY = (self._rfMaxY.clip(min=validPyramid[1], max=validPyramid[3]) - \
              self._rfMinY.clip(min=validPyramid[1], max=validPyramid[3])) * \
              self._rfInvLenY
    # At this point the validX and validY numpy vectors contain values
    # between 0 and 1 that encode the validity of each output location
    # with respect to the X and Y spatial dimensions, respectively.

    # Now we map the raw validities of each output location into
    # suppression factors; i.e., a scalar (for each output location)
    # that will be multiplied against each response for that particular
    # output location.

    # Use a hard threshold:

    # Discovered a nasty, subtle bug here.  The code used to be like this:
    #
    # suppressionFactor = ((validX * validY) >= self._validitySuppressionLow).astype(RealNumpyDType)
    #
    # However, in the case of validitySuppressionLow of 1.0, numpy experienced
    # "random" roundoff errors, and nodes for which both validX and validY were
    # 1.0 would be computed as 1 - epsilon, which would fail the test against
    # validitySuppressionLow, and thus get suppressed incorrectly.
    # So we introduced an epsilon to deal with this situation.
    suppressionFactor = ((validX * validY) + self._epsilon >= \
                         self._validitySuppressionLow).astype(RealNumpyDType)

    # Apply the suppression factor to the output response array
    response *= suppressionFactor[:, numpy.newaxis]

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _dumpStats(self, response, statsLogPath):
    """
    In order to do a kind of "unit testing" of the GaborNode
    tuning parameters for a particular application, it is useful
    to dump statistics on the responses at different scales
    and orientations/phases.

    We'll dump the following statistics for each (scale, orientation) tuple:
      * response mean
      * response standard deviation
      * power mean (squared response mean)
      * response max

    @param response -- response array of shape (totNumOutputLocns, numOrients)
    """
    meanResponse = []
    meanPower = []
    stddevResponse = []
    maxResponse = []

    # Compute a squared (power) response
    power = response * response

    # Compute our mean/max/stddev statistics over the spatial dimensions
    # for each scale and for each orientation.  The result will be four
    # array of shape: (numScales, numOrients) which will contain the
    # statistics over the spatial dimensions for each scale and orientation.
    numLayers = len(self._outputPyramidTopology)
    layerOffsets = self._computeLayerOffsets(self._outputPyramidTopology)
    for k in xrange(numLayers):
      startOffset = layerOffsets[k]
      stopOffset  = layerOffsets[k+1]
      # Mean response
      meanResponse += [response[startOffset:stopOffset].mean(axis=0)[numpy.newaxis, :]]
      # Max response
      maxResponse += [response[startOffset:stopOffset].max(axis=0)[numpy.newaxis, :]]
      # Std. deviation response
      stddevResponse += [response[startOffset:stopOffset].std(axis=0)[numpy.newaxis, :]]
      # Mean power
      meanPower += [power[startOffset:stopOffset].mean(axis=0)[numpy.newaxis, :]]

    # Now compile the responses at each scale into overall arrays
    # of shape: (numScales, numOrientations)
    meanResponse = numpy.array(meanResponse).reshape(numLayers, self._numPlanes)
    maxResponse = numpy.array(maxResponse).reshape(numLayers, self._numPlanes)
    stddevResponse = numpy.array(stddevResponse).reshape(numLayers, self._numPlanes)
    meanPower = numpy.array(meanPower).reshape(numLayers, self._numPlanes)

    # Finally, form the different statistics into a single desriptive vector
    responseStats = numpy.concatenate((meanResponse[numpy.newaxis,:,:],
                                       maxResponse[numpy.newaxis,:,:],
                                       stddevResponse[numpy.newaxis,:,:],
                                       meanPower[numpy.newaxis,:,:]), axis=0)

    # Append to the stats log
    fpStatsLog = open(statsLogPath, "a")
    response = " ".join(["%f" % x for x in responseStats.flatten().tolist()])
    fpStatsLog.write(response + "\n")
    fpStatsLog.close()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _doTopDownInfer(self, tdInput, tdNumParents, buOutput, buInput):
    """
    Actual top down compute() implementation.  This is a placeholder that should
    be overridden by derived sub-classes.

    @param tdInput -- a 3D array containing the top-down inputs to each baby node.
                      Think of this as N 2D arrays, where N is the number of baby nodes.
                      Each baby node's 2D array has R rows, where each row is the top-down
                      output from one of the parents. The width of each row is equal to the
                      width of the bottomUpOut of the baby node. If a baby node
                      has only 2 parents, but R is 5 for example, then the last 3 rows
                      of the 2D array will contain all 0's. The tdNumParents argument
                      can be referenced to find out how many parents the node actually has.
                      The tdInput array is structured in this manner to make it easy to
                      sum the contributions from the parents. All the sub-class needs to
                      do is a numpy.add.reduce(tdInput, axis=1).
    @param tdNumParents a vector whose length is equal to the number of baby nodes. Each
                      element contains the number of parents of each baby node.
    @param buInput -- a 2D array containing the bottom-up inputs to each baby node.
                      This is the same input that is passed to the _doCompute() method,
                      but it is called rfInput there.
    @param buOutput -- a 2D array containing the results of the bottomUp compute for
                      this node. This is a copy of the return value returned from the
                      _doCompute method of the node.
    Returns:
      tdOutput -- a 2-D numpy array containing the outputs from each baby node. Each
                  row is a baby node output.
    """

    # NOTE: Making this a float32 makes the copy to the node outputs at the end of
    #  the compute faster.
    #tdOutput = numpy.zeros(self._inputSplitter.shape, dtype='float32')

#     print "Top-down infer called on a Gabor node.  Use breakpoint to step through"
#     print "and make sure things are as expected:"
#     import pdb; pdb.set_trace()

    numBabyNodes = len(tdInput)
    numOrients = len(tdInput[0][0])
    assert self._numPlanes == numOrients # Number of filters must match top-down input
    tdThreshold = numpy.ones((numBabyNodes, numOrients))
    version=('tdThreshold', 'combine', 'td_normalize')
    minResponse=1e-10

    # Average top-down inputs for each baby Node
    tdInput_avg = numpy.add.reduce(tdInput, axis=1) / tdNumParents

    # For the gabor node, we will usually get 1 orientation fed down from
    #  the complex level above us. This is because the SparsePooler above that
    #  sparsified it's inputs and only saves one orientation from each complex node.
    # But, for the Gabor node which is at the bottom of the hierarchy, it makes more
    #  sense to spread the topdown activation among all the orientations since
    #  each gabor covers only a few pixels and won't select one object from another.
    tdMaxes = tdInput_avg.max(axis=1)
    tdInput_avg *= 0
    tdInput_avg += tdMaxes.reshape(-1,1)

    if tdInput_avg.max() <= minResponse:
      #print "Top-down Input is Blank"
      pass
    else:
      if 'combine' in version:  # Combine top-down and bottom-up inputs
        tdInput_avg *= buOutput
      if 'td_normalize' in version: # Normalize top-down inputs for viewing
#         td_max = tdInput_avg.max()
#         tdInput_avg /= td_max
        td_max = tdInput_avg.max()
        if td_max != 0:
          tdInput_avg /= td_max
      if 'tdThreshold' in version: # Use tdInput_avg to threshold bottomUp outputs
        if not hasattr(self, '_tdThreshold'):
          self._tdThreshold = 0.01
        tdThreshold = tdInput_avg > self._tdThreshold

    self.tdInput = tdInput_avg
    self.selectedBottomUpOut = buOutput * tdThreshold
    theMax = self.selectedBottomUpOut.max()
    if theMax > 0:
      self.selectedBottomUpOut /= theMax

    # Generate response images
    if self._makeResponseImages:
      self._genResponseImages(self.tdInput, preSuppression=False, phase='topDown')
      self._genResponseImages(self.selectedBottomUpOut, preSuppression=False,
                              phase='combined')

    # Generate the topDown outputs. At this point, tdMaxes contains the max gabor orientation
    #  output from each baby node. We will simply "spread" this value across all of the
    #  topDown outputs for each baby node as an indication of their input activation level.
    # In a perfect world, you would try and reconstruct the input by summing the inverse of the
    #  gabor operation for each output orientation. But, for now, we are only using the top
    #  down output of the Gabor as an indication of the relative input strength to each gabor
    #  filter - essentially as a mask on the input image.
    tdOutput = numpy.ones(self._inputSplitter.shape, dtype='float32')
    tdOutput *= tdMaxes.reshape(-1,1)

    # Save the maxTopDownOut for each baby node so that it can be returned as a read-only
    # parameter. This provides faster performance for things like the top down image inspector
    # that only need the max output from each node
    self._maxTopDownOut = tdMaxes
    return tdOutput


  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  def _computeWithC(self,
                    inputPlane,
                    validRegionIn,
                    outputs,
                    offImagePixelValue,
                    validAlpha):
    """
    Perform Gabor processing using custom C library.
    """
    if validRegionIn is None:
      validRegionIn = (0, 0, self._inWidth, self._inHeight)

    inputLen = len(inputPlane)
    if self._inputPyramidTopology is None or \
       inputLen == self._inWidth * self._inHeight * len(self._inputPyramidTopology):
      isPadded = True
    else:
      assert inputLen == sum([lvl['numNodes'][0] * lvl['numNodes'][1] \
                             for lvl in self._inputPyramidTopology])
      isPadded = False

    # Extract the bounding box signal (if present).
    validPyramid = validRegionIn / numpy.array([self._inWidth,
                                               self._inHeight,
                                               self._inWidth,
                                               self._inHeight],
                                   dtype=RealNumpyDType)

    # First extract a numpy array containing the entire input vector
    assert inputPlane.dtype == numpy.float32

    # Convert the output images to a numpy vector
    #outputPlane = outputs['bottomUpOut'].wvector()[:].array()
    outputPlane = outputs['bottomUpOut']
    assert outputPlane.dtype == numpy.float32

    inputOffset  = 0
    outputOffset = 0
    for scaleIndex in xrange(self._numScales):

      # Handle padded case (normal)
      if isPadded:
        inputScaleIndex = 0
      # Handle packed case (deployed)
      else:
        inputScaleIndex = scaleIndex

      # Determine proper input/output dimensions
      inHeight,  inWidth  = self._inputDims[inputScaleIndex]
      outHeight, outWidth = self._outputDims[scaleIndex]
      inputSize  = inHeight * inWidth
      outputSize = outHeight * outWidth * self._numPlanes

      # Locate correct portion of input
      inputVector = inputPlane[inputOffset:inputOffset+inputSize]
      inputOffset += inputSize
      inputVector.shape = (inHeight, inWidth)

      # Locate correct portion of output
      outputVector = outputPlane[outputOffset:outputOffset+outputSize]
      outputVector.shape = (self._numPlanes, outHeight, outWidth)

      # Compute the bounding box to use for our C implementation
      bbox = self._computeBBox(validPyramid, self._inputDims[scaleIndex][1],
                                             self._inputDims[scaleIndex][0])
      imageBox = numpy.array([0, 0, self._inputDims[scaleIndex][1],
                                    self._inputDims[scaleIndex][0]],
                                    dtype=numpy.int32)

      ## --- DEBUG CODE ----
      #global id
      #o = inputVector
      #print outputVector.shape, len(o)
      #f = os.path.abspath('gabor_input_%d.txt' % id)
      #print f
      #numpy.savetxt(f, o)
      #id += 1
      ##from dbgp.client import brk; brk(port=9019)
      ## --- DEBUG CODE END ----

      # Erode and/or dilate the alpha channel
      # @todo -- This should be moved into the C function
      if validAlpha is not None:
        validAlpha = self._adjustAlphaChannel(validAlpha)

      # Perform gabor processing
      self._doGabor(inputVector,
                     bbox,
                     imageBox,
                     outputVector,
                     scaleIndex,
                     offImagePixelValue,
                     validAlpha)

      # Optionally, dump working buffers for debugging purposes
      if self._debugLogBuffers:
        self._logDebugBuffers(outputVector, scaleIndex);

      # Note: it would be much better if we did not have to do this
      # post-processing "transposition" operation, and instead just
      # performed all the different orientation computations for
      # each pixel.
      # Note: this operation costs us about 1 msec
      outputVector = numpy.rollaxis(outputVector, 0, 3)
      outputVector = outputVector.reshape(outWidth * outHeight, self._numPlanes)
      assert outputVector.dtype == numpy.float32

      # Perform the zeroOutThreshold clipping now if requested
      # @todo -- This should be moved into the C function
      if self._zeroThresholdOut > 0.0:
        # Get the max of each node
        nodeMax = outputVector.max(axis=1).reshape(outWidth * outHeight)
        # Zero out children where all elements are below the threshold
        outputVector[nodeMax < self._zeroThresholdOut] = 0.0

      outputPlane[outputOffset:outputOffset+outputSize] = outputVector.flatten()
      outputOffset += outputSize

    # Generate final response images (after suppression)
    if self._makeResponseImages:
      self._genResponseImages(outputPlane, preSuppression=False)

    # Store the response so that it can be retrieved later
    self.response = outputPlane

    ## --- DEBUG CODE ----
    #global id
    #o = outputPlane
    ##print outputVector.shape, len(o)
    #f = os.path.abspath('gabor_output_%d.txt' % id)
    #print f
    #numpy.savetxt(f, o)
    #id += 1
    ##from dbgp.client import brk; brk(port=9019)
    ## --- DEBUG CODE END ----

    # De-multiplex inputs/outputs
    #outputs['bottomUpOut'].wvector()[:] = outputPlane
    outputs['bottomUpOut'] = outputPlane

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _adjustAlphaChannel(self, alphaMask):
    """
    Apply an alpha suppression channel (in place) to each plane
    of gabor responses.

    @param alphaMask: a numpy array of shape (numPixels, 1)
          containing the alpha mask that determines which responses
          are to be suppressed.  If the values in the alpha mask
          are in the range (0.0, 255.0), then the alpha mask will
          be eroded by halfFilterDim; if the values in the alpha
          mask are in the range (-255.0, 0.0), then the mask will
          be dilated by halfFilterDim.
    """

    # Determine whether to erode or dilate.
    # In order to make this determination, we check
    # the sign of the first alpha pixel:
    #
    # MorphOp     true mask[0,0]     alpha[0,0] code
    # =======     ==============     ===============
    # erode       0   (background)   0
    # erode       255 (foreground)   255
    # dilate      0   (background)   -1
    # dilate      255 (foreground)   -256
    indicatorValue = alphaMask[0,0]
    if indicatorValue < 0.0:
      operation = 'dilate'
      # Convert the alpha value back to it's
      # true value
      alphaMask[0,0] = -1.0 - indicatorValue
    else:
      operation = 'erode'

    # We need to perform enough iterations to cover
    # half of the filter dimension
    halfFilterDim = (self._filterDim - 1) / 2

    if self._morphologyMethod == "opencv" or \
       (self._morphologyMethod == "best" and cv is not None):
      # Use the faster OpenCV code path
      assert cv is not None

      # Lazily allocate the necessary OpenCV wrapper structure(s)
      self._prepMorphology()

      # Make the OpenCV image header structure's pixel buffer
      # pointer point at the underlying memory buffer of
      # the alpha channel (numpy array)
      self._morphHeader.contents.imageData = alphaMask.ctypes.data

      # Perform dilation in place
      if operation == 'dilate':
        cv.Dilate(self._morphHeader, self._morphHeader, iterations=halfFilterDim)

      # Perform erosion in place
      else:
        cv.Erode(self._morphHeader, self._morphHeader, iterations=halfFilterDim)

    else:
      # Use the custom C++ code path
      if not self._erosion:
        from nupic.bindings.algorithms import Float32Erosion
        self._erosion = Float32Erosion()
        self._erosion.init(int(self._inHeight), int(self._inWidth))
      # Perform the erosion/dilation in-place
      self._erosion.compute(alphaMask,
                            alphaMask,
                            halfFilterDim,
                            (operation=='dilate'))

    # Legacy numpy method
    # If we are in constrained mode, then the size of our
    # response planes will be less than the size of our
    # alpha mask (by halfFilterDim along each edge).
    # So we need to "shave off" halfFilterDim pixels
    # from all edges of the alpha mask before applying
    # suppression to the response planes.
    inWidth = int(self._inWidth)
    inHeight = int(self._inHeight)

    # For erosion mode, we need to shave off halfFilterDim
    # from the four edges of the alpha mask.
    if operation == "erode":
      alphaMask.shape = (inHeight, inWidth)
      alphaMask[:halfFilterDim, :]  = 0.0
      alphaMask[-halfFilterDim:, :] = 0.0
      alphaMask[:, :halfFilterDim]  = 0.0
      alphaMask[:, -halfFilterDim:] = 0.0
      alphaMask.shape = (inHeight * inWidth, 1)

    # For dilation mode, we need to shave off halfFilterDim
    # from any edge of the alpha mask that touches the
    # image boundary *unless* the alpha mask is "full"
    # (i.e., consumes the entire image.)
    elif operation == "dilate":
      # Handle top, bottom, left, and right
      alphaMask.shape = (inHeight, inWidth)
      zapTop = numpy.where(alphaMask[0,:])[0]
      zapBottom = numpy.where(alphaMask[-1,:])[0]
      zapLeft = numpy.where(alphaMask[:,0])[0]
      zapRight = numpy.where(alphaMask[:,-1])[0]
      # Apply zaps unless all of them are of the full
      # length possible
      if len(zapTop) < inWidth or len(zapBottom) < inWidth or \
         len(zapLeft) < inHeight or len(zapRight) < inHeight:
        alphaMask[:halfFilterDim, zapTop] = 0.0
        alphaMask[-halfFilterDim:, zapBottom] = 0.0
        alphaMask[zapLeft, :halfFilterDim] = 0.0
        alphaMask[zapRight, -halfFilterDim:] = 0.0
      alphaMask.shape = (inHeight * inWidth, 1)

    return alphaMask

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _prepMorphology(self):
    """
    Prepare buffers used for eroding/dilating alpha
    channels.
    """

    # Check if we've already allocated a header
    #if not hasattr(self, '_morphHeader'):
    if not getattr(self, '_morphHeader', None):

      if cv is None:
        raise RuntimeError("OpenCV not available on this platform")

      # Create a header only (not backed by data memory) that will
      # allow us to operate on numpy arrays (valid alpha channels)
      # using OpenCV operations
      self._morphHeader = cv.CreateImageHeader(cv.Size(int(self._inWidth),
                                                       int(self._inHeight)), 32, 1)

      # @todo: this will leak a small bit of memory every time
      # we create and use a new GaborNode unless we find a way
      # to guarantee the invocation of cv.ReleaseImageHeader()

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

  def _logDebugBuffers(self, outputVector, scaleIndex, outPrefix="debug"):
    """
    Dump detailed debugging information to disk (specifically, the
    state of internal working buffers used by C implementaiton.

    @param outPrefix -- Prefix to prepend to standard names
          for debugging images.
    """
    # Save input buffer
    self._saveImage(self._bufferSetIn[scaleIndex],
                    "%s.buffer.in.%02d.png" % (outPrefix, scaleIndex))

    # Save output buffer planes
    for k in xrange(self._bufferSetOut[scaleIndex].shape[0]):
      # We do integer arithmetic shifted by 12 bits
      buf = (self._bufferSetOut[scaleIndex][k] / 4096).clip(min=0, max=255);
      self._saveImage(buf, "%s.buffer.out.%02d.%02d.png" % (outPrefix, scaleIndex, k))

    # Save raw gabor output images (from C implementation)
    for k in xrange(self._numPlanes):
      self._saveImage(outputVector[k], "%s.out.%02d.%02d.png" % \
                      (outPrefix, scaleIndex, k))

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _saveImage(self, imgArray, outPath):
    imgDims = imgArray.shape
    img = Image.new('L', (imgDims[1], imgDims[0]))
    if imgArray.dtype == numpy.float32:
      img.putdata( ((254.9 * imgArray.flatten()).clip(min=0.0, max=255.0)).astype(numpy.uint8) )
      #img.putdata((255.0 * imgArray.flatten()).astype(numpy.uint8))
    elif imgArray.dtype == numpy.int32:
      img.putdata((imgArray.flatten()).astype(numpy.uint8))
    else:
      assert imgArray.dtype == numpy.uint8
      img.putdata(imgArray.flatten())
    img.save(outPath)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _doGabor(self, inputVector,
                     bbox,
                     imageBox,
                     outputVector,
                     scaleIndex,
                     offImagePixelValue=None,
                     validAlpha=None):
    """
    Prepare arguments and invoke C function for
    performing actual 2D convolution, rectification,
    normalization, and post-processing.
    """
    if offImagePixelValue is None:
      assert type(offImagePixelValue) in [type(0), type(0.0)]
      offImagePixelValue = self._offImagePixelValue

    # If we actually have a valid validAlpha mask,
    # then reshape it to the input image size
    if validAlpha is not None:
      origAlphaShape = validAlpha.shape
      validAlpha.shape = inputVector.shape

    # Invoke C function
    result = self._gaborComputeProc(
              self._wrapArray(self._gaborBank),
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
              self._wrapArray(self._bufferSetIn[scaleIndex]),
              self._wrapArray(self._bufferSetOut[scaleIndex]),
              self._wrapArray(self._postProcLUT),
              ctypes.c_float(self._postProcLutScalar),
              )
    if result < 0:
      raise Exception("gaborCompute failed")

    # If we actually have a valid validAlpha mask,
    # then reshape it back to it's original shape
    if validAlpha is not None:
      validAlpha.shape = origAlphaShape

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _convertEnumValue(self, enumValue):
    """
    Convert a Python integer object into a ctypes integer
    that can be passed to a C function and seen as an
    int on the C side.
    """
    return ctypes.c_int(enumValue)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

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
  # Private helper methods
  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _getValidEdgeModes(self):
    """
    Returns a list of the valid edge modes.
    """
    return ['constrained', 'sweepOff']

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _serializeImage(self, image):
    """
    Serialize a PIL image so that it can be transported through
    the runtime engine.
    """
    s = StringIO()
    format = 'png'
    if hasattr(image, 'format') and image.format:
      format = image.format
    try:
      image.save(s, format=format)
    except:
      image.save(s, format='png')
    return s.getvalue()

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _getResponseKey(self, preSuppression):
    """
    Returns a key used to index the response image dict
    (either 'raw' or 'final')
    """
    if preSuppression:
      return 'raw'
    else:
      return 'final'

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _genResponseImages(self, rawResponse, preSuppression, phase='bottomUp'):
    """
    Generate PIL images from the response array.

    @param preSuppression -- a boolean, which indicates whether to
          store the generated images using the key 'raw' (if True)
          or 'final' (if False) within the _responseImages member dict.
    @param phase -- 'bottomUp', 'topDown', or 'combined', depending on which
          phase of response image we're generating

    Generate a dict of dicts.  The primary dict is keyed by response,
    which can be either 'all' or an integer between 0 and numOrients-1;
    the secondary dicts are keyed by scale, which can be either 'all'
    or an integer between 0 and numScales.
    """

    if phase not in ('bottomUp', 'topDown', 'combined'):
      raise RuntimeError, "phase must be either 'bottomUp', 'topDown', or 'combined'"

    numLocns = len(rawResponse.flatten()) / self._numPlanes
    response = rawResponse.reshape(numLocns, self._numPlanes)

    #numScales = len(self._inputPyramidTopology)
    numScales = self._numScales

    imageSet = {}

    # Build all the single-orientation responses
    for responseIdx in xrange(self._numPlanes):
      responseSet = {}

      # Build all the scales
      for scaleIdx in xrange(numScales):
        responseSet[scaleIdx] = self._makeImage(response, scaleIdx, responseIdx)

      # Build the "all scale" list
      #responseSet['all'] = responseSet.values()
      imageSet[responseIdx] = responseSet

    # Build the composite respones
    responseSet = {}
    for scaleIdx in xrange(numScales):
      scaleSet = [imageSet[orientIdx][scaleIdx] for orientIdx in xrange(self._numPlanes)]
      responseSet[scaleIdx] = self._makeCompositeImage(scaleSet)
    imageSet['all'] = responseSet

    # Serialize all images
    for orientIdx, orientResponses in imageSet.items():
      for scaleIdx, scaleResponse in orientResponses.items():
        imageSet[orientIdx][scaleIdx] = self._serializeImage(scaleResponse)
      imageSet[orientIdx]['all'] = imageSet[orientIdx].values()

    # Store the image set
    if self._responseImages is None:
      self._responseImages = {self._getResponseKey(preSuppression): {}}
    self._responseImages[self._getResponseKey(preSuppression)][phase] = imageSet

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _getNodeRangeByScale(self, whichScale):
    """
    Returns a 2-tuple of node indices corresponding to the set of
    nodes associated with the specified 'whichScale'.
    """
    assert whichScale >= 0
    #assert whichScale < len(self._outputPyramidTopology)
    assert whichScale < self._numScales
    startNodeIdx = 0
    #for scaleIndex, outputTopo in enumerate(self._outputPyramidTopology):
    for scaleIndex, outputDim in enumerate(self._outputDims):
      #nCols, nRows = outputTopo['numNodes']
      nRows, nCols = outputDim
      stopNodeIdx = startNodeIdx + nCols * nRows
      if scaleIndex == whichScale:
        return (startNodeIdx, stopNodeIdx)
      else:
        startNodeIdx = stopNodeIdx
    assert False

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _makeImage(self, response, whichScale, whichOrient, gain=1.0):
    """
    Generate a single PIL image (using the raw response array) for a
    particular scale and orientation.
    """
    #nCols, nRows = self._outputPyramidTopology[whichScale]['numNodes']
    nRows, nCols = self._outputDims[whichScale]
    img = Image.new('L', (nCols, nRows))
    startNodeIdx, stopNodeIdx = self._getNodeRangeByScale(whichScale)
    img.putdata((gain * 255.0 * response[startNodeIdx:stopNodeIdx,
                 whichOrient]).clip(min=0.0, max=255.0).astype(numpy.uint8))
    return img

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _makeCompositeImage(self, imageSet):
    """
    Create a false color composite image of the individiual
    orientation-specific gabor response images in 'imageSet'.
    """
    # Generate the bands
    numBands = 3
    bands = [Image.new('L',imageSet[0].size)] * numBands
    for k, img in enumerate(imageSet):
      whichBand = k % numBands
      bands[whichBand] = ImageChops.add(bands[whichBand], img)

    # Make final composite for this scale
    compositeImage = Image.merge(mode='RGB', bands=bands)
    return compositeImage

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  if False:
    def _getEffectiveOrients(self):
      """
      Internal helper method that returns the number of "effective"
      orientations (which treats the dual phases responses as a
      single orientation.)
      """
      numEffectiveOrients = self._numPlanes
      if self._phaseMode == 'dual':
        numEffectiveOrients /= 2
      if self._centerSurround:
        numEffectiveOrients -= 1
      return numEffectiveOrients

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _buildGaborBank(self):
    """
    Build an array of Gabor filters.  Also build a 1-D vector of
    filter bank indices that maps each output location to a particular
    (customized) bank of gabor filters.

    """

    # Make sure dimensions of our Gabor filters are odd
    assert self._filterDim % 2 == 1

    # Create mesh grid indices.  The result will be a numpy array of
    # shape (2, filterDim, filterDim).
    # Then meshGrid[0] stores the row indices of the master grid,
    # and meshGrid[1] stores the column indices.
    lowerIndex = -(self._filterDim / 2)
    upperIndex = 1 + self._filterDim / 2
    meshGrid = numpy.mgrid[lowerIndex:upperIndex, lowerIndex:upperIndex]

    # If we are supposed to produce only center-surround output
    # (no oriented responses), then we will still go through the
    # process of making a minimalist bank of 2 oriented gabor
    # filters since that is needed by the center-surround filter
    # generation code
    numOrientations = self._numOrientations
    if numOrientations == 0:
      numOrientations = 2

    # Select the orientation sample points (in radians)
    radianInterval = numpy.pi / float(numOrientations)
    orientations = numpy.array(range(numOrientations), dtype=RealNumpyDType) * \
                   radianInterval

    # Compute trigonometric functions of orientation
    sinTheta = numpy.sin(orientations).reshape(numOrientations, 1, 1)
    cosTheta = numpy.cos(orientations).reshape(numOrientations, 1, 1)

    # Construct two filterDim X filterDim arrays containing y (row) and
    # x (column) coordinates (in dimensions of pixels), respectively.
    y = meshGrid[0].reshape(1, self._filterDim, self._filterDim)
    x = meshGrid[1].reshape(1, self._filterDim, self._filterDim)
    X = x * cosTheta - y * sinTheta
    Y = x * sinTheta + y * cosTheta

    # Build the Gabor filters
    #if hasattr(self, '_phase') and self._phase == 'edge':
    if self._targetType == 'edge':
      sinusoidalTerm = numpy.sin(2.0 * numpy.pi / self._wavelength * X)
    else:
      sinusoidalTerm = numpy.cos(2.0 * numpy.pi / self._wavelength * X)
    numerator = (X * X + self._aspectRatio * self._aspectRatio * Y * Y)
    denominator = -2.0 * self._effectiveWidth * self._effectiveWidth
    exponentialTerm = numpy.exp(numerator / denominator)
    gaborBank = sinusoidalTerm * exponentialTerm

    # Add center-surround filters, if requsted
    if self._centerSurround:
      expFilter = exponentialTerm[0] * exponentialTerm[numOrientations/2]
      # Cubing the raw exponential component seems to give a nice
      # center-surround filter
      centerSurround = expFilter * expFilter * expFilter
      # If our center-surround filter is in addition to the oriented
      # filter, then concatenate it to our filter bank; otherwise
      # it is the filter bank
      if self._numOrientations > 0:
        gaborBank = numpy.concatenate((gaborBank, centerSurround[numpy.newaxis,:,:]))
      else:
        gaborBank = centerSurround[numpy.newaxis,:,:]

    # Apply lobe suppression: Suppress the outer lobes of the sinusoidal
    # component of the Gabor filters so as to avoid "ringing" effects in
    # the Gabor response maps.
    #
    # We make a single lobe-suppression mask (which is directionally
    # oriented.)  Then we rotate this mask by each orientation and
    # apply it to the pre-suppressed filter bank.
    # In order to minimize discontinuities in the gradients, the
    # suppression mask will be constructed as follows:
    #
    #   y = 1 - |x|^p
    #
    # where:
    #   y = Suppression (0 for total suppression, 1 for no-suppression)
    #   x = position relative to center
    #   p = Some exponent that controls the sharpness of suppression

    numGaborFilters = gaborBank.shape[0]

    # New lobe suppression.
    if self._lobeSuppression:
      # The orientation is always vertical, so we'll locate the discrete
      # filter cell where we go negative
      halfFilterDim = (self._filterDim - 1) / 2
      firstBadCell = None
      for cellIdx in xrange(halfFilterDim, self._filterDim):
        if gaborBank[0, 0, cellIdx] < 0.0:
          firstBadCell = cellIdx - halfFilterDim
          break
      if firstBadCell is not None:
        radialDist = numpy.abs(X / float(halfFilterDim))
        # Establish a radial distance threshold that is halfway
        # between the first discrete bad cell and the last good cell.
        if firstBadCell == halfFilterDim:
          distThresh = 0.5 * (radialDist[0, 0, halfFilterDim + firstBadCell] + \
                              radialDist[0, 0, halfFilterDim + firstBadCell - 1])
        else:
          assert firstBadCell < halfFilterDim
          # Establish a radial distance threshold that is halfway
          # between the first discrete bad cell and the second bad cell.
          # This seems to give good results in practice.
          distThresh = 0.5 * (radialDist[0, 0, halfFilterDim + firstBadCell] + \
                              radialDist[0, 0, halfFilterDim + firstBadCell + 1])
        suppressTerm = (radialDist < distThresh).astype(RealNumpyDType)
        if self._centerSurround:
          suppressTerm = numpy.concatenate((suppressTerm,
                               numpy.ones((1, self._filterDim, self._filterDim),
                               dtype=RealNumpyDType)))
        gaborBank *= suppressTerm

    # Normalize so that mean of each filter is zero
    means = gaborBank.mean(axis=2).mean(axis=1).reshape(numGaborFilters, 1, 1)
    offsets = means.repeat(self._filterDim, axis=1).repeat(self._filterDim, axis=2)
    gaborBank -= offsets

    # Normalize so that sum of squares over each filter is one
    squareSums = (gaborBank * gaborBank).sum(axis=2).sum(axis=1).reshape(numGaborFilters, 1, 1)
    scalars = 1.0 / numpy.sqrt(squareSums)
    gaborBank *= scalars

    # Log gabor filters to disk
    if self._logPrefix:
      for k in xrange(numGaborFilters):
        img = Image.new('L', (self._filterDim, self._filterDim))
        minVal = gaborBank[k].min()
        gaborFilter = gaborBank[k] - minVal
        gaborFilter *= (254.99 / gaborFilter.max())
        img.putdata(gaborFilter.flatten().astype(numpy.uint8))
        img.save("%s.filter.%03d.png" % (self._logPrefix, k))

    # Store the Gabor Bank as a transposed set of 'numOrients' 1-D column-vectors
    # which can be easily dot-producted-ed against the split input vectors
    # during our compute() calls.
    self._gaborBank = (gaborBank.astype(numpy.float32) * 4096.0).astype(numpy.int32)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  @classmethod
  def getSpec(cls):
    ns = Spec(description = cls.__doc__,
                  singleNodeOnly=False)

    ns.inputs = dict(
      bottomUpIn=InputSpec(
        description="""The input signal, conceptually organized as an
                      image pyramid data structure, but internally
                      organized as a flattened vector.""",
        dataType='float',
        regionLevel=False,
        requireSplitterMap=False),

      validRegionIn=InputSpec(
        description="""A bounding box around the valid region of the image,
                      expressed in pixel coordinates; if the first element
                      of the bounding box is negative, then the valid
                      region is specified by 'validAlphaIn', in the form
                      of a non-rectangular alpha channel.""",
        dataType='float',
        regionLevel=True,
        requireSplitterMap=False),

      validAlphaIn=InputSpec(
        description="""An alpha channel that may be used (in place of the
                      'validRegionIn' bounding box) to specify the valid
                      region of the image on a per-pixel basis; the channel
                      should be an image of identical size to the finest
                      resolution data input image.""",
        dataType='float',
        regionLevel=True,
        requireSplitterMap=False)
    )

    ns.outputs = dict(
      bottomUpOut=OutputSpec(
        description="""The output signal, conceptually organized as an
                       image pyramid data structure, but internally
                       organized as a flattened vector.""",
        dataType='float',
        count=0,
        regionLevel=False,
        isDefaultOutput=True
      ),

      topDownOut=OutputSpec(
        description="""The feedback output signal, sent to the topDownIn
                      input of the next level down.""",
        dataType='float',
        count=0,
        regionLevel=True)
    )


    ns.parameters = dict(
      # -------------------------------------
      # Create/Read-only parameters
      filterDim=ParameterSpec(dataType='int', accessMode='Create',
                   description="""
                    The size (in pixels) of both the width and height of the
                    gabor filters.  Defaults to 9x9.
                   """,
                   defaultValue=9),
      numOrientations=ParameterSpec(dataType='int', accessMode='Create',
                   description="""
                    The number of gabor filter orientations to produce.
                    The half-circle (180 degrees) of rotational angle will be evenly partitioned.
                    Defaults to 4, which produces a gabor bank containing filters oriented
                    at 0, 45, 90, and 135 degrees.
                   """),
      phaseMode=ParameterSpec(dataType='str', accessMode='Create',
                   description="""
                    The number of separate phases to compute per orientation.
                    Valid values are: 'single' or 'dual'.  In 'single', responses to each such
                    orientation are rectified by absolutizing them; i.e., a 90-degree edge
                    will produce the same responses as a 270-degree edge, and the two
                    responses will be indistinguishable.  In "dual" mode, the responses to
                    each orientation are rectified by clipping at zero, and then creating
                    a second output response by inverting the raw response and again clipping
                    at zero; i.e., a 90-degree edge will produce a response only in the
                    90-degree-oriented plane, and a 270-degree edge will produce a response
                    only the dual phase plane associated with the 90-degree plane (an
                    implicit 270-degree plane.)  Default is 'single'.
                   """,
                   constraints="enum: single, dual",
                   defaultValue='single'),
      centerSurround=ParameterSpec(dataType='int', accessMode='Create',
                   description="""
                    Controls whether an additional filter corresponding to
                    a non-oriented "center surround" response is applied to the image.
                    If phaseMode is "dual", then a second "center surround" response plane
                    is added as well (the inverted version of the center-surround response.)
                    Defaults to False.
                   """,
                   defaultValue=0),
      targetType=ParameterSpec(dataType='str', accessMode='Create',
                   description="""
                    The preferred "target" of the gabor filters.  A value of
                    'line' specifies that line detectors (peaks in the center and troughs
                    on either side) are to be used.  A value of 'edge' specifies that edge
                    detectors (with a peak on one side and a trough on the other) are to
                    be used.  Default is 'edge'.
                   """,
                   constraints="enum: line,edge",
                   defaultValue='edge'),
      gainConstant=ParameterSpec(dataType='float', accessMode='ReadWrite',
                   description="""
                    A multiplicative amplifier that is applied to the gabor
                    responses after any normalization.  Defaults to 1.0; larger values
                    increase the sensitivity to edges.
                   """),
      normalizationMethod=ParameterSpec(dataType='str', accessMode='ReadWrite',
                   description="""
                    Controls the method by which responses are
                    normalized on a per image (and per scale) basis.  Accepts the following
                    three legal values:
                      "fixed": No response normalization;
                      "max":   Applies a global gain value to the responses so that the
                               max response equals the value of 'gainConstant'
                      "mean":  Applies a global gain value to the responses so that the
                               mean response equals the value of 'gainConstant'
                    Default is 'fixed'.
                   """,
                   constraints="enum: fixed, mean, max"
                   ),
      perPlaneNormalization=ParameterSpec(dataType='int', accessMode='ReadWrite',
                   description="""
                    Controls whether normalization (as specified by
                    'normalizationMethod') is applied globally across all response planes
                    (for a given scale), or individually to each response plane.  Default
                    is False.  Note: this parameter is ignored if normalizationMethod is "fixed".
                   """,
                   ),
      perPhaseNormalization=ParameterSpec(dataType='int', accessMode='ReadWrite',
                   description="""
                    Controls whether normalization (as specified by
                    'normalizationMethod') is applied globally across both phases for a
                    particular response orientation and scale, or individually to each
                    phase of the response.  Default is True.  Note: this parameter is
                    ignored if normalizationMethod is "fixed".
                   """,
                   ),
      postProcessingMethod=ParameterSpec(dataType='str', accessMode='ReadWrite',
                   description="""
                    Controls what type of post-processing (if any)
                    is to be performed on the normalized responses. Valid value are:
                      "raw":       No post-processing is performed; final output values are
                                   unmodified after normalization
                      "sigmoid":   Passes normalized output values through a sigmoid function
                                   parameterized by 'postProcessingSlope' and 'postProcessingCenter'.
                      "threshold": Passes normalized output values through a piecewise linear
                                   thresholding function parameterized by 'postProcessingMin'
                                   and 'postProcessingMax'.
                   """,
                   constraints="enum: raw, sigmoid, threshold"),
      postProcessingSlope=ParameterSpec(dataType='float', accessMode='ReadWrite',
                   description="""
                    Specifies the slope of the sigmoid function to apply if the
                    post-processing mode is set to 'sigmoid'.
                   """),
      postProcessingCenter=ParameterSpec(dataType='float', accessMode='ReadWrite',
                   description="""
                    Specifies the mid-point of the sigmoid function to apply if the
                    post-processing mode is set to 'sigmoid'.
                   """),
      postProcessingMin=ParameterSpec(dataType='float', accessMode='ReadWrite',
                   description="""
                    Specifies the value below which responses will be clipped to zero
                    when post-processing mode is set to 'threshold'.
                   """),
      postProcessingMax=ParameterSpec(dataType='float', accessMode='ReadWrite',
                   description="""
                    Specifies the value above which responses will be clipped to one
                    when post-processing mode is set to 'threshold'.
                   """),
      zeroThresholdOut=ParameterSpec(dataType='float', accessMode='ReadWrite',
                   description="""
                    If all outputs of a gabor node are below this threshold,
                    they will all be driven to absolute 0. This is useful in conjunction with
                    using the product mode/don't care spatial pooler which needs to know when
                    an input should be treated as 0 vs being normalized to sum to 1.
                   """),
      boundaryMode=ParameterSpec(dataType='str', accessMode='Create',
                   description="""
                    Controls how GaborNode deals with boundary effects.  Accepts
                    two valid parameters:
                        'constrained' -- Gabor responses are normally only computed for image locations
                                that are far enough from the edge of the input image so that the entire
                                filter mask fits within the input image.  Thus, the spatial dimensions of
                                the output gabor maps will be smaller than the input image layers.
                        'sweepOff' -- Gabor responses will be generated at every location within
                                the input image layer.  Thus, the spatial dimensions of the output gabor
                                maps will be identical to the spatial dimensions of the input image.
                                For input image locations that are near the edge (i.e., a portion of
                                the gabor filter extends off the edge of the input image), the values
                                of pixels that are off the edge of the image are taken to be as specifed
                                by the parameter 'offImagePixelValue'.
                    Default is 'constrained'.
                   """,
                   constraints='enum: constrained, sweepOff',
                   defaultValue='constrained'),

      offImagePixelValue=ParameterSpec(dataType="str", accessMode='ReadWrite',
                   description="""
                    If 'boundaryMode' is set to 'sweepOff', then this
                    parameter specifies the value of the input pixel to use for "filling"
                    enough image locations outside the bounds of the original image.
                    Ignored if 'boundaryMode' is 'constrained'.  Default value is 0.
                   """
                   ),
      suppressOutsideBox=ParameterSpec(dataType='int', accessMode='ReadWrite',
                   description="""
                    If True, then gabor responses outside of the bounding
                    box (provided from the sensor) are suppressed.  Internally, the bounding
                    box is actually expanded by half the filter dimension (respecting the edge
                    of the image, of course) so that responses can be computed for all image
                    locations within the original bounding box.
                   """),
      forceBoxContraction=ParameterSpec(dataType='int', accessMode='ReadWrite',
                   description="""
                    Fine-tunes the behavior of bounding box suppression.
                    If False (the default), then the bounding box will only be 'contracted'
                    (by the half-width of the filter) in the dimenion(s) in which it is not
                    the entire span of the image.  If True, then the bounding box will be
                    contracted unconditionally.
                   """),
      suppressByAlpha=ParameterSpec(dataType='int', accessMode='ReadWrite',
                   description="""
                    A boolean that, if True, instructs GaborNode to use
                    the pixel-accurate alpha mask received on the input 'validAlphaIn' for
                    the purpose of suppression of responses.
                   """),
      logPrefix=ParameterSpec(dataType='str', accessMode='ReadWrite',
                   description="""
                    If non-None, causes the response planes at each scale, and
                    for each input image, to be written to disk using the specified prefix
                    for the name of the log images.  Default is None (no such logging.)
                   """),

      maxTopDownOut=ParameterSpec(dataType='float', accessMode='Read', count=0,
                   description="""
                    The max top-down output from each node. It is faster to access this
                    variable than to fetch the entire top-down output of every node. The
                    top down image inspector fetches this parameter (if available)
                    instead of the topDownOut output variable for better performance.
                   """),

      # -------------------------------------
      # Undocumented parameters

      nta_aspectRatio=ParameterSpec(dataType='float', accessMode='Create',
                   description="""
                    Controls how "fat" (i.e., how oriented) the Gabor
                    filters are.  A value of 1 would produce completely non-oriented
                    (circular) filters; smaller values will produce a more oriented
                    filter.  Default is 0.3.
                   """,
                   defaultValue=0.3),

      nta_effectiveWidth=ParameterSpec(dataType='float', accessMode='Create',
                   description="""
                    Controls the rate of exponential drop-off in
                    the Gaussian component of the Gabor filter.  Default is 4.5.
                   """,
                   defaultValue=4.5),

      nta_wavelength=ParameterSpec(dataType='float', accessMode='Create',
                   description="""
                    Controls the frequency of the sinusoidal component
                    of the Gabor filter.  Default is 5.6.
                   """,
                   defaultValue=5.6),
      nta_lobeSuppression=ParameterSpec(dataType='int', accessMode='Create',
                   description="""
                    Controls whether or not the secondary lobes of the
                    Gabor filters are suppressed.  The suppression is performed based
                    on the radial distance from the oriented edge to which the Gabor
                    filter is tuned.  If True, then the secondary lobes produced
                    by the pure mathematical Gabor equation will be suppressed
                    and have no effect; if False, then the pure mathematical
                    Gabor equation (digitized into discrete sampling points, of
                    course) will be used.  Default is True.
                   """,
                   defaultValue=1),
      nta_debugLogBuffers=ParameterSpec(dataType='int', accessMode='ReadWrite',
                   description="""
                    If enabled, causes internal memory buffers used
                    C implementation to be dumped to disk after each compute()
                    cycle as an aid in the debugging of the C code path.
                    Defaults to False.
                   """,
                   ),

      nta_width=ParameterSpec(dataType="int", accessMode='Read',
                   description="""Width of the maximum resolution."""),

      nta_height=ParameterSpec(dataType="int", accessMode='Read',
                   description="""Width of the maximum resolution."""),

      nta_morphologyMethod=ParameterSpec(dataType='str', accessMode='ReadWrite',
                   description="""
                    Controls the routines used to perform dilation and erosion of
                    valid alpha masks.  Legal values are:
                        'opencv' -- use faster OpenCV routines;
                        'nta' -- use the slower Numenta routines;
                        'best' -- use OpenCV if it is available on the platform,
                            otherwise use the slower routines.
                    Default is 'best'.
                   """),
    )

    return ns.toDict()

  #---------------------------------------------------------------------------------
  def getOutputElementCount(self, name):
    """This method will be called only when the node is used in nuPIC 2"""
    if name == 'bottomUpOut':
      return self.getNumPlanes()
    elif name == 'topDownOut':
      return 0
    else:
      raise Exception('Unknown output: ' + name)

#+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
# Command line unit testing
#+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
if __name__=='__main__':
  from nupic.engine import Network
  n = Network()
  gabor = n.addRegion(
    'gabor',
    'py.GaborNode2',
    """{  filterDim: 5,
          numOrientations: 2,
          centerSurround: 1,
          phaseMode: single,
          targetType: edge,
          gainConstant: 1.0,
          normalizationMethod: max,
          postProcessingMethod: threshold,
          postProcessingMin: 0.15,
          postProcessingMax: 1.0,
          boundaryMode: sweepOff,
          #suppressOutsideBox: False,
          #suppressByAlpha: True,
          offImagePixelValue: colorKey,
          zeroThresholdOut: 0.003
    }""")

  print 'Done.'
