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

import nupic
from PIL import Image
from enthought.traits.api import *
from enthought.traits.ui.api import *
#from nupic.support import title
from nupic.ui.enthought import ImageEditor, ImageListEditor, FileOrDirectoryEditor, alignCenter
from nupic.analysis.inspectors.region.RegionInspector import RegionInspector
from nupic.analysis.inspectors.region.tabs import *

def _getSpecParameters(region):
  return region.spec.parameters

def _getSpatialParameters(region):
  return region.getSelf()._spatialSpec

def _getTemporalParameters(region):
  return region.getSelf()._temporalSpec

def _getOtherParameters(region):
  return region.getSelf()._otherSpec

def _getDescription(spec):
  return spec.description

class _SpatialTab(ParametersTab):

  title = 'Spatial'

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""

    return not region.getParameter('disableSpatial')

  def __init__(self, region):
    parameters = _getSpatialParameters(region).keys()
    parameters.remove('disableSpatial')

    # We can show this if needed, it's not very useful...
    parameters.remove('sparseCoincidenceMatrix')

    self.allowedParameters = parameters
    ParametersTab.__init__(self, region)

  def _addTraits(self):
    ParametersTab._addTraits(self)
    parameters = _getSpecParameters(self.region)
    name = 'spOverlapDistribution'
    spec = parameters[name]
    desc = _getDescription(spec)
    self.add_trait(name, List(name=name, desc=desc))
    self.parameters[name] = spec

class _TemporalTab(ParametersTab):

  title = 'Temporal'

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""

    return not region.getParameter('disableTemporal')

  def __init__(self, region):
    parameters = _getTemporalParameters(region).keys()
    parameters.remove('disableTemporal')
    self.allowedParameters = parameters
    ParametersTab.__init__(self, region)


class _OtherTab(ParametersTab):

  title = 'Other'

  def __init__(self, region):
    parameters = _getOtherParameters(region).keys()

    parameters += ['breakPdb']
    self.allowedParameters = parameters
    ParametersTab.__init__(self, region)

class _CoincsTab(RegionInspectorTab):

  """
  The CoincsTab shows all the leaned SP coincidences.
  """

  def __init__(self, region):
    RegionInspectorTab.__init__(self, region)
    self.sp = region.getSelf()._sfdr
    assert self.sp
    self.tp = region.getSelf()._tfdr
    self.coincCount = self.sp._allConnectedM.nRows()
    self._prevOutput = [-1] * self.coincCount
    self._prevCoincs = [self.sp.getLearnedCmRowAsDenseArray(i) for i in range(self.coincCount)]
    self.coincWidth = 300
    self.encoder = self.region.network.regions['sensor'].getSelf().encoder
    self._addTraits()
    self._createView()

  def _addTraits(self):
    """Add additional traits for the full tab."""
    self.add_trait('coincImages', Instance(numpy.ndarray))

  def onMotion(self, x, y, mouseDown):
    if x == -1:
      return

  def _createView(self):
    """Set up a view for the traits."""
    # Width and height of each coincidence
    w, h = self.coincWidth, 5
    sp = self.region.getSelf()._sfdr


    imageListHeight = 400

    # 1D array for individual colors
    coincsGroup = Group(
      #Group(*items,
      #      show_labels=False,
      #      orientation='vertical'),

      Item('coincImages',
            editor=ImageListEditor(height=imageListHeight,
                                   width=w,
                                   wantMagnifier=True,
                                   interpolate=False,
                                   onMotion=self.onMotion,
                                   getLabel=self.getDecodedCoincidence,
                                   ),
                                   style='simple',

                                   ),
      label='Learned Coincidences',
      show_labels=False,
      show_border=True
    )

    self.traits_view = View(
      coincsGroup,
      title='Coincidences'
    )


  def getDecodedCoincidence(self, i):
    coinc = self.sp.getLearnedCmRowAsDenseArray(i)
    decoded = self.encoder.decode(coinc)
    s = self.encoder.decodedToStr(decoded)
    return s

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- Class method that was called.
    @param elementName -- Name of RuntimeElement.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """
    sp = self.sp
    # 1D array for individual colors

    coincWidth = sp._inputCount

    output = self.region.getParameter('spatialPoolerOutput')
    self.spatialPoolerOutput = output
    if len(output) == 0:
      output = [0] * self.coincCount
    else:
      assert len(output) == self.coincCount
    gap = 10
    total = 0
    coincidences = []

    for i in range(self.coincCount):
      coinc = sp.getLearnedCmRowAsDenseArray(i)
      if self._prevOutput[i] == output[i] and all(coinc == self._prevCoincs[i]):
        continue
      total += 1
      self._prevCoincs[i] = coinc

      # Array from which we form the image
      # Image is 5 pixels high to make it easier to position the mouse
      formattedCoinc = numpy.zeros((15, coincWidth + gap, 3), dtype='uint8')
      gdata = numpy.zeros((coincWidth+gap,), dtype='uint8')
      rdata = numpy.zeros((coincWidth+gap,), dtype='uint8')
      bdata = numpy.zeros((coincWidth+gap,), dtype='uint8')
      coinc = sp.getLearnedCmRowAsDenseArray(i)
      assert len(coinc) == coincWidth

      for j in range(0, gap):
        rdata[j] = gdata[j] = bdata[j] = 224

      for j, x in enumerate(coinc):
        if x:
          gdata[j+gap] = 255

      if output[i] > 0:
        rdata[:5] = 255
        gdata[:5] = 0
        bdata[:5] = 0

      # "on" bits are green.
      formattedCoinc[:,:,0] = rdata   # R
      formattedCoinc[:,:,1] = gdata   # G
      formattedCoinc[:,:,2] = bdata   # B

      coincidences.append(formattedCoinc)

    self._prevOutput = output

    self.coincImages = numpy.array(coincidences)

    #title(additional='(), processed %d coincidences' % total)

class CLARegionInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = [_CoincsTab, _OtherTab, _SpatialTab, _TemporalTab]
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)