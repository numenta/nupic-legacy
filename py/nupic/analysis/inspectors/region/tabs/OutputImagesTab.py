# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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
from enthought.traits.api import *
from enthought.traits.ui.api import *

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought import alignCenter, ImageEditor
import nupic

def _getOutputSpecs(region):
    return region.spec.outputs

def _getElementCount(spec):
    return spec.count

def _getOutput(region, name):
  return region.getOutputData(name)

class OutputImagesTab(RegionInspectorTab):

  """
  Displays the activation of a multiregion's baby regions as an image.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""
    return not region.spec.singleNodeOnly

  def __init__(self, region):

    RegionInspectorTab.__init__(self, region)

    self._addTraits()
    self._createView()

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- Class method that was called.
    @param elementName -- Name of RuntimeElement.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """

    # Get the dimensions of this layer

    (height, width) = tuple(self.multiRegion.dimensions)


    # Do the BottomUp Out:
    if hasattr(self, 'bottomUpImage'):
      # For faster operation, let's get the entire output of the multi-region from the
      #  runtime in one shot
      buOutput = _getOutput(self.multiRegion, 'bottomUpOut')

      # Get the outputs for this layer only
      begin = self.regionOffsetByLayer[layerIdx] * self.buOutputSizePerRegion
      end = self.regionOffsetByLayer[layerIdx+1] * self.buOutputSizePerRegion
      layerOut = numpy.array(buOutput[begin:end]).reshape(\
                                                (height*width, self.buOutputSizePerRegion))

      # Take the max of each region
      pixels = layerOut.max(axis=1)

      # Scale from 0 to 255
      pixelMax = pixels.max()
      maxLocation = pixels.argmax()
      maxY = maxLocation / width
      maxX = maxLocation % width
      if pixelMax > 0:
        pixels = (pixels * 255.0) / pixelMax

      # Construct our bottomUP image
      newImage = Image.new('L', (width, height))
      newImage.putdata(pixels)
      self.bottomUpImage = newImage
      self.bottomUpImageInfo = "max output value: %f at (%d,%d)" % (pixelMax, maxY, maxX)

    # Do the topDown out
    if hasattr(self, 'topDownImage') and self.tdOutputSizePerRegion > 0:

      # Get the topDown outs using the faster 'maxTopDownOut' param, if available
      if self.multiRegion.hasParameter('maxTopDownOut'):
        tdMaxes = numpy.array(self.multiRegion.getParameter('maxTopDownOut'))
      else:
        tdOutput = _getOutput(self.multiRegion, 'topDownOut')
        tdOutput = tdOutput.reshape(-1, self.tdOutputSizePerRegion)
        tdMaxes = tdOutput.max(axis=1)

      # Get the outputs for this layer only
      begin = self.regionOffsetByLayer[layerIdx]
      end = self.regionOffsetByLayer[layerIdx+1]
      pixels = tdMaxes[begin:end]

      # Scale from 0 to 255
      pixelMax = pixels.max()
      maxLocation = pixels.argmax()
      maxY = maxLocation / width
      maxX = maxLocation % width
      if pixelMax > 0:
        pixels = (pixels * 255.0) / pixelMax

      # Construct our topDownOut image
      newImage = Image.new('L', (width, height))
      newImage.putdata(pixels)
      self.topDownImage = newImage
      self.topDownImageInfo = "max output value: %f at (%d,%d)" % (pixelMax, maxY, maxX)

    def switchRegion(self, region):
      """Switch to a different region within the same region or multiregion."""

      self.region = region
      # Some inspectors may wish to override this method to skip the update
      # self.update()

  def _addTraits(self):
    """Use the Spec to add outputs as traits."""

    outputs = _getOutputSpecs(self.region)
    for name, spec in outputs.items():
      if name == 'bottomUpOut':
        self.add_trait('bottomUpImage', Instance(Image.Image))
        self.buOutputSizePerRegion = _getElementCount(spec)
        self.add_trait('bottomUpImageInfo', Str)
      if name == 'topDownOut':
        self.tdOutputSizePerRegion = _getElementCount(spec)
        if self.tdOutputSizePerRegion > 0:
          self.add_trait('topDownImage', Instance(Image.Image))
          self.add_trait('topDownImageInfo', Str)

    # Collect the information needed to update the visualizers
    #mnName = self.region.getName().split('[')[0] + "[]"
    #region = self.region.getContainer()
    #net = region.getContainer()
    #self.multiRegion = net.getElement(mnName)
    self.multiRegion = self.region

    # Get the number of regions in each layer (for MRG networks)
    self.regionOffsetByLayer = [0]
    regionCount = 0

    self._handleLayout()
    #region = self.region.getContainer()
    #layout = region.getLayoutInfo()
    #if layout['layoutType'] == 'Multi-resolution Grid Layout':
    #  self.dimsPerLayer = eval(layout['dimensions'])
    #  # NOTE: When there is only one layer, layout['dimensions'] is a tuple, not a
    #  #  tuple of tuples, so we must correct that here
    #  if type(self.dimsPerLayer[0]) != type(()):
    #    self.dimsPerLayer = (self.dimsPerLayer,)
    #  for dim in self.dimsPerLayer:
    #    regionCount += dim[0]*dim[1]
    #    self.regionOffsetByLayer.append(regionCount)
    #else:
    #  dims = region.getDimensions()
    #  # Handle special case of 1 region: dims will be (1,)
    #  if len(dims) == 1:
    #    self.dimsPerLayer = ((dims[0],1),)
    #  else:
    #    self.dimsPerLayer = (region.getDimensions(),)
    #  self.regionOffsetByLayer.append(region.getElementCount())

  def _handleLayout(self):
    dims = self.region.dimensions
    # Handle special case of 1 region: dims will be (1,)
    if len(dims) == 1:
      self.dimsPerLayer = ((dims[0],1),)
    else:
      self.dimsPerLayer = (dims,)
    self.regionOffsetByLayer.append(dims.getCount())

  def _createView(self):
    """Set up the view for the traits."""

    # Make our display width and height have the same aspect ratio as the region's
    #  width and height
    regionWidth = self.dimsPerLayer[0][0]
    regionHeight = self.dimsPerLayer[0][1]

    displayWidth = 180
    displayHeight = displayWidth * float(regionHeight)/float(regionWidth)

    imageItems = []
    if hasattr(self, 'topDownImage'):
      imageItems.append(
          alignCenter(Item(name='topDownImage',
               editor=ImageEditor(width = displayWidth,
                                  height = displayHeight,
                                  caption = 'TopDown Outputs',
                                  interpolate = False),
               style='custom',
               show_label=False))
        )
      self.topDownImageInfo = 'max output value: %f at (%d,%d)' % (1.0, 10, 10)
      imageItems.append(
          alignCenter(Item(name='topDownImageInfo', style='readonly', show_label=False))
        )

    if hasattr(self, 'bottomUpImage'):
      imageItems.append(
          alignCenter(Item(name='bottomUpImage',
               editor=ImageEditor(width = displayWidth,
                                  height = displayHeight,
                                  caption = 'BottomUp Outputs',
                                  interpolate = False),
               style='custom',
               show_label=False))
        )
      self.bottomUpImageInfo = 'max output value: %f at (%d,%d)' % (1.0, 10, 10)
      imageItems.append(
          alignCenter(Item(name='bottomUpImageInfo', style='readonly', show_label=False))
        )

    self.traits_view = View(
      Group(*imageItems),
      title='OutputImages'
    )