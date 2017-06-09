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
