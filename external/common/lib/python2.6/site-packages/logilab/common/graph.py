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
"""Graph manipulation utilities.

(dot generation adapted from pypy/translator/tool/make_dot.py)
"""

__docformat__ = "restructuredtext en"

__metaclass__ = type

import os.path as osp
import os
import sys
import tempfile
from logilab.common.compat import str_encode

def escape(value):
    """Make <value> usable in a dot file."""
    lines = [line.replace('"', '\\"') for line in value.split('\n')]
    data = '\\l'.join(lines)
    return '\\n' + data

def target_info_from_filename(filename):
    """Transforms /some/path/foo.png into ('/some/path', 'foo.png', 'png')."""
    basename = osp.basename(filename)
    storedir = osp.dirname(osp.abspath(filename))
    target = filename.split('.')[-1]
    return storedir, basename, target


class DotBackend:
    """Dot File backend."""
    def __init__(self, graphname, rankdir=None, size=None, ratio=None,
            charset='utf-8', renderer='dot', additionnal_param={}):
        self.graphname = graphname
        self.renderer = renderer
        self.lines = []
        self._source = None
        self.emit("digraph %s {" % normalize_node_id(graphname))
        if rankdir:
            self.emit('rankdir=%s' % rankdir)
        if ratio:
            self.emit('ratio=%s' % ratio)
        if size:
            self.emit('size="%s"' % size)
        if charset:
            assert charset.lower() in ('utf-8', 'iso-8859-1', 'latin1'), \
                   'unsupported charset %s' % charset
            self.emit('charset="%s"' % charset)
        for param in additionnal_param.iteritems():
            self.emit('='.join(param))

    def get_source(self):
        """returns self._source"""
        if self._source is None:
            self.emit("}\n")
            self._source = '\n'.join(self.lines)
            del self.lines
        return self._source

    source = property(get_source)

    def generate(self, outputfile=None, dotfile=None, mapfile=None):
        """Generates a graph file.

        :param outputfile: filename and path [defaults to graphname.png]
        :param dotfile: filename and path [defaults to graphname.dot]

        :rtype: str
        :return: a path to the generated file
        """
        import subprocess # introduced in py 2.4
        name = self.graphname
        if not dotfile:
            # if 'outputfile' is a dot file use it as 'dotfile'
            if outputfile and outputfile.endswith(".dot"):
                dotfile = outputfile
            else:
                dotfile = '%s.dot' % name
        if outputfile is not None:
            storedir, basename, target = target_info_from_filename(outputfile)
            if target != "dot":
                pdot, dot_sourcepath = tempfile.mkstemp(".dot", name)
                os.close(pdot)
            else:
                dot_sourcepath = osp.join(storedir, dotfile)
        else:
            target = 'png'
            pdot, dot_sourcepath = tempfile.mkstemp(".dot", name)
            ppng, outputfile = tempfile.mkstemp(".png", name)
            os.close(pdot)
            os.close(ppng)
        pdot = open(dot_sourcepath, 'w')
        pdot.write(str_encode(self.source, 'utf8'))
        pdot.close()
        if target != 'dot':
            if sys.platform == 'win32':
                use_shell = True
            else:
                use_shell = False
            if mapfile:
                subprocess.call([self.renderer,  '-Tcmapx', '-o', mapfile, '-T', target, dot_sourcepath, '-o', outputfile],
                                shell=use_shell)
            else:
                subprocess.call([self.renderer, '-T',  target,
                                 dot_sourcepath, '-o',  outputfile],
                                shell=use_shell)
            os.unlink(dot_sourcepath)
        return outputfile

    def emit(self, line):
        """Adds <line> to final output."""
        self.lines.append(line)

    def emit_edge(self, name1, name2, **props):
        """emit an edge from <name1> to <name2>.
        edge properties: see http://www.graphviz.org/doc/info/attrs.html
        """
        attrs = ['%s="%s"' % (prop, value) for prop, value in props.items()]
        n_from, n_to = normalize_node_id(name1), normalize_node_id(name2)
        self.emit('%s -> %s [%s];' % (n_from, n_to, ", ".join(attrs)) )

    def emit_node(self, name, **props):
        """emit a node with given properties.
        node properties: see http://www.graphviz.org/doc/info/attrs.html
        """
        attrs = ['%s="%s"' % (prop, value) for prop, value in props.items()]
        self.emit('%s [%s];' % (normalize_node_id(name), ", ".join(attrs)))

def normalize_node_id(nid):
    """Returns a suitable DOT node id for `nid`."""
    return '"%s"' % nid

class GraphGenerator:
    def __init__(self, backend):
        # the backend is responsible to output the graph in a particular format
        self.backend = backend

    # XXX doesn't like space in outpufile / mapfile
    def generate(self, visitor, propshdlr, outputfile=None, mapfile=None):
        # the visitor
        # the property handler is used to get node and edge properties
        # according to the graph and to the backend
        self.propshdlr = propshdlr
        for nodeid, node in visitor.nodes():
            props = propshdlr.node_properties(node)
            self.backend.emit_node(nodeid, **props)
        for subjnode, objnode, edge in visitor.edges():
            props = propshdlr.edge_properties(edge, subjnode, objnode)
            self.backend.emit_edge(subjnode, objnode, **props)
        return self.backend.generate(outputfile=outputfile, mapfile=mapfile)


class UnorderableGraph(Exception):
    pass

def ordered_nodes(graph):
    """takes a dependency graph dict as arguments and return an ordered tuple of
    nodes starting with nodes without dependencies and up to the outermost node.

    If there is some cycle in the graph, :exc:`UnorderableGraph` will be raised.

    Also the given graph dict will be emptied.
    """
    # check graph consistency
    cycles = get_cycles(graph)
    if cycles:
        cycles = '\n'.join([' -> '.join(cycle) for cycle in cycles])
        raise UnorderableGraph('cycles in graph: %s' % cycles)
    vertices = set(graph)
    to_vertices = set()
    for edges in graph.values():
        to_vertices |= set(edges)
    missing_vertices = to_vertices - vertices
    if missing_vertices:
        raise UnorderableGraph('missing vertices: %s' % ', '.join(missing_vertices))
    # order vertices
    order = []
    order_set = set()
    old_len = None
    while graph:
        if old_len == len(graph):
            raise UnorderableGraph('unknown problem with %s' % graph)
        old_len = len(graph)
        deps_ok = []
        for node, node_deps in graph.items():
            for dep in node_deps:
                if dep not in order_set:
                    break
            else:
                deps_ok.append(node)
        order.append(deps_ok)
        order_set |= set(deps_ok)
        for node in deps_ok:
            del graph[node]
    result = []
    for grp in reversed(order):
        result.extend(sorted(grp))
    return tuple(result)


def get_cycles(graph_dict, vertices=None):
    '''given a dictionary representing an ordered graph (i.e. key are vertices
    and values is a list of destination vertices representing edges), return a
    list of detected cycles
    '''
    if not graph_dict:
        return ()
    result = []
    if vertices is None:
        vertices = graph_dict.keys()
    for vertice in vertices:
        _get_cycles(graph_dict, vertice, [], result)
    return result

def _get_cycles(graph_dict, vertice=None, path=None, result=None):
    """recursive function doing the real work for get_cycles"""
    if vertice in path:
        cycle = [vertice]
        for node in path[::-1]:
            if node == vertice:
                break
            cycle.insert(0, node)
        # make a canonical representation
        start_from = min(cycle)
        index = cycle.index(start_from)
        cycle = cycle[index:] + cycle[0:index]
        # append it to result if not already in
        if not cycle in result:
            result.append(cycle)
        return
    path.append(vertice)
    try:
        for node in graph_dict[vertice]:
            _get_cycles(graph_dict, node, path, result)
    except KeyError:
        pass
    path.pop()

def has_path(graph_dict, fromnode, tonode, path=None):
    """generic function taking a simple graph definition as a dictionary, with
    node has key associated to a list of nodes directly reachable from it.

    Return None if no path exists to go from `fromnode` to `tonode`, else the
    first path found (as a list including the destination node at last)
    """
    if path is None:
        path = []
    elif fromnode in path:
        return None
    path.append(fromnode)
    for destnode in graph_dict[fromnode]:
        if destnode == tonode or has_path(graph_dict, destnode, tonode, path):
            return path[1:] + [tonode]
    path.pop()
    return None

