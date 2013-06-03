# Copyright (c) 2003-2007 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""exceptions handling (raising, catching, exceptions classes) checker
"""
import sys

from logilab.common.compat import builtins
BUILTINS_NAME = builtins.__name__
from logilab import astng
from logilab.astng import YES, Instance, unpack_infer

from pylint.checkers import BaseChecker
from pylint.checkers.utils import is_empty, is_raising
from pylint.interfaces import IASTNGChecker


OVERGENERAL_EXCEPTIONS = ('Exception',)

MSGS = {
    'E0701': ('Bad except clauses order (%s)',
              'bad-except-order',
              'Used when except clauses are not in the correct order (from the '
              'more specific to the more generic). If you don\'t fix the order, '
              'some exceptions may not be catched by the most specific handler.'),
    'E0702': ('Raising %s while only classes, instances or string are allowed',
              'raising-bad-type',
              'Used when something which is neither a class, an instance or a \
              string is raised (i.e. a `TypeError` will be raised).'),
    'E0710': ('Raising a new style class which doesn\'t inherit from BaseException',
              'raising-non-exception',
              'Used when a new style class which doesn\'t inherit from \
               BaseException is raised.'),
    'E0711': ('NotImplemented raised - should raise NotImplementedError',
              'notimplemented-raised',
              'Used when NotImplemented is raised instead of \
              NotImplementedError'),
    
    'W0701': ('Raising a string exception',
              'raising-string',
              'Used when a string exception is raised.'),
    'W0702': ('No exception type(s) specified',
              'bare-except',
              'Used when an except clause doesn\'t specify exceptions type to \
              catch.'),
    'W0703': ('Catching too general exception %s',
              'broad-except',
              'Used when an except catches a too general exception, \
              possibly burying unrelated errors.'),
    'W0704': ('Except doesn\'t do anything',
              'pointless-except',
              'Used when an except clause does nothing but "pass" and there is\
              no "else" clause.'),
    'W0710': ('Exception doesn\'t inherit from standard "Exception" class',
              'nonstandard-exception',
              'Used when a custom exception class is raised but doesn\'t \
              inherit from the builtin "Exception" class.'),
    'W0711': ('Exception to catch is the result of a binary "%s" operation',
              'binary-op-exception',
              'Used when the exception to catch is of the form \
              "except A or B:".  If intending to catch multiple, \
              rewrite as "except (A, B):"'),
    }


if sys.version_info < (3, 0):
    EXCEPTIONS_MODULE = "exceptions"
else:
    EXCEPTIONS_MODULE = "builtins"

class ExceptionsChecker(BaseChecker):
    """checks for                                                              
    * excepts without exception filter                                         
    * type of raise argument : string, Exceptions, other values
    """
    
    __implements__ = IASTNGChecker

    name = 'exceptions'
    msgs = MSGS
    priority = -4
    options = (('overgeneral-exceptions',
                {'default' : OVERGENERAL_EXCEPTIONS,
                 'type' :'csv', 'metavar' : '<comma-separated class names>',
                 'help' : 'Exceptions that will emit a warning '
                          'when being caught. Defaults to "%s"' % (
                              ', '.join(OVERGENERAL_EXCEPTIONS),)}
                ),
               )

    def visit_raise(self, node):
        """visit raise possibly inferring value"""
        # ignore empty raise
        if node.exc is None:
            return
        expr = node.exc
        if self._check_raise_value(node, expr):
            return
        else:
            try:
                value = unpack_infer(expr).next()
            except astng.InferenceError:
                return
            self._check_raise_value(node, value)

    def _check_raise_value(self, node, expr):
        """check for bad values, string exception and class inheritance
        """
        value_found = True
        if isinstance(expr, astng.Const):
            value = expr.value
            if isinstance(value, str):
                self.add_message('W0701', node=node)
            else:
                self.add_message('E0702', node=node,
                                 args=value.__class__.__name__)
        elif (isinstance(expr, astng.Name) and \
                 expr.name in ('None', 'True', 'False')) or \
                 isinstance(expr, (astng.List, astng.Dict, astng.Tuple, 
                                   astng.Module, astng.Function)):
            self.add_message('E0702', node=node, args=expr.name)
        elif ( (isinstance(expr, astng.Name) and expr.name == 'NotImplemented')
               or (isinstance(expr, astng.CallFunc) and
                   isinstance(expr.func, astng.Name) and
                   expr.func.name == 'NotImplemented') ):
            self.add_message('E0711', node=node)
        elif isinstance(expr, astng.BinOp) and expr.op == '%':
            self.add_message('W0701', node=node)
        elif isinstance(expr, (Instance, astng.Class)):
            if isinstance(expr, Instance):
                expr = expr._proxied
            if (isinstance(expr, astng.Class) and
                    not inherit_from_std_ex(expr) and
                    expr.root().name != BUILTINS_NAME):
                if expr.newstyle:
                    self.add_message('E0710', node=node)
                else:
                    self.add_message('W0710', node=node)
            else:
                value_found = False
        else:
            value_found = False
        return value_found


    def visit_tryexcept(self, node):
        """check for empty except"""
        exceptions_classes = []
        nb_handlers = len(node.handlers)
        for index, handler  in enumerate(node.handlers):
            # single except doing nothing but "pass" without else clause
            if nb_handlers == 1 and is_empty(handler.body) and not node.orelse:
                self.add_message('W0704', node=handler.type or handler.body[0])
            if handler.type is None:
                if nb_handlers == 1 and not is_raising(handler.body):
                    self.add_message('W0702', node=handler)
                # check if a "except:" is followed by some other
                # except
                elif index < (nb_handlers - 1):
                    msg = 'empty except clause should always appear last'
                    self.add_message('E0701', node=node, args=msg)

            elif isinstance(handler.type, astng.BoolOp):
                self.add_message('W0711', node=handler, args=handler.type.op)
            else:
                try:
                    excs = list(unpack_infer(handler.type))
                except astng.InferenceError:
                    continue
                for exc in excs:
                    # XXX skip other non class nodes 
                    if exc is YES or not isinstance(exc, astng.Class):
                        continue
                    exc_ancestors = [anc for anc in exc.ancestors()
                                     if isinstance(anc, astng.Class)]
                    for previous_exc in exceptions_classes:
                        if previous_exc in exc_ancestors:
                            msg = '%s is an ancestor class of %s' % (
                                previous_exc.name, exc.name)
                            self.add_message('E0701', node=handler.type, args=msg)
                    if (exc.name in self.config.overgeneral_exceptions
                        and exc.root().name == EXCEPTIONS_MODULE
                        and nb_handlers == 1 and not is_raising(handler.body)):
                        self.add_message('W0703', args=exc.name, node=handler.type)
                exceptions_classes += excs


def inherit_from_std_ex(node):
    """return true if the given class node is subclass of
    exceptions.Exception
    """
    if node.name in ('Exception', 'BaseException') \
            and node.root().name == EXCEPTIONS_MODULE:
        return True
    for parent in node.ancestors(recurs=False):
        if inherit_from_std_ex(parent):
            return True
    return False

def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(ExceptionsChecker(linter))
