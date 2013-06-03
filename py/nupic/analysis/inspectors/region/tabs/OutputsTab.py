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

import traceback
import numpy

from enthought.traits.api import *
from enthought.traits.ui.api import *

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought import PlotEditor


def _getOutputs(region):
  ns = region.spec
  for name, o in ns.outputs.items():
    if o.count == 0:
      count = len(_getOutput(region, o.name))
      o.item.count = count
      assert o.count == count
  return ns.outputs

def _getElementCount(spec):
  return spec.count

def _getDescription(spec):
  return spec.description

def _hasParameter(region, name):
  return name in region.spec.parameters

def _getOutput(region, name):
    return region.getOutputData(name)

class OutputsTab(RegionInspectorTab):
  """
  Displays the region's outputs.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""

    # Check if the region has any inputs
    result = bool(_getOutputs(region))
    return result

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

    for name, spec in self.outputs.iteritems():
      try:
        values = [float(v) for v in _getOutput(self.region, name)]
      except Exception, e:
        traceback.print_exc()
        continue
      if _getElementCount(spec) == 1:
        values = values[0]

      # Display the indices of the top N max outputs.
      else:
        valArray = numpy.array(values)
        numArgs = (valArray>0).sum()
        displayLimit = 15
        numArgs = min(displayLimit, numArgs)
        outStr0 = "Maxes: "
        outStr1 = "Values: "
        outStr2 = "NumNonZeros: "
        if numArgs == 0:
          outStr0 += "NA"
          outStr1 += "NA"
          outStr2 += "NA"
        else:
          args = valArray.argsort()[-numArgs:]
          args = args[::-1]
          for arg in args:
            outStr0 += "%d, " % arg
            outStr1 += "%f, " % valArray[arg]
          if numArgs == displayLimit:
            outStr0 += "..."
            outStr1 += "..."
        setattr(self, name+"_maxIndices", outStr0)
        setattr(self, name+"_maxValues", outStr1)
        setattr(self, name+"_numNonZeros", "NumNonZeros: %d" % (valArray!=0).sum())

      setattr(self, name, values)

  def _addTraits(self):
    """Use the Spec to add outputs as traits."""

    self.outputs = {}
    outputs = _getOutputs(self.region)
    for name, spec in outputs.items():
      description = _getDescription(spec)
      elementCount = _getElementCount(spec)
      if elementCount == 0:
        continue
      elif elementCount == 1:
        self.add_trait(name, Float(label=name, desc=description))
      else:
        self.add_trait(name, List(label=name, desc=description))
        # Add traits to display the max outputs as well
        self.add_trait(name+"_maxIndices", Str(label=name+"_maxIndices", desc=description))
        self.add_trait(name+"_maxValues", Str(label=name+"_maxValues", desc=description))
        self.add_trait(name+"_numNonZeros", Str(label=name+"_numNonZeros", desc=description))
      # Store the Spec in the dictionary of outputs
      self.outputs[name] = spec

  def _createView(self):
    """Set up the view for the traits."""

    plotItems = []
    floatItems = []
    # If it's a log mode output, set the y limits so we don't waste a lot of graph
    #  space on the 0's (very large negative numbers)
    if _hasParameter(self.region, 'logModeOut') and self.region.getParameter('logModeOut'):
      ylim = [-13, None]
    else:
      ylim = None
    for name in sorted(self.outputs):
      if _getElementCount(self.outputs[name]) == 1:
        floatItems.append(Item(name=name, style='readonly'))
      else:
        plotItems.append(Group(
          Item(name=name, editor=PlotEditor(title=name, verticalToolbar=True, ylim=ylim),
               show_label=False, style='custom',
               width=self.plotSize[0], height=-self.plotSize[1]),
          Item(name=name+"_maxIndices", show_label=False, style='readonly',
                editor=TextEditor(auto_set=False, enter_set=True)),
          Item(name=name+"_maxValues", show_label=False, style='readonly',
                editor=TextEditor(auto_set=False, enter_set=True)),
          Item(name=name+"_numNonZeros", show_label=False, style='readonly',
                editor=TextEditor(auto_set=False, enter_set=True)),
        ))
    self.traits_view = View(plotItems + floatItems, title='Outputs')