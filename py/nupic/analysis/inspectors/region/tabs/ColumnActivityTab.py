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

# Python imports
import itertools

import wx

from enthought.traits.api import *
from enthought.traits.ui.api import *
import numpy
from PIL import Image
from PIL import ImageDraw

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought.editors import ImageEditor
from nupic.image import deserializeImage

from nupic.research import FDRCSpatial, fdrutilities

# Used by our subclasses to tell which images to show...
kShowSpColumns = "ShowSpColumns"
kShowTpColumns = "ShowTpColumns"


# We'll try to make each of the pictures this big, ideally...
# ...numbers are sorta arbitrary.
_kIdealColumnImageSize                = (400, 400)
_kIdealCoincImageSize                 = (400, 400)

# We'll shrink the width and height by this amount, so it doesn't take too much
# space...
_kIdealLocationImageShrinkage         = 4.


_kShowInputCheckboxStr  = \
  "Show input"
_kSpatialColumnsTemplateStr  = \
  "Num Spatial Columns Active: %d; avg. saturation: %.1f%% (%.1f%% inner areas)"
_kTemporalColumnsTemplateStr = \
  "Num Temporal Columns Active: %d; avg. saturation: %.1f%% (%.1f%% inner areas)"

_kUnderMouseTemplateStr = \
  "Column # under mouse: %d (%d, %d); input # under mouse: %d (%d, %d)"

_kSynStatsZoomAreaCheckboxStr = \
  "Active syns in zoom area"
_kSynStatsZoomAreaValueStr = \
  "%d syns, min: %.1f; max: %.1f; avg: %.1f; 3sigma: %.1f-%.1f"

_kClickedColumnNumberTemplateStr = \
  "Clicked column #: %d (overlap=%d (%.1f%%), isSpatialFiring=%s, isTemporalFiring=%s)"

_kHelpText = (
"""This tab shows two 2D maps of column activity on a CLARegion.\n\n"""

"""Each "pixel" in these maps represents one column.  In the spatial map, """
"""the pixel will be red if the spatial pooler fired for that column.  In """
"""the temporal map, the pixel will be red or green if the temporal pooler """
"""fired for that column.  Red indicates firing for "sequence" out, whereas """
"""green indicates firing for non-"sequence" out.\n\n"""

"""The column map is overlayed on the input to the region corresponding to """
"""the point where each column is CENTERED.  Remember that columns actually """
"""sample from a larger area than that point (see coincInputRadius).  We """
"""also show (in gray) a border.  The pixels in this border don't correspond """
"""to actual columns, but serve to give context.\n\n"""

"""There are some side effects of visualizing things where each column is """
"""placed over the pixel at it's center:\n\n"""

"""* If two columns are centered above the same input, that input will be """
"""repeated on the map.\n\n\n"""

"""Note that clicking on a pixel will show the coincidence associated with """
"""this column, also overlayed on the input.  In this case, the """
"""picture shown is in "input space", not "column space"."""
)

def _getSelf(region):
    return region.getSelf()

def _getInput(region):
  return region.getInputData('bottomUpIn')

def _getOutput(region):
  return region.getOutputData('bottomUpOut')

def _getParameterNumpyArray(region, name):
  a = region.getSelf().getParameter(name)
  return numpy.array(a)

################################################################################
class ColumnActivityTab(RegionInspectorTab):
  """Displays column activity in both spatial and temporal areas of column.

  This tab will show the activation of the spatial and temporal parts of all
  of the columns, overlayed on top of the input to the region.
  """

  ####################################################################
  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise.

    @return isRegionSupported  True if this is a supported region.
    """
    # Only subclasses are shown...
    return False

  ####################################################################
  def __init__(self, region, showWhat=''):
    """ColumnActivityTab constructor.

    @param  region      The RuntimeRegion.
    @param  showWhat  What to show (SP columns, TP columns)
    """
    # Call superclass.  This will init, among other things, self.region...
    super(ColumnActivityTab, self).__init__(region)

    # Keep track of what we're showing...
    assert showWhat in (kShowSpColumns, kShowTpColumns), \
           "Subclass tells what to show"
    self._showWhat = showWhat

    # --------------------------------------------------------------------
    # Init members, just to be pretty.  Many of these are actually set in
    # self.switchRegion().
    self._regionRef = None
    # Which region has the SP - could be this region or the one below it in the network
    self._spRegionRef = None
    self._spRegion = None
    # Which region has the TP - could be this region or the one above it in the network
    self._tpRegionRef = None
    self._tpRegion = None

    self._inputShape = (-1, -1)
    self._columnsShape = (-1, -1)
    self._coincCentres = None

    # Cached by update for use in click-handling code...
    self._input = None
    self._spatialPoolerOutput = None
    self._temporalPoolerOutput = None

    self.switchRegion(self.region, update=False)

    self.add_trait('locationZoom', Range(1, 16, 1, mode='spinner'))
    self.add_trait('locationImage', Instance(Image.Image))
    self.add_trait('showInputCheckbox', Bool(True))

    # Original and learned version of coincidence
    if showWhat == kShowSpColumns:
      self.add_trait('spatialColumns', Instance(Image.Image))
      self.add_trait('spatialColumnsActive',
                     Str(_kSpatialColumnsTemplateStr % (0, 0, 0)))
    if self._showWhat == kShowTpColumns:
      self.add_trait('temporalColumns', Instance(Image.Image))
      self.add_trait('temporalColumnsActive',
                     Str(_kTemporalColumnsTemplateStr % (0, 0, 0)))
      self.add_trait('synStatsZoomAreaCheckbox', Bool(False))
      self.add_trait('synStatsZoomAreaValueStr', Str())

    self.add_trait('underMouseStr', Str())


    self.add_trait('coincImage', Instance(Image.Image))
    self.add_trait('clickedColumnInfoStr', Str())

    self.add_trait('_spacer1', Str())

    # NOTE: Disabled help for now to fit things better...
    #self.add_trait('helpButton',
    #  Button(label="Help",
    #         width_padding=6, height_padding=3))

    # Calculate magnifications...
    columnImageMagnification = self._calcMagnification(
      (self._inputMapWidth, self._inputMapHeight), _kIdealColumnImageSize
    )
    coincMagnification = self._calcMagnification(
      (self._inputShape[1], self._inputShape[0]), _kIdealCoincImageSize
    )

    # Figure out how big the column images are...
    self._columnImageWidth  = int(self._inputMapWidth*columnImageMagnification)
    self._columnImageHeight = int(self._inputMapHeight*columnImageMagnification)

    # Start the location bbox in the center; it can be moved by clicking...

    self._locationBbox = (
      max(0, (self._inputMapWidth-self._columnImageWidth)/2),
      max(0, (self._inputMapHeight-self._columnImageHeight)/2),
      min(self._inputMapWidth,
          self._columnImageWidth + (self._inputMapWidth-self._columnImageWidth)/2),
      min(self._inputMapHeight,
          self._columnImageHeight + (self._inputMapHeight-self._columnImageHeight)/2)
    )

    # View
    viewItems = []
    viewItems.extend((
      Group(
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        Item('locationZoom', show_label=False),
        Item('_spacer1', style='readonly', show_label=False, springy=False),
        Item('locationImage',
             editor=ImageEditor(
              width=self._columnImageWidth / _kIdealLocationImageShrinkage,
              height=self._columnImageHeight / _kIdealLocationImageShrinkage,
              caption="Location Image - click to move",
              nearestNeighbor=False,
              onMotion=self._onLocationMouseMotion,
              onClick=self._onLocationMouseMotion
             ),
             show_label=False),
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        orientation='horizontal'
      ),
    ))

    if showWhat == kShowSpColumns:
      viewItems.extend((
        Group(
          Item('_spacer1', style='readonly', show_label=False, springy=True),
          Group(
            Item('_spacer1', style='readonly', show_label=False, springy=True),
            Item('spatialColumns',
                 editor=ImageEditor(
                  width=self._columnImageWidth,
                  height=self._columnImageHeight,
                  caption="Spatial Columns",
                  nearestNeighbor=True,
                  onMotion=self._onSpatialMouseMotion,
                  onClick=self._onSpatialMouseMotion,
                  wantMagnifier=True,
                  integralScale=True
                 ),
                 show_label=False),
            Item('_spacer1', style='readonly', show_label=False, springy=True),
          ),
          Item('_spacer1', style='readonly', show_label=False, springy=True),
          Group(
            Item('_spacer1', style='readonly', show_label=False, springy=True),
            Item('coincImage',
                 editor=ImageEditor(
                  width=int(self._inputShape[1]*coincMagnification),
                  height=int(self._inputShape[0]*coincMagnification),
                  caption="Clicked Coincidence Image",
                  nearestNeighbor=(coincMagnification>=1)
                 ),
                 show_label=False),
            Item('_spacer1', style='readonly', show_label=False, springy=True),
          ),
          Item('_spacer1', style='readonly', show_label=False, springy=True),
          orientation='horizontal'
        ),
        Group(
          Item('showInputCheckbox', label=_kShowInputCheckboxStr),
        ),
        Group(
          Item('spatialColumnsActive', style='readonly', show_label=False),
        ),
      ))

    if showWhat == kShowTpColumns:
      viewItems.extend((
        Group(
          Item('_spacer1', style='readonly', show_label=False, springy=True),
          Group(
            Item('_spacer1', style='readonly', show_label=False, springy=True),
            Item('temporalColumns',
                 editor=ImageEditor(
                  width=self._columnImageWidth,
                  height=self._columnImageHeight,
                  caption="Temporal Columns",
                  nearestNeighbor=True,
                  onMotion=self._onTemporalMouseMotion,
                  onClick=self._onTemporalMouseMotion,
                  wantMagnifier=True,
                  integralScale=True
                ),
                show_label=False),
            Item('_spacer1', style='readonly', show_label=False, springy=True),
          ),
          Item('_spacer1', style='readonly', show_label=False, springy=True),
          Group(
            Item('_spacer1', style='readonly', show_label=False, springy=True),
            Item('coincImage',
                 editor=ImageEditor(
                  width=int(self._inputShape[1]*coincMagnification),
                  height=int(self._inputShape[0]*coincMagnification),
                  caption="Clicked Coincidence Image",
                  nearestNeighbor=(coincMagnification>=1)
                 ),
                 show_label=False),
            Item('_spacer1', style='readonly', show_label=False, springy=True),
          ),
          Item('_spacer1', style='readonly', show_label=False, springy=True),
          orientation='horizontal'
        ),
        Group(
          Item('showInputCheckbox', label=_kShowInputCheckboxStr),
        ),
        Group(
          Item('temporalColumnsActive', style='readonly', show_label=False),
        ),
        Group(
          Item('synStatsZoomAreaCheckbox', label=_kSynStatsZoomAreaCheckboxStr),
          Item('synStatsZoomAreaValueStr', style='readonly', show_label=False),
          orientation='horizontal'
        ),
      ))

    viewItems.extend((
      Item('underMouseStr', style='readonly', show_label=False),

      Item('clickedColumnInfoStr', style='readonly', show_label=False),

      #Item('helpButton', show_label=False),
    ))

    if showWhat == kShowSpColumns:
      self.traits_view = View(*viewItems, title='ColumnActivity-SP')
    elif showWhat == kShowTpColumns:
      self.traits_view = View(*viewItems, title='ColumnActivity-TP')

  ####################################################################
  @staticmethod
  def _calcMagnification(actualSize, idealSize):
    """Calculate the magnification needed to scale from actualSize to idealSize.

    This will calculate a magification such that:
    - Magnification is integral, unless less than 1.
    - Aspect ratio remains unchanged.
    - Magnifying actualSize by this amount will make it <= idealSize.

    @param  actualSize     A (width, height) tuple of the starting size.
    @param  idealWize      A (width, height) tuple of the ideal size we'd like
                           to end up at.
    @return magnification  The integral magnification (if 1 or greater), else
                           the floating point magnification.
    """
    actualWidth, actualHeight = actualSize
    idealWidth, idealHeight = idealSize

    widthMagnification  = idealWidth / float(actualWidth)
    heightMagnification = idealHeight / float(actualHeight)

    magnification = min(widthMagnification, heightMagnification)

    if magnification >= 1:
      magnification = int(magnification)

    return magnification

  ####################################################################
  def _updateColumnAndInputNumbers(self, x, y):
    """Update the underMouseStr.

    This is called from mouse motion on both of our images.

    @param  x            The x coord, in image space (topLeft is 0, 0)
    @param  y            The y coord, in image space (topLeft is 0, 0)
    """
    if (x, y) == (-1, -1):
      self.underMouseStr = ""
    else:
      columnsHeight, columnsWidth = self._columnsShape
      columnNumber = x + (y * columnsWidth)

      inputHeight, inputWidth = self._inputShape
      inputNumber = self._coincCentres[columnNumber]
      inputY, inputX = divmod(inputNumber, inputWidth)
      self.underMouseStr = _kUnderMouseTemplateStr % (
        columnNumber, x, y, inputNumber, inputX, inputY
      )

  ####################################################################
  def _onColumnImageMouseMotion(self, x, y, isMouseDown=True):
    """Handle mouse motion common to both spatial and temporal images.

    @param  x            The x coord, in image space (topLeft is 0, 0)
    @param  y            The y coord, in image space (topLeft is 0, 0)
    @param  isMouseDown  True if the mouse is down; when called for the mouse
                         down event, this will default to true.
    """
    # Add in location if needed...
    if (x, y) != (-1, -1):
      x += self._locationBbox[0]
      y += self._locationBbox[1]

    # Figure out column x and y, dealing with border...
    startX, startY, stopX, stopY = self._realInputBbox
    if (x < startX) or (y < startY) or (x >= stopX) or (y >= stopY):
      x, y = (-1, -1)
    else:
      x = x - startX
      y = y - startY

    self._updateColumnAndInputNumbers(x, y)

    if isMouseDown and (self._input is not None) and ((x, y) != (-1, -1)) \
          and self._spRegionRef is not None:

      columnsHeight, columnsWidth = self._columnsShape
      columnNumber = x + (y * columnsWidth)

      # Get learned row...
      learnedData = self._spRegionRef.getSfdrLearnedRow(int(columnNumber))

      numpyImage = numpy.zeros((len(self._input), 3), 'uint8')
      numpyImage[self._input]  = (  0,    0, 255)
      numpyImage[learnedData]  = ( 255,   0,   0)
      numpyImage[self._input & learnedData]  = (   0, 255,   0)

      numpyImage = numpyImage.reshape((self._inputShape[0],
                                       self._inputShape[1], 3))
      self.coincImage = Image.fromarray(numpyImage, 'RGB')

      overlapCount = sum(self._input & learnedData)
      overlapPct = 100.0 * overlapCount / sum(learnedData)
      isSpatialFiring = (self._spatialPoolerOutput is not None) and \
                        (self._spatialPoolerOutput[columnNumber])
      isTemporalFiring = (self._temporalPoolerOutput is not None) and \
                         (self._temporalPoolerOutput[columnNumber])
      self.clickedColumnInfoStr = _kClickedColumnNumberTemplateStr % (
        columnNumber, overlapCount, overlapPct, str(isSpatialFiring),
        str(isTemporalFiring))

      # If the temporal column is firing, display the strengths of the
      #  active synapses
      if isTemporalFiring and self._tpRegionRef is not None:
        activations = \
          self._tpRegionRef.getTfdrActiveSynapses([columnNumber],
                                                self._spatialPoolerOutput)
        syns = activations[columnNumber]
        if len(syns) > 0:
          # Sort in decreasing order of strength
          syns.sort(cmp=lambda x,y: int(y[1]-x[1]))
          (srcCells, strengths) = zip(*syns)
          print "Source cells (%d):" % len(srcCells), srcCells
          print "Strengths:        ", strengths


  ####################################################################
  def _onSpatialMouseMotion(self, x, y, isMouseDown=True):
    """Handle mouse motion and mouse down events on the spatial image.

    @param  x            The x coord, in image space (topLeft is 0, 0)
    @param  y            The y coord, in image space (topLeft is 0, 0)
    @param  isMouseDown  True if the mouse is down; when called for the mouse
                         down event, this will default to true.
    """
    self._onColumnImageMouseMotion(x, y, isMouseDown)

  ####################################################################
  def _onTemporalMouseMotion(self, x, y, isMouseDown=True):
    """Handle mouse motion and mouse down events on the temporal image.

    @param  x            The x coord, in image space (topLeft is 0, 0)
    @param  y            The y coord, in image space (topLeft is 0, 0)
    @param  isMouseDown  True if the mouse is down; when called for the mouse
                         down event, this will default to true.
    """
    self._onColumnImageMouseMotion(x, y, isMouseDown)

  ####################################################################
  def _onLocationMouseMotion(self, x, y, isMouseDown=True):
    """Handle mouse motion and mouse down events on the location image.

    @param  x            The x coord, in image space (topLeft is 0, 0)
    @param  y            The y coord, in image space (topLeft is 0, 0)
    @param  isMouseDown  True if the mouse is down; when called for the mouse
                         down event, this will default to true.
    """
    if (not isMouseDown) or (self._input is None) or ((x, y) == (-1, -1)):
      return

    # We'll try to put (x, y) in the center...

    zoomedWidth = int(self._columnImageWidth / self.locationZoom)
    zoomedHeight = int(self._columnImageHeight / self.locationZoom)

    # First, figure out top-left x, y by trying to put (x, y) in the center; but
    # make sure that both coords are at least 0...
    tlX = max(0, x - (zoomedWidth/2))
    tlY = max(0, y - (zoomedHeight/2))

    # Set bottom-right x and y based on top-left, but make sure that they
    # don't blow out the lower right corder of the input map...
    brX = min(self._inputMapWidth, tlX + zoomedWidth)
    brY = min(self._inputMapHeight, tlY + zoomedHeight)

    # Re-adjust top-left x and y, since we might have adjusted the bottom-right
    # with the min() call above.  Make sure that this doesn't make things
    # negative, which could happen if the zoomedWidth is larger than the
    # inputMapWidth...
    tlX = max(0, brX - zoomedWidth)
    tlY = max(0, brY - zoomedHeight)

    self._locationBbox = (tlX, tlY, brX, brY)

    self.update()

  ###########################################################################
  def _computeSaturationLevel(self, outputs, outputsShape):
    """
    Compute the saturation. This breaks the output into
    regions, computes the saturation level for each region, and
    returns the average seen in the non-empty regions.

    Parameters:
    --------------------------------------------
    outputs:      Dense outputs
    outputsShape: The shape of the outputs of the level (height, width)
    retval:       (sat, innerSat)
                  sat: saturation percent, considering all non-empty local areas
                  innerSat: saturation percent, considering only inner local areas

    """

    (satLevels, innerSatLevels) = fdrutilities.computeSaturationLevels(outputs,
                                    outputsShape)

    # Compute average saturation
    satLevels = numpy.array(satLevels)
    if len(satLevels) > 0:
      saturation = satLevels.mean()
    else:
      saturation = 0

    innerSatLevels = numpy.array(innerSatLevels)
    if len(innerSatLevels) > 0:
      innerSaturation = innerSatLevels.mean()
    else:
      innerSaturation = saturation

    return (100.0 * saturation, 100.0 * innerSaturation)

  ####################################################################
  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- Class method that was called.
    @param elementName -- Name of RuntimeElement.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """

    if methodName and methodName != 'run':
      return
    if not self._regionRef.hasRunInference():
      return

    # Get out input as a flat array and make it boolean...
    input = _getInput(self._spRegion)
    input = (input != 0)

    # Keep input around...
    self._input = input

    # Inver input to make things easier to see...
    input = (input == False)

    # Get all inputs in "column space"...
    # ...we will paste temporal and spatial images (generated below) onto
    # this to give them a proper border...
    inputsInColSpace = input[self._inputMap].astype('uint8')

    # Gray out 'inputsInColSpaceImg' and convert to PIL; this makes it a good
    # border...
    inputsInColSpaceImg = (inputsInColSpace * 127)
    inputsInColSpaceImg = inputsInColSpaceImg.reshape((self._inputMapHeight,
                                                 self._inputMapWidth))
    inputsInColSpaceImg = \
      Image.fromarray(inputsInColSpaceImg, 'L').convert('RGB')


    # Draw the location image...
    # Make a non-grayed out version of inputsInColSpaceImg
    locationImageBlk = (inputsInColSpace * 255).reshape((self._inputMapHeight,
                                                         self._inputMapWidth))
    locationImageBlk = Image.fromarray(locationImageBlk, 'L').convert('RGB')

    # Location image is grayed out version / non-grayed in 'real input' bbox.
    locationImage = inputsInColSpaceImg.copy()
    locationImage.paste(locationImageBlk.crop(self._realInputBbox),
                        self._realInputBbox)

    # Drawing an alpha-blended box is a little weird in PIL.  Also note
    # that ImageDraw's "box" doesn't match docs--bottom-right pt is included
    # the box...
    boxImage = Image.new('L', locationImage.size)
    ImageDraw.Draw(boxImage).rectangle(
      (self._locationBbox[0],   self._locationBbox[1],
       self._locationBbox[2]-1, self._locationBbox[3]-1), fill=127
    )
    locationImage.paste((255, 255, 0), None, boxImage)

    self.locationImage = locationImage

    # Get inputs in 'column space'...
    columnInputs = input[self._coincCentres]

    # Handle spatial case...
    if (self._spRegion is not None):
      # Convert spatial array into boolean numpy array
      spatialPoolerOutput = _getParameterNumpyArray(self._spRegion, 'spatialPoolerOutput')
      spatialPoolerOutput = (spatialPoolerOutput != 0)

      # Keep output around...
      self._spatialPoolerOutput = spatialPoolerOutput

      if self._showWhat == kShowSpColumns:
        # Figure out different color combinations, then generate a "flat"
        # RGB image.  Combos are:
        # - no input, no output: black
        # - input, but no output: white
        # - no input, output: dark red
        # - input and output: bright red
        # NOTE: The terminology used above is a bit confusing because we are
        #  working with inverted input. So, when we see "no input" here, it
        #  means we HAVE input, and vice-versa.
        if not self.showInputCheckbox:
          columnInputs.fill(True)
        zeroWithInput  = (columnInputs & (~spatialPoolerOutput))
        oneWithNoInput = (spatialPoolerOutput & (~columnInputs))
        oneWithInput   = (columnInputs & spatialPoolerOutput)
        spNumpyImage = numpy.zeros((len(zeroWithInput), 3), 'uint8')
        #spNumpyImage += 255  # incomment to remove bottom-up black pixels
        spNumpyImage[zeroWithInput]  = (255, 255, 255)
        spNumpyImage[oneWithNoInput] = (223,  87, 223)
        spNumpyImage[oneWithInput]   = (255, 127, 255)

        # Reshape, then convert to PIL...
        spNumpyImage = spNumpyImage.reshape((self._columnsShape[0],
                                             self._columnsShape[1], 3))
        realSpatialColumns = Image.fromarray(spNumpyImage, 'RGB')
        spatialColumns = inputsInColSpaceImg.copy()
        spatialColumns.paste(realSpatialColumns, self._realInputBbox)
        if self._locationBbox is not None:
          spatialColumns = spatialColumns.crop(self._locationBbox)
        self.spatialColumns = spatialColumns

        # Compute and print saturation
        (saturation, innerSat) = self._computeSaturationLevel(
                          spatialPoolerOutput, self._columnsShape)
        self.spatialColumnsActive = \
          _kSpatialColumnsTemplateStr % (spatialPoolerOutput.sum(), saturation,
                                          innerSat)
    else:
      self._spatialPoolerOutput = None

    # Handle the temporal case...
    if self._tpRegion is not None:
      # Convert temporal array into boolean numpy array
      temporalPoolerOutput = _getOutput(self._tpRegion)
      temporalPoolerOutput = (temporalPoolerOutput != 0)

      # Keep output around...
      self._temporalPoolerOutput = temporalPoolerOutput

      if self._showWhat == kShowTpColumns:
        # Allocate the sequence output--it starts out as all zeros...
        temporalPoolerSeqOutput = numpy.zeros(temporalPoolerOutput.shape,
                                              'bool')

        # If the sequence output is not an int, it means that we have actual
        # sequence output.
        tpSeqOutputNonZeros = self._tpRegion.getParameter('tpSeqOutputNonZeros')
        if not isinstance(tpSeqOutputNonZeros, int):
          # Skip the count...
          tpSeqOutputNonZeros = \
            _getParameterNumpyArray(self._tpRegion, 'tpSeqOutputNonZeros')[1:]
          #tpSeqOutputNonZeros = numpy.array(tpSeqOutputNonZeros)[1:]

          # Make it non-sparse...
          temporalPoolerSeqOutput[tpSeqOutputNonZeros] = True

          # Switch to True to enable these assertions...
          if False:
            # Check to make sure seq output doesn't have any extra bits that
            # full output doesn't have...
            assert ((temporalPoolerSeqOutput | temporalPoolerOutput) == \
                    temporalPoolerOutput).all(), \
                   "Seq output assumed to be subset of output"

            # Check to make sure that temporal pooler has every bit that's
            # part of the sequence output.
            assert ((temporalPoolerSeqOutput & temporalPoolerOutput) == \
                    temporalPoolerSeqOutput).all(), \
                   "Seq output assumed to be subset of output"

        # Different color combinations, then generate a "flat" RGB image:
        # Note that this terminology is a bit confusing because we are working
        #  with inverted input. So, when we see "no input" here, it means we
        #  HAVE input, and vice-versa.
        # - no input, no output: black
        # - input, but no output: white
        # - no input, sequence output: dark green
        # - input and sequence output: bright green
        # - no input, output: dark red
        # - input and output: bright red
        if not self.showInputCheckbox:
          columnInputs.fill(True)
        zeroWithInput  = (columnInputs & (~temporalPoolerOutput))
        oneWithNoInput = (temporalPoolerOutput & (~columnInputs))
        oneWithInput   = (columnInputs & temporalPoolerOutput)
        seqWithNoInput = (temporalPoolerSeqOutput & (~columnInputs))
        seqWithInput   = (columnInputs & temporalPoolerSeqOutput)
        tpNumpyImage = numpy.zeros((len(zeroWithInput), 3), 'uint8')
        tpNumpyImage[zeroWithInput]  = (255, 255, 255)
        tpNumpyImage[oneWithNoInput] = (  0, 191,   0)
        tpNumpyImage[oneWithInput]   = (  0, 255,   0)
        tpNumpyImage[seqWithNoInput] = (223,  87, 223)
        tpNumpyImage[seqWithInput]   = (255, 127, 255)

        # Reshape, then convert to PIL...
        tpNumpyImage = tpNumpyImage.reshape((self._columnsShape[0],
                                             self._columnsShape[1], 3))
        realTemporalColumns = Image.fromarray(tpNumpyImage, 'RGB')
        temporalColumns = inputsInColSpaceImg.copy()
        temporalColumns.paste(realTemporalColumns, self._realInputBbox)
        if self._locationBbox is not None:
          temporalColumns = temporalColumns.crop(self._locationBbox)
        self.temporalColumns = temporalColumns

        # Compute and print saturation
        (saturation, innerSat) = self._computeSaturationLevel(temporalPoolerOutput,
                                                  self._columnsShape)
        self.temporalColumnsActive = \
          _kTemporalColumnsTemplateStr % (temporalPoolerOutput.sum(), saturation,
                                          innerSat)


        # ----------------------------------------------------------------------
        # Compute a histogram of the permanence strengths of all the active
        #  synapses in this area
        if self.synStatsZoomAreaCheckbox:
          (left, top, right, bottom) = self._locationBbox
          left -= self._realInputBbox[0]
          right -= self._realInputBbox[0]
          top -= self._realInputBbox[1]
          bottom -= self._realInputBbox[1]

          tpOutputs = temporalPoolerOutput.reshape(self._columnsShape)

          nzTPOutputs = tpOutputs.nonzero()

          validCellIndices = (
            int(y * self._columnsShape[1] + x)
            for (y, x) in itertools.izip(nzTPOutputs[0], nzTPOutputs[1])
            if top <= y < bottom and left <= x < right
          )

          activations = self._tpRegionRef.getTfdrActiveSynapses(
            validCellIndices, self._spatialPoolerOutput
          )

          synStrengths = []
          for syns in activations.itervalues():
            synStrengths.extend(strength for (srcCell, strength) in syns)


          # Got all the strengths
          if len(synStrengths) > 0:
            synStrengths = numpy.array(synStrengths)
            threeSigma = 3 * synStrengths.std()
            mean = synStrengths.mean()

            self.synStatsZoomAreaValueStr = _kSynStatsZoomAreaValueStr % (
                len(synStrengths),
                synStrengths.min(), synStrengths.max(), synStrengths.mean(),
                mean-threeSigma/2, mean+threeSigma/2
            )

          else:
            self.synStatsZoomAreaValueStr = "No active synapses within zoomed-in area"
        else:
          self.synStatsZoomAreaValueStr = ""

    else:
      self._temporalPoolerOutput = None

    # Clear these, since they are no longer valid...  User must click again...
    self.clickedColumnInfoStr = ""
    self.coincImage = None

  ####################################################################
  def switchRegion(self, region, update=True):
    """Switch to a different region within the same region or multiregion.

    @param  region    The RuntimeRegion to switch to.
    @param  update  If True, we'll call self.update().
    """

    # Save the region, plus a reference to the real region itself...
    self.region = region

    self._regionRef = _getSelf(self.region)

    # ----------------------------------------------------------------------
    # If this region has disableSpatial or disableTemporal, then see if we
    #  can find the corresponding spatial or temporal region above or below
    #  us in the network
    if self.region.getParameter('disableSpatial') or self.region.getParameter('disableTemporal'):

      net = self.region.network
      thisLevelIdx = net.getPhases(self.region.name)[0]
      regions = net.regions
      # sort regions by phase

      prevRegion = None
      nextRegion = None
      for name, r in regions.items():
        phase = net.getPhases(name)[0]
        if phase == thisLevelIdx + 1:
          nextRegion = r
        elif phase == thisLevelIdx - 1:
            prevRegion = r

      if thisLevelIdx > 0 and self.region.getParameter('disableSpatial'):
        self._tpRegion = self.region
        self._tpRegionRef = self._regionRef
        if 'CLARegion' in prevRegion.type and not prevRegion.getParameter('disableSpatial'):
          self._spRegion = prevRegion
          self._spRegionRef = _getSelf(self._spRegion)
      elif thisLevelIdx < len(regions)-1 and self.region.getParameter('disableTemporal'):
        self._spRegion = self.region
        self._spRegionRef = self._regionRef
        if 'CLARegion' in nextRegion.type and not nextRegion.getParameter('disableTemporal'):
          self._tpRegion = nextRegion
          self._tpRegionRef = _getSelf(self._tpRegion)
    else:
      self._spRegion = self._tpRegion = self.region
      self._spRegionRef = self._tpRegionRef = self._regionRef

    # ----------------------------------------------------------------------
    # Store a few parameters to the region that will be useful in our
    # visualization...
    assert (self._spRegionRef is not None)
    self._inputShape = self._spRegionRef.inputShape
    self._columnsShape = self._spRegionRef.coincidencesShape

    inputHeight, inputWidth = self._inputShape
    columnsHeight, columnsWidth = self._columnsShape

    # Create a list of (y, x) coincidence centers...
    coincCenters = numpy.array(self._spRegionRef.getCoincCenters())


    # OK, now comes the tricky part: computing the "fake" columns that we need
    # to pretend we have in order to get a border...
    #
    # The 'coincCenters' gives us an easy mapping from "column space" to input
    # space.  In other words, we can easily find the input associated with the
    # center of each column.  The problem is that not every input has a column
    # over it.  Specifically, the inputs "coincInputRadius" away from the edge
    # don't have columns over them.  It is confusing that these inputs aren't
    # shown in our visualization.
    #
    # Since we want to see all inputs, yet we are viewing things in "column
    # space" (where there is a pixel for every column), we need to make fake
    # columns around the borders so that we can show all inputs.
    #
    # This is trickier than it sounds, since we want the following properties
    # to be true:
    # - The non-fake columns need to be perfect.  That is, we want to know
    #   exactly what input was under the center of the column--it can't be one
    #   pixel off.
    # - The fake columns should have roughly the same "input to column" ratio
    #   as the fake columns, so that the input looks right.

    # Compute how many "fake" columns we'll show.  These are columns that don't
    # really exist, but that we pretend are there so that we can show what would
    # be under them (this allows us to show a "border" with the same input to
    # column ratio as the real columns)...
    #
    # Note: this calculation is a bit unnecessary, since top, bottom, left and
    # right are all based on coincInputRadius so should be the same...
    tlY, tlX = coincCenters.min(axis=0)
    brY, brX = coincCenters.max(axis=0)

    xScale = (brX+1-tlX) / float(columnsWidth)
    yScale = (brY+1-tlY) / float(columnsHeight)

    fakeLeftColumns   = int(round(tlX / xScale))
    fakeRightColumns  = int(round((inputWidth - (brX+1)) / xScale))
    fakeTopColumns    = int(round(tlY / yScale))
    fakeBottomColumns = int(round((inputHeight - (brY+1)) / yScale))

    # Figure out how big our "input map" will be, with all of the fake and
    # real columns together.
    inputMapWidth  = columnsWidth + fakeLeftColumns + fakeRightColumns
    inputMapHeight = columnsHeight + fakeTopColumns + fakeBottomColumns

    # Figure out the x values / y values for the fake columns...
    leftColumns   = numpy.linspace(0, tlX, fakeLeftColumns,
                                   endpoint=False).astype('int32')
    rightColumns  = numpy.linspace(brX+1, inputWidth, fakeRightColumns,
                                   endpoint=False).astype('int32')
    topColumns    = numpy.linspace(0, tlY, fakeTopColumns,
                                   endpoint=False).astype('int32')
    bottomColumns = numpy.linspace(brY+1, inputHeight, fakeBottomColumns,
                                   endpoint=False).astype('int32')

    # Build up the input map.  We will use this to get a view of the inputs
    # in "column space" with: input[self._inputMap].  This is probably overly
    # complicated, but does ensure that the non-fake columsn are exactly what
    # the spatial pooler was using...
    inputMap = numpy.zeros((inputMapHeight, inputMapWidth, 2))

    inputMap[fakeTopColumns:-fakeBottomColumns,
             fakeLeftColumns:-fakeRightColumns] = \
      coincCenters.reshape((columnsHeight, columnsWidth, 2))

    inputMap[:, :fakeLeftColumns, 1]    = leftColumns
    inputMap[:, -fakeRightColumns:, 1]  = rightColumns
    inputMap[:fakeTopColumns, :, 0]     = topColumns.reshape((-1, 1))
    inputMap[-fakeBottomColumns:, :, 0] = bottomColumns.reshape((-1, 1))

    inputMap[:fakeTopColumns, fakeLeftColumns:-fakeRightColumns, 1] = \
      inputMap[fakeTopColumns, fakeLeftColumns:-fakeRightColumns, 1]
    inputMap[-fakeBottomColumns:, fakeLeftColumns:-fakeRightColumns, 1] = \
      inputMap[-fakeBottomColumns-1, fakeLeftColumns:-fakeRightColumns, 1]
    inputMap[fakeTopColumns:-fakeBottomColumns, :fakeLeftColumns, 0] = \
      inputMap[fakeTopColumns:-fakeBottomColumns,
               fakeLeftColumns, 0                ].reshape((-1, 1))
    inputMap[fakeTopColumns:-fakeBottomColumns, -fakeRightColumns:, 0] = \
      inputMap[fakeTopColumns:-fakeBottomColumns,
               -fakeRightColumns-1, 0            ].reshape((-1, 1))


    # Create flat versions...
    self._inputMap = numpy.fromiter(
      ( (y * inputWidth + x) for (y, x) in inputMap.reshape((-1, 2)) ),
      'int32'
    )

    self._coincCentres = numpy.fromiter(
      ( (y * inputWidth + x) for (y, x) in coincCenters ),
      'int32'
    )

    # Store other helpful tidbits...
    self._inputMapWidth = inputMapWidth
    self._inputMapHeight = inputMapHeight
    self._realInputBbox = ((fakeLeftColumns,
                            fakeTopColumns,
                            fakeLeftColumns+columnsWidth,
                            fakeTopColumns+columnsHeight))

    if update:
      self.update()

  ####################################################################
  def _locationZoom_changed(self):
    """Handle when the location zoom level changes."""
    cx = (self._locationBbox[0] + self._locationBbox[2]) / 2
    cy = (self._locationBbox[1] + self._locationBbox[3]) / 2
    self._onLocationMouseMotion(cx, cy, True)

  ####################################################################
  def _helpButton_fired(self):
    """Handle showing help text."""
    wx.MessageBox(_kHelpText, "Help")

  ####################################################################
  def _synStatsZoomAreaCheckbox_changed(self):
    """Handle when the synStatsZoomAreaCheckbox changes."""
    self.update()

  ####################################################################
  def _showInputCheckbox_changed(self):
    """Handle when the showInputCheckbox changes."""
    self.update()