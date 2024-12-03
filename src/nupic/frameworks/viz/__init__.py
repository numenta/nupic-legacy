# Copyright 2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.-
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

