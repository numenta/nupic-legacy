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
"""tests for specific behaviour of astng scoped nodes (i.e. module, class and
function)
"""

import sys
from os.path import join, abspath, dirname

from logilab.common.testlib import TestCase, unittest_main

from logilab.astng import builder, nodes, scoped_nodes, \
     BUILTINS_MODULE, InferenceError, NotFoundError
from logilab.astng.bases import Instance, BoundMethod, UnboundMethod

abuilder = builder.ASTNGBuilder()
DATA = join(dirname(abspath(__file__)), 'data')
REGRTEST_DATA = join(dirname(abspath(__file__)), 'regrtest_data')
MODULE = abuilder.file_build(join(DATA, 'module.py'), 'data.module')
MODULE2 = abuilder.file_build(join(DATA, 'module2.py'), 'data.module2')
NONREGR = abuilder.file_build(join(DATA, 'nonregr.py'), 'data.nonregr')

PACK = abuilder.file_build(join(DATA, '__init__.py'), 'data')

def _test_dict_interface(self, node, test_attr):
    self.assert_(node[test_attr] is node[test_attr])
    self.assert_(test_attr in node)
    node.keys()
    node.values()
    node.items()
    iter(node)


class ModuleNodeTC(TestCase):

    def test_special_attributes(self):
        self.assertEqual(len(MODULE.getattr('__name__')), 1)
        self.assertIsInstance(MODULE.getattr('__name__')[0], nodes.Const)
        self.assertEqual(MODULE.getattr('__name__')[0].value, 'data.module')
        self.assertEqual(len(MODULE.getattr('__doc__')), 1)
        self.assertIsInstance(MODULE.getattr('__doc__')[0], nodes.Const)
        self.assertEqual(MODULE.getattr('__doc__')[0].value, 'test module for astng\n')
        self.assertEqual(len(MODULE.getattr('__file__')), 1)
        self.assertIsInstance(MODULE.getattr('__file__')[0], nodes.Const)
        self.assertEqual(MODULE.getattr('__file__')[0].value, join(DATA, 'module.py'))
        self.assertEqual(len(MODULE.getattr('__dict__')), 1)
        self.assertIsInstance(MODULE.getattr('__dict__')[0], nodes.Dict)
        self.assertRaises(NotFoundError, MODULE.getattr, '__path__')
        self.assertEqual(len(PACK.getattr('__path__')), 1)
        self.assertIsInstance(PACK.getattr('__path__')[0], nodes.List)

    def test_dict_interface(self):
        _test_dict_interface(self, MODULE, 'YO')

    def test_getattr(self):
        yo = MODULE.getattr('YO')[0]
        self.assertIsInstance(yo, nodes.Class)
        self.assertEqual(yo.name, 'YO')
        red = MODULE.igetattr('redirect').next()
        self.assertIsInstance(red, nodes.Function)
        self.assertEqual(red.name, 'four_args')
        spawn = MODULE.igetattr('spawn').next()
        self.assertIsInstance(spawn, nodes.Class)
        self.assertEqual(spawn.name, 'Execute')
        # resolve packageredirection
        sys.path.insert(1, DATA)
        mod = abuilder.file_build(join(DATA, 'appl/myConnection.py'),
                                  'appl.myConnection')
        try:
            ssl = mod.igetattr('SSL1').next()
            cnx = ssl.igetattr('Connection').next()
            self.assertEqual(cnx.__class__, nodes.Class)
            self.assertEqual(cnx.name, 'Connection')
            self.assertEqual(cnx.root().name, 'SSL1.Connection1')
        finally:
            del sys.path[1]
        self.assertEqual(len(NONREGR.getattr('enumerate')), 2)
        # raise ResolveError
        self.assertRaises(InferenceError, MODULE.igetattr, 'YOAA')

    def test_wildard_import_names(self):
        m = abuilder.file_build(join(DATA, 'all.py'), 'all')
        self.assertEqual(m.wildcard_import_names(), ['Aaa', '_bla', 'name'])
        m = abuilder.file_build(join(DATA, 'notall.py'), 'notall')
        res = sorted(m.wildcard_import_names())
        self.assertEqual(res, ['Aaa', 'func', 'name', 'other'])

    def test_module_getattr(self):
        data = '''
appli = application
appli += 2
del appli
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        # test del statement not returned by getattr
        self.assertEqual(len(astng.getattr('appli')), 2,
                          astng.getattr('appli'))

    def test_relative_to_absolute_name(self):
        # package
        mod = nodes.Module('very.multi.package', 'doc')
        mod.package = True
        modname = mod.relative_to_absolute_name('utils', 1)
        self.assertEqual(modname, 'very.multi.package.utils')
        modname = mod.relative_to_absolute_name('utils', 2)
        self.assertEqual(modname, 'very.multi.utils')
        modname = mod.relative_to_absolute_name('utils', 0)
        self.assertEqual(modname, 'very.multi.package.utils')
        modname = mod.relative_to_absolute_name('', 1)
        self.assertEqual(modname, 'very.multi.package')
        # non package
        mod = nodes.Module('very.multi.module', 'doc')
        mod.package = False
        modname = mod.relative_to_absolute_name('utils', 0)
        self.assertEqual(modname, 'very.multi.utils')
        modname = mod.relative_to_absolute_name('utils', 1)
        self.assertEqual(modname, 'very.multi.utils')
        modname = mod.relative_to_absolute_name('utils', 2)
        self.assertEqual(modname, 'very.utils')
        modname = mod.relative_to_absolute_name('', 1)
        self.assertEqual(modname, 'very.multi')

    def test_import_1(self):
        data = '''from . import subpackage'''
        astng = abuilder.string_build(data, 'package', join(REGRTEST_DATA, 'package', '__init__.py'))
        sys.path.insert(1, REGRTEST_DATA)
        try:
            m = astng.import_module('', level=1)
            self.assertEqual(m.name, 'package')
            infered = list(astng.igetattr('subpackage'))
            self.assertEqual(len(infered), 1)
            self.assertEqual(infered[0].name, 'package.subpackage')
        finally:
            del sys.path[1]


    def test_import_2(self):
        data = '''from . import subpackage as pouet'''
        astng = abuilder.string_build(data, 'package', join(dirname(abspath(__file__)), 'regrtest_data', 'package', '__init__.py'))
        sys.path.insert(1, REGRTEST_DATA)
        try:
            m = astng.import_module('', level=1)
            self.assertEqual(m.name, 'package')
            infered = list(astng.igetattr('pouet'))
            self.assertEqual(len(infered), 1)
            self.assertEqual(infered[0].name, 'package.subpackage')
        finally:
            del sys.path[1]


class FunctionNodeTC(TestCase):

    def test_special_attributes(self):
        func = MODULE2['make_class']
        self.assertEqual(len(func.getattr('__name__')), 1)
        self.assertIsInstance(func.getattr('__name__')[0], nodes.Const)
        self.assertEqual(func.getattr('__name__')[0].value, 'make_class')
        self.assertEqual(len(func.getattr('__doc__')), 1)
        self.assertIsInstance(func.getattr('__doc__')[0], nodes.Const)
        self.assertEqual(func.getattr('__doc__')[0].value, 'check base is correctly resolved to Concrete0')
        self.assertEqual(len(MODULE.getattr('__dict__')), 1)
        self.assertIsInstance(MODULE.getattr('__dict__')[0], nodes.Dict)

    def test_dict_interface(self):
        _test_dict_interface(self, MODULE['global_access'], 'local')

    def test_default_value(self):
        func = MODULE2['make_class']
        self.assertIsInstance(func.args.default_value('base'), nodes.Getattr)
        self.assertRaises(scoped_nodes.NoDefault, func.args.default_value, 'args')
        self.assertRaises(scoped_nodes.NoDefault, func.args.default_value, 'kwargs')
        self.assertRaises(scoped_nodes.NoDefault, func.args.default_value, 'any')
        #self.assertIsInstance(func.mularg_class('args'), nodes.Tuple)
        #self.assertIsInstance(func.mularg_class('kwargs'), nodes.Dict)
        #self.assertEqual(func.mularg_class('base'), None)

    def test_navigation(self):
        function = MODULE['global_access']
        self.assertEqual(function.statement(), function)
        l_sibling = function.previous_sibling()
        # check taking parent if child is not a stmt
        self.assertIsInstance(l_sibling, nodes.Assign)
        child = function.args.args[0]
        self.assert_(l_sibling is child.previous_sibling())
        r_sibling = function.next_sibling()
        self.assertIsInstance(r_sibling, nodes.Class)
        self.assertEqual(r_sibling.name, 'YO')
        self.assert_(r_sibling is child.next_sibling())
        last = r_sibling.next_sibling().next_sibling().next_sibling()
        self.assertIsInstance(last, nodes.Assign)
        self.assertEqual(last.next_sibling(), None)
        first = l_sibling.previous_sibling().previous_sibling().previous_sibling().previous_sibling().previous_sibling()
        self.assertEqual(first.previous_sibling(), None)

    def test_nested_args(self):
        if sys.version_info >= (3, 0):
            self.skipTest("nested args has been removed in py3.x")
        code = '''
def nested_args(a, (b, c, d)):
    "nested arguments test"
        '''
        tree = abuilder.string_build(code)
        func = tree['nested_args']
        self.assertEqual(sorted(func.locals), ['a', 'b', 'c', 'd'])
        self.assertEqual(func.args.format_args(), 'a, (b, c, d)')

    def test_four_args(self):
        func = MODULE['four_args']
        #self.assertEqual(func.args.args, ['a', ('b', 'c', 'd')])
        local = sorted(func.keys())
        self.assertEqual(local, ['a', 'b', 'c', 'd'])
        self.assertEqual(func.type, 'function')

    def test_format_args(self):
        func = MODULE2['make_class']
        self.assertEqual(func.args.format_args(), 'any, base=data.module.YO, *args, **kwargs')
        func = MODULE['four_args']
        self.assertEqual(func.args.format_args(), 'a, b, c, d')

    def test_is_abstract(self):
        method = MODULE2['AbstractClass']['to_override']
        self.assert_(method.is_abstract(pass_is_abstract=False))
        self.failUnlessEqual(method.qname(), 'data.module2.AbstractClass.to_override')
        self.failUnlessEqual(method.pytype(), '%s.instancemethod' % BUILTINS_MODULE)
        method = MODULE2['AbstractClass']['return_something']
        self.assert_(not method.is_abstract(pass_is_abstract=False))
        # non regression : test raise "string" doesn't cause an exception in is_abstract
        func = MODULE2['raise_string']
        self.assert_(not func.is_abstract(pass_is_abstract=False))

##     def test_raises(self):
##         method = MODULE2['AbstractClass']['to_override']
##         self.assertEqual([str(term) for term in method.raises()],
##                           ["CallFunc(Name('NotImplementedError'), [], None, None)"] )

##     def test_returns(self):
##         method = MODULE2['AbstractClass']['return_something']
##         # use string comp since Node doesn't handle __cmp__
##         self.assertEqual([str(term) for term in method.returns()],
##                           ["Const('toto')", "Const(None)"])

    def test_lambda_pytype(self):
        data = '''
def f():
        g = lambda: None
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        g = list(astng['f'].ilookup('g'))[0]
        self.failUnlessEqual(g.pytype(), '%s.function' % BUILTINS_MODULE)

    def test_lambda_qname(self):
        astng = abuilder.string_build('''
lmbd = lambda: None
''', __name__, __file__)
        self.assertEqual('%s.<lambda>' % __name__, astng['lmbd'].parent.value.qname())

    def test_is_method(self):
        data = '''
class A:
    def meth1(self):
        return 1
    @classmethod
    def meth2(cls):
        return 2
    @staticmethod
    def meth3():
        return 3

def function():
    return 0

@staticmethod
def sfunction():
    return -1
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        self.failUnless(astng['A']['meth1'].is_method())
        self.failUnless(astng['A']['meth2'].is_method())
        self.failUnless(astng['A']['meth3'].is_method())
        self.failIf(astng['function'].is_method())
        self.failIf(astng['sfunction'].is_method())

    def test_argnames(self):
        if sys.version_info < (3, 0):
            code = 'def f(a, (b, c), *args, **kwargs): pass'
        else:
            code = 'def f(a, b, c, *args, **kwargs): pass'
        astng = abuilder.string_build(code, __name__, __file__)
        self.assertEqual(astng['f'].argnames(), ['a', 'b', 'c', 'args', 'kwargs'])

    def test_return_nothing(self):
        """test infered value on a function with empty return"""
        data = '''
def func():
    return

a = func()
'''
        astng = abuilder.string_build(data, __name__, __file__)
        call = astng.body[1].value
        func_vals = call.infered()
        self.assertEqual(len(func_vals), 1)
        self.assertIsInstance(func_vals[0], nodes.Const)
        self.assertEqual(func_vals[0].value, None)

    def test_func_instance_attr(self):
        """test instance attributes for functions"""
        data= """
def test():
    print(test.bar)

test.bar = 1
test()
        """
        astng = abuilder.string_build(data, 'mod', __file__)
        func = astng.body[2].value.func.infered()[0]
        self.assertIsInstance(func, nodes.Function)
        self.assertEqual(func.name, 'test')
        one = func.getattr('bar')[0].infered()[0]
        self.assertIsInstance(one, nodes.Const)
        self.assertEqual(one.value, 1)


class ClassNodeTC(TestCase):

    def test_dict_interface(self):
        _test_dict_interface(self, MODULE['YOUPI'], 'method')

    def test_cls_special_attributes_1(self):
        cls = MODULE['YO']
        self.assertEqual(len(cls.getattr('__bases__')), 1)
        self.assertEqual(len(cls.getattr('__name__')), 1)
        self.assertIsInstance(cls.getattr('__name__')[0], nodes.Const)
        self.assertEqual(cls.getattr('__name__')[0].value, 'YO')
        self.assertEqual(len(cls.getattr('__doc__')), 1)
        self.assertIsInstance(cls.getattr('__doc__')[0], nodes.Const)
        self.assertEqual(cls.getattr('__doc__')[0].value, 'hehe')
        self.assertEqual(len(cls.getattr('__module__')), 1)
        self.assertIsInstance(cls.getattr('__module__')[0], nodes.Const)
        self.assertEqual(cls.getattr('__module__')[0].value, 'data.module')
        self.assertEqual(len(cls.getattr('__dict__')), 1)
        self.assertRaises(NotFoundError, cls.getattr, '__mro__')
        for cls in (nodes.List._proxied, nodes.Const(1)._proxied):
            self.assertEqual(len(cls.getattr('__bases__')), 1)
            self.assertEqual(len(cls.getattr('__name__')), 1)
            self.assertEqual(len(cls.getattr('__doc__')), 1, (cls, cls.getattr('__doc__')))
            self.assertEqual(cls.getattr('__doc__')[0].value, cls.doc)
            self.assertEqual(len(cls.getattr('__module__')), 1)
            self.assertEqual(len(cls.getattr('__dict__')), 1)
            self.assertEqual(len(cls.getattr('__mro__')), 1)

    def test_cls_special_attributes_2(self):
        astng = abuilder.string_build('''
class A: pass
class B: pass

A.__bases__ += (B,)
''', __name__, __file__)
        self.assertEqual(len(astng['A'].getattr('__bases__')), 2)
        self.assertIsInstance(astng['A'].getattr('__bases__')[0], nodes.Tuple)
        self.assertIsInstance(astng['A'].getattr('__bases__')[1], nodes.AssAttr)

    def test_instance_special_attributes(self):
        for inst in (Instance(MODULE['YO']), nodes.List(), nodes.Const(1)):
            self.assertRaises(NotFoundError, inst.getattr, '__mro__')
            self.assertRaises(NotFoundError, inst.getattr, '__bases__')
            self.assertRaises(NotFoundError, inst.getattr, '__name__')
            self.assertEqual(len(inst.getattr('__dict__')), 1)
            self.assertEqual(len(inst.getattr('__doc__')), 1)

    def test_navigation(self):
        klass = MODULE['YO']
        self.assertEqual(klass.statement(), klass)
        l_sibling = klass.previous_sibling()
        self.assert_(isinstance(l_sibling, nodes.Function), l_sibling)
        self.assertEqual(l_sibling.name, 'global_access')
        r_sibling = klass.next_sibling()
        self.assertIsInstance(r_sibling, nodes.Class)
        self.assertEqual(r_sibling.name, 'YOUPI')

    def test_local_attr_ancestors(self):
        klass2 = MODULE['YOUPI']
        it = klass2.local_attr_ancestors('__init__')
        anc_klass = it.next()
        self.assertIsInstance(anc_klass, nodes.Class)
        self.assertEqual(anc_klass.name, 'YO')
        self.assertRaises(StopIteration, it.next)
        it = klass2.local_attr_ancestors('method')
        self.assertRaises(StopIteration, it.next)

    def test_instance_attr_ancestors(self):
        klass2 = MODULE['YOUPI']
        it = klass2.instance_attr_ancestors('yo')
        anc_klass = it.next()
        self.assertIsInstance(anc_klass, nodes.Class)
        self.assertEqual(anc_klass.name, 'YO')
        self.assertRaises(StopIteration, it.next)
        klass2 = MODULE['YOUPI']
        it = klass2.instance_attr_ancestors('member')
        self.assertRaises(StopIteration, it.next)

    def test_methods(self):
        klass2 = MODULE['YOUPI']
        methods = sorted([m.name for m in klass2.methods()])
        self.assertEqual(methods, ['__init__', 'class_method',
                                   'method', 'static_method'])
        methods = [m.name for m in klass2.mymethods()]
        methods.sort()
        self.assertEqual(methods, ['__init__', 'class_method',
                                   'method', 'static_method'])
        klass2 = MODULE2['Specialization']
        methods = [m.name for m in klass2.mymethods()]
        methods.sort()
        self.assertEqual(methods, [])
        method_locals = klass2.local_attr('method')
        self.assertEqual(len(method_locals), 1)
        self.assertEqual(method_locals[0].name, 'method')
        self.assertRaises(NotFoundError, klass2.local_attr, 'nonexistant')
        methods = [m.name for m in klass2.methods()]
        methods.sort()
        self.assertEqual(methods, ['__init__', 'class_method',
                                   'method', 'static_method'])

    #def test_rhs(self):
    #    my_dict = MODULE['MY_DICT']
    #    self.assertIsInstance(my_dict.rhs(), nodes.Dict)
    #    a = MODULE['YO']['a']
    #    value = a.rhs()
    #    self.assertIsInstance(value, nodes.Const)
    #    self.assertEqual(value.value, 1)

    def test_ancestors(self):
        klass = MODULE['YOUPI']
        ancs = [a.name for a in klass.ancestors()]
        self.assertEqual(ancs, ['YO'])
        klass = MODULE2['Specialization']
        ancs = [a.name for a in klass.ancestors()]
        self.assertEqual(ancs, ['YOUPI', 'YO'])

    def test_type(self):
        klass = MODULE['YOUPI']
        self.assertEqual(klass.type, 'class')
        klass = MODULE2['Metaclass']
        self.assertEqual(klass.type, 'metaclass')
        klass = MODULE2['MyException']
        self.assertEqual(klass.type, 'exception')
        klass = MODULE2['MyIFace']
        self.assertEqual(klass.type, 'interface')
        klass = MODULE2['MyError']
        self.assertEqual(klass.type, 'exception')

    def test_interfaces(self):
        for klass, interfaces in (('Concrete0', ['MyIFace']),
                                  ('Concrete1', ['MyIFace', 'AnotherIFace']),
                                  ('Concrete2', ['MyIFace', 'AnotherIFace']),
                                  ('Concrete23', ['MyIFace', 'AnotherIFace'])):
            klass = MODULE2[klass]
            self.assertEqual([i.name for i in klass.interfaces()],
                              interfaces)

    def test_concat_interfaces(self):
        astng = abuilder.string_build('''
class IMachin: pass

class Correct2:
    """docstring"""
    __implements__ = (IMachin,)

class BadArgument:
    """docstring"""
    __implements__ = (IMachin,)

class InterfaceCanNowBeFound:
    """docstring"""
    __implements__ = BadArgument.__implements__ + Correct2.__implements__

        ''')
        self.assertEqual([i.name for i in astng['InterfaceCanNowBeFound'].interfaces()],
                          ['IMachin'])

    def test_inner_classes(self):
        eee = NONREGR['Ccc']['Eee']
        self.assertEqual([n.name for n in eee.ancestors()], ['Ddd', 'Aaa', 'object'])


    def test_classmethod_attributes(self):
        data = '''
class WebAppObject(object):
    def registered(cls, application):
        cls.appli = application
        cls.schema = application.schema
        cls.config = application.config
        return cls
    registered = classmethod(registered)
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        cls = astng['WebAppObject']
        self.assertEqual(sorted(cls.locals.keys()),
                          ['appli', 'config', 'registered', 'schema'])


    def test_class_getattr(self):
        data = '''
class WebAppObject(object):
    appli = application
    appli += 2
    del self.appli
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        cls = astng['WebAppObject']
        # test del statement not returned by getattr
        self.assertEqual(len(cls.getattr('appli')), 2)


    def test_instance_getattr(self):
        data =         '''
class WebAppObject(object):
    def __init__(self, application):
        self.appli = application
        self.appli += 2
        del self.appli
         '''
        astng = abuilder.string_build(data, __name__, __file__)
        inst = Instance(astng['WebAppObject'])
        # test del statement not returned by getattr
        self.assertEqual(len(inst.getattr('appli')), 2)


    def test_instance_getattr_with_class_attr(self):
        data = '''
class Parent:
    aa = 1
    cc = 1

class Klass(Parent):
    aa = 0
    bb = 0

    def incr(self, val):
        self.cc = self.aa
        if val > self.aa:
            val = self.aa
        if val < self.bb:
            val = self.bb
        self.aa += val
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        inst = Instance(astng['Klass'])
        self.assertEqual(len(inst.getattr('aa')), 3, inst.getattr('aa'))
        self.assertEqual(len(inst.getattr('bb')), 1, inst.getattr('bb'))
        self.assertEqual(len(inst.getattr('cc')), 2, inst.getattr('cc'))


    def test_getattr_method_transform(self):
        data = '''
class Clazz(object):

    def m1(self, value):
        self.value = value
    m2 = m1

def func(arg1, arg2):
    "function that will be used as a method"
    return arg1.value + arg2

Clazz.m3 = func
inst = Clazz()
inst.m4 = func
        '''
        astng = abuilder.string_build(data, __name__, __file__)
        cls = astng['Clazz']
        # test del statement not returned by getattr
        for method in ('m1', 'm2', 'm3'):
            inferred = list(cls.igetattr(method))
            self.assertEqual(len(inferred), 1)
            self.assertIsInstance(inferred[0], UnboundMethod)
            inferred = list(Instance(cls).igetattr(method))
            self.assertEqual(len(inferred), 1)
            self.assertIsInstance(inferred[0], BoundMethod)
        inferred = list(Instance(cls).igetattr('m4'))
        self.assertEqual(len(inferred), 1)
        self.assertIsInstance(inferred[0], nodes.Function)

    def test_getattr_from_grandpa(self):
        data = '''
class Future:
    attr = 1

class Present(Future):
    pass

class Past(Present):
    pass
'''
        astng = abuilder.string_build(data)
        past = astng['Past']
        attr = past.getattr('attr')
        self.assertEqual(len(attr), 1)
        attr1 = attr[0]
        self.assertIsInstance(attr1, nodes.AssName)
        self.assertEqual(attr1.name, 'attr')

    def test_function_with_decorator_lineno(self):
        data = '''
@f(a=2,
   b=3)
def g1(x):
    print x

@f(a=2,
   b=3)
def g2():
    pass
'''
        astng = abuilder.string_build(data)
        self.assertEqual(astng['g1'].fromlineno, 4)
        self.assertEqual(astng['g1'].tolineno, 5)
        self.assertEqual(astng['g2'].fromlineno, 9)
        self.assertEqual(astng['g2'].tolineno, 10)


__all__ = ('ModuleNodeTC', 'ImportNodeTC', 'FunctionNodeTC', 'ClassNodeTC')

if __name__ == '__main__':
    unittest_main()
