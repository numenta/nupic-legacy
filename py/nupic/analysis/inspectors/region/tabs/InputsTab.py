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
import numpy

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought import PlotEditor

from nupic.engine import Array

def _getElementCount(spec):
  return spec.count

def _getDescription(spec):
  return spec.description

def _hasParameter(region, name):
  return name in region.spec.parameters

def _getInput(region, name):
  return region.getInputData(name)

def _getInputs(region):
  ns = region.spec
  for name, o in ns.inputs.items():
    if o.count == 0:
      count = len(_getInput(region, name))
      o.item.count = count
      assert o.count == count
  return ns.inputs

def _hasSVDDims(region):
  return 'SVDDimCount' in region.spec.parameters and \
        region.getParameter('SVDDimCount')

def _hasInput(region, name):
  return name in region.spec.inputs

def _getSelf(region):
  return region.getSelf()

class InputsTab(RegionInspectorTab):

  """
  Displays the region's inputs. Also handles PCA by projecting onto the new basis.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""
    return len(region.spec.inputs) > 0

  def __init__(self, region):

    RegionInspectorTab.__init__(self, region)
    # Determine whether the region has performed PCA
    self.pcaBasis = None
    self.pcaPrevious = None

    if _hasSVDDims(self.region):
      if not region.hasInput('bottomUpIn'):
        raise Exception("Region has performed PCA but bottomUpIn not found")
      # Set pcaBasis = (basis vectors, mean)
      x = _getSelf(self.region)
      if "KNNClassifierRegion" in self.region.type:
        knn = x._knn._vt
        mean = x._knn._mean
        self.pcaBasis = (knn, mean)
      elif "SVMClassifierRegion" in self.region.type:
        self.pcaBasis = (x._vt, x._mean)

    self._addInputs()
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
    inputsToRemove = set()
    for name, spec in _getInputs(self.region).items():
      try:
        values = self.region.getInputData(name)
        # Convert values to a list of floats
        values = [float(v) for v in values]
        if len(values) == 0:
          inputsToRemove.add(input)
          continue
      except Exception, e:
        if "Invalid variable name" in e.message:
          inputsToRemove.add(input)
          continue
        else:
          raise

      if _getElementCount(spec) == 1:
        if len(values) == 0:
          import pdb; pdb.set_trace()
        values = values[0]
      # Display the indices of the top N max inputs.
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

    # TODO: Remove inputs that cannot be accessed.

    if self.pcaBasis:
      # Compute the projection of bottomUpIn onto the pca basis
      projection = numpy.dot(self.pcaBasis[0],
                             self.bottomUpIn - self.pcaBasis[1])
      self.PCA = list(projection)
      if self.pcaPrevious is not None:
        self.PCA_diff_with_previous_iteration = \
          list(projection - self.pcaPrevious)
      self.pcaPrevious = projection

  def _addInputs(self):
    """Use the Spec to add inputs as traits."""

    self.inputs = {}
    inputs = _getInputs(self.region)
    for name, spec in inputs.items():
      description = _getDescription(spec)
      elementCount = _getElementCount(spec)
      if elementCount > 0:
        # Skipping this check because it might be expensive.
        if True: # self.region.getSchema().isInputConnected(name):

          if elementCount == 1:
            self.add_trait(name, Float(label=name, desc=description))
          else:
            self.add_trait(name, List(label=name, desc=description))
            # Add traits to display the max outputs as well
            self.add_trait(name+"_maxIndices", Str(label=name+"_maxIndices", desc=description))
            self.add_trait(name+"_maxValues", Str(label=name+"_maxValues", desc=description))
            self.add_trait(name+"_numNonZeros", Str(label=name+"_numNonZeros", desc=description))
          # Store the Spec in the dictionary of inputs
          self.inputs[name] = spec
    if self.pcaBasis:
      # Add another trait for the projected input
      self.add_trait('PCA', List())
      self.add_trait('PCA_diff_with_previous_iteration', List())

  def _createView(self):
    """Set up the view for the traits."""

    plotItems = []
    floatItems = []
    # If it's a log mode input, set the y limits so we don't waste a lot of graph
    #  space on the 0's (very large negative numbers)
    if _hasParameter(self.region, 'logModeIn') and self.region.getParameter('logModeIn'):
      ylim = [-13, None]
    else:
      ylim = None

    inputNames = sorted(self.inputs)
    if self.pcaBasis:
      # Add the PCA plots at the top
      inputNames.insert(0, 'PCA')
      inputNames.insert(1, 'PCA_diff_with_previous_iteration')
    for name in inputNames:
      if not name.startswith('PCA') and _getElementCount(self.inputs[name]) == 1:
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
    self.traits_view = View(plotItems + floatItems, title='Inputs')