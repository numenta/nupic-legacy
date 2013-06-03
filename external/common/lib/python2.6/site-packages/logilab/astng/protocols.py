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
"""this module contains a set of functions to handle python protocols for nodes
where it makes sense.
"""

__doctype__ = "restructuredtext en"

from logilab.astng.exceptions import InferenceError, NoDefault
from logilab.astng.node_classes import unpack_infer
from logilab.astng.bases import copy_context, \
     raise_if_nothing_infered, yes_if_nothing_infered, Instance, Generator, YES
from logilab.astng.nodes import const_factory
from logilab.astng import nodes

# unary operations ############################################################

def tl_infer_unary_op(self, operator):
    if operator == 'not':
        return const_factory(not bool(self.elts))
    raise TypeError() # XXX log unsupported operation
nodes.Tuple.infer_unary_op = tl_infer_unary_op
nodes.List.infer_unary_op = tl_infer_unary_op


def dict_infer_unary_op(self, operator):
    if operator == 'not':
        return const_factory(not bool(self.items))
    raise TypeError() # XXX log unsupported operation
nodes.Dict.infer_unary_op = dict_infer_unary_op


def const_infer_unary_op(self, operator):
    if operator == 'not':
        return const_factory(not self.value)
    # XXX log potentially raised TypeError
    elif operator == '+':
        return const_factory(+self.value)
    else: # operator == '-':
        return const_factory(-self.value)
nodes.Const.infer_unary_op = const_infer_unary_op


# binary operations ###########################################################

BIN_OP_IMPL = {'+':  lambda a, b: a + b,
               '-':  lambda a, b: a - b,
               '/':  lambda a, b: a / b,
               '//': lambda a, b: a // b,
               '*':  lambda a, b: a * b,
               '**': lambda a, b: a ** b,
               '%':  lambda a, b: a % b,
               '&':  lambda a, b: a & b,
               '|':  lambda a, b: a | b,
               '^':  lambda a, b: a ^ b,
               '<<': lambda a, b: a << b,
               '>>': lambda a, b: a >> b,
               }
for key, impl in BIN_OP_IMPL.items():
    BIN_OP_IMPL[key+'='] = impl

def const_infer_binary_op(self, operator, other, context):
    for other in other.infer(context):
        if isinstance(other, nodes.Const):
            try:
                impl = BIN_OP_IMPL[operator]

                try:
                    yield const_factory(impl(self.value, other.value))
                except Exception:
                    # ArithmeticError is not enough: float >> float is a TypeError
                    # TODO : let pylint know about the problem
                    pass
            except TypeError:
                # XXX log TypeError
                continue
        elif other is YES:
            yield other
        else:
            try:
                for val in other.infer_binary_op(operator, self, context):
                    yield val
            except AttributeError:
                yield YES
nodes.Const.infer_binary_op = yes_if_nothing_infered(const_infer_binary_op)


def tl_infer_binary_op(self, operator, other, context):
    for other in other.infer(context):
        if isinstance(other, self.__class__) and operator == '+':
            node = self.__class__()
            elts = [n for elt in self.elts for n in elt.infer(context)
                    if not n is YES]
            elts += [n for elt in other.elts for n in elt.infer(context)
                     if not n is YES]
            node.elts = elts
            yield node
        elif isinstance(other, nodes.Const) and operator == '*':
            if not isinstance(other.value, int):
                yield YES
                continue
            node = self.__class__()
            elts = [n for elt in self.elts for n in elt.infer(context)
                    if not n is YES] * other.value
            node.elts = elts
            yield node
        elif isinstance(other, Instance) and not isinstance(other, nodes.Const):
            yield YES
    # XXX else log TypeError
nodes.Tuple.infer_binary_op = yes_if_nothing_infered(tl_infer_binary_op)
nodes.List.infer_binary_op = yes_if_nothing_infered(tl_infer_binary_op)


def dict_infer_binary_op(self, operator, other, context):
    for other in other.infer(context):
        if isinstance(other, Instance) and isinstance(other._proxied, nodes.Class):
            yield YES
        # XXX else log TypeError
nodes.Dict.infer_binary_op = yes_if_nothing_infered(dict_infer_binary_op)


# assignment ##################################################################

"""the assigned_stmts method is responsible to return the assigned statement
(e.g. not inferred) according to the assignment type.

The `asspath` argument is used to record the lhs path of the original node.
For instance if we want assigned statements for 'c' in 'a, (b,c)', asspath
will be [1, 1] once arrived to the Assign node.

The `context` argument is the current inference context which should be given
to any intermediary inference necessary.
"""

def _resolve_looppart(parts, asspath, context):
    """recursive function to resolve multiple assignments on loops"""
    asspath = asspath[:]
    index = asspath.pop(0)
    for part in parts:
        if part is YES:
            continue
        # XXX handle __iter__ and log potentially detected errors
        if not hasattr(part, 'itered'):
            continue
        try:
            itered = part.itered()
        except TypeError:
            continue # XXX log error
        for stmt in itered:
            try:
                assigned = stmt.getitem(index, context)
            except (AttributeError, IndexError):
                continue
            except TypeError, exc: # stmt is unsubscriptable Const
                continue
            if not asspath:
                # we achieved to resolved the assignment path,
                # don't infer the last part
                yield assigned
            elif assigned is YES:
                break
            else:
                # we are not yet on the last part of the path
                # search on each possibly inferred value
                try:
                    for infered in _resolve_looppart(assigned.infer(context),
                                                     asspath, context):
                        yield infered
                except InferenceError:
                    break


def for_assigned_stmts(self, node, context=None, asspath=None):
    if asspath is None:
        for lst in self.iter.infer(context):
            if isinstance(lst, (nodes.Tuple, nodes.List)):
                for item in lst.elts:
                    yield item
    else:
        for infered in _resolve_looppart(self.iter.infer(context),
                                         asspath, context):
            yield infered

nodes.For.assigned_stmts = raise_if_nothing_infered(for_assigned_stmts)
nodes.Comprehension.assigned_stmts = raise_if_nothing_infered(for_assigned_stmts)


def mulass_assigned_stmts(self, node, context=None, asspath=None):
    if asspath is None:
        asspath = []
    asspath.insert(0, self.elts.index(node))
    return self.parent.assigned_stmts(self, context, asspath)
nodes.Tuple.assigned_stmts = mulass_assigned_stmts
nodes.List.assigned_stmts = mulass_assigned_stmts


def assend_assigned_stmts(self, context=None):
    return self.parent.assigned_stmts(self, context=context)
nodes.AssName.assigned_stmts = assend_assigned_stmts
nodes.AssAttr.assigned_stmts = assend_assigned_stmts


def _arguments_infer_argname(self, name, context):
    # arguments information may be missing, in which case we can't do anything
    # more
    if not (self.args or self.vararg or self.kwarg):
        yield YES
        return
    # first argument of instance/class method
    if self.args and getattr(self.args[0], 'name', None) == name:
        functype = self.parent.type
        if functype == 'method':
            yield Instance(self.parent.parent.frame())
            return
        if functype == 'classmethod':
            yield self.parent.parent.frame()
            return
    if name == self.vararg:
        yield const_factory(())
        return
    if name == self.kwarg:
        yield const_factory({})
        return
    # if there is a default value, yield it. And then yield YES to reflect
    # we can't guess given argument value
    try:
        context = copy_context(context)
        for infered in self.default_value(name).infer(context):
            yield infered
        yield YES
    except NoDefault:
        yield YES


def arguments_assigned_stmts(self, node, context, asspath=None):
    if context.callcontext:
        # reset call context/name
        callcontext = context.callcontext
        context = copy_context(context)
        context.callcontext = None
        for infered in callcontext.infer_argument(self.parent, node.name, context):
            yield infered
        return
    for infered in _arguments_infer_argname(self, node.name, context):
        yield infered
nodes.Arguments.assigned_stmts = arguments_assigned_stmts


def assign_assigned_stmts(self, node, context=None, asspath=None):
    if not asspath:
        yield self.value
        return
    for infered in _resolve_asspart(self.value.infer(context), asspath, context):
        yield infered
nodes.Assign.assigned_stmts = raise_if_nothing_infered(assign_assigned_stmts)
nodes.AugAssign.assigned_stmts = raise_if_nothing_infered(assign_assigned_stmts)


def _resolve_asspart(parts, asspath, context):
    """recursive function to resolve multiple assignments"""
    asspath = asspath[:]
    index = asspath.pop(0)
    for part in parts:
        if hasattr(part, 'getitem'):
            try:
                assigned = part.getitem(index, context)
            # XXX raise a specific exception to avoid potential hiding of
            # unexpected exception ?
            except (TypeError, IndexError):
                return
            if not asspath:
                # we achieved to resolved the assignment path, don't infer the
                # last part
                yield assigned
            elif assigned is YES:
                return
            else:
                # we are not yet on the last part of the path search on each
                # possibly inferred value
                try:
                    for infered in _resolve_asspart(assigned.infer(context),
                                                    asspath, context):
                        yield infered
                except InferenceError:
                    return


def excepthandler_assigned_stmts(self, node, context=None, asspath=None):
    for assigned in unpack_infer(self.type):
        if isinstance(assigned, nodes.Class):
            assigned = Instance(assigned)
        yield assigned
nodes.ExceptHandler.assigned_stmts = raise_if_nothing_infered(excepthandler_assigned_stmts)


def with_assigned_stmts(self, node, context=None, asspath=None):
    if asspath is None:
        for lst in self.vars.infer(context):
            if isinstance(lst, (nodes.Tuple, nodes.List)):
                for item in lst.nodes:
                    yield item
nodes.With.assigned_stmts = raise_if_nothing_infered(with_assigned_stmts)


