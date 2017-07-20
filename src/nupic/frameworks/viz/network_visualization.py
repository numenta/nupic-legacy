# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2017, Numenta, Inc.  Unless you have an agreement
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

import networkx as nx

from nupic.frameworks.viz import DotRenderer as DEFAULT_RENDERER



class NetworkVisualizer(object):
  """
  Network visualization framework entry point.

  Usage:

  .. code-block:: python
  
    NetworkVisualizer(network).render()

  You may optionally specify a specific renderers. e.g.:

  .. code-block:: python
  
    viz = NetworkVisualizer(network)
    viz.render(renderer=GraphVizRenderer)
    viz.render(renderer=NetworkXRenderer)

  :param network: (:class:`nupic.engine.Network`)
  """

  def __init__(self, network):
    self.network = network


  def export(self):
    """
    Exports a network as a networkx MultiDiGraph intermediate representation
    suitable for visualization.

    :return: networkx MultiDiGraph
    """
    graph = nx.MultiDiGraph()

    # Add regions to graph as nodes, annotated by name
    regions = self.network.getRegions()

    for idx in xrange(regions.getCount()):
      regionPair = regions.getByIndex(idx)
      regionName = regionPair[0]
      graph.add_node(regionName, label=regionName)

    # Add links between regions to graph as edges, annotate by input-output
    # name pairs
    for linkName, link in self.network.getLinks():
      graph.add_edge(link.getSrcRegionName(),
                     link.getDestRegionName(),
                     src=link.getSrcOutputName(),
                     dest=link.getDestInputName())

    return graph


  def render(self, renderer=DEFAULT_RENDERER):
    """
    Render network. Default is 
    :class:`~nupic.frameworks.viz.dot_renderer.DotRenderer`.

    :param renderer: Constructor parameter to a "renderer" implementation.
           Return value for which must have a "render" method that accepts a 
           single argument (a networkx graph instance).
    """
    renderer().render(self.export())
