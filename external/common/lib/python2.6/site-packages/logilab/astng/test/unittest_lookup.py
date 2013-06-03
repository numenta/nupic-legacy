# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
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

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""tests for the astng variable lookup capabilities
"""
import sys
from os.path import join, abspath, dirname
from logilab.common.testlib import TestCase, unittest_main

from logilab.astng import builder, nodes, scoped_nodes, \
     InferenceError, NotFoundError, UnresolvableName
from logilab.astng.scoped_nodes import builtin_lookup
from logilab.astng.bases import YES
from unittest_inference import get_name_node

builder = builder.ASTNGBuilder()
DATA = join(dirname(abspath(__file__)), 'data')
MODULE = builder.file_build(join(DATA, 'module.py'), 'data.module')
MODULE2 = builder.file_build(join(DATA, 'module2.py'), 'data.module2')
NONREGR = builder.file_build(join(DATA, 'nonregr.py'), 'data.nonregr')

class LookupTC(TestCase):

    def test_limit(self):
        code = '''
l = [a
     for a,b in list]

a = 1
b = a
a = None

def func():
    c = 1
        '''
        astng = builder.string_build(code, __name__, __file__)
        # a & b
        a = astng.nodes_of_class(nodes.Name).next()
        self.assertEqual(a.lineno, 2)
        if sys.version_info < (3, 0):
            self.failUnlessEqual(len(astng.lookup('b')[1]), 2)
            self.failUnlessEqual(len(astng.lookup('a')[1]), 3)
            b = astng.locals['b'][1]
        else:
            self.failUnlessEqual(len(astng.lookup('b')[1]), 1)
            self.failUnlessEqual(len(astng.lookup('a')[1]), 2)
            b = astng.locals['b'][0]
        stmts = a.lookup('a')[1]
        self.failUnlessEqual(len(stmts), 1)
        self.assertEqual(b.lineno, 6)
        b_infer = b.infer()
        b_value = b_infer.next()
        self.failUnlessEqual(b_value.value, 1)
        # c
        self.failUnlessRaises(StopIteration, b_infer.next)
        func = astng.locals['func'][0]
        self.failUnlessEqual(len(func.lookup('c')[1]), 1)

    def test_module(self):
        astng = builder.string_build('pass', __name__, __file__)
        # built-in objects
        none = astng.ilookup('None').next()
        self.assertEqual(none.value, None)
        obj = astng.ilookup('object').next()
        self.assertIsInstance(obj, nodes.Class)
        self.assertEqual(obj.name, 'object')
        self.assertRaises(InferenceError, astng.ilookup('YOAA').next)

        # XXX
        self.assertEqual(len(list(NONREGR.ilookup('enumerate'))), 2)

    def test_class_ancestor_name(self):
        code = '''
class A:
    pass

class A(A):
    pass
        '''
        astng = builder.string_build(code, __name__, __file__)
        cls1 = astng.locals['A'][0]
        cls2 = astng.locals['A'][1]
        name = cls2.nodes_of_class(nodes.Name).next()
        self.assertEqual(name.infer().next(), cls1)

    ### backport those test to inline code
    def test_method(self):
        method = MODULE['YOUPI']['method']
        my_dict = method.ilookup('MY_DICT').next()
        self.assert_(isinstance(my_dict, nodes.Dict), my_dict)
        none = method.ilookup('None').next()
        self.assertEqual(none.value, None)
        self.assertRaises(InferenceError, method.ilookup('YOAA').next)


    def test_function_argument_with_default(self):
        make_class = MODULE2['make_class']
        base = make_class.ilookup('base').next()
        self.assert_(isinstance(base, nodes.Class), base.__class__)
        self.assertEqual(base.name, 'YO')
        self.assertEqual(base.root().name, 'data.module')


    def test_class(self):
        klass = MODULE['YOUPI']
        my_dict = klass.ilookup('MY_DICT').next()
        self.assertIsInstance(my_dict, nodes.Dict)
        none = klass.ilookup('None').next()
        self.assertEqual(none.value, None)
        obj = klass.ilookup('object').next()
        self.assertIsInstance(obj, nodes.Class)
        self.assertEqual(obj.name, 'object')
        self.assertRaises(InferenceError, klass.ilookup('YOAA').next)


    def test_inner_classes(self):
        ddd = list(NONREGR['Ccc'].ilookup('Ddd'))
        self.assertEqual(ddd[0].name, 'Ddd')


    def test_loopvar_hiding(self):
        astng = builder.string_build("""
x = 10
for x in range(5):
    print (x)

if x > 0:
    print ('#' * x)
        """, __name__, __file__)
        xnames = [n for n in astng.nodes_of_class(nodes.Name) if n.name == 'x']
        # inside the loop, only one possible assignment
        self.assertEqual(len(xnames[0].lookup('x')[1]), 1)
        # outside the loop, two possible assignments
        self.assertEqual(len(xnames[1].lookup('x')[1]), 2)
        self.assertEqual(len(xnames[2].lookup('x')[1]), 2)

    def test_list_comps(self):
        astng = builder.string_build("""
print ([ i for i in range(10) ])
print ([ i for i in range(10) ])
print ( list( i for i in range(10) ) )
        """, __name__, __file__)
        xnames = [n for n in astng.nodes_of_class(nodes.Name) if n.name == 'i']
        self.assertEqual(len(xnames[0].lookup('i')[1]), 1)
        self.assertEqual(xnames[0].lookup('i')[1][0].lineno, 2)
        self.assertEqual(len(xnames[1].lookup('i')[1]), 1)
        self.assertEqual(xnames[1].lookup('i')[1][0].lineno, 3)
        self.assertEqual(len(xnames[2].lookup('i')[1]), 1)
        self.assertEqual(xnames[2].lookup('i')[1][0].lineno, 4)

    def test_list_comp_target(self):
        """test the list comprehension target"""
        astng = builder.string_build("""
ten = [ var for var in range(10) ]
var
        """)
        var = astng.body[1].value
        if sys.version_info < (3, 0):
            self.assertEqual(var.infered(), [YES])
        else:
            self.assertRaises(UnresolvableName, var.infered)


    def test_dict_comps(self):
        if sys.version_info < (2, 7):
            self.skipTest('this test require python >= 2.7')
        astng = builder.string_build("""
print ({ i: j for i in range(10) for j in range(10) })
print ({ i: j for i in range(10) for j in range(10) })
        """, __name__, __file__)
        xnames = [n for n in astng.nodes_of_class(nodes.Name) if n.name == 'i']
        self.assertEqual(len(xnames[0].lookup('i')[1]), 1)
        self.assertEqual(xnames[0].lookup('i')[1][0].lineno, 2)
        self.assertEqual(len(xnames[1].lookup('i')[1]), 1)
        self.assertEqual(xnames[1].lookup('i')[1][0].lineno, 3)

        xnames = [n for n in astng.nodes_of_class(nodes.Name) if n.name == 'j']
        self.assertEqual(len(xnames[0].lookup('i')[1]), 1)
        self.assertEqual(xnames[0].lookup('i')[1][0].lineno, 2)
        self.assertEqual(len(xnames[1].lookup('i')[1]), 1)
        self.assertEqual(xnames[1].lookup('i')[1][0].lineno, 3)


    def test_set_comps(self):
        if sys.version_info < (2, 7):
            self.skipTest('this test require python >= 2.7')
        astng = builder.string_build("""
print ({ i for i in range(10) })
print ({ i for i in range(10) })
        """, __name__, __file__)
        xnames = [n for n in astng.nodes_of_class(nodes.Name) if n.name == 'i']
        self.assertEqual(len(xnames[0].lookup('i')[1]), 1)
        self.assertEqual(xnames[0].lookup('i')[1][0].lineno, 2)
        self.assertEqual(len(xnames[1].lookup('i')[1]), 1)
        self.assertEqual(xnames[1].lookup('i')[1][0].lineno, 3)

    def test_set_comp_closure(self):
        if sys.version_info < (2, 7):
            self.skipTest('this test require python >= 2.7')
        astng = builder.string_build("""
ten = { var for var in range(10) }
var
        """)
        var = astng.body[1].value
        self.assertRaises(UnresolvableName, var.infered)

    def test_generator_attributes(self):
        tree = builder.string_build("""
def count():
    "ntesxt"
    yield 0

iterer = count()
num = iterer.next()
        """)
        next = tree.body[2].value.func # Getattr
        gener = next.expr.infered()[0] # Genrator
        # XXX gener._proxied is a Function which has no instance_attr
        self.assertRaises(AttributeError, gener.getattr, 'next')

    def test_explicit___name__(self):
        code = '''
class Pouet:
    __name__ = "pouet"
p1 = Pouet()

class PouetPouet(Pouet): pass
p2 = Pouet()

class NoName: pass
p3 = NoName()
'''
        astng = builder.string_build(code, __name__, __file__)
        p1 = astng['p1'].infer().next()
        self.failUnless(p1.getattr('__name__'))
        p2 = astng['p2'].infer().next()
        self.failUnless(p2.getattr('__name__'))
        self.failUnless(astng['NoName'].getattr('__name__'))
        p3 = astng['p3'].infer().next()
        self.assertRaises(NotFoundError, p3.getattr, '__name__')


    def test_function_module_special(self):
        astng = builder.string_build('''
def initialize(linter):
    """initialize linter with checkers in this package """
    package_load(linter, __path__[0])
        ''', 'data.__init__', 'data/__init__.py')
        path = [n for n in astng.nodes_of_class(nodes.Name) if n.name == '__path__'][0]
        self.assertEqual(len(path.lookup('__path__')[1]), 1)


    def test_builtin_lookup(self):
        self.assertEqual(builtin_lookup('__dict__')[1], ())
        intstmts = builtin_lookup('int')[1]
        self.assertEqual(len(intstmts), 1)
        self.assertIsInstance(intstmts[0], nodes.Class)
        self.assertEqual(intstmts[0].name, 'int')
        self.assertIs(intstmts[0], nodes.const_factory(1)._proxied)


    def test_decorator_arguments_lookup(self):
        code = '''
def decorator(value):
    def wrapper(function):
        return function
    return wrapper

class foo:
    member = 10

    @decorator(member) #This will cause pylint to complain
    def test(self):
        pass
        '''
        astng = builder.string_build(code, __name__, __file__)
        member = get_name_node(astng['foo'], 'member')
        it = member.infer()
        obj = it.next()
        self.assertIsInstance(obj, nodes.Const)
        self.assertEqual(obj.value, 10)
        self.assertRaises(StopIteration, it.next)


    def test_inner_decorator_member_lookup(self):
        code = '''
class FileA:
    def decorator(bla):
        return bla

    @decorator
    def funcA():
        return 4
        '''
        astng = builder.string_build(code, __name__, __file__)
        decname = get_name_node(astng['FileA'], 'decorator')
        it = decname.infer()
        obj = it.next()
        self.assertIsInstance(obj, nodes.Function)
        self.assertRaises(StopIteration, it.next)


    def test_static_method_lookup(self):
        code = '''
class FileA:
    @staticmethod
    def funcA():
        return 4


class Test:
    FileA = [1,2,3]

    def __init__(self):
        print (FileA.funcA())
        '''
        astng = builder.string_build(code, __name__, __file__)
        it = astng['Test']['__init__'].ilookup('FileA')
        obj = it.next()
        self.assertIsInstance(obj, nodes.Class)
        self.assertRaises(StopIteration, it.next)


    def test_global_delete(self):
        code = '''
def run2():
    f = Frobble()

class Frobble:
    pass
Frobble.mumble = True

del Frobble

def run1():
    f = Frobble()
'''
        astng = builder.string_build(code, __name__, __file__)
        stmts = astng['run2'].lookup('Frobbel')[1]
        self.failUnlessEqual(len(stmts), 0)
        stmts = astng['run1'].lookup('Frobbel')[1]
        self.failUnlessEqual(len(stmts), 0)

if __name__ == '__main__':
    unittest_main()
