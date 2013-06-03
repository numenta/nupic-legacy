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

import nupic
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

    # The spOverlapDistribution is a multiple value parameter, and by default
    #  these are not presented by the inspector
    #parameters = getSpec(self.region)['parameters']
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

class CLARegionSimpleInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = defaultTabs[:]
    index = tabs.index(ParametersTab)
    tabs[index] = _OtherTab
    tabs.insert(index, _TemporalTab)
    tabs.insert(index, _SpatialTab)
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)