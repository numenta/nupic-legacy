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
"""provides unit tests for compat module"""

from logilab.common.testlib import TestCase, unittest_main
import sys
import types
from logilab.common.compat import builtins

class CompatTCMixIn:
    MODNAMES = {}
    BUILTINS = []
    ALTERED_BUILTINS = {}

    def setUp(self):
        self.builtins_backup = {}
        self.modules_backup = {}
        self.remove_builtins()
        self.alter_builtins()
        self.remove_modules()

    def tearDown(self):
        for modname in self.MODNAMES:
            del sys.modules[modname]
        for funcname, func in self.builtins_backup.items():
            setattr(builtins, funcname, func)
            # delattr(builtins, 'builtin_%s' % funcname)
        for modname, mod in self.modules_backup.items():
            sys.modules[modname] = mod
        try:
            del sys.modules['logilab.common.compat']
        except KeyError:
            pass

    def remove_builtins(self):
        for builtin in self.BUILTINS:
            func = getattr(builtins, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = func
                delattr(builtins, builtin)
                # setattr(builtins, 'builtin_%s' % builtin, func)
    def alter_builtins(self):
        for builtin, func in self.ALTERED_BUILTINS.iteritems():
            old_func = getattr(builtins, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = old_func
                setattr(builtins, builtin, func)
                # setattr(builtins, 'builtin_%s' % builtin, func)

    def remove_modules(self):
        for modname in self.MODNAMES:
            if modname in sys.modules:
                self.modules_backup[modname] = sys.modules[modname]
            sys.modules[modname] = types.ModuleType('faked%s' % modname)

    def test_removed_builtins(self):
        """tests that builtins are actually uncallable"""
        for builtin in self.BUILTINS:
            self.assertRaises(NameError, eval, builtin, {})

    def test_removed_modules(self):
        """tests that builtins are actually emtpy"""
        for modname, funcnames in self.MODNAMES.items():
            import_stmt = 'from %s import %s' % (modname, ', '.join(funcnames))
            # FIXME: use __import__ instead
            code = compile(import_stmt, 'foo.py', 'exec')
            self.assertRaises(ImportError, eval, code)


class Py25CompatTC(CompatTCMixIn, TestCase):
    BUILTINS = ('any', 'all',)

    def test_any(self):
        from logilab.common.compat import any
        testdata = ([], (), '', 'abc', xrange(0, 10), xrange(0, -10, -1))
        self.assertEqual(any([]), False)
        self.assertEqual(any(()), False)
        self.assertEqual(any(''), False)
        self.assertEqual(any('abc'), True)
        self.assertEqual(any(xrange(10)), True)
        self.assertEqual(any(xrange(0, -10, -1)), True)
        # python2.5's any consumes iterables
        irange = iter(range(10))
        self.assertEqual(any(irange), True)
        self.assertEqual(irange.next(), 2)


    def test_all(self):
        from logilab.common.compat import all
        testdata = ([], (), '', 'abc', xrange(0, 10), xrange(0, -10, -1))
        self.assertEqual(all([]), True)
        self.assertEqual(all(()), True)
        self.assertEqual(all(''), True)
        self.assertEqual(all('abc'), True)
        self.assertEqual(all(xrange(10)), False)
        self.assertEqual(all(xrange(0, -10, -1)), False)
        # python2.5's all consumes iterables
        irange = iter(range(10))
        self.assertEqual(all(irange), False)
        self.assertEqual(irange.next(), 1)



if __name__ == '__main__':
    unittest_main()
