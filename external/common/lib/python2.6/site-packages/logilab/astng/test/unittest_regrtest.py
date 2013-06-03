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

from logilab.common.testlib import unittest_main, TestCase

from logilab.astng import ResolveError, MANAGER, Instance, nodes, YES, InferenceError
from logilab.astng.builder import ASTNGBuilder
from logilab.astng.raw_building import build_module
from logilab.astng.manager import ASTNGManager

import sys
from os.path import join, abspath, dirname

class NonRegressionTC(TestCase):

    def setUp(self):
        sys.path.insert(0, join(dirname(abspath(__file__)), 'regrtest_data'))

    def tearDown(self):
        sys.path.pop(0)

    def brainless_manager(self):
        manager = ASTNGManager()
        # avoid caching into the ASTNGManager borg since we get problems
        # with other tests :
        manager.__dict__ = {}
        manager.astng_cache = {}
        manager._mod_file_cache = {}
        manager.transformers = {}
        return manager

    def test_module_path(self):
        man = self.brainless_manager()
        mod = man.astng_from_module_name('package.import_package_subpackage_module')
        package = mod.igetattr('package').next()
        self.failUnlessEqual(package.name, 'package')
        subpackage = package.igetattr('subpackage').next()
        self.assertIsInstance(subpackage, nodes.Module)
        self.assertTrue(subpackage.package)
        self.failUnlessEqual(subpackage.name, 'package.subpackage')
        module = subpackage.igetattr('module').next()
        self.failUnlessEqual(module.name, 'package.subpackage.module')


    def test_package_sidepackage(self):
        manager = self.brainless_manager()
        assert 'package.sidepackage' not in MANAGER.astng_cache
        package = manager.astng_from_module_name('absimp')
        self.assertIsInstance(package, nodes.Module)
        self.assertTrue(package.package)
        subpackage = package.getattr('sidepackage')[0].infer().next()
        self.assertIsInstance(subpackage, nodes.Module)
        self.assertTrue(subpackage.package)
        self.failUnlessEqual(subpackage.name, 'absimp.sidepackage')


    def test_living_property(self):
        builder = ASTNGBuilder()
        builder._done = {}
        builder._module = sys.modules[__name__]
        builder.object_build(build_module('module_name', ''), Whatever)


    def test_new_style_class_detection(self):
        try:
            import pygtk
        except ImportError:
            self.skipTest('test skipped: pygtk is not available')
        # XXX may fail on some pygtk version, because objects in
        # gobject._gobject have __module__ set to gobject :(
        builder = ASTNGBuilder()
        data = """
import pygtk
pygtk.require("2.6")
import gobject

class A(gobject.GObject):
    pass
"""
        astng = builder.string_build(data, __name__, __file__)
        a = astng['A']
        self.failUnless(a.newstyle)


    def test_pylint_config_attr(self):
        try:
            from pylint import lint
        except ImportError:
            self.skipTest('pylint not available')
        mod = MANAGER.astng_from_module_name('pylint.lint')
        pylinter = mod['PyLinter']
        expect = ['OptionsManagerMixIn', 'object', 'MessagesHandlerMixIn',
                  'ReportsHandlerMixIn', 'BaseRawChecker', 'BaseChecker',
                  'OptionsProviderMixIn', 'ASTWalker']
        self.assertListEqual([c.name for c in pylinter.ancestors()],
                             expect)
        self.assert_(list(Instance(pylinter).getattr('config')))
        infered = list(Instance(pylinter).igetattr('config'))
        self.assertEqual(len(infered), 1)
        self.assertEqual(infered[0].root().name, 'optparse')
        self.assertEqual(infered[0].name, 'Values')

    def test_numpy_crash(self):
        """test don't crash on numpy"""
        #a crash occured somewhere in the past, and an
        # InferenceError instead of a crash was better, but now we even infer!
        try:
            import numpy
        except ImportError:
            self.skipTest('test skipped: numpy is not available')
        builder = ASTNGBuilder()
        data = """
from numpy import multiply

multiply(1, 2, 3)
"""
        astng = builder.string_build(data, __name__, __file__)
        callfunc = astng.body[1].value.func
        infered = callfunc.infered()
        self.assertEqual(len(infered), 1)
        self.assertIsInstance(infered[0], Instance)


class Whatever(object):
    a = property(lambda x: x, lambda x: x)

if __name__ == '__main__':
    unittest_main()
