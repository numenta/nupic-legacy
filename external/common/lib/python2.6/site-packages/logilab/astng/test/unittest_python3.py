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
import sys

from logilab.common.testlib import TestCase, unittest_main

from logilab.astng.node_classes import Assign
from logilab.astng.manager import ASTNGManager
from logilab.astng.builder import ASTNGBuilder


class Python3TC(TestCase):
    def setUp(self):
        self.manager = ASTNGManager()
        self.builder = ASTNGBuilder(self.manager)
        self.manager.astng_cache.clear()

    def test_starred_notation(self):
        if sys.version_info < (3, 0):
            self.skipTest("test python 3k specific")
        astng = self.builder.string_build("*a, b = [1, 2, 3]", 'test', 'test')

        # Get the star node
        node = next(next(next(astng.get_children()).get_children()).get_children())

        self.assertTrue(isinstance(node.ass_type(), Assign))

if __name__ == '__main__':
    unittest_main()
