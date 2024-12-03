# Copyright 2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import io
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg



class GraphVizRenderer(object):
  """
  Network visualization "renderer" implementation to render a network with
  graphviz.
  """

  def render(self, graph):
    graph = nx.nx_agraph.to_agraph(graph)
    graph.layout()

    buffer = io.BytesIO()
    graph.draw(buffer, format="png", prog="dot")
    buffer.seek(0)
    img = mpimg.imread(buffer)
    plt.imshow(img)
    plt.show()
