# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
# Copyright (c) 2009-2010 Arista Networks, Inc.
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
"""basic checker for Python code"""


from logilab import astng
from logilab.common.ureports import Table
from logilab.astng import are_exclusive

from pylint.interfaces import IASTNGChecker
from pylint.reporters import diff_string
from pylint.checkers import BaseChecker, EmptyReport
from pylint.checkers.utils import check_messages, clobber_in_except, is_inside_except


import re

# regex for class/function/variable/constant name
CLASS_NAME_RGX = re.compile('[A-Z_][a-zA-Z0-9]+$')
MOD_NAME_RGX = re.compile('(([a-z_][a-z0-9_]*)|([A-Z][a-zA-Z0-9]+))$')
CONST_NAME_RGX = re.compile('(([A-Z_][A-Z0-9_]*)|(__.*__))$')
COMP_VAR_RGX = re.compile('[A-Za-z_][A-Za-z0-9_]*$')
DEFAULT_NAME_RGX = re.compile('[a-z_][a-z0-9_]{2,30}$')
# do not require a doc string on system methods
NO_REQUIRED_DOC_RGX = re.compile('__.*__')

del re

def in_loop(node):
    """return True if the node is inside a kind of for loop"""
    parent = node.parent
    while parent is not None:
        if isinstance(parent, (astng.For, astng.ListComp, astng.SetComp,
                               astng.DictComp, astng.GenExpr)):
            return True
        parent = parent.parent
    return False

def in_nested_list(nested_list, obj):
    """return true if the object is an element of <nested_list> or of a nested
    list
    """
    for elmt in nested_list:
        if isinstance(elmt, (list, tuple)):
            if in_nested_list(elmt, obj):
                return True
        elif elmt == obj:
            return True
    return False

def report_by_type_stats(sect, stats, old_stats):
    """make a report of

    * percentage of different types documented
    * percentage of different types with a bad name
    """
    # percentage of different types documented and/or with a bad name
    nice_stats = {}
    for node_type in ('module', 'class', 'method', 'function'):
        try:
            total = stats[node_type]
        except KeyError:
            raise EmptyReport()
        nice_stats[node_type] = {}
        if total != 0:
            try:
                documented = total - stats['undocumented_'+node_type]
                percent = (documented * 100.) / total
                nice_stats[node_type]['percent_documented'] = '%.2f' % percent
            except KeyError:
                nice_stats[node_type]['percent_documented'] = 'NC'
            try:
                percent = (stats['badname_'+node_type] * 100.) / total
                nice_stats[node_type]['percent_badname'] = '%.2f' % percent
            except KeyError:
                nice_stats[node_type]['percent_badname'] = 'NC'
    lines = ('type', 'number', 'old number', 'difference',
             '%documented', '%badname')
    for node_type in ('module', 'class', 'method', 'function'):
        new = stats[node_type]
        old = old_stats.get(node_type, None)
        if old is not None:
            diff_str = diff_string(old, new)
        else:
            old, diff_str = 'NC', 'NC'
        lines += (node_type, str(new), str(old), diff_str,
                  nice_stats[node_type].get('percent_documented', '0'),
                  nice_stats[node_type].get('percent_badname', '0'))
    sect.append(Table(children=lines, cols=6, rheaders=1))

def redefined_by_decorator(node):
    """return True if the object is a method redefined via decorator.

    For example:
        @property
        def x(self): return self._x
        @x.setter
        def x(self, value): self._x = value
    """
    if node.decorators:
        for decorator in node.decorators.nodes:
            if (isinstance(decorator, astng.Getattr) and
                getattr(decorator.expr, 'name', None) == node.name):
                return True
    return False

class _BasicChecker(BaseChecker):
    __implements__ = IASTNGChecker
    name = 'basic'

class BasicErrorChecker(_BasicChecker):
    msgs = {
    'E0100': ('__init__ method is a generator',
              'init-is-generator',
              'Used when the special class method __init__ is turned into a '
              'generator by a yield in its body.'),
    'E0101': ('Explicit return in __init__',
              'return-in-init',
              'Used when the special class method __init__ has an explicit \
              return value.'),
    'E0102': ('%s already defined line %s',
              'function-redefined',
              'Used when a function / class / method is redefined.'),
    'E0103': ('%r not properly in loop',
              'not-in-loop',
              'Used when break or continue keywords are used outside a loop.'),

    'E0104': ('Return outside function',
              'return-outside-function',
              'Used when a "return" statement is found outside a function or '
              'method.'),
    'E0105': ('Yield outside function',
              'yield-outside-function',
              'Used when a "yield" statement is found outside a function or '
              'method.'),
    'E0106': ('Return with argument inside generator',
              'return-arg-in-generator',
              'Used when a "return" statement with an argument is found '
              'outside in a generator function or method (e.g. with some '
              '"yield" statements).'),
    'E0107': ("Use of the non-existent %s operator",
              'nonexistent-operator',
              "Used when you attempt to use the C-style pre-increment or"
              "pre-decrement operator -- and ++, which doesn't exist in Python."),
    }

    def __init__(self, linter):
        _BasicChecker.__init__(self, linter)

    @check_messages('E0102')
    def visit_class(self, node):
        self._check_redefinition('class', node)

    @check_messages('E0100', 'E0101', 'E0102', 'E0106')
    def visit_function(self, node):
        if not redefined_by_decorator(node):
            self._check_redefinition(node.is_method() and 'method' or 'function', node)
        # checks for max returns, branch, return in __init__
        returns = node.nodes_of_class(astng.Return,
                                      skip_klass=(astng.Function, astng.Class))
        if node.is_method() and node.name == '__init__':
            if node.is_generator():
                self.add_message('E0100', node=node)
            else:
                values = [r.value for r in returns]
                if  [v for v in values if not (v is None or
                    (isinstance(v, astng.Const) and v.value is None)
                    or  (isinstance(v, astng.Name) and v.name == 'None'))]:
                    self.add_message('E0101', node=node)
        elif node.is_generator():
            # make sure we don't mix non-None returns and yields
            for retnode in returns:
                if isinstance(retnode.value, astng.Const) and \
                       retnode.value.value is not None:
                    self.add_message('E0106', node=node,
                                     line=retnode.fromlineno)

    @check_messages('E0104')
    def visit_return(self, node):
        if not isinstance(node.frame(), astng.Function):
            self.add_message('E0104', node=node)

    @check_messages('E0105')
    def visit_yield(self, node):
        if not isinstance(node.frame(), astng.Function):
            self.add_message('E0105', node=node)

    @check_messages('E0103')
    def visit_continue(self, node):
        self._check_in_loop(node, 'continue')

    @check_messages('E0103')
    def visit_break(self, node):
        self._check_in_loop(node, 'break')

    @check_messages('E0107')
    def visit_unaryop(self, node):
        """check use of the non-existent ++ adn -- operator operator"""
        if ((node.op in '+-') and
            isinstance(node.operand, astng.UnaryOp) and
            (node.operand.op == node.op)):
            self.add_message('E0107', node=node, args=node.op*2)

    def _check_in_loop(self, node, node_name):
        """check that a node is inside a for or while loop"""
        _node = node.parent
        while _node:
            if isinstance(_node, (astng.For, astng.While)):
                break
            _node = _node.parent
        else:
            self.add_message('E0103', node=node, args=node_name)

    def _check_redefinition(self, redeftype, node):
        """check for redefinition of a function / method / class name"""
        defined_self = node.parent.frame()[node.name]
        if defined_self is not node and not are_exclusive(node, defined_self):
            self.add_message('E0102', node=node,
                             args=(redeftype, defined_self.fromlineno))



class BasicChecker(_BasicChecker):
    """checks for :
    * doc strings
    * modules / classes / functions / methods / arguments / variables name
    * number of arguments, local variables, branches, returns and statements in
functions, methods
    * required module attributes
    * dangerous default values as arguments
    * redefinition of function / method / class
    * uses of the global statement
    """

    __implements__ = IASTNGChecker

    name = 'basic'
    msgs = {
    'W0101': ('Unreachable code',
              'unreachable',
              'Used when there is some code behind a "return" or "raise" \
              statement, which will never be accessed.'),
    'W0102': ('Dangerous default value %s as argument',
              'dangerous-default-value',
              'Used when a mutable value as list or dictionary is detected in \
              a default value for an argument.'),
    'W0104': ('Statement seems to have no effect',
              'pointless-statement',
              'Used when a statement doesn\'t have (or at least seems to) \
              any effect.'),
    'W0105': ('String statement has no effect',
              'pointless-string-statement',
              'Used when a string is used as a statement (which of course \
              has no effect). This is a particular case of W0104 with its \
              own message so you can easily disable it if you\'re using \
              those strings as documentation, instead of comments.'),
    'W0106': ('Expression "%s" is assigned to nothing',
              'expression-not-assigned',
              'Used when an expression that is not a function call is assigned\
              to nothing. Probably something else was intended.'),
    'W0108': ('Lambda may not be necessary',
              'unnecessary-lambda',
              'Used when the body of a lambda expression is a function call \
              on the same argument list as the lambda itself; such lambda \
              expressions are in all but a few cases replaceable with the \
              function being called in the body of the lambda.'),
    'W0109': ("Duplicate key %r in dictionary",
              'duplicate-key',
              "Used when a dictionary expression binds the same key multiple \
              times."),
    'W0122': ('Use of the exec statement',
              'exec-statement',
              'Used when you use the "exec" statement, to discourage its \
              usage. That doesn\'t mean you can not use it !'),

    'W0141': ('Used builtin function %r',
              'bad-builtin',
              'Used when a black listed builtin function is used (see the '
              'bad-function option). Usual black listed functions are the ones '
              'like map, or filter , where Python offers now some cleaner '
              'alternative like list comprehension.'),
    'W0142': ('Used * or ** magic',
              'star-args',
              'Used when a function or method is called using `*args` or '
              '`**kwargs` to dispatch arguments. This doesn\'t improve '
              'readability and should be used with care.'),
    'W0150': ("%s statement in finally block may swallow exception",
              'lost-exception',
              "Used when a break or a return statement is found inside the \
              finally clause of a try...finally block: the exceptions raised \
              in the try clause will be silently swallowed instead of being \
              re-raised."),
    'W0199': ('Assert called on a 2-uple. Did you mean \'assert x,y\'?',
              'assert-on-tuple',
              'A call of assert on a tuple will always evaluate to true if '
              'the tuple is not empty, and will always evaluate to false if '
              'it is.'),

    'C0121': ('Missing required attribute "%s"', # W0103
              'missing-module-attribute',
              'Used when an attribute required for modules is missing.'),

    }

    options = (('required-attributes',
                {'default' : (), 'type' : 'csv',
                 'metavar' : '<attributes>',
                 'help' : 'Required attributes for module, separated by a '
                          'comma'}
                ),
               ('bad-functions',
                {'default' : ('map', 'filter', 'apply', 'input'),
                 'type' :'csv', 'metavar' : '<builtin function names>',
                 'help' : 'List of builtins function names that should not be '
                          'used, separated by a comma'}
                ),
               )
    reports = ( ('RP0101', 'Statistics by type', report_by_type_stats), )

    def __init__(self, linter):
        _BasicChecker.__init__(self, linter)
        self.stats = None
        self._tryfinallys = None

    def open(self):
        """initialize visit variables and statistics
        """
        self._tryfinallys = []
        self.stats = self.linter.add_stats(module=0, function=0,
                                           method=0, class_=0)

    def visit_module(self, node):
        """check module name, docstring and required arguments
        """
        self.stats['module'] += 1
        for attr in self.config.required_attributes:
            if attr not in node:
                self.add_message('C0121', node=node, args=attr)

    def visit_class(self, node):
        """check module name, docstring and redefinition
        increment branch counter
        """
        self.stats['class'] += 1

    @check_messages('W0104', 'W0105')
    def visit_discard(self, node):
        """check for various kind of statements without effect"""
        expr = node.value
        if isinstance(expr, astng.Const) and isinstance(expr.value,
                                                        basestring):
            # treat string statement in a separated message
            self.add_message('W0105', node=node)
            return
        # ignore if this is :
        # * a direct function call
        # * the unique child of a try/except body
        # * a yield (which are wrapped by a discard node in _ast XXX)
        # warn W0106 if we have any underlying function call (we can't predict
        # side effects), else W0104
        if (isinstance(expr, (astng.Yield, astng.CallFunc)) or
            (isinstance(node.parent, astng.TryExcept) and
             node.parent.body == [node])):
            return
        if any(expr.nodes_of_class(astng.CallFunc)):
            self.add_message('W0106', node=node, args=expr.as_string())
        else:
            self.add_message('W0104', node=node)

    @check_messages('W0108')
    def visit_lambda(self, node):
        """check whether or not the lambda is suspicious
        """
        # if the body of the lambda is a call expression with the same
        # argument list as the lambda itself, then the lambda is
        # possibly unnecessary and at least suspicious.
        if node.args.defaults:
            # If the arguments of the lambda include defaults, then a
            # judgment cannot be made because there is no way to check
            # that the defaults defined by the lambda are the same as
            # the defaults defined by the function called in the body
            # of the lambda.
            return
        call = node.body
        if not isinstance(call, astng.CallFunc):
            # The body of the lambda must be a function call expression
            # for the lambda to be unnecessary.
            return
        # XXX are lambda still different with astng >= 0.18 ?
        # *args and **kwargs need to be treated specially, since they
        # are structured differently between the lambda and the function
        # call (in the lambda they appear in the args.args list and are
        # indicated as * and ** by two bits in the lambda's flags, but
        # in the function call they are omitted from the args list and
        # are indicated by separate attributes on the function call node).
        ordinary_args = list(node.args.args)
        if node.args.kwarg:
            if (not call.kwargs
                or not isinstance(call.kwargs, astng.Name)
                or node.args.kwarg != call.kwargs.name):
                return
        elif call.kwargs:
            return
        if node.args.vararg:
            if (not call.starargs
                or not isinstance(call.starargs, astng.Name)
                or node.args.vararg != call.starargs.name):
                return
        elif call.starargs:
            return
        # The "ordinary" arguments must be in a correspondence such that:
        # ordinary_args[i].name == call.args[i].name.
        if len(ordinary_args) != len(call.args):
            return
        for i in xrange(len(ordinary_args)):
            if not isinstance(call.args[i], astng.Name):
                return
            if node.args.args[i].name != call.args[i].name:
                return
        self.add_message('W0108', line=node.fromlineno, node=node)

    def visit_function(self, node):
        """check function name, docstring, arguments, redefinition,
        variable names, max locals
        """
        self.stats[node.is_method() and 'method' or 'function'] += 1
        # check for dangerous default values as arguments
        for default in node.args.defaults:
            try:
                value = default.infer().next()
            except astng.InferenceError:
                continue
            if isinstance(value, (astng.Dict, astng.List)):
                if value is default:
                    msg = default.as_string()
                else:
                    msg = '%s (%s)' % (default.as_string(), value.as_string())
                self.add_message('W0102', node=node, args=(msg,))
            if value.qname() == '__builtin__.set':
                if isinstance(default, astng.CallFunc):
                    msg = default.as_string()
                else:
                    msg = '%s (%s)' % (default.as_string(), value.qname())
                self.add_message('W0102', node=node, args=(msg,))

    @check_messages('W0101', 'W0150')
    def visit_return(self, node):
        """1 - check is the node has a right sibling (if so, that's some
        unreachable code)
        2 - check is the node is inside the finally clause of a try...finally
        block
        """
        self._check_unreachable(node)
        # Is it inside final body of a try...finally bloc ?
        self._check_not_in_finally(node, 'return', (astng.Function,))

    @check_messages('W0101')
    def visit_continue(self, node):
        """check is the node has a right sibling (if so, that's some unreachable
        code)
        """
        self._check_unreachable(node)

    @check_messages('W0101', 'W0150')
    def visit_break(self, node):
        """1 - check is the node has a right sibling (if so, that's some
        unreachable code)
        2 - check is the node is inside the finally clause of a try...finally
        block
        """
        # 1 - Is it right sibling ?
        self._check_unreachable(node)
        # 2 - Is it inside final body of a try...finally bloc ?
        self._check_not_in_finally(node, 'break', (astng.For, astng.While,))

    @check_messages('W0101')
    def visit_raise(self, node):
        """check is the node has a right sibling (if so, that's some unreachable
        code)
        """
        self._check_unreachable(node)

    @check_messages('W0122')
    def visit_exec(self, node):
        """just print a warning on exec statements"""
        self.add_message('W0122', node=node)

    @check_messages('W0141', 'W0142')
    def visit_callfunc(self, node):
        """visit a CallFunc node -> check if this is not a blacklisted builtin
        call and check for * or ** use
        """
        if isinstance(node.func, astng.Name):
            name = node.func.name
            # ignore the name if it's not a builtin (i.e. not defined in the
            # locals nor globals scope)
            if not (name in node.frame() or
                    name in node.root()):
                if name in self.config.bad_functions:
                    self.add_message('W0141', node=node, args=name)
        if node.starargs or node.kwargs:
            scope = node.scope()
            if isinstance(scope, astng.Function):
                toprocess = [(n, vn) for (n, vn) in ((node.starargs, scope.args.vararg),
                                                     (node.kwargs, scope.args.kwarg)) if n]
                if toprocess:
                    for cfnode, fargname in toprocess[:]:
                        if getattr(cfnode, 'name', None) == fargname:
                            toprocess.remove((cfnode, fargname))
                    if not toprocess:
                        return # W0142 can be skipped
            self.add_message('W0142', node=node.func)

    @check_messages('W0199')
    def visit_assert(self, node):
        """check the use of an assert statement on a tuple."""
        if node.fail is None and isinstance(node.test, astng.Tuple) and \
           len(node.test.elts) == 2:
            self.add_message('W0199', line=node.fromlineno, node=node)

    @check_messages('W0109')
    def visit_dict(self, node):
        """check duplicate key in dictionary"""
        keys = set()
        for k, _ in node.items:
            if isinstance(k, astng.Const):
                key = k.value
                if key in keys:
                    self.add_message('W0109', node=node, args=key)
                keys.add(key)

    def visit_tryfinally(self, node):
        """update try...finally flag"""
        self._tryfinallys.append(node)

    def leave_tryfinally(self, node):
        """update try...finally flag"""
        self._tryfinallys.pop()

    def _check_unreachable(self, node):
        """check unreachable code"""
        unreach_stmt = node.next_sibling()
        if unreach_stmt is not None:
            self.add_message('W0101', node=unreach_stmt)

    def _check_not_in_finally(self, node, node_name, breaker_classes=()):
        """check that a node is not inside a finally clause of a
        try...finally statement.
        If we found before a try...finally bloc a parent which its type is
        in breaker_classes, we skip the whole check."""
        # if self._tryfinallys is empty, we're not a in try...finally bloc
        if not self._tryfinallys:
            return
        # the node could be a grand-grand...-children of the try...finally
        _parent = node.parent
        _node = node
        while _parent and not isinstance(_parent, breaker_classes):
            if hasattr(_parent, 'finalbody') and _node in _parent.finalbody:
                self.add_message('W0150', node=node, args=node_name)
                return
            _node = _parent
            _parent = _node.parent



class NameChecker(_BasicChecker):
    msgs = {
    'C0102': ('Black listed name "%s"',
              'blacklisted-name',
              'Used when the name is listed in the black list (unauthorized \
              names).'),
    'C0103': ('Invalid name "%s" for type %s (should match %s)',
              'invalid-name',
              'Used when the name doesn\'t match the regular expression \
              associated to its type (constant, variable, class...).'),

    }
    options = (('module-rgx',
                {'default' : MOD_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'module names'}
                ),
               ('const-rgx',
                {'default' : CONST_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'module level names'}
                ),
               ('class-rgx',
                {'default' : CLASS_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'class names'}
                ),
               ('function-rgx',
                {'default' : DEFAULT_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'function names'}
                ),
               ('method-rgx',
                {'default' : DEFAULT_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'method names'}
                ),
               ('attr-rgx',
                {'default' : DEFAULT_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'instance attribute names'}
                ),
               ('argument-rgx',
                {'default' : DEFAULT_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'argument names'}),
               ('variable-rgx',
                {'default' : DEFAULT_NAME_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'variable names'}
                ),
               ('inlinevar-rgx',
                {'default' : COMP_VAR_RGX,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match correct '
                          'list comprehension / generator expression variable \
                          names'}
                ),
               # XXX use set
               ('good-names',
                {'default' : ('i', 'j', 'k', 'ex', 'Run', '_'),
                 'type' :'csv', 'metavar' : '<names>',
                 'help' : 'Good variable names which should always be accepted,'
                          ' separated by a comma'}
                ),
               ('bad-names',
                {'default' : ('foo', 'bar', 'baz', 'toto', 'tutu', 'tata'),
                 'type' :'csv', 'metavar' : '<names>',
                 'help' : 'Bad variable names which should always be refused, '
                          'separated by a comma'}
                ),
               )

    def open(self):
        self.stats = self.linter.add_stats(badname_module=0,
                                           badname_class=0, badname_function=0,
                                           badname_method=0, badname_attr=0,
                                           badname_const=0,
                                           badname_variable=0,
                                           badname_inlinevar=0,
                                           badname_argument=0)

    @check_messages('C0102', 'C0103')
    def visit_module(self, node):
        self._check_name('module', node.name.split('.')[-1], node)

    @check_messages('C0102', 'C0103')
    def visit_class(self, node):
        self._check_name('class', node.name, node)
        for attr, anodes in node.instance_attrs.iteritems():
            self._check_name('attr', attr, anodes[0])

    @check_messages('C0102', 'C0103')
    def visit_function(self, node):
        self._check_name(node.is_method() and 'method' or 'function',
                         node.name, node)
        # check arguments name
        args = node.args.args
        if args is not None:
            self._recursive_check_names(args, node)

    @check_messages('C0102', 'C0103')
    def visit_assname(self, node):
        """check module level assigned names"""
        frame = node.frame()
        ass_type = node.ass_type()
        if isinstance(ass_type, (astng.Comprehension, astng.Comprehension)):
            self._check_name('inlinevar', node.name, node)
        elif isinstance(frame, astng.Module):
            if isinstance(ass_type, astng.Assign) and not in_loop(ass_type):
                self._check_name('const', node.name, node)
            elif isinstance(ass_type, astng.ExceptHandler):
                self._check_name('variable', node.name, node)
        elif isinstance(frame, astng.Function):
            # global introduced variable aren't in the function locals
            if node.name in frame:
                self._check_name('variable', node.name, node)

    def _recursive_check_names(self, args, node):
        """check names in a possibly recursive list <arg>"""
        for arg in args:
            if isinstance(arg, astng.AssName):
                self._check_name('argument', arg.name, node)
            else:
                self._recursive_check_names(arg.elts, node)

    def _check_name(self, node_type, name, node):
        """check for a name using the type's regexp"""
        if is_inside_except(node):
            clobbering, _ = clobber_in_except(node)
            if clobbering:
                return
        if name in self.config.good_names:
            return
        if name in self.config.bad_names:
            self.stats['badname_' + node_type] += 1
            self.add_message('C0102', node=node, args=name)
            return
        regexp = getattr(self.config, node_type + '_rgx')
        if regexp.match(name) is None:
            type_label = {'inlinedvar': 'inlined variable',
                          'const': 'constant',
                          'attr': 'attribute',
                          }.get(node_type, node_type)
            self.add_message('C0103', node=node, args=(name, type_label, regexp.pattern))
            self.stats['badname_' + node_type] += 1


class DocStringChecker(_BasicChecker):
    msgs = {
    'C0111': ('Missing docstring', # W0131
              'missing-docstring',
              'Used when a module, function, class or method has no docstring.\
              Some special methods like __init__ doesn\'t necessary require a \
              docstring.'),
    'C0112': ('Empty docstring', # W0132
              'empty-docstring',
              'Used when a module, function, class or method has an empty \
              docstring (it would be too easy ;).'),
    }
    options = (('no-docstring-rgx',
                {'default' : NO_REQUIRED_DOC_RGX,
                 'type' : 'regexp', 'metavar' : '<regexp>',
                 'help' : 'Regular expression which should only match '
                          'functions or classes name which do not require a '
                          'docstring'}
                ),
               )

    def open(self):
        self.stats = self.linter.add_stats(undocumented_module=0,
                                           undocumented_function=0,
                                           undocumented_method=0,
                                           undocumented_class=0)

    def visit_module(self, node):
        self._check_docstring('module', node)

    def visit_class(self, node):
        if self.config.no_docstring_rgx.match(node.name) is None:
            self._check_docstring('class', node)

    def visit_function(self, node):
        if self.config.no_docstring_rgx.match(node.name) is None:
            ftype = node.is_method() and 'method' or 'function'
            if isinstance(node.parent.frame(), astng.Class):
                overridden = False
                # check if node is from a method overridden by its ancestor
                for ancestor in node.parent.frame().ancestors():
                    if node.name in ancestor and \
                       isinstance(ancestor[node.name], astng.Function):
                        overridden = True
                        break
                if not overridden:
                    self._check_docstring(ftype, node)
            else:
                self._check_docstring(ftype, node)

    def _check_docstring(self, node_type, node):
        """check the node has a non empty docstring"""
        docstring = node.doc
        if docstring is None:
            self.stats['undocumented_'+node_type] += 1
            self.add_message('C0111', node=node)
        elif not docstring.strip():
            self.stats['undocumented_'+node_type] += 1
            self.add_message('C0112', node=node)


class PassChecker(_BasicChecker):
    """check is the pass statement is really necessary"""
    msgs = {'W0107': ('Unnecessary pass statement',
                      'unnecessary-pass',
                      'Used when a "pass" statement that can be avoided is '
                      'encountered.)'),
            }

    def visit_pass(self, node):
        if len(node.parent.child_sequence(node)) > 1:
            self.add_message('W0107', node=node)


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(BasicErrorChecker(linter))
    linter.register_checker(BasicChecker(linter))
    linter.register_checker(NameChecker(linter))
    linter.register_checker(DocStringChecker(linter))
    linter.register_checker(PassChecker(linter))
