# Copyright (c) 2005-2006 LOGILAB S.A. (Paris, FRANCE).
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
"""check for new / old style related problems
"""

from logilab import astng

from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker
from pylint.checkers.utils import check_messages

MSGS = {
    'E1001': ('Use of __slots__ on an old style class',
              'slots-on-old-class',
              'Used when an old style class uses the __slots__ attribute.'),
    'E1002': ('Use of super on an old style class',
              'super-on-old-class',
              'Used when an old style class uses the super builtin.'),
    'E1003': ('Bad first argument %r given to super class',
              'bad-super-call',
              'Used when another argument than the current class is given as \
              first argument of the super builtin.'),
    'W1001': ('Use of "property" on an old style class',
              'property-on-old-class',
              'Used when PyLint detect the use of the builtin "property" \
              on an old style class while this is relying on new style \
              classes features'),
    }


class NewStyleConflictChecker(BaseChecker):
    """checks for usage of new style capabilities on old style classes and
    other new/old styles conflicts problems                                    
    * use of property, __slots__, super                                        
    * "super" usage                                                            
    """
    
    __implements__ = (IASTNGChecker,)

    # configuration section name
    name = 'newstyle'
    # messages
    msgs = MSGS
    priority = -2
    # configuration options
    options = ()

    @check_messages('E1001')
    def visit_class(self, node):
        """check __slots__ usage
        """        
        if '__slots__' in node and not node.newstyle:
            self.add_message('E1001', node=node)

    @check_messages('W1001')
    def visit_callfunc(self, node):
        """check property usage"""
        parent = node.parent.frame()
        if (isinstance(parent, astng.Class) and
            not parent.newstyle and
            isinstance(node.func, astng.Name)):
            name = node.func.name
            if name == 'property':
                self.add_message('W1001', node=node)

    @check_messages('E1002', 'E1003')
    def visit_function(self, node):
        """check use of super"""
        # ignore actual functions or method within a new style class
        if not node.is_method():
            return
        klass = node.parent.frame()
        for stmt in node.nodes_of_class(astng.CallFunc):
            expr = stmt.func
            if not isinstance(expr, astng.Getattr):
                continue
            call = expr.expr
            # skip the test if using super
            if isinstance(call, astng.CallFunc) and \
               isinstance(call.func, astng.Name) and \
               call.func.name == 'super':
                if not klass.newstyle:
                    # super should not be used on an old style class
                    self.add_message('E1002', node=node)
                else:
                    # super first arg should be the class
                    try:
                        supcls = (call.args and call.args[0].infer().next()
                                  or None)
                    except astng.InferenceError:
                        continue
                    if klass is not supcls:
                        supcls = getattr(supcls, 'name', supcls)
                        self.add_message('E1003', node=node, args=supcls)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(NewStyleConflictChecker(linter))
