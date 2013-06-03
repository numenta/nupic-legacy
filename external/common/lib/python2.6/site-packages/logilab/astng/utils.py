# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
# copyright 2003-2010 Sylvain Thenault, all rights reserved.
# contact mailto:thenault@gmail.com
#
# This file is part of logilab-astng.
#
# logilab-astng is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# logilab-astng is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-astng. If not, see <http://www.gnu.org/licenses/>.
"""this module contains some utilities to navigate in the tree or to
extract information from it
"""

__docformat__ = "restructuredtext en"

from logilab.astng.exceptions import ASTNGBuildingException


class ASTWalker:
    """a walker visiting a tree in preorder, calling on the handler:

    * visit_<class name> on entering a node, where class name is the class of
    the node in lower case

    * leave_<class name> on leaving a node, where class name is the class of
    the node in lower case
    """

    def __init__(self, handler):
        self.handler = handler
        self._cache = {}

    def walk(self, node, _done=None):
        """walk on the tree from <node>, getting callbacks from handler"""
        if _done is None:
            _done = set()
        if node in _done:
            raise AssertionError((id(node), node, node.parent))
        _done.add(node)
        self.visit(node)
        for child_node in node.get_children():
            self.handler.set_context(node, child_node)
            assert child_node is not node
            self.walk(child_node, _done)
        self.leave(node)
        assert node.parent is not node

    def get_callbacks(self, node):
        """get callbacks from handler for the visited node"""
        klass = node.__class__
        methods = self._cache.get(klass)
        if methods is None:
            handler = self.handler
            kid = klass.__name__.lower()
            e_method = getattr(handler, 'visit_%s' % kid,
                               getattr(handler, 'visit_default', None))
            l_method = getattr(handler, 'leave_%s' % kid,
                               getattr(handler, 'leave_default', None))
            self._cache[klass] = (e_method, l_method)
        else:
            e_method, l_method = methods
        return e_method, l_method

    def visit(self, node):
        """walk on the tree from <node>, getting callbacks from handler"""
        method = self.get_callbacks(node)[0]
        if method is not None:
            method(node)

    def leave(self, node):
        """walk on the tree from <node>, getting callbacks from handler"""
        method = self.get_callbacks(node)[1]
        if method is not None:
            method(node)


class LocalsVisitor(ASTWalker):
    """visit a project by traversing the locals dictionary"""
    def __init__(self):
        ASTWalker.__init__(self, self)
        self._visited = {}

    def visit(self, node):
        """launch the visit starting from the given node"""
        if node in self._visited:
            return
        self._visited[node] = 1 # FIXME: use set ?
        methods = self.get_callbacks(node)
        if methods[0] is not None:
            methods[0](node)
        if 'locals' in node.__dict__: # skip Instance and other proxy
            for name, local_node in node.items():
                self.visit(local_node)
        if methods[1] is not None:
            return methods[1](node)


def _check_children(node):
    """a helper function to check children - parent relations"""
    for child in node.get_children():
        ok = False
        if child is None:
            print "Hm, child of %s is None" % node
            continue
        if not hasattr(child, 'parent'):
            print " ERROR: %s has child %s %x with no parent" % (node, child, id(child))
        elif not child.parent:
            print " ERROR: %s has child %s %x with parent %r" % (node, child, id(child), child.parent)
        elif child.parent is not node:
            print " ERROR: %s %x has child %s %x with wrong parent %s" % (node,
                                      id(node), child, id(child), child.parent)
        else:
            ok = True
        if not ok:
            print "lines;", node.lineno, child.lineno
            print "of module", node.root(), node.root().name
            raise ASTNGBuildingException
        _check_children(child)


from _ast import PyCF_ONLY_AST
def parse(string):
    return compile(string, "<string>", 'exec', PyCF_ONLY_AST)

class TreeTester(object):
    '''A helper class to see _ast tree and compare with astng tree

    indent: string for tree indent representation
    lineno: bool to tell if we should print the line numbers

    >>> tester = TreeTester('print')
    >>> print tester.native_tree_repr()

    <Module>
    .   body = [
    .   <Print>
    .   .   nl = True
    .   ]
    >>> print tester.astng_tree_repr()
    Module()
        body = [
        Print()
            dest = 
            values = [
            ]
        ]
    '''

    indent = '.   '
    lineno = False

    def __init__(self, sourcecode):
        self._string = ''
        self.sourcecode = sourcecode
        self._ast_node = None
        self.build_ast()

    def build_ast(self):
        """build the _ast tree from the source code"""
        self._ast_node = parse(self.sourcecode)

    def native_tree_repr(self, node=None, indent=''):
        """get a nice representation of the _ast tree"""
        self._string = ''
        if node is None:
            node = self._ast_node
        self._native_repr_tree(node, indent)
        return self._string


    def _native_repr_tree(self, node, indent, _done=None):
        """recursive method for the native tree representation"""
        from _ast import Load as _Load, Store as _Store, Del as _Del
        from _ast import AST as Node
        if _done is None:
            _done = set()
        if node in _done:
            self._string += '\nloop in tree: %r (%s)' % (node,
                                            getattr(node, 'lineno', None))
            return
        _done.add(node)
        self._string += '\n' + indent +  '<%s>' % node.__class__.__name__
        indent += self.indent
        if not hasattr(node, '__dict__'):
            self._string += '\n' + self.indent + " ** node has no __dict__ " + str(node)
            return
        node_dict = node.__dict__
        if hasattr(node, '_attributes'):
            for a in node._attributes:
                attr = node_dict[a]
                if attr is None:
                    continue
                if a in ("lineno", "col_offset") and not self.lineno:
                    continue
                self._string +='\n' +  indent + a + " = " + repr(attr)
        for field in node._fields or ():
            attr = node_dict[field]
            if attr is None:
                continue
            if isinstance(attr, list):
                if not attr:
                    continue
                self._string += '\n' + indent + field + ' = ['
                for elt in attr:
                    self._native_repr_tree(elt, indent, _done)
                self._string += '\n' + indent + ']'
                continue
            if isinstance(attr, (_Load, _Store, _Del)):
                continue
            if isinstance(attr, Node):
                self._string += '\n' + indent + field + " = "
                self._native_repr_tree(attr, indent, _done)
            else:
                self._string += '\n' + indent + field + " = " + repr(attr)


    def build_astng_tree(self):
        """build astng tree from the _ast tree
        """
        from logilab.astng.builder import ASTNGBuilder
        tree = ASTNGBuilder().string_build(self.sourcecode)
        return tree

    def astng_tree_repr(self, ids=False):
        """build the astng tree and return a nice tree representation"""
        mod = self.build_astng_tree()
        return mod.repr_tree(ids)


__all__ = ('LocalsVisitor', 'ASTWalker',)

