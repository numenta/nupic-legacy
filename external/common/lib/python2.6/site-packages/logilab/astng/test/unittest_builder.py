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
"""tests for the astng builder and rebuilder module"""

import unittest
import sys
from os.path import join, abspath, dirname

from logilab.common.testlib import TestCase, unittest_main
from pprint import pprint

from logilab.astng import BUILTINS_MODULE, builder, nodes, InferenceError, NotFoundError
from logilab.astng.nodes import Module
from logilab.astng.bases import YES, BUILTINS_NAME
from logilab.astng.as_string import as_string
from logilab.astng.manager import ASTNGManager

MANAGER = ASTNGManager()


from unittest_inference import get_name_node

import data
from data import module as test_module

DATA = join(dirname(abspath(__file__)), 'data')

class FromToLineNoTC(TestCase):

    astng = builder.ASTNGBuilder().file_build(join(DATA, 'format.py'))

    def test_callfunc_lineno(self):
        stmts = self.astng.body
        # on line 4:
        #    function('aeozrijz\
        #    earzer', hop)
        discard = stmts[0]
        self.assertIsInstance(discard, nodes.Discard)
        self.assertEqual(discard.fromlineno, 4)
        self.assertEqual(discard.tolineno, 5)
        callfunc = discard.value
        self.assertIsInstance(callfunc, nodes.CallFunc)
        self.assertEqual(callfunc.fromlineno, 4)
        self.assertEqual(callfunc.tolineno, 5)
        name = callfunc.func
        self.assertIsInstance(name, nodes.Name)
        self.assertEqual(name.fromlineno, 4)
        self.assertEqual(name.tolineno, 4)
        strarg = callfunc.args[0]
        self.assertIsInstance(strarg, nodes.Const)
        self.assertEqual(strarg.fromlineno, 5) # no way for this one (is 4 actually)
        self.assertEqual(strarg.tolineno, 5)
        namearg = callfunc.args[1]
        self.assertIsInstance(namearg, nodes.Name)
        self.assertEqual(namearg.fromlineno, 5)
        self.assertEqual(namearg.tolineno, 5)
        # on line 10:
        #    fonction(1,
        #             2,
        #             3,
        #             4)
        discard = stmts[2]
        self.assertIsInstance(discard, nodes.Discard)
        self.assertEqual(discard.fromlineno, 10)
        self.assertEqual(discard.tolineno, 13)
        callfunc = discard.value
        self.assertIsInstance(callfunc, nodes.CallFunc)
        self.assertEqual(callfunc.fromlineno, 10)
        self.assertEqual(callfunc.tolineno, 13)
        name = callfunc.func
        self.assertIsInstance(name, nodes.Name)
        self.assertEqual(name.fromlineno, 10)
        self.assertEqual(name.tolineno, 10)
        for i, arg in enumerate(callfunc.args):
            self.assertIsInstance(arg, nodes.Const)
            self.assertEqual(arg.fromlineno, 10+i)
            self.assertEqual(arg.tolineno, 10+i)

    def test_function_lineno(self):
        stmts = self.astng.body
        # on line 15:
        #    def definition(a,
        #                   b,
        #                   c):
        #        return a + b + c
        function = stmts[3]
        self.assertIsInstance(function, nodes.Function)
        self.assertEqual(function.fromlineno, 15)
        self.assertEqual(function.tolineno, 18)
        return_ = function.body[0]
        self.assertIsInstance(return_, nodes.Return)
        self.assertEqual(return_.fromlineno, 18)
        self.assertEqual(return_.tolineno, 18)
        if sys.version_info < (3, 0):
            self.assertEqual(function.blockstart_tolineno, 17)
        else:
            self.skipTest('FIXME  http://bugs.python.org/issue10445 '
                          '(no line number on function args)')

    def test_decorated_function_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
@decorator
def function(
    arg):
    print (arg)
''', __name__, __file__)
        function = astng['function']
        self.assertEqual(function.fromlineno, 3) # XXX discussable, but that's what is expected by pylint right now
        self.assertEqual(function.tolineno, 5)
        self.assertEqual(function.decorators.fromlineno, 2)
        self.assertEqual(function.decorators.tolineno, 2)
        if sys.version_info < (3, 0):
            self.assertEqual(function.blockstart_tolineno, 4)
        else:
            self.skipTest('FIXME  http://bugs.python.org/issue10445 '
                          '(no line number on function args)')


    def test_class_lineno(self):
        stmts = self.astng.body
        # on line 20:
        #    class debile(dict,
        #                 object):
        #       pass
        class_ = stmts[4]
        self.assertIsInstance(class_, nodes.Class)
        self.assertEqual(class_.fromlineno, 20)
        self.assertEqual(class_.tolineno, 22)
        self.assertEqual(class_.blockstart_tolineno, 21)
        pass_ = class_.body[0]
        self.assertIsInstance(pass_, nodes.Pass)
        self.assertEqual(pass_.fromlineno, 22)
        self.assertEqual(pass_.tolineno, 22)

    def test_if_lineno(self):
        stmts = self.astng.body
        # on line 20:
        #    if aaaa: pass
        #    else:
        #        aaaa,bbbb = 1,2
        #        aaaa,bbbb = bbbb,aaaa
        if_ = stmts[5]
        self.assertIsInstance(if_, nodes.If)
        self.assertEqual(if_.fromlineno, 24)
        self.assertEqual(if_.tolineno, 27)
        self.assertEqual(if_.blockstart_tolineno, 24)
        self.assertEqual(if_.orelse[0].fromlineno, 26)
        self.assertEqual(if_.orelse[1].tolineno, 27)

    def test_for_while_lineno(self):
        for code in ('''
for a in range(4):
  print (a)
  break
else:
  print ("bouh")
''', '''
while a:
  print (a)
  break
else:
  print ("bouh")
''',
                     ):
            astng = builder.ASTNGBuilder().string_build(code, __name__, __file__)
            stmt = astng.body[0]
            self.assertEqual(stmt.fromlineno, 2)
            self.assertEqual(stmt.tolineno, 6)
            self.assertEqual(stmt.blockstart_tolineno, 2)
            self.assertEqual(stmt.orelse[0].fromlineno, 6) # XXX
            self.assertEqual(stmt.orelse[0].tolineno, 6)


    def test_try_except_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
try:
  print (a)
except:
  pass
else:
  print ("bouh")
''', __name__, __file__)
        try_ = astng.body[0]
        self.assertEqual(try_.fromlineno, 2)
        self.assertEqual(try_.tolineno, 7)
        self.assertEqual(try_.blockstart_tolineno, 2)
        self.assertEqual(try_.orelse[0].fromlineno, 7) # XXX
        self.assertEqual(try_.orelse[0].tolineno, 7)
        hdlr = try_.handlers[0]
        self.assertEqual(hdlr.fromlineno, 4)
        self.assertEqual(hdlr.tolineno, 5)
        self.assertEqual(hdlr.blockstart_tolineno, 4)


    def test_try_finally_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
try:
  print (a)
finally:
  print ("bouh")
''', __name__, __file__)
        try_ = astng.body[0]
        self.assertEqual(try_.fromlineno, 2)
        self.assertEqual(try_.tolineno, 5)
        self.assertEqual(try_.blockstart_tolineno, 2)
        self.assertEqual(try_.finalbody[0].fromlineno, 5) # XXX
        self.assertEqual(try_.finalbody[0].tolineno, 5)


    def test_try_finally_25_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
try:
  print (a)
except:
  pass
finally:
  print ("bouh")
''', __name__, __file__)
        try_ = astng.body[0]
        self.assertEqual(try_.fromlineno, 2)
        self.assertEqual(try_.tolineno, 7)
        self.assertEqual(try_.blockstart_tolineno, 2)
        self.assertEqual(try_.finalbody[0].fromlineno, 7) # XXX
        self.assertEqual(try_.finalbody[0].tolineno, 7)


    def test_with_lineno(self):
        astng = builder.ASTNGBuilder().string_build('''
from __future__ import with_statement
with file("/tmp/pouet") as f:
    print (f)
''', __name__, __file__)
        with_ = astng.body[1]
        self.assertEqual(with_.fromlineno, 3)
        self.assertEqual(with_.tolineno, 4)
        self.assertEqual(with_.blockstart_tolineno, 3)



class BuilderTC(TestCase):

    def setUp(self):
        self.builder = builder.ASTNGBuilder()

    def test_border_cases(self):
        """check that a file with no trailing new line is parseable"""
        self.builder.file_build(join(DATA, 'noendingnewline.py'), 'data.noendingnewline')
        self.assertRaises(builder.ASTNGBuildingException,
                          self.builder.file_build, join(DATA, 'inexistant.py'), 'whatever')

    def test_inspect_build0(self):
        """test astng tree build from a living object"""
        builtin_astng = MANAGER.astng_from_module_name(BUILTINS_NAME)
        if sys.version_info < (3, 0):
            fclass = builtin_astng['file']
            self.assert_('name' in fclass)
            self.assert_('mode' in fclass)
            self.assert_('read' in fclass)
            self.assert_(fclass.newstyle)
            self.assert_(fclass.pytype(), '%s.type' % BUILTINS_MODULE)
            self.assertIsInstance(fclass['read'], nodes.Function)
            # check builtin function has args.args == None
            dclass = builtin_astng['dict']
            self.assertEqual(dclass['has_key'].args.args, None)
        # just check type and object are there
        builtin_astng.getattr('type')
        objectastng = builtin_astng.getattr('object')[0]
        self.assertIsInstance(objectastng.getattr('__new__')[0], nodes.Function)
        # check open file alias
        builtin_astng.getattr('open')
        # check 'help' is there (defined dynamically by site.py)
        builtin_astng.getattr('help')
        # check property has __init__
        pclass = builtin_astng['property']
        self.assert_('__init__' in pclass)
        self.assertIsInstance(builtin_astng['None'], nodes.Const)
        self.assertIsInstance(builtin_astng['True'], nodes.Const)
        self.assertIsInstance(builtin_astng['False'], nodes.Const)
        if sys.version_info < (3, 0):
            self.assertIsInstance(builtin_astng['Exception'], nodes.From)
            self.assertIsInstance(builtin_astng['NotImplementedError'], nodes.From)
        else:
            self.assertIsInstance(builtin_astng['Exception'], nodes.Class)
            self.assertIsInstance(builtin_astng['NotImplementedError'], nodes.Class)

    def test_inspect_build1(self):
        time_astng = MANAGER.astng_from_module_name('time')
        self.assert_(time_astng)
        self.assertEqual(time_astng['time'].args.defaults, [])

    def test_inspect_build2(self):
        """test astng tree build from a living object"""
        try:
            from mx import DateTime
        except ImportError:
            self.skipTest('test skipped: mxDateTime is not available')
        else:
            dt_astng = self.builder.inspect_build(DateTime)
            dt_astng.getattr('DateTime')
            # this one is failing since DateTimeType.__module__ = 'builtins' !
            #dt_astng.getattr('DateTimeType')

    def test_inspect_build3(self):
        self.builder.inspect_build(unittest)

    def test_inspect_build_instance(self):
        """test astng tree build from a living object"""
        if sys.version_info >= (3, 0):
            self.skipTest('The module "exceptions" is gone in py3.x')
        import exceptions
        builtin_astng = self.builder.inspect_build(exceptions)
        fclass = builtin_astng['OSError']
        # things like OSError.strerror are now (2.5) data descriptors on the
        # class instead of entries in the __dict__ of an instance
        container = fclass
        self.assert_('errno' in container)
        self.assert_('strerror' in container)
        self.assert_('filename' in container)

    def test_inspect_build_type_object(self):
        builtin_astng = MANAGER.astng_from_module_name(BUILTINS_NAME)

        infered = list(builtin_astng.igetattr('object'))
        self.assertEqual(len(infered), 1)
        infered = infered[0]
        self.assertEqual(infered.name, 'object')
        as_string(infered)

        infered = list(builtin_astng.igetattr('type'))
        self.assertEqual(len(infered), 1)
        infered = infered[0]
        self.assertEqual(infered.name, 'type')
        as_string(infered)

    def test_package_name(self):
        """test base properties and method of a astng module"""
        datap = self.builder.file_build(join(DATA, '__init__.py'), 'data')
        self.assertEqual(datap.name, 'data')
        self.assertEqual(datap.package, 1)
        datap = self.builder.file_build(join(DATA, '__init__.py'), 'data.__init__')
        self.assertEqual(datap.name, 'data')
        self.assertEqual(datap.package, 1)

    def test_yield_parent(self):
        """check if we added discard nodes as yield parent (w/ compiler)"""
        data = """
def yiell():
    yield 0
    if noe:
        yield more
"""
        func = self.builder.string_build(data).body[0]
        self.assertIsInstance(func, nodes.Function)
        stmt = func.body[0]
        self.assertIsInstance(stmt, nodes.Discard)
        self.assertIsInstance(stmt.value, nodes.Yield)
        self.assertIsInstance(func.body[1].body[0], nodes.Discard)
        self.assertIsInstance(func.body[1].body[0].value, nodes.Yield)

    def test_object(self):
        obj_astng = self.builder.inspect_build(object)
        self.failUnless('__setattr__' in obj_astng)

    def test_newstyle_detection(self):
        data = '''
class A:
    "old style"

class B(A):
    "old style"

class C(object):
    "new style"

class D(C):
    "new style"

__metaclass__ = type

class E(A):
    "old style"

class F:
    "new style"
'''
        mod_astng = self.builder.string_build(data, __name__, __file__)
        self.failIf(mod_astng['A'].newstyle)
        self.failIf(mod_astng['B'].newstyle)
        self.failUnless(mod_astng['C'].newstyle)
        self.failUnless(mod_astng['D'].newstyle)
        self.failIf(mod_astng['E'].newstyle)
        self.failUnless(mod_astng['F'].newstyle)

    def test_globals(self):
        data = '''
CSTE = 1

def update_global():
    global CSTE
    CSTE += 1

def global_no_effect():
    global CSTE2
    print (CSTE)
'''
        astng = self.builder.string_build(data, __name__, __file__)
        self.failUnlessEqual(len(astng.getattr('CSTE')), 2)
        self.assertIsInstance(astng.getattr('CSTE')[0], nodes.AssName)
        self.failUnlessEqual(astng.getattr('CSTE')[0].fromlineno, 2)
        self.failUnlessEqual(astng.getattr('CSTE')[1].fromlineno, 6)
        self.assertRaises(NotFoundError,
                          astng.getattr, 'CSTE2')
        self.assertRaises(InferenceError,
                          astng['global_no_effect'].ilookup('CSTE2').next)

    def test_socket_build(self):
        import socket
        astng = self.builder.module_build(socket)
        # XXX just check the first one. Actually 3 objects are inferred (look at
        # the socket module) but the last one as those attributes dynamically
        # set and astng is missing this.
        for fclass in astng.igetattr('socket'):
            #print fclass.root().name, fclass.name, fclass.lineno
            self.assert_('connect' in fclass)
            self.assert_('send' in fclass)
            self.assert_('close' in fclass)
            break

    def test_gen_expr_var_scope(self):
        data = 'l = list(n for n in range(10))\n'
        astng = self.builder.string_build(data, __name__, __file__)
        # n unavailable outside gen expr scope
        self.failIf('n' in astng)
        # test n is inferable anyway
        n = get_name_node(astng, 'n')
        self.failIf(n.scope() is astng)
        self.failUnlessEqual([i.__class__ for i in n.infer()],
                             [YES.__class__])

class FileBuildTC(TestCase):

    module = builder.ASTNGBuilder().file_build(join(DATA, 'module.py'), 'data.module')

    def test_module_base_props(self):
        """test base properties and method of a astng module"""
        module = self.module
        self.assertEqual(module.name, 'data.module')
        self.assertEqual(module.doc, "test module for astng\n")
        self.assertEqual(module.fromlineno, 0)
        self.assertEqual(module.parent, None)
        self.assertEqual(module.frame(), module)
        self.assertEqual(module.root(), module)
        self.assertEqual(module.file, join(abspath(data.__path__[0]), 'module.py'))
        self.assertEqual(module.pure_python, 1)
        self.assertEqual(module.package, 0)
        self.assert_(not module.is_statement)
        self.assertEqual(module.statement(), module)
        self.assertEqual(module.statement(), module)

    def test_module_locals(self):
        """test the 'locals' dictionary of a astng module"""
        module = self.module
        _locals = module.locals
        self.assert_(_locals is module.globals)
        keys = sorted(_locals.keys())
        should = ['MY_DICT', 'YO', 'YOUPI',
                '__revision__',  'global_access','modutils', 'four_args',
                 'os', 'redirect', 'spawn', 'LocalsVisitor', 'ASTWalker']
        should.sort()
        self.assertEqual(keys, should)

    def test_function_base_props(self):
        """test base properties and method of a astng function"""
        module = self.module
        function = module['global_access']
        self.assertEqual(function.name, 'global_access')
        self.assertEqual(function.doc, 'function test')
        self.assertEqual(function.fromlineno, 11)
        self.assert_(function.parent)
        self.assertEqual(function.frame(), function)
        self.assertEqual(function.parent.frame(), module)
        self.assertEqual(function.root(), module)
        self.assertEqual([n.name for n in function.args.args], ['key', 'val'])
        self.assertEqual(function.type, 'function')

    def test_function_locals(self):
        """test the 'locals' dictionary of a astng function"""
        _locals = self.module['global_access'].locals
        self.assertEqual(len(_locals), 4)
        keys = sorted(_locals.keys())
        self.assertEqual(keys, ['i', 'key', 'local', 'val'])

    def test_class_base_props(self):
        """test base properties and method of a astng class"""
        module = self.module
        klass = module['YO']
        self.assertEqual(klass.name, 'YO')
        self.assertEqual(klass.doc, 'hehe')
        self.assertEqual(klass.fromlineno, 25)
        self.assert_(klass.parent)
        self.assertEqual(klass.frame(), klass)
        self.assertEqual(klass.parent.frame(), module)
        self.assertEqual(klass.root(), module)
        self.assertEqual(klass.basenames, [])
        self.assertEqual(klass.newstyle, False)

    def test_class_locals(self):
        """test the 'locals' dictionary of a astng class"""
        module = self.module
        klass1 = module['YO']
        locals1 = klass1.locals
        keys = sorted(locals1.keys())
        self.assertEqual(keys, ['__init__', 'a'])
        klass2 = module['YOUPI']
        locals2 = klass2.locals
        keys = locals2.keys()
        keys.sort()
        self.assertEqual(keys, ['__init__', 'class_attr', 'class_method',
                                 'method', 'static_method'])

    def test_class_instance_attrs(self):
        module = self.module
        klass1 = module['YO']
        klass2 = module['YOUPI']
        self.assertEqual(klass1.instance_attrs.keys(), ['yo'])
        self.assertEqual(klass2.instance_attrs.keys(), ['member'])

    def test_class_basenames(self):
        module = self.module
        klass1 = module['YO']
        klass2 = module['YOUPI']
        self.assertEqual(klass1.basenames, [])
        self.assertEqual(klass2.basenames, ['YO'])

    def test_method_base_props(self):
        """test base properties and method of a astng method"""
        klass2 = self.module['YOUPI']
        # "normal" method
        method = klass2['method']
        self.assertEqual(method.name, 'method')
        self.assertEqual([n.name for n in method.args.args], ['self'])
        self.assertEqual(method.doc, 'method test')
        self.assertEqual(method.fromlineno, 47)
        self.assertEqual(method.type, 'method')
        # class method
        method = klass2['class_method']
        self.assertEqual([n.name for n in method.args.args], ['cls'])
        self.assertEqual(method.type, 'classmethod')
        # static method
        method = klass2['static_method']
        self.assertEqual(method.args.args, [])
        self.assertEqual(method.type, 'staticmethod')

    def test_method_locals(self):
        """test the 'locals' dictionary of a astng method"""
        method = self.module['YOUPI']['method']
        _locals = method.locals
        keys = sorted(_locals)
        if sys.version_info < (3, 0):
            self.assertEqual(len(_locals), 5)
            self.assertEqual(keys, ['a', 'autre', 'b', 'local', 'self'])
        else:# ListComp variables are no more accessible outside
            self.assertEqual(len(_locals), 3)
            self.assertEqual(keys, ['autre', 'local', 'self'])


class ModuleBuildTC(FileBuildTC):

    def setUp(self):
        abuilder = builder.ASTNGBuilder()
        self.module = abuilder.module_build(test_module)


class MoreTC(TestCase):

    def setUp(self):
        self.builder = builder.ASTNGBuilder()

    def test_infered_build(self):
        code = '''class A: pass
A.type = "class"

def A_ass_type(self):
    print (self)
A.ass_type = A_ass_type
    '''
        astng = self.builder.string_build(code)
        lclass = list(astng.igetattr('A'))
        self.assertEqual(len(lclass), 1)
        lclass = lclass[0]
        self.assert_('ass_type' in lclass.locals, lclass.locals.keys())
        self.assert_('type' in lclass.locals.keys())

    def test_augassign_attr(self):
        astng = self.builder.string_build("""class Counter:
    v = 0
    def inc(self):
        self.v += 1
        """, __name__, __file__)
        # Check self.v += 1 generate AugAssign(AssAttr(...)), not AugAssign(GetAttr(AssName...))

    def test_dumb_module(self):
        astng = self.builder.string_build("pouet")

    def test_infered_dont_pollute(self):
        code = '''
def func(a=None):
    a.custom_attr = 0
def func2(a={}):
    a.custom_attr = 0
    '''
        astng = self.builder.string_build(code)
        nonetype = nodes.const_factory(None)
        self.failIf('custom_attr' in nonetype.locals)
        self.failIf('custom_attr' in nonetype.instance_attrs)
        nonetype = nodes.const_factory({})
        self.failIf('custom_attr' in nonetype.locals)
        self.failIf('custom_attr' in nonetype.instance_attrs)


    def test_asstuple(self):
        code = 'a, b = range(2)'
        astng = self.builder.string_build(code)
        self.failUnless('b' in astng.locals)
        code = '''
def visit_if(self, node):
    node.test, body = node.tests[0]
'''
        astng = self.builder.string_build(code)
        self.failUnless('body' in astng['visit_if'].locals)

    def test_build_constants(self):
        '''test expected values of constants after rebuilding'''
        code = '''
def func():
    return None
    return
    return 'None'
'''
        astng = self.builder.string_build(code)
        none, nothing, chain = [ret.value for ret in astng.body[0].body]
        self.assertIsInstance(none, nodes.Const)
        self.assertEqual(none.value, None)
        self.assertEqual(nothing, None)
        self.assertIsInstance(chain, nodes.Const)
        self.assertEqual(chain.value, 'None')


    def test_lgc_classproperty(self):
        '''test expected values of constants after rebuilding'''
        code = '''
from logilab.common.decorators import classproperty

class A(object):
    @classproperty
    def hop(cls):
        return None
'''
        astng = self.builder.string_build(code)
        self.assertEqual(astng['A']['hop'].type, 'classmethod')


if sys.version_info < (3, 0):
    guess_encoding = builder._guess_encoding

    class TestGuessEncoding(TestCase):

        def testEmacs(self):
            e = guess_encoding('# -*- coding: UTF-8  -*-')
            self.failUnlessEqual(e, 'UTF-8')
            e = guess_encoding('# -*- coding:UTF-8 -*-')
            self.failUnlessEqual(e, 'UTF-8')
            e = guess_encoding('''
            ### -*- coding: ISO-8859-1  -*-
            ''')
            self.failUnlessEqual(e, 'ISO-8859-1')
            e = guess_encoding('''

            ### -*- coding: ISO-8859-1  -*-
            ''')
            self.failUnlessEqual(e, None)

        def testVim(self):
            e = guess_encoding('# vim:fileencoding=UTF-8')
            self.failUnlessEqual(e, 'UTF-8')
            e = guess_encoding('''
            ### vim:fileencoding=ISO-8859-1
            ''')
            self.failUnlessEqual(e, 'ISO-8859-1')
            e = guess_encoding('''

            ### vim:fileencoding= ISO-8859-1
            ''')
            self.failUnlessEqual(e, None)

        def test_wrong_coding(self):
            # setting "coding" varaible
            e = guess_encoding("coding = UTF-8")
            self.failUnlessEqual(e, None)
            # setting a dictionnary entry
            e = guess_encoding("coding:UTF-8")
            self.failUnlessEqual(e, None)
            # setting an arguement
            e = guess_encoding("def do_something(a_word_with_coding=None):")
            self.failUnlessEqual(e, None)


        def testUTF8(self):
            e = guess_encoding('\xef\xbb\xbf any UTF-8 data')
            self.failUnlessEqual(e, 'UTF-8')
            e = guess_encoding(' any UTF-8 data \xef\xbb\xbf')
            self.failUnlessEqual(e, None)

if __name__ == '__main__':
    unittest_main()
