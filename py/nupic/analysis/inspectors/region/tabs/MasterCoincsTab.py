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
from nupic.ui.enthought import FileOrDirectoryEditor
import numpy
from PIL import Image
import wx
import os

# NuPIC Imports
import nupic
from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought.editors import ImageEditor

_kBorderPix = 1
_kMaxZoom = 8

def _getSelf(region):
  return region.getSelf()

################################################################################
class MasterCoincsTab(RegionInspectorTab):
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
    """MasterCoincsTab constructor.

    @param  region  The RuntimeRegion.
    """
    # Call superclass.  This will init, among other things, self.region...
    super(MasterCoincsTab, self).__init__(region)

    # --------------------------------------------------------------------
    # Init members, just to be pretty.  Many of these are actually set in
    # self.switchRegion().
    self._regionRef = None

    self._coincInputRadius = -1
    self._outputCloningWidth = -1
    self._outputCloningHeight = -1

    self._coincRfWidth = -1
    self._coincRfHeight = -1
    self._imgMaxWidth = -1      # When maximum zoom
    self._imgMaxHeight = -1     # When maximum zoom
    self._imgWidth = -1
    self._imgHeight = -1

    self._kScaling = 1.0

    self.add_trait('showLearned', Bool(True))
    self.add_trait('zoomFactor', Range(1, _kMaxZoom, 1, mode='spinner'))
    self.add_trait('img', Instance(Image.Image))
    self.add_trait('saveImage', Directory)
    self.add_trait('_spacer1', Str())

    self.switchRegion(self.region, update=False)


    # View
    viewItems = []
    viewItems.extend((
      Item('showLearned', label="Show Learned"),
      Group(
        Item('zoomFactor', label="Zoom"),
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        Item('_spacer1', style='readonly', show_label=False, springy=False),
        orientation='horizontal',
      ),
      Group(
        Item('saveImage', show_label=False,
          editor=FileOrDirectoryEditor(directory=True,
            buttonLabel="Save image...",
            dialogTitle="Save as masterCoinc.jpg in...")),
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        Item('_spacer1', style='readonly', show_label=False, springy=False),
        orientation='horizontal',
      ),
      Group(
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        Item('img',
             editor=ImageEditor(
              width=self._imgMaxWidth,
              height=self._imgMaxHeight,
              caption="Master Coincidences",
              nearestNeighbor=True,
             ),
             show_label=False),
        Item('_spacer1', style='readonly', show_label=False, springy=True),
        orientation='horizontal',
      ),
    ))

    self.traits_view = View(*viewItems, title='MasterCoincs', scrollable=True)

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

    # Make a subset where the coincidences will be drawn
    self._coincImg = Image.new('RGB', (self._imgWidth, self._imgHeight),
                        (255, 0, 0))


    for rowNum in xrange(self._outputCloningHeight):
      for colNum in xrange(self._outputCloningWidth):
        masterNum = rowNum * self._outputCloningWidth + colNum

        mlc = self._regionRef.getSfdrMasterLearnedCoincidence(masterNum)
        if self.showLearned:
          denseCoinc = numpy.zeros((self._coincRfHeight, self._coincRfWidth),
                                   'uint8')
          denseCoinc[mlc] = 255
          img = Image.fromarray(denseCoinc, 'L')
        else:
          mHist = self._regionRef.getSfdrMasterHistogram(masterNum)
          if hasattr(self._regionRef, 'synPermConnected'):  # New SP
            vmax = self._regionRef.synPermConnected * 2
          else:
            vmax = mHist.max()
          mHist = (mHist * 255.0 / vmax).astype('uint8')

          # Don't show red and blue wherever the MLC is...
          rb = mHist.copy()
          rb[mlc] = 0

          rbImg = Image.fromarray(rb, 'L')
          gImg  = Image.fromarray(mHist, 'L')
          img = Image.merge('RGB', (rbImg, gImg, rbImg))

        img = img.resize((int(self._kScaling * self._coincRfWidth),
                          int(self._kScaling * self._coincRfHeight)),
                          Image.NEAREST)

        self._coincImg.paste(
          img,
          (_kBorderPix + colNum * (int(self._kScaling * self._coincRfWidth) + _kBorderPix),
           _kBorderPix + rowNum * (int(self._kScaling * self._coincRfHeight) + _kBorderPix))
        )

    # Make a blank image in gray
    fullImg = Image.new('RGB', (self._imgMaxWidth, self._imgMaxHeight),
                        (128, 128, 128))

    fullImg.paste(self._coincImg, (0,0))
    self.img = fullImg

  ####################################################################
  def switchRegion(self, region, update=True):
    """Switch to a different region within the same region or multiregion.

    @param  region    The RuntimeRegion to switch to.
    @param  update  If True, we'll call self.update().
    """

    # Save the region, plus a reference to the real region itself...
    self.region = region
    self._regionRef = _getSelf(region)

    # ----------------------------------------------------------------------
    # Store a few parameters to the region that will be useful in our
    # visualization...
    self._coincInputRadius = self._regionRef.coincInputRadius
    self._outputCloningHeight = self._regionRef.outputCloningHeight
    self._outputCloningWidth = self._regionRef.outputCloningWidth

    self._coincRfWidth  = (2 * self._coincInputRadius + 1)
    self._coincRfHeight = (2 * self._coincInputRadius + 1)

    # Figure out a decent scaling factor
    self._kScaling = (640.0 - (self._outputCloningWidth-1) * _kBorderPix) \
                   / (self._coincRfWidth * self._outputCloningWidth)
    maxScaling = self._kScaling * _kMaxZoom
    self._kScaling *= self.zoomFactor

    self._imgWidth  = int(
      (self._coincRfWidth * self._outputCloningWidth * self._kScaling) +
      ((self._outputCloningWidth-1) * _kBorderPix))

    self._imgHeight = int (
      (self._coincRfHeight * self._outputCloningHeight * self._kScaling) +
      ((self._outputCloningHeight-1) * _kBorderPix))

    self._imgMaxWidth  = int(
      (self._coincRfWidth * self._outputCloningWidth * maxScaling) +
      ((self._outputCloningWidth-1) * _kBorderPix))

    self._imgMaxHeight = int (
      (self._coincRfHeight * self._outputCloningHeight * maxScaling) +
      ((self._outputCloningHeight-1) * _kBorderPix))

    if update:
      self.update()

  ####################################################################
  def _showLearned_changed(self):
    """Handle when showLearned changes."""
    self.update()

  def _zoomFactor_changed(self):
    """Handle when zoomFactor changes."""
    self.switchRegion(self.region, update=True)

  def _saveImage_changed(self):
    """Handle when user clicks to save the image."""
    self._coincImg.save(os.path.join(self.saveImage, 'masterCoinc.jpg'))
    self.saveImage = ''