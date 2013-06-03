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
"""variables checkers for Python code
"""

import sys
from copy import copy

from logilab import astng
from logilab.astng import are_exclusive, builtin_lookup, ASTNGBuildingException

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import (PYMETHODS, is_ancestor_name, is_builtin,
     is_defined_before, is_error, is_func_default, is_func_decorator,
     assign_parent, check_messages, is_inside_except, clobber_in_except,
     get_all_elements)


def in_for_else_branch(parent, stmt):
    """Returns True if stmt in inside the else branch for a parent For stmt."""
    return (isinstance(parent, astng.For) and
            any(else_stmt.parent_of(stmt) for else_stmt in parent.orelse))

def overridden_method(klass, name):
    """get overridden method if any"""
    try:
        parent = klass.local_attr_ancestors(name).next()
    except (StopIteration, KeyError):
        return None
    try:
        meth_node = parent[name]
    except KeyError:
        # We have found an ancestor defining <name> but it's not in the local
        # dictionary. This may happen with astng built from living objects.
        return None
    if isinstance(meth_node, astng.Function):
        return meth_node
    return None


MSGS = {
    'E0601': ('Using variable %r before assignment',
              'used-before-assignment',
              'Used when a local variable is accessed before it\'s \
              assignment.'),
    'E0602': ('Undefined variable %r',
              'undefined-variable',
              'Used when an undefined variable is accessed.'),
    'E0603': ('Undefined variable name %r in __all__',
              'undefined-all-variable',
              'Used when an undefined variable name is referenced in __all__.'),
    'E0611': ('No name %r in module %r',
              'no-name-in-module',
              'Used when a name cannot be found in a module.'),

    'W0601': ('Global variable %r undefined at the module level',
              'global-variable-undefined',
              'Used when a variable is defined through the "global" statement \
              but the variable is not defined in the module scope.'),
    'W0602': ('Using global for %r but no assignment is done',
              'global-variable-not-assigned',
              'Used when a variable is defined through the "global" statement \
              but no assignment to this variable is done.'),
    'W0603': ('Using the global statement', # W0121
              'global-statement',
              'Used when you use the "global" statement to update a global \
              variable. PyLint just try to discourage this \
              usage. That doesn\'t mean you can not use it !'),
    'W0604': ('Using the global statement at the module level', # W0103
              'global-at-module-level',
              'Used when you use the "global" statement at the module level \
              since it has no effect'),
    'W0611': ('Unused import %s',
              'unused-import',
              'Used when an imported module or variable is not used.'),
    'W0612': ('Unused variable %r',
              'unused-variable',
              'Used when a variable is defined but not used.'),
    'W0613': ('Unused argument %r',
              'unused-argument',
              'Used when a function or method argument is not used.'),
    'W0614': ('Unused import %s from wildcard import',
              'unused-wildcard-import',
              'Used when an imported module or variable is not used from a \
              \'from X import *\' style import.'),

    'W0621': ('Redefining name %r from outer scope (line %s)',
              'redefined-outer-name',
              'Used when a variable\'s name hide a name defined in the outer \
              scope.'),
    'W0622': ('Redefining built-in %r',
              'redefined-builtin',
              'Used when a variable or function override a built-in.'),
    'W0623': ('Redefining name %r from %s in exception handler',
              'redefine-in-handler',
              'Used when an exception handler assigns the exception \
               to an existing name'),

    'W0631': ('Using possibly undefined loop variable %r',
              'undefined-loop-variable',
              'Used when an loop variable (i.e. defined by a for loop or \
              a list comprehension or a generator expression) is used outside \
              the loop.'),
    }

class VariablesChecker(BaseChecker):
    """checks for
    * unused variables / imports
    * undefined variables
    * redefinition of variable from builtins or from an outer scope
    * use of variable before assignment
    * __all__ consistency
    """

    __implements__ = IASTNGChecker

    name = 'variables'
    msgs = MSGS
    priority = -1
    options = (
               ("init-import",
                {'default': 0, 'type' : 'yn', 'metavar' : '<y_or_n>',
                 'help' : 'Tells whether we should check for unused import in \
__init__ files.'}),
               ("dummy-variables-rgx",
                {'default': ('_|dummy'),
                 'type' :'regexp', 'metavar' : '<regexp>',
                 'help' : 'A regular expression matching the beginning of \
                  the name of dummy variables (i.e. not used).'}),
               ("additional-builtins",
                {'default': (), 'type' : 'csv',
                 'metavar' : '<comma separated list>',
                 'help' : 'List of additional names supposed to be defined in \
builtins. Remember that you should avoid to define new builtins when possible.'
                 }),
               )
    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)
        self._to_consume = None
        self._checking_mod_attr = None

    def visit_module(self, node):
        """visit module : update consumption analysis variable
        checks globals doesn't overrides builtins
        """
        self._to_consume = [(copy(node.locals), {}, 'module')]
        for name, stmts in node.locals.iteritems():
            if is_builtin(name) and not is_inside_except(stmts[0]):
                # do not print Redefining builtin for additional builtins
                self.add_message('W0622', args=name, node=stmts[0])

    @check_messages('W0611', 'W0614')
    def leave_module(self, node):
        """leave module: check globals
        """
        assert len(self._to_consume) == 1
        not_consumed = self._to_consume.pop()[0]
        # attempt to check for __all__ if defined
        if '__all__' in node.locals:
            assigned = node.igetattr('__all__').next()
            for elt in getattr(assigned, 'elts', ()):
                elt_name = elt.value
                # If elt is in not_consumed, remove it from not_consumed
                if elt_name in not_consumed:
                    del not_consumed[elt_name]
                    continue
                if elt_name not in node.locals:
                    self.add_message('E0603', args=elt_name, node=elt)
        # don't check unused imports in __init__ files
        if not self.config.init_import and node.package:
            return
        for name, stmts in not_consumed.iteritems():
            stmt = stmts[0]
            if isinstance(stmt, astng.Import):
                self.add_message('W0611', args=name, node=stmt)
            elif isinstance(stmt, astng.From) and stmt.modname != '__future__':
                if stmt.names[0][0] == '*':
                    self.add_message('W0614', args=name, node=stmt)
                else:
                    self.add_message('W0611', args=name, node=stmt)
        del self._to_consume

    def visit_class(self, node):
        """visit class: update consumption analysis variable
        """
        self._to_consume.append((copy(node.locals), {}, 'class'))

    def leave_class(self, _):
        """leave class: update consumption analysis variable
        """
        # do not check for not used locals here (no sense)
        self._to_consume.pop()

    def visit_lambda(self, node):
        """visit lambda: update consumption analysis variable
        """
        self._to_consume.append((copy(node.locals), {}, 'lambda'))

    def leave_lambda(self, _):
        """leave lambda: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_genexpr(self, node):
        """visit genexpr: update consumption analysis variable
        """
        self._to_consume.append((copy(node.locals), {}, 'comprehension'))

    def leave_genexpr(self, _):
        """leave genexpr: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_dictcomp(self, node):
        """visit dictcomp: update consumption analysis variable
        """
        self._to_consume.append((copy(node.locals), {}, 'comprehension'))

    def leave_dictcomp(self, _):
        """leave dictcomp: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_setcomp(self, node):
        """visit setcomp: update consumption analysis variable
        """
        self._to_consume.append((copy(node.locals), {}, 'comprehension'))

    def leave_setcomp(self, _):
        """leave setcomp: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

    def visit_function(self, node):
        """visit function: update consumption analysis variable and check locals
        """
        self._to_consume.append((copy(node.locals), {}, 'function'))
        if not set(('W0621', 'W0622')) & self.active_msgs:
            return
        globs = node.root().globals
        for name, stmt in node.items():
            if is_inside_except(stmt):
                continue
            if name in globs and not isinstance(stmt, astng.Global):
                line = globs[name][0].lineno
                self.add_message('W0621', args=(name, line), node=stmt)
            elif is_builtin(name):
                # do not print Redefining builtin for additional builtins
                self.add_message('W0622', args=name, node=stmt)

    def leave_function(self, node):
        """leave function: check function's locals are consumed"""
        not_consumed = self._to_consume.pop()[0]
        if not set(('W0612', 'W0613')) & self.active_msgs:
            return
        # don't check arguments of function which are only raising an exception
        if is_error(node):
            return
        # don't check arguments of abstract methods or within an interface
        is_method = node.is_method()
        klass = node.parent.frame()
        if is_method and (klass.type == 'interface' or node.is_abstract()):
            return
        authorized_rgx = self.config.dummy_variables_rgx
        called_overridden = False
        argnames = node.argnames()
        for name, stmts in not_consumed.iteritems():
            # ignore some special names specified by user configuration
            if authorized_rgx.match(name):
                continue
            # ignore names imported by the global statement
            # FIXME: should only ignore them if it's assigned latter
            stmt = stmts[0]
            if isinstance(stmt, astng.Global):
                continue
            # care about functions with unknown argument (builtins)
            if name in argnames:
                if is_method:
                    # don't warn for the first argument of a (non static) method
                    if node.type != 'staticmethod' and name == argnames[0]:
                        continue
                    # don't warn for argument of an overridden method
                    if not called_overridden:
                        overridden = overridden_method(klass, node.name)
                        called_overridden = True
                    if overridden is not None and name in overridden.argnames():
                        continue
                    if node.name in PYMETHODS and node.name not in ('__init__', '__new__'):
                        continue
                # don't check callback arguments XXX should be configurable
                if node.name.startswith('cb_') or node.name.endswith('_cb'):
                    continue
                self.add_message('W0613', args=name, node=stmt)
            else:
                self.add_message('W0612', args=name, node=stmt)

    @check_messages('W0601', 'W0602', 'W0603', 'W0604', 'W0622')
    def visit_global(self, node):
        """check names imported exists in the global scope"""
        frame = node.frame()
        if isinstance(frame, astng.Module):
            self.add_message('W0604', node=node)
            return
        module = frame.root()
        default_message = True
        for name in node.names:
            try:
                assign_nodes = module.getattr(name)
            except astng.NotFoundError:
                # unassigned global, skip
                assign_nodes = []
            for anode in assign_nodes:
                if anode.parent is None:
                    # node returned for builtin attribute such as __file__,
                    # __doc__, etc...
                    continue
                if anode.frame() is frame:
                    # same scope level assignment
                    break
            else:
                # global but no assignment
                self.add_message('W0602', args=name, node=node)
                default_message = False
            if not assign_nodes:
                continue
            for anode in assign_nodes:
                if anode.parent is None:
                    self.add_message('W0622', args=name, node=node)
                    break
                if anode.frame() is module:
                    # module level assignment
                    break
            else:
                # global undefined at the module scope
                self.add_message('W0601', args=name, node=node)
                default_message = False
        if default_message:
            self.add_message('W0603', node=node)

    def _loopvar_name(self, node, name):
        # filter variables according to node's scope
        # XXX used to filter parents but don't remember why, and removing this
        # fixes a W0631 false positive reported by Paul Hachmann on 2008/12 on
        # python-projects (added to func_use_for_or_listcomp_var test)
        #astmts = [stmt for stmt in node.lookup(name)[1]
        #          if hasattr(stmt, 'ass_type')] and
        #          not stmt.statement().parent_of(node)]
        if 'W0631' not in self.active_msgs:
            return
        astmts = [stmt for stmt in node.lookup(name)[1]
                  if hasattr(stmt, 'ass_type')]
        # filter variables according their respective scope test is_statement
        # and parent to avoid #74747. This is not a total fix, which would
        # introduce a mechanism similar to special attribute lookup in
        # modules. Also, in order to get correct inference in this case, the
        # scope lookup rules would need to be changed to return the initial
        # assignment (which does not exist in code per se) as well as any later
        # modifications.
        if not astmts or (astmts[0].is_statement or astmts[0].parent) \
             and astmts[0].statement().parent_of(node):
            _astmts = []
        else:
            _astmts = astmts[:1]
        for i, stmt in enumerate(astmts[1:]):
            if (astmts[i].statement().parent_of(stmt)
                and not in_for_else_branch(astmts[i].statement(), stmt)):
                continue
            _astmts.append(stmt)
        astmts = _astmts
        if len(astmts) == 1:
            ass = astmts[0].ass_type()
            if isinstance(ass, (astng.For, astng.Comprehension, astng.GenExpr)) \
                   and not ass.statement() is node.statement():
                self.add_message('W0631', args=name, node=node)

    def visit_excepthandler(self, node):
        for name in get_all_elements(node.name):
            clobbering, args = clobber_in_except(name)
            if clobbering:
                self.add_message('W0623', args=args, node=name)

    def visit_assname(self, node):
        if isinstance(node.ass_type(), astng.AugAssign):
            self.visit_name(node)

    def visit_delname(self, node):
        self.visit_name(node)

    def visit_name(self, node):
        """check that a name is defined if the current scope and doesn't
        redefine a built-in
        """
        stmt = node.statement()
        if stmt.fromlineno is None:
            # name node from a astng built from live code, skip
            assert not stmt.root().file.endswith('.py')
            return
        name = node.name
        frame = stmt.scope()
        # if the name node is used as a function default argument's value or as
        # a decorator, then start from the parent frame of the function instead
        # of the function frame - and thus open an inner class scope
        if (is_func_default(node) or is_func_decorator(node)
            or is_ancestor_name(frame, node)):
            start_index = len(self._to_consume) - 2
        else:
            start_index = len(self._to_consume) - 1
        # iterates through parent scopes, from the inner to the outer
        base_scope_type = self._to_consume[start_index][-1]
        for i in range(start_index, -1, -1):
            to_consume, consumed, scope_type = self._to_consume[i]
            # if the current scope is a class scope but it's not the inner
            # scope, ignore it. This prevents to access this scope instead of
            # the globals one in function members when there are some common
            # names. The only exception is when the starting scope is a
            # comprehension and its direct outer scope is a class
            if scope_type == 'class' and i != start_index and not (
                base_scope_type == 'comprehension' and i == start_index-1):
                # XXX find a way to handle class scope in a smoother way
                continue
            # the name has already been consumed, only check it's not a loop
            # variable used outside the loop
            if name in consumed:
                self._loopvar_name(node, name)
                break
            # mark the name as consumed if it's defined in this scope
            # (i.e. no KeyError is raised by "to_consume[name]")
            try:
                consumed[name] = to_consume[name]
            except KeyError:
                continue
            # checks for use before assignment
            defnode = assign_parent(to_consume[name][0])
            if defnode is not None:
                defstmt = defnode.statement()
                defframe = defstmt.frame()
                maybee0601 = True
                if not frame is defframe:
                    maybee0601 = False
                elif defframe.parent is None:
                    # we are at the module level, check the name is not
                    # defined in builtins
                    if name in defframe.scope_attrs or builtin_lookup(name)[1]:
                        maybee0601 = False
                else:
                    # we are in a local scope, check the name is not
                    # defined in global or builtin scope
                    if defframe.root().lookup(name)[1]:
                        maybee0601 = False
                if (maybee0601
                    and stmt.fromlineno <= defstmt.fromlineno
                    and not is_defined_before(node)
                    and not are_exclusive(stmt, defstmt, ('NameError', 'Exception', 'BaseException'))):
                    if defstmt is stmt and isinstance(node, (astng.DelName,
                                                             astng.AssName)):
                        self.add_message('E0602', args=name, node=node)
                    elif self._to_consume[-1][-1] != 'lambda':
                        # E0601 may *not* occurs in lambda scope
                        self.add_message('E0601', args=name, node=node)
            if not isinstance(node, astng.AssName): # Aug AssName
                del to_consume[name]
            else:
                del consumed[name]
            # check it's not a loop variable used outside the loop
            self._loopvar_name(node, name)
            break
        else:
            # we have not found the name, if it isn't a builtin, that's an
            # undefined name !
            if not (name in astng.Module.scope_attrs or is_builtin(name)
                    or name in self.config.additional_builtins):
                self.add_message('E0602', args=name, node=node)

    @check_messages('E0611')
    def visit_import(self, node):
        """check modules attribute accesses"""
        for name, _ in node.names:
            parts = name.split('.')
            try:
                module = node.infer_name_module(parts[0]).next()
            except astng.ResolveError:
                continue
            self._check_module_attrs(node, module, parts[1:])

    @check_messages('E0611')
    def visit_from(self, node):
        """check modules attribute accesses"""
        name_parts = node.modname.split('.')
        level = getattr(node, 'level', None)
        try:
            module = node.root().import_module(name_parts[0], level=level)
        except ASTNGBuildingException:
            return
        except Exception, exc:
            print 'Unhandled exception in VariablesChecker:', exc
            return
        module = self._check_module_attrs(node, module, name_parts[1:])
        if not module:
            return
        for name, _ in node.names:
            if name == '*':
                continue
            self._check_module_attrs(node, module, name.split('.'))

    def _check_module_attrs(self, node, module, module_names):
        """check that module_names (list of string) are accessible through the
        given module
        if the latest access name corresponds to a module, return it
        """
        assert isinstance(module, astng.Module), module
        while module_names:
            name = module_names.pop(0)
            if name == '__dict__':
                module = None
                break
            try:
                module = module.getattr(name)[0].infer().next()
                if module is astng.YES:
                    return None
            except astng.NotFoundError:
                self.add_message('E0611', args=(name, module.name), node=node)
                return None
            except astng.InferenceError:
                return None
        if module_names:
            # FIXME: other message if name is not the latest part of
            # module_names ?
            modname = module and module.name or '__dict__'
            self.add_message('E0611', node=node,
                             args=('.'.join(module_names), modname))
            return None
        if isinstance(module, astng.Module):
            return module
        return None


class VariablesChecker3k(VariablesChecker):
    '''Modified variables checker for 3k'''
    # listcomp have now also their scope

    def visit_listcomp(self, node):
        """visit dictcomp: update consumption analysis variable
        """
        self._to_consume.append((copy(node.locals), {}, 'comprehension'))

    def leave_listcomp(self, _):
        """leave dictcomp: update consumption analysis variable
        """
        # do not check for not used locals here
        self._to_consume.pop()

if sys.version_info >= (3, 0):
    VariablesChecker = VariablesChecker3k


def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(VariablesChecker(linter))
