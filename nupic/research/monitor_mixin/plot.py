# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

"""
Plot class used in monitor mixin framework.
"""

import abc

import matplotlib.pyplot as plt



class Plot(object):
  """
  A plot graphed over a list of numbers.
  """
  __metaclass__ = abc.ABCMeta


  def __init__(self, monitor, title, data,
               label=None, xlabel=None, ylabel=None):
    """
    @param monitor (MonitorMixinBase) Monitor Mixin instance that generated
                                      this plot
    @param title   (string)           Title
    @param data    (list)             List of numbers to graph plot over
    """
    self._monitor = monitor
    self._title = title
    self._label = label
    self._xlabel = xlabel
    self._ylabel = ylabel

    self._fig = self._initFigure()
    self._graphPlot(data)
    plt.ion()
    plt.show()


  @abc.abstractmethod
  def _graphPlot(self, data):
    """
    @param data (list) List of numbers to graph plot over
    """


  def _initFigure(self):
    fig = plt.figure()
    fig.canvas.set_window_title(self._prettyPrintTitle())
    fig.suptitle(self._label)
    return fig


  def _prettyPrintTitle(self):
    return ("[{0}] {1}".format(self._monitor.mmName, self._title)
            if self._monitor.mmName is not None else self._title)



class HistogramPlot(Plot):
  """
  Histogram plot
  """

  def __init__(self, *args, **kwargs):
    self._bucketSize = kwargs.get("bucketSize")
    if "bucketSize" in kwargs:
      del kwargs["bucketSize"]

    super(HistogramPlot, self).__init__(*args, **kwargs)


  def _graphPlot(self, data):
    """
    @param data (list) List of numbers to graph plot over

    @return (matplotlib.figure) figure
    """
    ax = self._fig.add_subplot(111)
    ax.set_xlabel(self._xlabel)
    ax.set_ylabel(self._ylabel)
    ax.hist(data, self._bucketSize, color="green", alpha=0.8)
