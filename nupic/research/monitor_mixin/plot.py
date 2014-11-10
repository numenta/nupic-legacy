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

import matplotlib.pyplot as plt



class Plot(object):
  """
  A plot graphed over a list of numbers.
  """
  def __init__(self, monitor, title):
    """
    @param monitor (MonitorMixinBase) Monitor Mixin instance that generated
                                      this plot
    @param title   (string)           Title
    @param data    (list)             List of numbers to graph plot over
    """
    self._monitor = monitor
    self._title = title

    self._fig = self._initFigure()
    plt.ion()
    plt.show()


  def addGraph(self, data, position=111, xlabel=None, ylabel=None):
    ax = self._addBase(position, xlabel=xlabel, ylabel=ylabel)
    ax.plot(data)
    plt.draw()


  def addHistogram(self, data, position=111, xlabel=None, ylabel=None,
                   bins=None):
    """
    @param bucketSize (int) Size of each bucket
    """
    ax = self._addBase(position, xlabel=xlabel, ylabel=ylabel)
    ax.hist(data, bins=bins, color="green", alpha=0.8)
    plt.draw()


  def _initFigure(self):
    fig = plt.figure()
    fig.suptitle(self._prettyPrintTitle())
    return fig


  def _addBase(self, position, xlabel=None, ylabel=None):
    """
    @param data (list) List of numbers to graph plot over

    @return (matplotlib.Axes) subplot
    """
    ax = self._fig.add_subplot(position)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return ax


  def _prettyPrintTitle(self):
    return ("[{0}] {1}".format(self._monitor.mmName, self._title)
            if self._monitor.mmName is not None else self._title)
