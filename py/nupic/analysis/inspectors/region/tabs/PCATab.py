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
import matplotlib

from nupic.analysis.inspectors.region.tabs import *
from nupic.ui.enthought import PlotEditor, WrappedTextEditor


class PCATab(RegionInspectorTab):

  """
  Plots the stored vectors projected onto the first two principal components.
  Colors each point to differentiate the categories.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""
    regionType = region.type
    if 'KNNClassifierRegion' in regionType:
      return True
    if 'SVMClassifierRegion' in regionType:
      return True
    return False

  # Traits
  data = Any
  size = Range(10, 50, 30)

  def __init__(self, region):
    RegionInspectorTab.__init__(self, region)

    message = None
    if 'SVMClassifierRegion' in self.region.type and (not hasattr(region, 'discardProblem') \
                                            or region.getParameter('discardProblem')):
      message = "The data is missing because the region's discardProblem " \
                "parameter is set to True. You must set it to False and " \
                "re-train the classifier."
    elif not self.region.getParameter('SVDDimCount'):
      message = "PCA has not been performed (SVDDimCount is 0)."
    if message:
      # Display the error message
      self.add_trait('message', Str(message))
      self.traits_view = View(
        Item('message', editor=WrappedTextEditor(width=self.plotSize[0]),
             show_label=False),
        title='PCA'
      )
    else:
      # Display the data
      self._getData()
      self.traits_view = View(
        Group(
          # There is a bug with setting the mode to 'spinner'; the range is
          # limited to [0, 1] unless we also set high_name as the dynamic
          # upper limit (even though the limit will be the same)
          Item('component0', editor=RangeEditor(mode='spinner',
                                                high_name='numSVDDims_1'),
            label="Select components (%d total):      x"
                  % self.region.getParameter('SVDDimCount')),
          Item('component1', editor=RangeEditor(mode='spinner',
                                                high_name='SVDDimCount_1'),
            label="  y"),
          orientation='horizontal'
        ),
        Item('data', style='custom', show_label=False,
             editor=PlotEditor(drawPlot=drawScatterPlot,
                               title='Selected principal components'),
             width=self.plotSize[0], height=self.plotSize[0]+self.toolbarSize),
        Group(Item('size', label='Marker size')),
        title='PCA'
      )

  def _getData(self):
    """
    Get the data to plot.

    This function has separate logic for each region type, as there is no
    consistent interface.
    """
    ss = self.region.getSelf()
    if 'KNNClassifierRegion' in self.region.type:
      # Get the first two components of each vector
      self.vectors = ss._knn._Memory
      # Get the category of each vector
      categories = ss._knn._categoryList
      self.categories = numpy.array(categories)
    elif 'SVMClassifierRegion' in self.region.type:
      # Get a matrix with the categories and components
      # The first column of the matrix contains the categories
      #data = self.region.interpret(
      #  'import numpy;'
      #  'problem = self._svm.get_problem();'
      #  'data = numpy.zeros((problem.size(), problem.n_dims() + 1),'
      #                     'dtype=numpy.float32);'
      #  'problem.get_samples(data);'
      #  'response = data', True)
      problem = ss._svm.get_problem()
      data = numpy.zeros((problem.size(), problem.n_dims() + 1),
        dtype=numpy.float32)
      problem.get_samples(data)

      self.categories = data[:,0].astype(numpy.int32)
      self.vectors = data[:,1:]

    # Get the name of each category, if possible
    self.names = None
    net = self.region.network
    if 'sensor' in net.regions:
      sensor = net.regions['sensor']
      if 'ImageSensor' in sensor.type:
        self.names = [c[0] for c in sensor.getParameter('categoryInfo')]


    # Add dropdowns to select the components
    # Use numSVDDims_1 as the upper limit
    # Due to the TraitsUI bug, we must use this trait as the upper limit
    # or else the spinner will not behave properly
    numSVDDims_1 = self.region.numSVDDims - 1
    self.add_trait('numSVDDims_1', Int(numSVDDims_1))
    self.add_trait('component0', Range(0, numSVDDims_1, 0))
    self.add_trait('component1', Range(0, numSVDDims_1, 1))

    self._setComponents()

  def _setComponents(self):
    """Update the plot when the components change."""

    # Plot the selected two components
    self.data = (self.vectors[:, self.component0],
                 self.vectors[:, self.component1],
                 self.categories, self.names, self.size)

  def _size_changed(self): self.data = self.data[:-1] + (self.size,)
  def _component0_changed(self): self._setComponents()
  def _component1_changed(self): self._setComponents()


def drawScatterPlot(editor, value):
  """
  Custom scatter plot drawing routine for PlotEditor.

  editor -- PlotEditor instance.
  value -- PlotEditor value (component0, component1, categories, names, size).
  """

  editor._axes.cla()

  if not value:
    return

  component0, component1, categories, names, size = value

  if not names:
    names = map(str, range(max(categories) + 1))

  # Need to plot each category separately in order to get a legend
  x = [component0[categories == i] for i in xrange(categories.max() + 1)]
  y = [component1[categories == i] for i in xrange(categories.max() + 1)]

  # Loop over the data for each category and plot them independently
  # Transform category index into [0, 1] and pass to colormap to convert
  for i in xrange(len(x)):
    editor._axes.scatter(x[i], y[i], s=size, label=names[i],
                         c=matplotlib.cm.jet(float(i) / (len(x)-1)))

  editor._axes.legend()