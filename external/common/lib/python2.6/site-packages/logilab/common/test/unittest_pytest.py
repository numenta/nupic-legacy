# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
from os.path import join
from logilab.common.testlib import TestCase, unittest_main
from logilab.common.pytest import *

class ModuleFunctionTC(TestCase):
    def test_this_is_testdir(self):
        self.assertTrue(this_is_a_testdir("test"))
        self.assertTrue(this_is_a_testdir("tests"))
        self.assertTrue(this_is_a_testdir("unittests"))
        self.assertTrue(this_is_a_testdir("unittest"))
        self.assertFalse(this_is_a_testdir("unit"))
        self.assertFalse(this_is_a_testdir("units"))
        self.assertFalse(this_is_a_testdir("undksjhqfl"))
        self.assertFalse(this_is_a_testdir("this_is_not_a_dir_test"))
        self.assertFalse(this_is_a_testdir("this_is_not_a_testdir"))
        self.assertFalse(this_is_a_testdir("unittestsarenothere"))
        self.assertTrue(this_is_a_testdir(join("coincoin", "unittests")))
        self.assertFalse(this_is_a_testdir(join("unittests", "spongebob")))

    def test_this_is_testfile(self):
        self.assertTrue(this_is_a_testfile("test.py"))
        self.assertTrue(this_is_a_testfile("testbabar.py"))
        self.assertTrue(this_is_a_testfile("unittest_celestine.py"))
        self.assertTrue(this_is_a_testfile("smoketest.py"))
        self.assertFalse(this_is_a_testfile("test.pyc"))
        self.assertFalse(this_is_a_testfile("zephir_test.py"))
        self.assertFalse(this_is_a_testfile("smoketest.pl"))
        self.assertFalse(this_is_a_testfile("unittest"))
        self.assertTrue(this_is_a_testfile(join("coincoin", "unittest_bibi.py")))
        self.assertFalse(this_is_a_testfile(join("unittest", "spongebob.py")))

if __name__ == '__main__':
    unittest_main()
