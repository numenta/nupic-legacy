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
