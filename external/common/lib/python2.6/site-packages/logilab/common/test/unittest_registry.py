# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of Logilab-Common.
#
# Logilab-Common is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# Logilab-Common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Logilab-Common.  If not, see <http://www.gnu.org/licenses/>.
"""unit tests for selectors mechanism"""
from __future__ import with_statement

import gc
import logging
import os.path as osp
import sys
from operator import eq, lt, le, gt
from contextlib import contextmanager

logging.basicConfig(level=logging.ERROR)

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.registry import *


class _1_(Predicate):
    def __call__(self, *args, **kwargs):
        return 1

class _0_(Predicate):
    def __call__(self, *args, **kwargs):
        return 0

def _2_(*args, **kwargs):
    return 2


class SelectorsTC(TestCase):
    def test_basic_and(self):
        selector = _1_() & _1_()
        self.assertEqual(selector(None), 2)
        selector = _1_() & _0_()
        self.assertEqual(selector(None), 0)
        selector = _0_() & _1_()
        self.assertEqual(selector(None), 0)

    def test_basic_or(self):
        selector = _1_() | _1_()
        self.assertEqual(selector(None), 1)
        selector = _1_() | _0_()
        self.assertEqual(selector(None), 1)
        selector = _0_() | _1_()
        self.assertEqual(selector(None), 1)
        selector = _0_() | _0_()
        self.assertEqual(selector(None), 0)

    def test_selector_and_function(self):
        selector = _1_() & _2_
        self.assertEqual(selector(None), 3)
        selector = _2_ & _1_()
        self.assertEqual(selector(None), 3)

    def test_three_and(self):
        selector = _1_() & _1_() & _1_()
        self.assertEqual(selector(None), 3)
        selector = _1_() & _0_() & _1_()
        self.assertEqual(selector(None), 0)
        selector = _0_() & _1_() & _1_()
        self.assertEqual(selector(None), 0)

    def test_three_or(self):
        selector = _1_() | _1_() | _1_()
        self.assertEqual(selector(None), 1)
        selector = _1_() | _0_() | _1_()
        self.assertEqual(selector(None), 1)
        selector = _0_() | _1_() | _1_()
        self.assertEqual(selector(None), 1)
        selector = _0_() | _0_() | _0_()
        self.assertEqual(selector(None), 0)

    def test_composition(self):
        selector = (_1_() & _1_()) & (_1_() & _1_())
        self.assertTrue(isinstance(selector, AndPredicate))
        self.assertEqual(len(selector.selectors), 4)
        self.assertEqual(selector(None), 4)
        selector = (_1_() & _0_()) | (_1_() & _1_())
        self.assertTrue(isinstance(selector, OrPredicate))
        self.assertEqual(len(selector.selectors), 2)
        self.assertEqual(selector(None), 2)

    def test_search_selectors(self):
        sel = _1_()
        self.assertIs(sel.search_selector(_1_), sel)
        csel = AndPredicate(sel, Predicate())
        self.assertIs(csel.search_selector(_1_), sel)
        csel = AndPredicate(Predicate(), sel)
        self.assertIs(csel.search_selector(_1_), sel)
        self.assertIs(csel.search_selector((AndPredicate, OrPredicate)), csel)
        self.assertIs(csel.search_selector((OrPredicate, AndPredicate)), csel)
        self.assertIs(csel.search_selector((_1_, _0_)),  sel)
        self.assertIs(csel.search_selector((_0_, _1_)), sel)

    def test_inplace_and(self):
        selector = _1_()
        selector &= _1_()
        selector &= _1_()
        self.assertEqual(selector(None), 3)
        selector = _1_()
        selector &= _0_()
        selector &= _1_()
        self.assertEqual(selector(None), 0)
        selector = _0_()
        selector &= _1_()
        selector &= _1_()
        self.assertEqual(selector(None), 0)
        selector = _0_()
        selector &= _0_()
        selector &= _0_()
        self.assertEqual(selector(None), 0)

    def test_inplace_or(self):
        selector = _1_()
        selector |= _1_()
        selector |= _1_()
        self.assertEqual(selector(None), 1)
        selector = _1_()
        selector |= _0_()
        selector |= _1_()
        self.assertEqual(selector(None), 1)
        selector = _0_()
        selector |= _1_()
        selector |= _1_()
        self.assertEqual(selector(None), 1)
        selector = _0_()
        selector |= _0_()
        selector |= _0_()
        self.assertEqual(selector(None), 0)

    def test_wrap_selectors(self):
        class _temp_(Predicate):
            def __call__(self, *args, **kwargs):
                return 0
        del _temp_ # test weakref
        s1 = _1_() & _1_()
        s2 = _1_() & _0_()
        s3 = _0_() & _1_()
        gc.collect()
        self.count = 0
        def decorate(f, self=self):
            def wrapper(*args, **kwargs):
                self.count += 1
                return f(*args, **kwargs)
            return wrapper
        wrap_predicates(decorate)
        self.assertEqual(s1(None), 2)
        self.assertEqual(s2(None), 0)
        self.assertEqual(s3(None), 0)
        self.assertEqual(self.count, 8)

@contextmanager
def prepended_syspath(path):
    sys.path.insert(0, path)
    yield
    sys.path = sys.path[1:]

class RegistryStoreTC(TestCase):

    def test_autoload(self):
        store = RegistryStore()
        store.setdefault('zereg')
        with prepended_syspath(self.datadir):
            store.register_objects([self.datapath('regobjects.py'),
                                    self.datapath('regobjects2.py')])
        self.assertEqual(['zereg'], store.keys())
        self.assertEqual(set(('appobject1', 'appobject2', 'appobject3')),
                         set(store['zereg']))


class RegistrableInstanceTC(TestCase):

    def test_instance_modulename(self):
        # no inheritance
        obj = RegistrableInstance()
        self.assertEqual(obj.__module__, 'unittest_registry')
        # with inheritance from another python file
        with prepended_syspath(self.datadir):
            from regobjects2 import instance, MyRegistrableInstance
            instance2 = MyRegistrableInstance()
            self.assertEqual(instance.__module__, 'regobjects2')
            self.assertEqual(instance2.__module__, 'unittest_registry')


if __name__ == '__main__':
    unittest_main()
