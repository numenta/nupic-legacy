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
import numpy
from nupic.regions.ImageSensorFilters.Convolution import Convolution


class GaborConvolution(Convolution):
  """
  Apply a bank of Gabor filters to the original image, and
  return one or more images (same dimensions as the original)
  containing the Gabor responses.
  """

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
  # Class constants
  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+
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
               offImagePixelValue='colorKey',
               suppressOutsideBox=True,
               forceBoxContraction=False,
               aspectRatio=0.3,
               effectiveWidth=4.5,
               orientationCount=4,
               targetType='edge',
               phaseMode='single',
               waveLength=5.6,
               lobeSuppression=True):
    """
    """
    assert phaseMode in ('single', 'dual')
    assert targetType in ('edge', 'line')

    self._orientationCount = orientationCount
    self._targetType = targetType
    self._phaseMode = phaseMode
    self._waveLength = waveLength
    self._lobeSuppression = lobeSuppression

    Convolution.__init__(self,
                         scaleDecimation,
                         filterDim,
                         gainConstant,
                         normalizationMethod,
                         perPlaneNormalization,
                         perPhaseNormalization,
                         postProcessingMethod,
                         postProcessingSlope,
                         postProcessingCenter,
                         postProcessingMin,
                         postProcessingMax,
                         zeroThresholdOut,
                         boundaryMode,
                         offImagePixelValue,
                         suppressOutsideBox,
                         forceBoxContraction,
                         aspectRatio,
                         effectiveWidth)

  def _buildFilterBank(self):
    """Build an array of Gabor filters.
    Also build a 1-D vector of filter bank indices that maps each output
    location to a particular (customized) bank of gabor filters.
    """
    #from dbgp.client import brk; brk(port=9001)
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
    orientationCount = self._orientationCount
    if orientationCount == 0:
      orientationCount = 2

    # Select the orientation sample points (in radians)
    radianInterval = numpy.pi / float(orientationCount)
    orientations = numpy.array(range(orientationCount), dtype=numpy.float32) * \
                   radianInterval

    # Compute trigonometric functions of orientation
    sinTheta = numpy.sin(orientations).reshape(orientationCount, 1, 1)
    cosTheta = numpy.cos(orientations).reshape(orientationCount, 1, 1)

    # Construct two filterDim X filterDim arrays containing y (row) and
    # x (column) coordinates (in dimensions of pixels), respectively.
    y = meshGrid[0].reshape(1, self._filterDim, self._filterDim)
    x = meshGrid[1].reshape(1, self._filterDim, self._filterDim)
    X = x * cosTheta - y * sinTheta
    Y = x * sinTheta + y * cosTheta

    # Build the Gabor filters
    #if hasattr(self, '_phase') and self._phase == 'edge':
    if self._targetType == 'edge':
      sinusoidalTerm = numpy.sin(2.0 * numpy.pi / self._waveLength * X)
    else:
      sinusoidalTerm = numpy.cos(2.0 * numpy.pi / self._waveLength * X)
    numerator = (X * X + self._aspectRatio * self._aspectRatio * Y * Y)
    denominator = -2.0 * self._effectiveWidth * self._effectiveWidth
    exponentialTerm = numpy.exp(numerator / denominator)
    gaborBank = sinusoidalTerm * exponentialTerm

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
        # between the first discrete bad cell and the second bad cell.
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
        suppressTerm = (radialDist < distThresh).astype(numpy.float32)
        gaborBank *= suppressTerm

    # Normalize so that mean of each filter is zero
    means = gaborBank.mean(axis=2).mean(axis=1).reshape(numGaborFilters, 1, 1)
    offsets = means.repeat(self._filterDim, axis=1).repeat(self._filterDim, axis=2)
    gaborBank -= offsets

    # Normalize so that sum of squares over each filter is one
    squareSums = (gaborBank * gaborBank).sum(axis=2).sum(axis=1).reshape(numGaborFilters, 1, 1)
    scalars = 1.0 / numpy.sqrt(squareSums)
    gaborBank *= scalars

    # Store the Gabor Bank as a transposed set of 'numOrients' 1-D column-vectors
    # which can be easily dot-producted-ed against the split input vectors
    # during our compute() calls.
    self._filterBank = (gaborBank.astype(numpy.float32) * 4096.0).astype(numpy.int32)

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _calcPlaneCount(self):
    """Computes the number of responses planes for a particular Gabor
    configuration.
    """
    if self._phaseMode == 'dual':
      return self._orientationCount * 2
    else:
      return self._orientationCount

  #+=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=++=+=+=+=+=+=+=+=+=+=+=+

  def _getNeededBufferCount(self):
    """Compute the number of allocated buffers to hold the responses.
    """
    return self._orientationCount
