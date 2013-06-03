# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""Module for some node classes. More nodes in scoped_nodes.py
"""

import sys

from logilab.astng import BUILTINS_MODULE
from logilab.astng.exceptions import NoDefault
from logilab.astng.bases import (NodeNG, Statement, Instance, InferenceContext,
                                 _infer_stmts, YES)
from logilab.astng.mixins import BlockRangeMixIn, AssignTypeMixin, \
                                 ParentAssignTypeMixin, FromImportMixIn


def unpack_infer(stmt, context=None):
    """recursively generate nodes inferred by the given statement.
    If the inferred value is a list or a tuple, recurse on the elements
    """
    if isinstance(stmt, (List, Tuple)):
        for elt in stmt.elts:
            for infered_elt in unpack_infer(elt, context):
                yield infered_elt
        return
    # if infered is a final node, return it and stop
    infered = stmt.infer(context).next()
    if infered is stmt:
        yield infered
        return
    # else, infer recursivly, except YES object that should be returned as is
    for infered in stmt.infer(context):
        if infered is YES:
            yield infered
        else:
            for inf_inf in unpack_infer(infered, context):
                yield inf_inf


def are_exclusive(stmt1, stmt2, exceptions=None):
    """return true if the two given statements are mutually exclusive

    `exceptions` may be a list of exception names. If specified, discard If
    branches and check one of the statement is in an exception handler catching
    one of the given exceptions.

    algorithm :
     1) index stmt1's parents
     2) climb among stmt2's parents until we find a common parent
     3) if the common parent is a If or TryExcept statement, look if nodes are
        in exclusive branches
    """
    # index stmt1's parents
    stmt1_parents = {}
    children = {}
    node = stmt1.parent
    previous = stmt1
    while node:
        stmt1_parents[node] = 1
        children[node] = previous
        previous = node
        node = node.parent
    # climb among stmt2's parents until we find a common parent
    node = stmt2.parent
    previous = stmt2
    while node:
        if node in stmt1_parents:
            # if the common parent is a If or TryExcept statement, look if
            # nodes are in exclusive branches
            if isinstance(node, If) and exceptions is None:
                if (node.locate_child(previous)[1]
                    is not node.locate_child(children[node])[1]):
                    return True
            elif isinstance(node, TryExcept):
                c2attr, c2node = node.locate_child(previous)
                c1attr, c1node = node.locate_child(children[node])
                if c1node is not c2node:
                    if ((c2attr == 'body' and c1attr == 'handlers' and children[node].catch(exceptions)) or
                        (c2attr == 'handlers' and c1attr == 'body' and previous.catch(exceptions)) or
                        (c2attr == 'handlers' and c1attr == 'orelse') or
                        (c2attr == 'orelse' and c1attr == 'handlers')):
                        return True
                elif c2attr == 'handlers' and c1attr == 'handlers':
                    return previous is not children[node]
            return False
        previous = node
        node = node.parent
    return False


class LookupMixIn(object):
    """Mixin looking up a name in the right scope
    """

    def lookup(self, name):
        """lookup a variable name

        return the scope node and the list of assignments associated to the given
        name according to the scope where it has been found (locals, globals or
        builtin)

        The lookup is starting from self's scope. If self is not a frame itself and
        the name is found in the inner frame locals, statements will be filtered
        to remove ignorable statements according to self's location
        """
        return self.scope().scope_lookup(self, name)

    def ilookup(self, name):
        """infered lookup

        return an iterator on infered values of the statements returned by
        the lookup method
        """
        frame, stmts = self.lookup(name)
        context = InferenceContext()
        return _infer_stmts(stmts, context, frame)

    def _filter_stmts(self, stmts, frame, offset):
        """filter statements to remove ignorable statements.

        If self is not a frame itself and the name is found in the inner
        frame locals, statements will be filtered to remove ignorable
        statements according to self's location
        """
        # if offset == -1, my actual frame is not the inner frame but its parent
        #
        # class A(B): pass
        #
        # we need this to resolve B correctly
        if offset == -1:
            myframe = self.frame().parent.frame()
        else:
            myframe = self.frame()
        if not myframe is frame or self is frame:
            return stmts
        mystmt = self.statement()
        # line filtering if we are in the same frame
        #
        # take care node may be missing lineno information (this is the case for
        # nodes inserted for living objects)
        if myframe is frame and mystmt.fromlineno is not None:
            assert mystmt.fromlineno is not None, mystmt
            mylineno = mystmt.fromlineno + offset
        else:
            # disabling lineno filtering
            mylineno = 0
        _stmts = []
        _stmt_parents = []
        for node in stmts:
            stmt = node.statement()
            # line filtering is on and we have reached our location, break
            if mylineno > 0 and stmt.fromlineno > mylineno:
                break
            assert hasattr(node, 'ass_type'), (node, node.scope(),
                                               node.scope().locals)
            ass_type = node.ass_type()

            if node.has_base(self):
                break

            _stmts, done = ass_type._get_filtered_stmts(self, node, _stmts, mystmt)
            if done:
                break

            optional_assign = ass_type.optional_assign
            if optional_assign and ass_type.parent_of(self):
                # we are inside a loop, loop var assigment is hidding previous
                # assigment
                _stmts = [node]
                _stmt_parents = [stmt.parent]
                continue

            # XXX comment various branches below!!!
            try:
                pindex = _stmt_parents.index(stmt.parent)
            except ValueError:
                pass
            else:
                # we got a parent index, this means the currently visited node
                # is at the same block level as a previously visited node
                if _stmts[pindex].ass_type().parent_of(ass_type):
                    # both statements are not at the same block level
                    continue
                # if currently visited node is following previously considered
                # assignement and both are not exclusive, we can drop the
                # previous one. For instance in the following code ::
                #
                #   if a:
                #     x = 1
                #   else:
                #     x = 2
                #   print x
                #
                # we can't remove neither x = 1 nor x = 2 when looking for 'x'
                # of 'print x'; while in the following ::
                #
                #   x = 1
                #   x = 2
                #   print x
                #
                # we can remove x = 1 when we see x = 2
                #
                # moreover, on loop assignment types, assignment won't
                # necessarily be done if the loop has no iteration, so we don't
                # want to clear previous assigments if any (hence the test on
                # optional_assign)
                if not (optional_assign or are_exclusive(_stmts[pindex], node)):
                    del _stmt_parents[pindex]
                    del _stmts[pindex]
            if isinstance(node, AssName):
                if not optional_assign and stmt.parent is mystmt.parent:
                    _stmts = []
                    _stmt_parents = []
            elif isinstance(node, DelName):
                _stmts = []
                _stmt_parents = []
                continue
            if not are_exclusive(self, node):
                _stmts.append(node)
                _stmt_parents.append(stmt.parent)
        return _stmts

# Name classes

class AssName(LookupMixIn, ParentAssignTypeMixin, NodeNG):
    """class representing an AssName node"""


class DelName(LookupMixIn, ParentAssignTypeMixin, NodeNG):
    """class representing a DelName node"""


class Name(LookupMixIn, NodeNG):
    """class representing a Name node"""




#####################   node classes   ########################################

class Arguments(NodeNG, AssignTypeMixin):
    """class representing an Arguments node"""
    _astng_fields = ('args', 'defaults')
    args = None
    defaults = None

    def __init__(self, vararg=None, kwarg=None):
        self.vararg = vararg
        self.kwarg = kwarg

    def _infer_name(self, frame, name):
        if self.parent is frame:
            return name
        return None

    def format_args(self):
        """return arguments formatted as string"""
        result = [_format_args(self.args, self.defaults)]
        if self.vararg:
            result.append('*%s' % self.vararg)
        if self.kwarg:
            result.append('**%s' % self.kwarg)
        return ', '.join(result)

    def default_value(self, argname):
        """return the default value for an argument

        :raise `NoDefault`: if there is no default value defined
        """
        i = _find_arg(argname, self.args)[0]
        if i is not None:
            idx = i - (len(self.args) - len(self.defaults))
            if idx >= 0:
                return self.defaults[idx]
        raise NoDefault()

    def is_argument(self, name):
        """return True if the name is defined in arguments"""
        if name == self.vararg:
            return True
        if name == self.kwarg:
            return True
        return self.find_argname(name, True)[1] is not None

    def find_argname(self, argname, rec=False):
        """return index and Name node with given name"""
        if self.args: # self.args may be None in some cases (builtin function)
            return _find_arg(argname, self.args, rec)
        return None, None


def _find_arg(argname, args, rec=False):
    for i, arg in enumerate(args):
        if isinstance(arg, Tuple):
            if rec:
                found = _find_arg(argname, arg.elts)
                if found[0] is not None:
                    return found
        elif arg.name == argname:
            return i, arg
    return None, None


def _format_args(args, defaults=None):
    values = []
    if args is None:
        return ''
    if defaults is not None:
        default_offset = len(args) - len(defaults)
    for i, arg in enumerate(args):
        if isinstance(arg, Tuple):
            values.append('(%s)' % _format_args(arg.elts))
        else:
            values.append(arg.name)
            if defaults is not None and i >= default_offset:
                values[-1] += '=' + defaults[i-default_offset].as_string()
    return ', '.join(values)


class AssAttr(NodeNG, ParentAssignTypeMixin):
    """class representing an AssAttr node"""
    _astng_fields = ('expr',)
    expr = None

class Assert(Statement):
    """class representing an Assert node"""
    _astng_fields = ('test', 'fail',)
    test = None
    fail = None

class Assign(Statement, AssignTypeMixin):
    """class representing an Assign node"""
    _astng_fields = ('targets', 'value',)
    targets = None
    value = None

class AugAssign(Statement, AssignTypeMixin):
    """class representing an AugAssign node"""
    _astng_fields = ('target', 'value',)
    target = None
    value = None

class Backquote(NodeNG):
    """class representing a Backquote node"""
    _astng_fields = ('value',)
    value = None

class BinOp(NodeNG):
    """class representing a BinOp node"""
    _astng_fields = ('left', 'right',)
    left = None
    right = None

class BoolOp(NodeNG):
    """class representing a BoolOp node"""
    _astng_fields = ('values',)
    values = None

class Break(Statement):
    """class representing a Break node"""


class CallFunc(NodeNG):
    """class representing a CallFunc node"""
    _astng_fields = ('func', 'args', 'starargs', 'kwargs')
    func = None
    args = None
    starargs = None
    kwargs = None

    def __init__(self):
        self.starargs = None
        self.kwargs = None

class Compare(NodeNG):
    """class representing a Compare node"""
    _astng_fields = ('left', 'ops',)
    left = None
    ops = None

    def get_children(self):
        """override get_children for tuple fields"""
        yield self.left
        for _, comparator in self.ops:
            yield comparator # we don't want the 'op'

    def last_child(self):
        """override last_child"""
        # XXX maybe if self.ops:
        return self.ops[-1][1]
        #return self.left

class Comprehension(NodeNG):
    """class representing a Comprehension node"""
    _astng_fields = ('target', 'iter' ,'ifs')
    target = None
    iter = None
    ifs = None

    optional_assign = True
    def ass_type(self):
        return self

    def _get_filtered_stmts(self, lookup_node, node, stmts, mystmt):
        """method used in filter_stmts"""
        if self is mystmt:
            if isinstance(lookup_node, (Const, Name)):
                return [lookup_node], True

        elif self.statement() is mystmt:
            # original node's statement is the assignment, only keeps
            # current node (gen exp, list comp)

            return [node], True

        return stmts, False


class Const(NodeNG, Instance):
    """represent a constant node like num, str, bool, None, bytes"""

    def __init__(self, value=None):
        self.value = value

    def getitem(self, index, context=None):
        if isinstance(self.value, basestring):
            return Const(self.value[index])
        raise TypeError('%r (value=%s)' % (self, self.value))

    def has_dynamic_getattr(self):
        return False

    def itered(self):
        if isinstance(self.value, basestring):
            return self.value
        raise TypeError()

    def pytype(self):
        return self._proxied.qname()


class Continue(Statement):
    """class representing a Continue node"""


class Decorators(NodeNG):
    """class representing a Decorators node"""
    _astng_fields = ('nodes',)
    nodes = None

    def __init__(self, nodes=None):
        self.nodes = nodes

    def scope(self):
        # skip the function node to go directly to the upper level scope
        return self.parent.parent.scope()

class DelAttr(NodeNG, ParentAssignTypeMixin):
    """class representing a DelAttr node"""
    _astng_fields = ('expr',)
    expr = None


class Delete(Statement, AssignTypeMixin):
    """class representing a Delete node"""
    _astng_fields = ('targets',)
    targets = None


class Dict(NodeNG, Instance):
    """class representing a Dict node"""
    _astng_fields = ('items',)

    def __init__(self, items=None):
        if items is None:
            self.items = []
        else:
            self.items = [(const_factory(k), const_factory(v))
                          for k,v in items.iteritems()]

    def pytype(self):
        return '%s.dict' % BUILTINS_MODULE

    def get_children(self):
        """get children of a Dict node"""
        # overrides get_children
        for key, value in self.items:
            yield key
            yield value

    def last_child(self):
        """override last_child"""
        if self.items:
            return self.items[-1][1]
        return None

    def itered(self):
        return self.items[::2]

    def getitem(self, key, context=None):
        for i in xrange(0, len(self.items), 2):
            for inferedkey in self.items[i].infer(context):
                if inferedkey is YES:
                    continue
                if isinstance(inferedkey, Const) and inferedkey.value == key:
                    return self.items[i+1]
        raise IndexError(key)


class Discard(Statement):
    """class representing a Discard node"""
    _astng_fields = ('value',)
    value = None


class Ellipsis(NodeNG):
    """class representing an Ellipsis node"""


class EmptyNode(NodeNG):
    """class representing an EmptyNode node"""


class ExceptHandler(Statement, AssignTypeMixin):
    """class representing an ExceptHandler node"""
    _astng_fields = ('type', 'name', 'body',)
    type = None
    name = None
    body = None

    def _blockstart_toline(self):
        if self.name:
            return self.name.tolineno
        elif self.type:
            return self.type.tolineno
        else:
            return self.lineno

    def set_line_info(self, lastchild):
        self.fromlineno = self.lineno
        self.tolineno = lastchild.tolineno
        self.blockstart_tolineno = self._blockstart_toline()

    def catch(self, exceptions):
        if self.type is None or exceptions is None:
            return True
        for node in self.type.nodes_of_class(Name):
            if node.name in exceptions:
                return True


class Exec(Statement):
    """class representing an Exec node"""
    _astng_fields = ('expr', 'globals', 'locals',)
    expr = None
    globals = None
    locals = None


class ExtSlice(NodeNG):
    """class representing an ExtSlice node"""
    _astng_fields = ('dims',)
    dims = None

class For(BlockRangeMixIn, AssignTypeMixin, Statement):
    """class representing a For node"""
    _astng_fields = ('target', 'iter', 'body', 'orelse',)
    target = None
    iter = None
    body = None
    orelse = None

    optional_assign = True
    def _blockstart_toline(self):
        return self.iter.tolineno


class From(FromImportMixIn, Statement):
    """class representing a From node"""

    def __init__(self,  fromname, names, level=0):
        self.modname = fromname
        self.names = names
        self.level = level

class Getattr(NodeNG):
    """class representing a Getattr node"""
    _astng_fields = ('expr',)
    expr = None


class Global(Statement):
    """class representing a Global node"""

    def __init__(self, names):
        self.names = names

    def _infer_name(self, frame, name):
        return name


class If(BlockRangeMixIn, Statement):
    """class representing an If node"""
    _astng_fields = ('test', 'body', 'orelse')
    test = None
    body = None
    orelse = None

    def _blockstart_toline(self):
        return self.test.tolineno

    def block_range(self, lineno):
        """handle block line numbers range for if statements"""
        if lineno == self.body[0].fromlineno:
            return lineno, lineno
        if lineno <= self.body[-1].tolineno:
            return lineno, self.body[-1].tolineno
        return self._elsed_block_range(lineno, self.orelse,
                                       self.body[0].fromlineno - 1)


class IfExp(NodeNG):
    """class representing an IfExp node"""
    _astng_fields = ('test', 'body', 'orelse')
    test = None
    body = None
    orelse = None


class Import(FromImportMixIn, Statement):
    """class representing an Import node"""


class Index(NodeNG):
    """class representing an Index node"""
    _astng_fields = ('value',)
    value = None


class Keyword(NodeNG):
    """class representing a Keyword node"""
    _astng_fields = ('value',)
    value = None


class List(NodeNG, Instance, ParentAssignTypeMixin):
    """class representing a List node"""
    _astng_fields = ('elts',)

    def __init__(self, elts=None):
        if elts is None:
            self.elts = []
        else:
            self.elts = [const_factory(e) for e in elts]

    def pytype(self):
        return '%s.list' % BUILTINS_MODULE

    def getitem(self, index, context=None):
        return self.elts[index]

    def itered(self):
        return self.elts


class Nonlocal(Statement):
    """class representing a Nonlocal node"""

    def __init__(self, names):
        self.names = names

    def _infer_name(self, frame, name):
        return name


class Pass(Statement):
    """class representing a Pass node"""


class Print(Statement):
    """class representing a Print node"""
    _astng_fields = ('dest', 'values',)
    dest = None
    values = None


class Raise(Statement):
    """class representing a Raise node"""
    exc = None
    if sys.version_info < (3, 0):
        _astng_fields = ('exc', 'inst', 'tback')
        inst = None
        tback = None
    else:
        _astng_fields = ('exc', 'cause')
        exc = None
        cause = None

    def raises_not_implemented(self):
        if not self.exc:
            return
        for name in self.exc.nodes_of_class(Name):
            if name.name == 'NotImplementedError':
                return True


class Return(Statement):
    """class representing a Return node"""
    _astng_fields = ('value',)
    value = None


class Set(NodeNG, Instance, ParentAssignTypeMixin):
    """class representing a Set node"""
    _astng_fields = ('elts',)

    def __init__(self, elts=None):
        if elts is None:
            self.elts = []
        else:
            self.elts = [const_factory(e) for e in elts]

    def pytype(self):
        return '%s.set' % BUILTINS_MODULE

    def itered(self):
        return self.elts


class Slice(NodeNG):
    """class representing a Slice node"""
    _astng_fields = ('lower', 'upper', 'step')
    lower = None
    upper = None
    step = None

class Starred(NodeNG, ParentAssignTypeMixin):
    """class representing a Starred node"""
    _astng_fields = ('value',)
    value = None


class Subscript(NodeNG):
    """class representing a Subscript node"""
    _astng_fields = ('value', 'slice')
    value = None
    slice = None


class TryExcept(BlockRangeMixIn, Statement):
    """class representing a TryExcept node"""
    _astng_fields = ('body', 'handlers', 'orelse',)
    body = None
    handlers = None
    orelse = None

    def _infer_name(self, frame, name):
        return name

    def _blockstart_toline(self):
        return self.lineno

    def block_range(self, lineno):
        """handle block line numbers range for try/except statements"""
        last = None
        for exhandler in self.handlers:
            if exhandler.type and lineno == exhandler.type.fromlineno:
                return lineno, lineno
            if exhandler.body[0].fromlineno <= lineno <= exhandler.body[-1].tolineno:
                return lineno, exhandler.body[-1].tolineno
            if last is None:
                last = exhandler.body[0].fromlineno - 1
        return self._elsed_block_range(lineno, self.orelse, last)


class TryFinally(BlockRangeMixIn, Statement):
    """class representing a TryFinally node"""
    _astng_fields = ('body', 'finalbody',)
    body = None
    finalbody = None

    def _blockstart_toline(self):
        return self.lineno

    def block_range(self, lineno):
        """handle block line numbers range for try/finally statements"""
        child = self.body[0]
        # py2.5 try: except: finally:
        if (isinstance(child, TryExcept) and child.fromlineno == self.fromlineno
            and lineno > self.fromlineno and lineno <= child.tolineno):
            return child.block_range(lineno)
        return self._elsed_block_range(lineno, self.finalbody)


class Tuple(NodeNG, Instance, ParentAssignTypeMixin):
    """class representing a Tuple node"""
    _astng_fields = ('elts',)

    def __init__(self, elts=None):
        if elts is None:
            self.elts = []
        else:
            self.elts = [const_factory(e) for e in elts]

    def pytype(self):
        return '%s.tuple' % BUILTINS_MODULE

    def getitem(self, index, context=None):
        return self.elts[index]

    def itered(self):
        return self.elts


class UnaryOp(NodeNG):
    """class representing an UnaryOp node"""
    _astng_fields = ('operand',)
    operand = None


class While(BlockRangeMixIn, Statement):
    """class representing a While node"""
    _astng_fields = ('test', 'body', 'orelse',)
    test = None
    body = None
    orelse = None

    def _blockstart_toline(self):
        return self.test.tolineno

    def block_range(self, lineno):
        """handle block line numbers range for for and while statements"""
        return self. _elsed_block_range(lineno, self.orelse)


class With(BlockRangeMixIn, AssignTypeMixin, Statement):
    """class representing a With node"""
    _astng_fields = ('expr', 'vars', 'body')
    expr = None
    vars = None
    body = None

    def _blockstart_toline(self):
        if self.vars:
            return self.vars.tolineno
        else:
            return self.expr.tolineno


class Yield(NodeNG):
    """class representing a Yield node"""
    _astng_fields = ('value',)
    value = None

# constants ##############################################################

CONST_CLS = {
    list: List,
    tuple: Tuple,
    dict: Dict,
    set: Set,
    type(None): Const,
    }

def _update_const_classes():
    """update constant classes, so the keys of CONST_CLS can be reused"""
    klasses = (bool, int, float, complex, str)
    if sys.version_info < (3, 0):
        klasses += (unicode, long)
    if sys.version_info >= (2, 6):
        klasses += (bytes,)
    for kls in klasses:
        CONST_CLS[kls] = Const
_update_const_classes()

def const_factory(value):
    """return an astng node for a python value"""
    # since const_factory is called to evaluate content of container (eg list,
    # tuple), it may be called with some node as argument that should be left
    # untouched
    if isinstance(value, NodeNG):
        return value
    try:
        return CONST_CLS[value.__class__](value)
    except (KeyError, AttributeError):
        # some constants (like from gtk._gtk) don't have their class in
        # CONST_CLS, though we can "assert isinstance(value, tuple(CONST_CLS))"
        if isinstance(value, tuple(CONST_CLS)):
            return Const(value)
        node = EmptyNode()
        node.object = value
        return node
