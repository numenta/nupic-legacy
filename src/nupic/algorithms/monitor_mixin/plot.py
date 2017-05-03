# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014-2015, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
Plot class used in monitor mixin framework.
"""

import os

try:
  # We import in here to avoid creating a matplotlib dependency in nupic.
  import matplotlib.pyplot as plt
  import matplotlib.cm as cm
except ImportError:
  # Suppress this optional dependency on matplotlib. NOTE we don't log this,
  # because python logging implicitly adds the StreamHandler to root logger when
  # calling `logging.debug`, etc., which may undermine an application's logging
  # configuration.
  plt = None
  cm = None



class Plot(object):


  def __init__(self, monitor, title, show=True):
    """

    @param monitor (MonitorMixinBase) Monitor Mixin instance that generated
                                      this plot

    @param title  (string)            Plot title
    """
    self._monitor = monitor
    self._title = title
    self._fig = self._initFigure()
    self._show = show
    if self._show:
      plt.ion()
      plt.show()


  def _initFigure(self):
    fig = plt.figure()
    fig.suptitle(self._prettyPrintTitle())
    return fig


  def _prettyPrintTitle(self):
    if self._monitor.mmName is not None:
      return "[{0}] {1}".format(self._monitor.mmName, self._title)
    return self._title


  def addGraph(self, data, position=111, xlabel=None, ylabel=None):
    """ Adds a graph to the plot's figure.

    @param data See matplotlib.Axes.plot documentation.
    @param position A 3-digit number. The first two digits define a 2D grid
            where subplots may be added. The final digit specifies the nth grid
            location for the added subplot
    @param xlabel text to be displayed on the x-axis
    @param ylabel text to be displayed on the y-axis
    """
    ax = self._addBase(position, xlabel=xlabel, ylabel=ylabel)
    ax.plot(data)
    plt.draw()


  def addHistogram(self, data, position=111, xlabel=None, ylabel=None,
                   bins=None):
    """ Adds a histogram to the plot's figure.

    @param data See matplotlib.Axes.hist documentation.
    @param position A 3-digit number. The first two digits define a 2D grid
            where subplots may be added. The final digit specifies the nth grid
            location for the added subplot
    @param xlabel text to be displayed on the x-axis
    @param ylabel text to be displayed on the y-axis
    """
    ax = self._addBase(position, xlabel=xlabel, ylabel=ylabel)
    ax.hist(data, bins=bins, color="green", alpha=0.8)
    plt.draw()


  def add2DArray(self, data, position=111, xlabel=None, ylabel=None, cmap=None,
                 aspect="auto", interpolation="nearest", name=None):
    """ Adds an image to the plot's figure.

    @param data a 2D array. See matplotlib.Axes.imshow documentation.
    @param position A 3-digit number. The first two digits define a 2D grid
            where subplots may be added. The final digit specifies the nth grid
            location for the added subplot
    @param xlabel text to be displayed on the x-axis
    @param ylabel text to be displayed on the y-axis
    @param cmap color map used in the rendering
    @param aspect how aspect ratio is handled during resize
    @param interpolation interpolation method
    """
    if cmap is None:
      # The default colormodel is an ugly blue-red model.
      cmap = cm.Greys

    ax = self._addBase(position, xlabel=xlabel, ylabel=ylabel)
    ax.imshow(data, cmap=cmap, aspect=aspect, interpolation=interpolation)

    if self._show:
      plt.draw()

    if name is not None:
      if not os.path.exists("log"):
        os.mkdir("log")
      plt.savefig("log/{name}.png".format(name=name), bbox_inches="tight",
                  figsize=(8, 6), dpi=400)



  def _addBase(self, position, xlabel=None, ylabel=None):
    """ Adds a subplot to the plot's figure at specified position.

    @param position A 3-digit number. The first two digits define a 2D grid
            where subplots may be added. The final digit specifies the nth grid
            location for the added subplot
    @param xlabel text to be displayed on the x-axis
    @param ylabel text to be displayed on the y-axis
    @returns (matplotlib.Axes) Axes instance
    """
    ax = self._fig.add_subplot(position)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return ax
