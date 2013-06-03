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

from PIL import (Image,
                 ImageFilter,
                 ImageEnhance,
                 ImageChops,
                 ImageDraw)

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab

from enthought.traits.api import Bool, Int, Str, Instance
from enthought.traits.api import Button
from enthought.traits.ui.api import Item, Group, HGroup, View, CodeEditor
from nupic.ui.enthought import PlotEditor

# For button icons.
from enthought.pyface.image_resource import ImageResource
from nupic.support.resources import getNTAImage

import sys

class LocalTAMTab(RegionInspectorTab):
  """
  Displays custom coincidence diagnostics for a particular region type.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""
    result = None
    try:
      # result = region.getInferenceEngines()[0].getExpandedTAM()
      result = ("TAMs" in region.getModels()[0])
      # NOTE: We currently run into memory allocation errors if the number of
      #  coincidences is too large (definitely crashed with 4100 C's....).
      if result and region.getParameter("_inputResponseDensity") > 350:
        print "Too many coincidences to display LocalTAMTab"
        result = None
    except:
      pass
    return result is not None

  # Traits
  topology = Str("")
  subTAM = Instance(numpy.ndarray)
  output = Str("")
  normalized = Bool(False)
  magnifyActivity = Bool(False)
  threshold = Str("")

  def __init__(self, region):
    RegionInspectorTab.__init__(self, region)
    self._numCoincidences = None
    self.__updateModel()    # So we get dimensions of TAM
    self._createView()

  def __updateModel(self):
    if not len(str(self.topology)):
      from nupic.analysis.inspectors.region.tabs.ContinuousTAMTab import \
          _guessRegionInputTopology2D
      self.topology = str(_guessRegionInputTopology2D(self.region))

    self._updateIndices()

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    if self._numCoincidences is None:
      self.__updateModel()

  def switchRegion(self, region):
    """Switch to a different RuntimeRegion within the same Region."""
    RegionInspectorTab.switchRegion(self, region)
    self.__updateModel()

  def _createView(self):
    """Set up a view for the traits."""

    # Figure out the ticks and ticklabels for the TAM. We want to put a tick on every
    #  coincidence. The dimensions of the TAM image we're showing are N*numCoincidences
    #  wide and tall.
    dim = self.subTAM.shape[0]
    tickWidth = dim / self._numCoincidences
    ticks = numpy.arange(tickWidth/2, dim, tickWidth, dtype='float')
    tickLabels = [str(x) for x in range(self._numCoincidences)]

    self._plotEditor = PlotEditor(colorbar=True, xTicks=ticks,
                        xTickLabels=tickLabels, yTicks=ticks, yTickLabels=tickLabels)
    self.traits_view = View(
      HGroup(
          Group(
              Group(
                  Item('topology', show_label=False, label="Topology", ),
                  Item('normalized', show_label=True),
                  Item('magnifyActivity', show_label=True),
                  Item('threshold', show_label=True),

                  orientation='horizontal',
                  show_left=False
                ),
              Group(
                  Item('subTAM',
                      style='custom',
                      show_label=False,
                      editor=PlotEditor(colorbar=True, xTicks=ticks,
                        xTickLabels=tickLabels, yTicks=ticks, yTickLabels=tickLabels),
                      width=-self.plotSize[0],
                      height=-self.plotSize[0]+self.toolbarSize,
                    ),
                  Item('output',
                      style='readonly',
                      show_label=False,
                      editor=CodeEditor(),
                    ),
                ),
            ),
        ),
        title='LocalTAM'
      )

  def _updateIndices(self):
    """Perform updates related to the coincidence index or topology changing."""

    numCoincidences = self.region.getParameter("_inputResponseDensity")

    rteIndex = self.region.getSchema().getRTEIndex()
    nRegions = self.region.getSchema().getContainer().getElementCount()
    topology = tuple(eval(self.region.getSchema().getContainer().
        getLayoutInfo()["dimensions"]))
    regionIndex = numpy.concatenate(
        numpy.where(numpy.arange(nRegions).reshape(topology) == rteIndex))

    # BUG! getModels() introduces an infinite recursion.
    # tams = self.region.getModels()[0]["TAMs"]
    # Interpret seems to be a work-around.
    if self.normalized:
      if not self.region.interpret("(self._inferenceEngines is not None)"):
        # Make sure the inference engines exist."
        self.region.getInferenceEngines()
      tams = self.region.interpret("self._inferenceEngines[0].normalizedTAMs")

    else:
      tams = self.region.interpret("self.getModels()[0]['TAMs']")

    threshold = str(self.threshold)
    if threshold:
      fThreshold = 0.0
      try:
        fThreshold = float(threshold)
      except Exception, e:
        print >>sys.stderr, "Failed to convert threshold '%s':\n%s" % \
            (threshold, e)
      for tam in tams:
        tam.threshold(fThreshold)
        tam.replaceNZ(tam.max()[2])

    incomingCounts = self.region.interpret("self.getModels()[0]['incomingCounts']")

    miniTAM = tams[rteIndex % len(tams)]
    counts = incomingCounts[rteIndex % len(tams)]
    # First order only.
    numSpatialLocations = miniTAM.shape[0] // miniTAM.shape[1]
    # Assume the spatial receptive field is square. If not,
    # get the shape from the region.
    spatialRF = int(round(numpy.sqrt(float(numSpatialLocations))))

    denseMiniTAM = miniTAM.toDense().reshape(spatialRF, spatialRF,
        numCoincidences, numCoincidences)

    denseMiniTAMRearranged = denseMiniTAM.transpose((2, 0, 3, 1))

    subTAM = denseMiniTAMRearranged

    # What is the right order to set these in?
    subTAM = subTAM.reshape(
        numCoincidences * spatialRF,
        numCoincidences * spatialRF,
      )

    # Are we magnifying the activity?
    if self.magnifyActivity:
      image = Image.new('L', (self.subTAM.shape[1], self.subTAM.shape[0]))
      oldMax = subTAM.max()
      subTAM = subTAM * 255.0 / subTAM.max()
      subTAMShape = subTAM.shape
      image.putdata(subTAM.reshape(-1))
      # Magnify so that each location of activity covers about 1% of the area
      filterSize = (subTAMShape[0] / 100 + 1) | 1
      image = image.filter(ImageFilter.MaxFilter(size=filterSize))
      subTAM = numpy.array(image.split()[0].getdata())
      subTAM = subTAM * oldMax / subTAM.max()
      subTAM.shape = subTAMShape

    self.subTAM = subTAM
    self._numCoincidences = numCoincidences  # used by _createView

  def _topology_changed(self):
    self._updateIndices()

  def _normalized_changed(self):
    self._updateIndices()

  def _threshold_changed(self):
    self._updateIndices()

  def _magnifyActivity_changed(self):
    self._updateIndices()