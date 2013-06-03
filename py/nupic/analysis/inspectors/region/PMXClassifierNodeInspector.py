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

from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import *

from nupic.analysis.inspectors.region.RegionInspector import RegionInspector
from nupic.analysis.inspectors.region.tabs import *
from nupic.ui.enthought import PlotEditor
from nupic.network import getSpec


class _ParametersTab(ParametersTab):

  ###########################################################################
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

    # Are we updating the spatial pooler output? If not, remove it so we
    #  don't incur the overhead of reading it in on every step
    if self.updateSpatialPoolerOutput:
      if 'spatialPoolerOutput' not in self.parameters:
        self.parameters['spatialPoolerOutput'] = self._spatialPoolerOutputParam
    else:
      if 'spatialPoolerOutput' in self.parameters:
        self.parameters.pop('spatialPoolerOutput')
        self.spatialPoolerOutput = []

    ParametersTab.update(self, methodName, elementName, args, kwargs)

    tdCoincidenceBounds = self.region.getParameter('tdCoincidenceBounds')
    self.tdCoincidenceBounds = str(tuple([int(x) for x in tdCoincidenceBounds]))

  ###########################################################################
  def _addTraits(self):
    """Use the Spec to add parameters as traits."""

    # Add our control items
    self.add_trait('updateSpatialPoolerOutput', Bool(False,
                      label='update spatial pooler output'))

    # Add the parameters that the base class can handle
    ParametersTab._addTraits(self)

    # Add ones that it normally skips
    self.add_trait('tdCoincidenceBounds', Str(label='tdCoincidenceBounds'))

    # Save the spatialPoolerOutput parameter info
    self._spatialPoolerOutputParam = self.parameters['spatialPoolerOutput']

  ###########################################################################
  def _createView(self):
    """Set up a view for the traits."""

    self.traits_view = View(
      Group(
        Group(
          Item(name='breakPdb', style='simple'),
          Item(name='breakKomodo', style='simple'),

          # BeliefProp mode only params
          Item(name='lbpIterations',
            visible_when='object.cdAlgorithm == "beliefProp_careInside"'),

          Item(name='k'),
          Item(name='whichTopDownWinner'),
          Item(name='numTopDownCategories'),
          Item(name='whichTopDownCoincidence'),
          Item(name='numTopDownCoincidences'),

          label='Dynamic',
          show_border=True
        ),
        Group(
          Group(
            Item(name='cdAlgorithm', style='readonly'),

            Item(name='tdCoincidenceBounds', style='readonly'),
            Item(name='updateSpatialPoolerOutput'),
            Item(name='spatialPoolerMaxValue', style='readonly'),
            Item(name='spatialPoolerMaxIdx', style='readonly'),
          ),

          Group(Item(name='spatialPoolerOutput', show_label=False,
                     editor=PlotEditor(title='spatialPoolerOutput',
                                       verticalToolbar=True),
                     style='custom', width=self.plotSize[0]-self.toolbarSize,
                     height=-self.plotSize[1])),

          label='Static',
          show_border=True
        )
      ),
      title='Parameters'
    )

class PMXClassifierRegionInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = defaultTabs[:]
    tabs[tabs.index(ParametersTab)] = _ParametersTab
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)