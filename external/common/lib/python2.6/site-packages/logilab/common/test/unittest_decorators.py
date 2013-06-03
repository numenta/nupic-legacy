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
"""unit tests for the decorators module
"""
import sys
import types

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.decorators import (monkeypatch, cached, clear_cache,
                                       copy_cache, cachedproperty)

class DecoratorsTC(TestCase):

    def test_monkeypatch_instance_method(self):
        class MyClass: pass
        @monkeypatch(MyClass)
        def meth1(self):
            return 12
        class XXX(object):
            @monkeypatch(MyClass)
            def meth2(self):
                return 12
        if sys.version_info < (3, 0):
            self.assertIsInstance(MyClass.meth1, types.MethodType)
            self.assertIsInstance(MyClass.meth2, types.MethodType)
        else:
            # with python3, unbound method are functions
            self.assertIsInstance(MyClass.meth1, types.FunctionType)
            self.assertIsInstance(MyClass.meth2, types.FunctionType)
        self.assertEqual(MyClass().meth1(), 12)
        self.assertEqual(MyClass().meth2(), 12)

    def test_monkeypatch_callable_non_callable(self):
        tester = self
        class MyClass: pass
        @monkeypatch(MyClass, methodname='prop1')
        @property
        def meth1(self):
            return 12
        # class XXX(object):
        #     def __call__(self, other):
        #         tester.assertIsInstance(other, MyClass)
        #         return 12
        # try:
        #     monkeypatch(MyClass)(XXX())
        # except AttributeError, err:
        #     self.assertTrue(str(err).endswith('has no __name__ attribute: you should provide an explicit `methodname`'))
        # monkeypatch(MyClass, 'foo')(XXX())
        # self.assertIsInstance(MyClass.prop1, property)
        # self.assertTrue(callable(MyClass.foo))
        self.assertEqual(MyClass().prop1, 12)
        # self.assertEqual(MyClass().foo(), 12)

    def test_monkeypatch_with_same_name(self):
        class MyClass: pass
        @monkeypatch(MyClass)
        def meth1(self):
            return 12
        self.assertEqual([attr for attr in dir(MyClass) if attr[:2] != '__'],
                          ['meth1'])
        inst = MyClass()
        self.assertEqual(inst.meth1(), 12)

    def test_monkeypatch_with_custom_name(self):
        class MyClass: pass
        @monkeypatch(MyClass, 'foo')
        def meth2(self, param):
            return param + 12
        self.assertEqual([attr for attr in dir(MyClass) if attr[:2] != '__'],
                          ['foo'])
        inst = MyClass()
        self.assertEqual(inst.foo(4), 16)

    def test_cannot_cache_generator(self):
        def foo():
            yield 42
        self.assertRaises(AssertionError, cached, foo)

    def test_cached_preserves_docstrings_and_name(self):
        class Foo(object):
            @cached
            def foo(self):
                """ what's up doc ? """
            def bar(self, zogzog):
                """ what's up doc ? """
            bar = cached(bar, 1)
            @cached
            def quux(self, zogzog):
                """ what's up doc ? """
        self.assertEqual(Foo.foo.__doc__, """ what's up doc ? """)
        self.assertEqual(Foo.foo.__name__, 'foo')
        self.assertEqual(Foo.foo.func_name, 'foo')
        self.assertEqual(Foo.bar.__doc__, """ what's up doc ? """)
        self.assertEqual(Foo.bar.__name__, 'bar')
        self.assertEqual(Foo.bar.func_name, 'bar')
        self.assertEqual(Foo.quux.__doc__, """ what's up doc ? """)
        self.assertEqual(Foo.quux.__name__, 'quux')
        self.assertEqual(Foo.quux.func_name, 'quux')

    def test_cached_single_cache(self):
        class Foo(object):
            @cached(cacheattr=u'_foo')
            def foo(self):
                """ what's up doc ? """
        foo = Foo()
        foo.foo()
        self.assertTrue(hasattr(foo, '_foo'))
        clear_cache(foo, 'foo')
        self.assertFalse(hasattr(foo, '_foo'))

    def test_cached_multi_cache(self):
        class Foo(object):
            @cached(cacheattr=u'_foo')
            def foo(self, args):
                """ what's up doc ? """
        foo = Foo()
        foo.foo(1)
        self.assertEqual(foo._foo, {(1,): None})
        clear_cache(foo, 'foo')
        self.assertFalse(hasattr(foo, '_foo'))

    def test_cached_keyarg_cache(self):
        class Foo(object):
            @cached(cacheattr=u'_foo', keyarg=1)
            def foo(self, other, args):
                """ what's up doc ? """
        foo = Foo()
        foo.foo(2, 1)
        self.assertEqual(foo._foo, {2: None})
        clear_cache(foo, 'foo')
        self.assertFalse(hasattr(foo, '_foo'))

    def test_cached_property(self):
        class Foo(object):
            @property
            @cached(cacheattr=u'_foo')
            def foo(self):
                """ what's up doc ? """
        foo = Foo()
        foo.foo
        self.assertEqual(foo._foo, None)
        clear_cache(foo, 'foo')
        self.assertFalse(hasattr(foo, '_foo'))

    def test_copy_cache(self):
        class Foo(object):
            @cached(cacheattr=u'_foo')
            def foo(self, args):
                """ what's up doc ? """
        foo = Foo()
        foo.foo(1)
        self.assertEqual(foo._foo, {(1,): None})
        foo2 = Foo()
        self.assertFalse(hasattr(foo2, '_foo'))
        copy_cache(foo2, 'foo', foo)
        self.assertEqual(foo2._foo, {(1,): None})


    def test_cachedproperty(self):
        class Foo(object):
            x = 0
            @cachedproperty
            def bar(self):
                self.__class__.x += 1
                return self.__class__.x
            @cachedproperty
            def quux(self):
                """ some prop """
                return 42

        foo = Foo()
        self.assertEqual(Foo.x, 0)
        self.assertFalse('bar' in foo.__dict__)
        self.assertEqual(foo.bar, 1)
        self.assertTrue('bar' in foo.__dict__)
        self.assertEqual(foo.bar, 1)
        self.assertEqual(foo.quux, 42)
        self.assertEqual(Foo.bar.__doc__,
                         '<wrapped by the cachedproperty decorator>')
        self.assertEqual(Foo.quux.__doc__,
                         '<wrapped by the cachedproperty decorator>\n some prop ')

        foo2 = Foo()
        self.assertEqual(foo2.bar, 2)
        # make sure foo.foo is cached
        self.assertEqual(foo.bar, 1)

        class Kallable(object):
            def __call__(self):
                return 42
        self.assertRaises(TypeError, cachedproperty, Kallable())

if __name__ == '__main__':
    unittest_main()
