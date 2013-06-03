# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
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
"""check for signs of poor design


 see http://intranet.logilab.fr/jpl/view?rql=Any%20X%20where%20X%20eid%201243
 FIXME: missing 13, 15, 16
"""

from logilab.astng import Function, If, InferenceError

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker

import re

# regexp for ignored argument name
IGNORED_ARGUMENT_NAMES = re.compile('_.*')

SPECIAL_METHODS = [('Context manager', set(('__enter__',
                                            '__exit__',))),
                   ('Container', set(('__len__',
                                      '__getitem__',
                                      '__setitem__',
                                      '__delitem__',))),
                   ('Callable', set(('__call__',))),
                   ]

class SpecialMethodChecker(object):
    """A functor that checks for consistency of a set of special methods"""
    def __init__(self, methods_found, on_error):
        """Stores the set of __x__ method names that were found in the
        class and a callable that will be called with args to R0024 if
        the check fails
        """
        self.methods_found = methods_found
        self.on_error = on_error

    def __call__(self, methods_required, protocol):
        """Checks the set of method names given to __init__ against the set
        required.

        If they are all present, returns true.
        If they are all absent, returns false.
        If some are present, reports the error and returns false.
        """
        required_methods_found = methods_required & self.methods_found
        if required_methods_found == methods_required:
            return True
        if required_methods_found != set():
            required_methods_missing  = methods_required - self.methods_found
            self.on_error((protocol,
                           ', '.join(sorted(required_methods_found)),
                           ', '.join(sorted(required_methods_missing))))
        return False


def class_is_abstract(klass):
    """return true if the given class node should be considered as an abstract
    class
    """
    for attr in klass.values():
        if isinstance(attr, Function):
            if attr.is_abstract(pass_is_abstract=False):
                return True
    return False


MSGS = {
    'R0901': ('Too many ancestors (%s/%s)',
              'too-many-ancestors',
              'Used when class has too many parent classes, try to reduce \
              this to get a more simple (and so easier to use) class.'),
    'R0902': ('Too many instance attributes (%s/%s)',
              'too-many-instance-attributes',
              'Used when class has too many instance attributes, try to reduce \
              this to get a more simple (and so easier to use) class.'),
    'R0903': ('Too few public methods (%s/%s)',
              'too-few-public-methods',
              'Used when class has too few public methods, so be sure it\'s \
              really worth it.'),
    'R0904': ('Too many public methods (%s/%s)',
              'too-many-public-methods',
              'Used when class has too many public methods, try to reduce \
              this to get a more simple (and so easier to use) class.'),

    'R0911': ('Too many return statements (%s/%s)',
              'too-many-return-statements',
              'Used when a function or method has too many return statement, \
              making it hard to follow.'),
    'R0912': ('Too many branches (%s/%s)',
              'too-many-branches',
              'Used when a function or method has too many branches, \
              making it hard to follow.'),
    'R0913': ('Too many arguments (%s/%s)',
              'too-many-arguments',
              'Used when a function or method takes too many arguments.'),
    'R0914': ('Too many local variables (%s/%s)',
              'too-many-locals',
              'Used when a function or method has too many local variables.'),
    'R0915': ('Too many statements (%s/%s)',
              'too-many-statements',
              'Used when a function or method has too many statements. You \
              should then split it in smaller functions / methods.'),

    'R0921': ('Abstract class not referenced',
              'abstract-class-not-used',
              'Used when an abstract class is not used as ancestor anywhere.'),
    'R0922': ('Abstract class is only referenced %s times',
              'abstract-class-little-used',
              'Used when an abstract class is used less than X times as \
              ancestor.'),
    'R0923': ('Interface not implemented',
              'interface-not-implemented',
              'Used when an interface class is not implemented anywhere.'),
    'R0924': ('Badly implemented %s, implements %s but not %s',
              'incomplete-protocol',
              'A class implements some of the special methods for a particular \
               protocol, but not all of them')
    }


class MisdesignChecker(BaseChecker):
    """checks for sign of poor/misdesign:
    * number of methods, attributes, local variables...
    * size, complexity of functions, methods
    """

    __implements__ = (IASTNGChecker,)

    # configuration section name
    name = 'design'
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = (('max-args',
                {'default' : 5, 'type' : 'int', 'metavar' : '<int>',
                 'help': 'Maximum number of arguments for function / method'}
                ),
               ('ignored-argument-names',
                {'default' : IGNORED_ARGUMENT_NAMES,
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'Argument names that match this expression will be '
                          'ignored. Default to name with leading underscore'}
                ),
               ('max-locals',
                {'default' : 15, 'type' : 'int', 'metavar' : '<int>',
                 'help': 'Maximum number of locals for function / method body'}
                ),
               ('max-returns',
                {'default' : 6, 'type' : 'int', 'metavar' : '<int>',
                 'help': 'Maximum number of return / yield for function / '
                         'method body'}
                ),
               ('max-branchs',
                {'default' : 12, 'type' : 'int', 'metavar' : '<int>',
                 'help': 'Maximum number of branch for function / method body'}
                ),
               ('max-statements',
                {'default' : 50, 'type' : 'int', 'metavar' : '<int>',
                 'help': 'Maximum number of statements in function / method '
                         'body'}
                ),
               ('max-parents',
                {'default' : 7,
                 'type' : 'int',
                 'metavar' : '<num>',
                 'help' : 'Maximum number of parents for a class (see R0901).'}
                ),
               ('max-attributes',
                {'default' : 7,
                 'type' : 'int',
                 'metavar' : '<num>',
                 'help' : 'Maximum number of attributes for a class \
(see R0902).'}
                ),
               ('min-public-methods',
                {'default' : 2,
                 'type' : 'int',
                 'metavar' : '<num>',
                 'help' : 'Minimum number of public methods for a class \
(see R0903).'}
                ),
               ('max-public-methods',
                {'default' : 20,
                 'type' : 'int',
                 'metavar' : '<num>',
                 'help' : 'Maximum number of public methods for a class \
(see R0904).'}
                ),
               )

    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)
        self.stats = None
        self._returns = None
        self._branchs = None
        self._used_abstracts = None
        self._used_ifaces = None
        self._abstracts = None
        self._ifaces = None
        self._stmts = 0

    def open(self):
        """initialize visit variables"""
        self.stats = self.linter.add_stats()
        self._returns = []
        self._branchs = []
        self._used_abstracts = {}
        self._used_ifaces = {}
        self._abstracts = []
        self._ifaces = []

    def close(self):
        """check that abstract/interface classes are used"""
        for abstract in self._abstracts:
            if not abstract in self._used_abstracts:
                self.add_message('R0921', node=abstract)
            elif self._used_abstracts[abstract] < 2:
                self.add_message('R0922', node=abstract,
                                 args=self._used_abstracts[abstract])
        for iface in self._ifaces:
            if not iface in self._used_ifaces:
                self.add_message('R0923', node=iface)

    def visit_class(self, node):
        """check size of inheritance hierarchy and number of instance attributes
        """
        self._inc_branch()
        # Is the total inheritance hierarchy is 7 or less?
        nb_parents = len(list(node.ancestors()))
        if nb_parents > self.config.max_parents:
            self.add_message('R0901', node=node,
                             args=(nb_parents, self.config.max_parents))
        # Does the class contain less than 20 attributes for
        # non-GUI classes (40 for GUI)?
        # FIXME detect gui classes
        if len(node.instance_attrs) > self.config.max_attributes:
            self.add_message('R0902', node=node,
                             args=(len(node.instance_attrs),
                                   self.config.max_attributes))
        # update abstract / interface classes structures
        if class_is_abstract(node):
            self._abstracts.append(node)
        elif node.type == 'interface' and node.name != 'Interface':
            self._ifaces.append(node)
            for parent in node.ancestors(False):
                if parent.name == 'Interface':
                    continue
                self._used_ifaces[parent] = 1
        try:
            for iface in node.interfaces():
                self._used_ifaces[iface] = 1
        except InferenceError:
            # XXX log ?
            pass
        for parent in node.ancestors():
            try:
                self._used_abstracts[parent] += 1
            except KeyError:
                self._used_abstracts[parent] = 1

    def leave_class(self, node):
        """check number of public methods"""
        nb_public_methods = 0
        special_methods = set()
        for method in node.methods():
            if not method.name.startswith('_'):
                nb_public_methods += 1
            if method.name.startswith("__"):
                special_methods.add(method.name)
        # Does the class contain less than 20 public methods ?
        if nb_public_methods > self.config.max_public_methods:
            self.add_message('R0904', node=node,
                             args=(nb_public_methods,
                                   self.config.max_public_methods))
        # stop here for exception, metaclass and interface classes
        if node.type != 'class':
            return
        # Does the class implement special methods consitently?
        # If so, don't enforce minimum public methods.
        check_special = SpecialMethodChecker(
            special_methods, lambda args: self.add_message('R0924', node=node, args=args))
        protocols = [check_special(pmethods, pname) for pname, pmethods in SPECIAL_METHODS]
        if True in protocols:
            return
        # Does the class contain more than 5 public methods ?
        if nb_public_methods < self.config.min_public_methods:
            self.add_message('R0903', node=node,
                             args=(nb_public_methods,
                                   self.config.min_public_methods))

    def visit_function(self, node):
        """check function name, docstring, arguments, redefinition,
        variable names, max locals
        """
        self._inc_branch()
        # init branch and returns counters
        self._returns.append(0)
        self._branchs.append(0)
        # check number of arguments
        args = node.args.args
        if args is not None:
            ignored_args_num = len(
                [arg for arg in args
                 if self.config.ignored_argument_names.match(arg.name)])
            argnum = len(args) - ignored_args_num
            if  argnum > self.config.max_args:
                self.add_message('R0913', node=node,
                                 args=(len(args), self.config.max_args))
        else:
            ignored_args_num = 0
        # check number of local variables
        locnum = len(node.locals) - ignored_args_num
        if locnum > self.config.max_locals:
            self.add_message('R0914', node=node,
                             args=(locnum, self.config.max_locals))
        # init statements counter
        self._stmts = 1

    def leave_function(self, node):
        """most of the work is done here on close:
        checks for max returns, branch, return in __init__
        """
        returns = self._returns.pop()
        if returns > self.config.max_returns:
            self.add_message('R0911', node=node,
                             args=(returns, self.config.max_returns))
        branchs = self._branchs.pop()
        if branchs > self.config.max_branchs:
            self.add_message('R0912', node=node,
                             args=(branchs, self.config.max_branchs))
        # check number of statements
        if self._stmts > self.config.max_statements:
            self.add_message('R0915', node=node,
                             args=(self._stmts, self.config.max_statements))

    def visit_return(self, _):
        """count number of returns"""
        if not self._returns:
            return # return outside function, reported by the base checker
        self._returns[-1] += 1

    def visit_default(self, node):
        """default visit method -> increments the statements counter if
        necessary
        """
        if node.is_statement:
            self._stmts += 1

    def visit_tryexcept(self, node):
        """increments the branchs counter"""
        branchs = len(node.handlers)
        if node.orelse:
            branchs += 1
        self._inc_branch(branchs)
        self._stmts += branchs

    def visit_tryfinally(self, _):
        """increments the branchs counter"""
        self._inc_branch(2)
        self._stmts += 2

    def visit_if(self, node):
        """increments the branchs counter"""
        branchs = 1
        # don't double count If nodes coming from some 'elif'
        if node.orelse and (len(node.orelse)>1 or
                            not isinstance(node.orelse[0], If)):
            branchs += 1
        self._inc_branch(branchs)
        self._stmts += branchs

    def visit_while(self, node):
        """increments the branchs counter"""
        branchs = 1
        if node.orelse:
            branchs += 1
        self._inc_branch(branchs)

    visit_for = visit_while

    def _inc_branch(self, branchsnum=1):
        """increments the branchs counter"""
        branchs = self._branchs
        for i in xrange(len(branchs)):
            branchs[i] += branchsnum

    # FIXME: make a nice report...

def register(linter):
    """required method to auto register this checker """
    linter.register_checker(MisdesignChecker(linter))
