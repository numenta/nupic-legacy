# Copyright (c) 2003-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
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
"""
unittest for the visitors.diadefs module
"""

import unittest
import sys
from os.path import join, abspath, dirname

from logilab.astng import nodes, inspector
from logilab.astng.bases import Instance, YES

from logilab.astng.manager import ASTNGManager, _silent_no_wrap
MANAGER = ASTNGManager()

def astng_wrapper(func, modname):
    return func(modname)


DATA2 = join(dirname(abspath(__file__)), 'data2')

from os.path import join, abspath, dirname

class LinkerTC(unittest.TestCase):
    
    def setUp(self):
        self.project = MANAGER.project_from_files([DATA2], astng_wrapper)
        self.linker = inspector.Linker(self.project)
        self.linker.visit(self.project)

    def test_class_implements(self):
        klass = self.project.get_module('data2.clientmodule_test')['Ancestor']
        self.assert_(hasattr(klass, 'implements'))
        self.assertEqual(len(klass.implements), 1)
        self.assert_(isinstance(klass.implements[0], nodes.Class))
        self.assertEqual(klass.implements[0].name, "Interface")
        klass = self.project.get_module('data2.clientmodule_test')['Specialization']
        self.assert_(hasattr(klass, 'implements'))
        self.assertEqual(len(klass.implements), 0)
        
    def test_locals_assignment_resolution(self):
        klass = self.project.get_module('data2.clientmodule_test')['Specialization']
        self.assert_(hasattr(klass, 'locals_type'))
        type_dict = klass.locals_type
        self.assertEqual(len(type_dict), 2)
        keys = sorted(type_dict.keys())
        self.assertEqual(keys, ['TYPE', 'top'])
        self.assertEqual(len(type_dict['TYPE']), 1)
        self.assertEqual(type_dict['TYPE'][0].value, 'final class')
        self.assertEqual(len(type_dict['top']), 1)
        self.assertEqual(type_dict['top'][0].value, 'class')
        
    def test_instance_attrs_resolution(self):
        klass = self.project.get_module('data2.clientmodule_test')['Specialization']
        self.assert_(hasattr(klass, 'instance_attrs_type'))
        type_dict = klass.instance_attrs_type
        self.assertEqual(len(type_dict), 3)
        keys = sorted(type_dict.keys())
        self.assertEqual(keys, ['_id', 'relation', 'toto'])
        self.assert_(isinstance(type_dict['relation'][0], Instance), type_dict['relation'])
        self.assertEqual(type_dict['relation'][0].name, 'DoNothing')
        self.assert_(isinstance(type_dict['toto'][0], Instance), type_dict['toto'])
        self.assertEqual(type_dict['toto'][0].name, 'Toto')
        self.assert_(type_dict['_id'][0] is YES, type_dict['_id'])


class LinkerTC2(LinkerTC):
    
    def setUp(self):
        self.project = MANAGER.project_from_files([DATA2], func_wrapper=_silent_no_wrap)
        self.linker = inspector.Linker(self.project)
        self.linker.visit(self.project)
        
__all__ = ('LinkerTC', 'LinkerTC2')

        
if __name__ == '__main__':
    unittest.main()
