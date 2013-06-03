# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""This module contains some mixins for the different nodes.
"""

from logilab.astng.exceptions import (ASTNGBuildingException, InferenceError,
                                      NotFoundError)


class BlockRangeMixIn(object):
    """override block range """
    def set_line_info(self, lastchild):
        self.fromlineno = self.lineno
        self.tolineno = lastchild.tolineno
        self.blockstart_tolineno = self._blockstart_toline()

    def _elsed_block_range(self, lineno, orelse, last=None):
        """handle block line numbers range for try/finally, for, if and while
        statements
        """
        if lineno == self.fromlineno:
            return lineno, lineno
        if orelse:
            if lineno >= orelse[0].fromlineno:
                return lineno, orelse[-1].tolineno
            return lineno, orelse[0].fromlineno - 1
        return lineno, last or self.tolineno

class FilterStmtsMixin(object):
    """Mixin for statement filtering and assignment type"""

    def _get_filtered_stmts(self, _, node, _stmts, mystmt):
        """method used in _filter_stmts to get statemtents and trigger break"""
        if self.statement() is mystmt:
            # original node's statement is the assignment, only keep
            # current node (gen exp, list comp)
            return [node], True
        return _stmts, False

    def ass_type(self):
        return self


class AssignTypeMixin(object):

    def ass_type(self):
        return self

    def _get_filtered_stmts(self, lookup_node, node, _stmts, mystmt):
        """method used in filter_stmts"""
        if self is mystmt:
            return _stmts, True
        if self.statement() is mystmt:
            # original node's statement is the assignment, only keep
            # current node (gen exp, list comp)
            return [node], True
        return _stmts, False


class ParentAssignTypeMixin(AssignTypeMixin):

    def ass_type(self):
        return self.parent.ass_type()



class FromImportMixIn(FilterStmtsMixin):
    """MixIn for From and Import Nodes"""

    def _infer_name(self, frame, name):
        return name

    def do_import_module(self, modname):
        """return the ast for a module whose name is <modname> imported by <self>
        """
        # handle special case where we are on a package node importing a module
        # using the same name as the package, which may end in an infinite loop
        # on relative imports
        # XXX: no more needed ?
        mymodule = self.root()
        level = getattr(self, 'level', None) # Import as no level
        # XXX we should investigate deeper if we really want to check
        # importing itself: modname and mymodule.name be relative or absolute
        if mymodule.relative_to_absolute_name(modname, level) == mymodule.name:
            # FIXME: we used to raise InferenceError here, but why ?
            return mymodule
        try:
            return mymodule.import_module(modname, level=level)
        except ASTNGBuildingException:
            raise InferenceError(modname)
        except SyntaxError, ex:
            raise InferenceError(str(ex))

    def real_name(self, asname):
        """get name from 'as' name"""
        for name, _asname in self.names:
            if name == '*':
                return asname
            if not _asname:
                name = name.split('.', 1)[0]
                _asname = name
            if asname == _asname:
                return name
        raise NotFoundError(asname)



