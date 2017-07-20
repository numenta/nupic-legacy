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
"""
This module provides tools for visualizing a Network graph in different ways.

Here is an example of usage:

.. code-block:: python

  from nupic.frameworks.viz import (NetworkVisualizer,
                                    GraphVizRenderer,
                                    NetworkXRenderer,
                                    DotRenderer)
  # Create Network instance
  network = Network()

  # Add three TestNode regions to network
  network.addRegion("region1", "TestNode", "")
  network.addRegion("region2", "TestNode", "")
  network.addRegion("region3", "TestNode", "")

  # Set dimensions on first region
  region1 = network.getRegions().getByName("region1")
  region1.setDimensions(Dimensions([1, 1]))

  # Link regions
  network.link("region1", "region2", "UniformLink", "")
  network.link("region2", "region1", "UniformLink", "")
  network.link("region1", "region3", "UniformLink", "")
  network.link("region2", "region3", "UniformLink", "")

  # Initialize network
  network.initialize()

  # Initialize Network Visualizer
  viz = NetworkVisualizer(network)

  # Render w/ graphviz
  viz.render(renderer=GraphVizRenderer)

  # Render w/ networkx
  viz.render(renderer=NetworkXRenderer)

  # Render to dot (stdout)
  viz.render(renderer=DotRenderer)

  # Render to dot (file)
  viz.render(renderer=lambda: DotRenderer(open("example.dot", "w")))

"""
from nupic.frameworks.viz.dot_renderer import DotRenderer
from nupic.frameworks.viz.graphviz_renderer import GraphVizRenderer
from nupic.frameworks.viz.networkx_renderer import NetworkXRenderer
from nupic.frameworks.viz.network_visualization import NetworkVisualizer

