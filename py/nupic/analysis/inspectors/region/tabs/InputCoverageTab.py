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


# Common 3rd party imports
from enthought.traits.api import *
from enthought.traits.ui.api import *
import numpy
from PIL import Image
import wx

# NuPIC Imports
import nupic
from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought.editors import ImageEditor

_kScaling = 2
_kInputCoverageScaling = 4
_kBorderPix = 1

_kImgCaptionStr = "Input Coverage of Learned Coincidences"
_kWantWinnersOnlyLabelStr = "Only Show Coverage of Winners"
_kShowUnderOverCoverageStr = "Show Under(green) and Over(red) Coverage of Input"

def _getSelf(region):
  return region.getSelf()

################################################################################
class InputCoverageTab(RegionInspectorTab):
  """Displays all master coincidences.

  This is expected to be useful in cloning, where there aren't too many.
  """

  ####################################################################
  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise.

    @return isRegionSupported  True if this is a supported region.
    """
    return ('CLARegion' in region.type) and (not region.getParameter('disableSpatial'))

  ####################################################################
  def __init__(self, region):
    """InputCoverageTab constructor.

    @param  region  The RuntimeRegion.
    """
    # Call superclass.  This will init, among other things, self.region...
    super(InputCoverageTab, self).__init__(region)

    # --------------------------------------------------------------------
    # Init members, just to be pretty.  Many of these are actually set in
    # self.switchRegion().
    self._regionRef = None

    self._inputShape = (-1, -1)
    self._columnsShape = (-1, -1)

    self.switchRegion(self.region, update=False)

    self.add_trait('inputCoverageImg', Instance(Image.Image))
    self.add_trait('wantWinnersOnly', Bool(True))
    self.add_trait('showUnderOverCoverage', Bool(False))
    self.add_trait('_spacer1', Str())

    # View
    viewItems = []
    viewItems.extend((
      Group(
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        Item('inputCoverageImg',
             editor=ImageEditor(
              width=self._inputShape[1]*_kInputCoverageScaling,
              height=self._inputShape[0]*_kInputCoverageScaling,
              caption=_kImgCaptionStr,
              nearestNeighbor=True,
             ),
             show_label=False),
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        orientation='horizontal',
      ),
      Item('wantWinnersOnly', label=_kWantWinnersOnlyLabelStr),
      Item('showUnderOverCoverage', label=_kShowUnderOverCoverageStr),
    ))

    self.traits_view = View(*viewItems, title='InputCoverage', scrollable=True)

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

    if self.wantWinnersOnly or self.showUnderOverCoverage:
      outputs = numpy.array(self.region.getParameter('spatialPoolerOutput'))
      outputs = (outputs != 0)

    # Make an image representing coverage over the input space...
    inputHeight, inputWidth = self._inputShape
    columnsHeight, columnsWidth = self._columnsShape

    # ------------------------------------------------------------------
    # Generate color image showing where we have over or under-coverage of the
    #  actual input
    if self.showUnderOverCoverage:
      coincCoverage = numpy.zeros(inputHeight*inputWidth, 'float32')
      activeCols = outputs.nonzero()[0]
      for col in activeCols:
        coincCoverage += self._regionRef.getSfdrLearnedRow(col)
      coincCoverage = coincCoverage > 0

      # Which inputs were covered?
      actInputs = numpy.array(self.region.getParameter('spatialPoolerInput')) > 0

      numpyImage = numpy.zeros((inputHeight*inputWidth, 3), 'uint8')

      # White for explained inputs
      numpyImage[actInputs & coincCoverage] = (255, 255, 255)

      # Green for under-coverage
      numpyImage[actInputs & numpy.logical_not(coincCoverage)] = (0, 255, 0)

      # Red for over -coverage
      numpyImage[coincCoverage & numpy.logical_not(actInputs)] = (255, 0, 0)
      numpyImage = numpyImage.reshape((inputHeight, inputWidth, 3))
      inputCoverageImg = Image.fromarray(numpyImage, 'RGB')


    # ------------------------------------------------------------------
    # Generate gray scale image showing where we have coverage
    else:
      inputCoverageArrayFlat = numpy.zeros(self._inputShape, 'float64').reshape(-1)
      for i in xrange(columnsWidth * columnsHeight):
        if (not self.wantWinnersOnly) or (outputs[i]):
          inputCoverageArrayFlat += self._regionRef.getSfdrLearnedRow(i)

      if True:
        inputCoverageArrayFlat *= 255 / inputCoverageArrayFlat.max()
        inputCoverageArray = inputCoverageArrayFlat.astype('uint8').reshape(self._inputShape)
      else:
        # Non-linear...
        neededForShowing = inputCoverageArrayFlat.max() * .40
        toShow = inputCoverageArrayFlat >= neededForShowing
        inputCoverageArray = numpy.zeros(inputCoverageArrayFlat.shape, 'uint8')
        inputCoverageArray[toShow] = 255
        inputCoverageArray = inputCoverageArray.reshape(self._inputShape)

      inputCoverageImg = Image.fromarray(inputCoverageArray, 'L')

    # Resize the image
    self.inputCoverageImg = inputCoverageImg.resize(
      (inputCoverageImg.size[0]*_kInputCoverageScaling,
       inputCoverageImg.size[1]*_kInputCoverageScaling),
      Image.NEAREST
    )

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
    # Store a few parameters to the region that will be useful in our
    # visualization...
    self._inputShape = self._regionRef.inputShape
    self._columnsShape = self._regionRef.coincidencesShape

    if update:
      self.update()

  ####################################################################
  def _wantWinnersOnly_changed(self):
    """Handle when the wantWinnersOnly changes."""
    self.update()

  ####################################################################
  def _showUnderOverCoverage_changed(self):
    """Handle when the showUnderOverCoverage changes."""

    if self.showUnderOverCoverage:
      self.wantWinnersOnly = True

    self.update()