# Copyright 2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import networkx as nx
import matplotlib.pyplot as plt



class NetworkXRenderer(object):
  """
  Network visualization "renderer" implementation to render a network with
  graphviz.
  """

  def __init__(self, layoutFn=nx.spring_layout):
    self.layoutFn = layoutFn

  def render(self, graph):
    pos = self.layoutFn(graph)
    nx.draw_networkx(graph, pos)
    nx.draw_networkx_edge_labels(graph, pos, clip_on=False, rotate=False)
    plt.show()
