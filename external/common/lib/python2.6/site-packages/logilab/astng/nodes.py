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
"""
on all nodes :
 .is_statement, returning true if the node should be considered as a
  statement node
 .root(), returning the root node of the tree (i.e. a Module)
 .previous_sibling(), returning previous sibling statement node
 .next_sibling(), returning next sibling statement node
 .statement(), returning the first parent node marked as statement node
 .frame(), returning the first node defining a new local scope (i.e.
  Module, Function or Class)
 .set_local(name, node), define an identifier <name> on the first parent frame,
  with the node defining it. This is used by the astng builder and should not
  be used from out there.

on From and Import :
 .real_name(name),


"""

__docformat__ = "restructuredtext en"

from logilab.astng.node_classes import Arguments, AssAttr, Assert, Assign, \
    AssName, AugAssign, Backquote, BinOp, BoolOp, Break, CallFunc, Compare, \
    Comprehension, Const, Continue, Decorators, DelAttr, DelName, Delete, \
    Dict, Discard, Ellipsis, EmptyNode, ExceptHandler, Exec, ExtSlice, For, \
    From, Getattr, Global, If, IfExp, Import, Index, Keyword, \
    List, Name, Nonlocal, Pass, Print, Raise, Return, Set, Slice, Starred, Subscript, \
    TryExcept, TryFinally, Tuple, UnaryOp, While, With, Yield, \
    const_factory
from logilab.astng.scoped_nodes import Module, GenExpr, Lambda, DictComp, \
    ListComp, SetComp, Function, Class

ALL_NODE_CLASSES = (
    Arguments, AssAttr, Assert, Assign, AssName, AugAssign,
    Backquote, BinOp, BoolOp, Break,
    CallFunc, Class, Compare, Comprehension, Const, Continue,
    Decorators, DelAttr, DelName, Delete,
    Dict, DictComp, Discard,
    Ellipsis, EmptyNode, ExceptHandler, Exec, ExtSlice,
    For, From, Function,
    Getattr, GenExpr, Global,
    If, IfExp, Import, Index,
    Keyword,
    Lambda, List, ListComp,
    Name, Nonlocal,
    Module,
    Pass, Print,
    Raise, Return,
    Set, SetComp, Slice, Starred, Subscript,
    TryExcept, TryFinally, Tuple,
    UnaryOp,
    While, With,
    Yield,
    )

