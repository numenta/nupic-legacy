# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""
unit tests for module modutils (module manipulation utilities)
"""

import sys
try:
    __file__
except NameError:
    __file__ = sys.argv[0]

from logilab.common.testlib import TestCase, unittest_main
from logilab.common import modutils

from os import path, getcwd, sep
from logilab import common
from logilab.common import tree

sys.path.insert(0, path.dirname(__file__))
DATADIR = path.join(path.dirname(__file__), 'data')


class ModutilsTestCase(TestCase):
    def setUp(self):
        super(ModutilsTestCase, self).setUp()
        self.__common_in_path = common.__path__[0] in sys.path
        if self.__common_in_path:
            sys.path.remove(common.__path__[0])

    def tearDown(self):
        if self.__common_in_path:
            sys.path.insert(0, common.__path__[0])
        super(ModutilsTestCase, self).tearDown()


class ModuleFileTC(ModutilsTestCase):
    package = "mypypa"

    def setUp(self):
        super(ModuleFileTC, self).setUp()
        for k in sys.path_importer_cache.keys():
            if 'MyPyPa' in k:
                del sys.path_importer_cache[k]

    def test_find_zipped_module(self):
        mtype, mfile = modutils._module_file([self.package], [path.join(DATADIR, 'MyPyPa-0.1.0.zip')])
        self.assertEqual(mtype, modutils.ZIPFILE)
        self.assertEqual(mfile.split(sep)[-4:], ["test", "data", "MyPyPa-0.1.0.zip", self.package])

    def test_find_egg_module(self):
        mtype, mfile = modutils._module_file([self.package], [path.join(DATADIR, 'MyPyPa-0.1.0-py2.5.egg')])
        self.assertEqual(mtype, modutils.ZIPFILE)
        self.assertEqual(mfile.split(sep)[-4:], ["test", "data", "MyPyPa-0.1.0-py2.5.egg", self.package])


class load_module_from_name_tc(ModutilsTestCase):
    """ load a python module from it's name """

    def test_knownValues_load_module_from_name_1(self):
        self.assertEqual(modutils.load_module_from_name('sys'), sys)

    def test_knownValues_load_module_from_name_2(self):
        self.assertEqual(modutils.load_module_from_name('os.path'), path)

    def test_raise_load_module_from_name_1(self):
        self.assertRaises(ImportError,
                          modutils.load_module_from_name, 'os.path', use_sys=0)


class get_module_part_tc(ModutilsTestCase):
    """given a dotted name return the module part of the name"""

    def test_knownValues_get_module_part_1(self):
        self.assertEqual(modutils.get_module_part('logilab.common.modutils'),
                         'logilab.common.modutils')

    def test_knownValues_get_module_part_2(self):
        self.assertEqual(modutils.get_module_part('logilab.common.modutils.get_module_part'),
                         'logilab.common.modutils')

    def test_knownValues_get_module_part_3(self):
        """relative import from given file"""
        self.assertEqual(modutils.get_module_part('interface.Interface',
                                                  modutils.__file__), 'interface')

    def test_knownValues_get_compiled_module_part(self):
        self.assertEqual(modutils.get_module_part('math.log10'), 'math')
        self.assertEqual(modutils.get_module_part('math.log10', __file__), 'math')

    def test_knownValues_get_builtin_module_part(self):
        self.assertEqual(modutils.get_module_part('sys.path'), 'sys')
        self.assertEqual(modutils.get_module_part('sys.path', '__file__'), 'sys')

    def test_get_module_part_exception(self):
        self.assertRaises(ImportError, modutils.get_module_part, 'unknown.module',
                          modutils.__file__)


class modpath_from_file_tc(ModutilsTestCase):
    """ given an absolute file path return the python module's path as a list """

    def test_knownValues_modpath_from_file_1(self):
        self.assertEqual(modutils.modpath_from_file(modutils.__file__),
                         ['logilab', 'common', 'modutils'])

    def test_knownValues_modpath_from_file_2(self):
        self.assertEqual(modutils.modpath_from_file('unittest_modutils.py',
                                                    {getcwd(): 'arbitrary.pkg'}),
                         ['arbitrary', 'pkg', 'unittest_modutils'])

    def test_raise_modpath_from_file_Exception(self):
        self.assertRaises(Exception, modutils.modpath_from_file, '/turlututu')


class load_module_from_path_tc(ModutilsTestCase):

    def test_do_not_load_twice(self):
        sys.path.insert(0, self.datadir)
        foo = modutils.load_module_from_modpath(['lmfp', 'foo'])
        lmfp = modutils.load_module_from_modpath(['lmfp'])
        self.assertEqual(len(sys.just_once), 1)
        sys.path.pop(0)
        del sys.just_once

class file_from_modpath_tc(ModutilsTestCase):
    """given a mod path (i.e. splited module / package name), return the
    corresponding file, giving priority to source file over precompiled file
    if it exists"""

    def test_knownValues_file_from_modpath_1(self):
        self.assertEqual(path.realpath(modutils.file_from_modpath(['logilab', 'common', 'modutils'])),
                         path.realpath(modutils.__file__.replace('.pyc', '.py')))

    def test_knownValues_file_from_modpath_2(self):
        from os import path
        self.assertEqual(path.realpath(modutils.file_from_modpath(['os', 'path']).replace('.pyc', '.py')),
                         path.realpath(path.__file__.replace('.pyc', '.py')))

    def test_knownValues_file_from_modpath_3(self):
        try:
            # don't fail if pyxml isn't installed
            from xml.dom import ext
        except ImportError:
            pass
        else:
            self.assertEqual(path.realpath(modutils.file_from_modpath(['xml', 'dom', 'ext']).replace('.pyc', '.py')),
                             path.realpath(ext.__file__.replace('.pyc', '.py')))

    def test_knownValues_file_from_modpath_4(self):
        self.assertEqual(modutils.file_from_modpath(['sys']),
                         None)

    def test_raise_file_from_modpath_Exception(self):
        self.assertRaises(ImportError, modutils.file_from_modpath, ['turlututu'])

class get_source_file_tc(ModutilsTestCase):

    def test(self):
        from os import path
        self.assertEqual(modutils.get_source_file(path.__file__),
                         path.__file__.replace('.pyc', '.py'))

    def test_raise(self):
        self.assertRaises(modutils.NoSourceFile, modutils.get_source_file, 'whatever')

class is_standard_module_tc(ModutilsTestCase):
    """
    return true if the module may be considered as a module from the standard
    library
    """

    def test_knownValues_is_standard_module_builtins(self):
        if sys.version_info < (3, 0):
            self.assertEqual(modutils.is_standard_module('__builtin__'), True)
            self.assertEqual(modutils.is_standard_module('builtins'), False)
        else:
            self.assertEqual(modutils.is_standard_module('__builtin__'), False)
            self.assertEqual(modutils.is_standard_module('builtins'), True)

    def test_knownValues_is_standard_module_builtin(self):
        self.assertEqual(modutils.is_standard_module('sys'), True)

    def test_knownValues_is_standard_module_nonstandard(self):
        self.assertEqual(modutils.is_standard_module('logilab'), False)

    def test_knownValues_is_standard_module_unknown(self):
        self.assertEqual(modutils.is_standard_module('unknown'), False)

    def test_knownValues_is_standard_module_4(self):
        self.assertEqual(modutils.is_standard_module('marshal'), True)
        self.assertEqual(modutils.is_standard_module('hashlib'), True)
        self.assertEqual(modutils.is_standard_module('pickle'), True)
        self.assertEqual(modutils.is_standard_module('email'), True)
        self.assertEqual(modutils.is_standard_module('io'), sys.version_info >= (2, 6))
        self.assertEqual(modutils.is_standard_module('StringIO'), sys.version_info < (3, 0))

    def test_knownValues_is_standard_module_custom_path(self):
        self.assertEqual(modutils.is_standard_module('data.module', (DATADIR,)), True)
        self.assertEqual(modutils.is_standard_module('data.module', (path.abspath(DATADIR),)), True)

class is_relative_tc(ModutilsTestCase):


    def test_knownValues_is_relative_1(self):
        self.assertEqual(modutils.is_relative('modutils', common.__path__[0]), True)

    def test_knownValues_is_relative_2(self):
        self.assertEqual(modutils.is_relative('modutils', tree.__file__), True)

    def test_knownValues_is_relative_3(self):
        self.assertEqual(modutils.is_relative('logilab.common.modutils',
                                              common.__path__[0]), False)

class get_modules_tc(ModutilsTestCase):

    def test_knownValues_get_modules_1(self): #  XXXFIXME: TOWRITE
        """given a directory return a list of all available python modules, even
        in subdirectories
        """
        import data.find_test as data
        mod_path = ("data", 'find_test')
        modules = sorted(modutils.get_modules(path.join(*mod_path),
                                              data.__path__[0]))
        self.assertSetEqual(set(modules),
            set([ '.'.join(mod_path + (mod, )) for mod in ('module', 'module2',
            'noendingnewline', 'nonregr')]))


class get_modules_files_tc(ModutilsTestCase):

    def test_knownValues_get_module_files_1(self): #  XXXFIXME: TOWRITE
        """given a directory return a list of all available python module's files, even
        in subdirectories
        """
        import data
        modules = sorted(modutils.get_module_files(path.join(DATADIR, 'find_test'),
                                                   data.__path__[0]))
        self.assertEqual(modules,
                         [path.join(DATADIR, 'find_test', x) for x in ['__init__.py', 'module.py', 'module2.py', 'noendingnewline.py', 'nonregr.py']])

    def test_load_module_set_attribute(self):
        import logilab.common.fileutils
        import logilab
        del logilab.common.fileutils
        del sys.modules['logilab.common.fileutils']
        m = modutils.load_module_from_modpath(['logilab', 'common', 'fileutils'])
        self.assertTrue( hasattr(logilab, 'common') )
        self.assertTrue( hasattr(logilab.common, 'fileutils') )
        self.assertTrue( m is logilab.common.fileutils )

from logilab.common.testlib import DocTest
class ModuleDocTest(DocTest):
    """test doc test in this module"""
    from logilab.common import modutils as module
del DocTest # necessary if we don't want it to be executed (we don't...)


if __name__ == '__main__':
    unittest_main()
