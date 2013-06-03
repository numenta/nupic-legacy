# unit tests for the cache module
# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.graph import get_cycles, has_path, ordered_nodes, UnorderableGraph

class getCyclesTC(TestCase):

    def test_known0(self):
        self.assertEqual(get_cycles({1:[2], 2:[3], 3:[1]}), [[1, 2, 3]])

    def test_known1(self):
        self.assertEqual(get_cycles({1:[2], 2:[3], 3:[1, 4], 4:[3]}), [[1, 2, 3], [3, 4]])

    def test_known2(self):
        self.assertEqual(get_cycles({1:[2], 2:[3], 3:[0], 0:[]}), [])


class hasPathTC(TestCase):

    def test_direct_connection(self):
        self.assertEqual(has_path({'A': ['B'], 'B': ['A']}, 'A', 'B'), ['B'])

    def test_indirect_connection(self):
        self.assertEqual(has_path({'A': ['B'], 'B': ['A', 'C'], 'C': ['B']}, 'A', 'C'), ['B', 'C'])

    def test_no_connection(self):
        self.assertEqual(has_path({'A': ['B'], 'B': ['A']}, 'A', 'C'), None)

    def test_cycle(self):
        self.assertEqual(has_path({'A': ['A']}, 'A', 'B'), None)

class ordered_nodesTC(TestCase):

    def test_one_item(self):
        graph = {'a':[]}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('a',))

    def test_single_dependency(self):
        graph = {'a':['b'], 'b':[]}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('a','b'))
        graph = {'a':[], 'b':['a']}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('b','a'))

    def test_two_items_no_dependency(self):
        graph = {'a':[], 'b':[]}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('a','b'))

    def test_three_items_no_dependency(self):
        graph = {'a':[], 'b':[], 'c':[]}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('a', 'b', 'c'))

    def test_three_items_one_dependency(self):
        graph = {'a': ['c'], 'b': [], 'c':[]}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('a', 'b', 'c'))

    def test_three_items_two_dependencies(self):
        graph = {'a': ['b'], 'b': ['c'], 'c':[]}
        ordered = ordered_nodes(graph)
        self.assertEqual(ordered, ('a', 'b', 'c'))

    def test_bad_graph(self):
        graph = {'a':['b']}
        self.assertRaises(UnorderableGraph, ordered_nodes, graph)

if __name__ == "__main__":
    unittest_main()
