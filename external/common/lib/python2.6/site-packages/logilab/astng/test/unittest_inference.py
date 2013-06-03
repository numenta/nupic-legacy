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
"""tests for the astng inference capabilities
"""
from os.path import join, dirname, abspath
import sys
from StringIO import StringIO
from logilab.common.testlib import TestCase, unittest_main

from logilab.astng import InferenceError, builder, nodes
from logilab.astng.inference import infer_end as inference_infer_end
from logilab.astng.bases import YES, Instance, BoundMethod, UnboundMethod,\
                                path_wrapper, BUILTINS_NAME

def get_name_node(start_from, name, index=0):
    return [n for n in start_from.nodes_of_class(nodes.Name) if n.name == name][index]

def get_node_of_class(start_from, klass):
    return start_from.nodes_of_class(klass).next()

builder = builder.ASTNGBuilder()

class InferenceUtilsTC(TestCase):

    def test_path_wrapper(self):
        def infer_default(self, *args):
            raise InferenceError
        infer_default = path_wrapper(infer_default)
        infer_end = path_wrapper(inference_infer_end)
        self.failUnlessRaises(InferenceError,
                              infer_default(1).next)
        self.failUnlessEqual(infer_end(1).next(), 1)

if sys.version_info < (3, 0):
    EXC_MODULE = 'exceptions'
else:
    EXC_MODULE = BUILTINS_NAME

class InferenceTC(TestCase):

    CODE = '''

class C(object):
    "new style"
    attr = 4

    def meth1(self, arg1, optarg=0):
        var = object()
        print ("yo", arg1, optarg)
        self.iattr = "hop"
        return var

    def meth2(self):
        self.meth1(*self.meth3)

    def meth3(self, d=attr):
        b = self.attr
        c = self.iattr
        return b, c

ex = Exception("msg")
v = C().meth1(1)
m_unbound = C.meth1
m_bound = C().meth1
a, b, c = ex, 1, "bonjour"
[d, e, f] = [ex, 1.0, ("bonjour", v)]
g, h = f
i, (j, k) = "glup", f

a, b= b, a # Gasp !
'''

    astng = builder.string_build(CODE, __name__, __file__)

    def test_module_inference(self):
        infered = self.astng.infer()
        obj = infered.next()
        self.failUnlessEqual(obj.name, __name__)
        self.failUnlessEqual(obj.root().name, __name__)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_class_inference(self):
        infered = self.astng['C'].infer()
        obj = infered.next()
        self.failUnlessEqual(obj.name, 'C')
        self.failUnlessEqual(obj.root().name, __name__)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_function_inference(self):
        infered = self.astng['C']['meth1'].infer()
        obj = infered.next()
        self.failUnlessEqual(obj.name, 'meth1')
        self.failUnlessEqual(obj.root().name, __name__)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_builtin_name_inference(self):
        infered = self.astng['C']['meth1']['var'].infer()
        var = infered.next()
        self.failUnlessEqual(var.name, 'object')
        self.failUnlessEqual(var.root().name, BUILTINS_NAME)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_tupleassign_name_inference(self):
        infered = self.astng['a'].infer()
        exc = infered.next()
        self.assertIsInstance(exc, Instance)
        self.failUnlessEqual(exc.name, 'Exception')
        self.failUnlessEqual(exc.root().name, EXC_MODULE)
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['b'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, 1)
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['c'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, "bonjour")
        self.failUnlessRaises(StopIteration, infered.next)

    def test_listassign_name_inference(self):
        infered = self.astng['d'].infer()
        exc = infered.next()
        self.assertIsInstance(exc, Instance)
        self.failUnlessEqual(exc.name, 'Exception')
        self.failUnlessEqual(exc.root().name, EXC_MODULE)
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['e'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, 1.0)
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['f'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Tuple)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_advanced_tupleassign_name_inference1(self):
        infered = self.astng['g'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, "bonjour")
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['h'].infer()
        var = infered.next()
        self.failUnlessEqual(var.name, 'object')
        self.failUnlessEqual(var.root().name, BUILTINS_NAME)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_advanced_tupleassign_name_inference2(self):
        infered = self.astng['i'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, u"glup")
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['j'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, "bonjour")
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng['k'].infer()
        var = infered.next()
        self.failUnlessEqual(var.name, 'object')
        self.failUnlessEqual(var.root().name, BUILTINS_NAME)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_swap_assign_inference(self):
        infered = self.astng.locals['a'][1].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, 1)
        self.failUnlessRaises(StopIteration, infered.next)
        infered = self.astng.locals['b'][1].infer()
        exc = infered.next()
        self.assertIsInstance(exc, Instance)
        self.failUnlessEqual(exc.name, 'Exception')
        self.failUnlessEqual(exc.root().name, EXC_MODULE)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_getattr_inference1(self):
        infered = self.astng['ex'].infer()
        exc = infered.next()
        self.assertIsInstance(exc, Instance)
        self.failUnlessEqual(exc.name, 'Exception')
        self.failUnlessEqual(exc.root().name, EXC_MODULE)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_getattr_inference2(self):
        infered = get_node_of_class(self.astng['C']['meth2'], nodes.Getattr).infer()
        meth1 = infered.next()
        self.failUnlessEqual(meth1.name, 'meth1')
        self.failUnlessEqual(meth1.root().name, __name__)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_getattr_inference3(self):
        infered = self.astng['C']['meth3']['b'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, 4)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_getattr_inference4(self):
        infered = self.astng['C']['meth3']['c'].infer()
        const = infered.next()
        self.assertIsInstance(const, nodes.Const)
        self.failUnlessEqual(const.value, "hop")
        self.failUnlessRaises(StopIteration, infered.next)

    def test_callfunc_inference(self):
        infered = self.astng['v'].infer()
        meth1 = infered.next()
        self.assertIsInstance(meth1, Instance)
        self.failUnlessEqual(meth1.name, 'object')
        self.failUnlessEqual(meth1.root().name, BUILTINS_NAME)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_unbound_method_inference(self):
        infered = self.astng['m_unbound'].infer()
        meth1 = infered.next()
        self.assertIsInstance(meth1, UnboundMethod)
        self.failUnlessEqual(meth1.name, 'meth1')
        self.failUnlessEqual(meth1.parent.frame().name, 'C')
        self.failUnlessRaises(StopIteration, infered.next)

    def test_bound_method_inference(self):
        infered = self.astng['m_bound'].infer()
        meth1 = infered.next()
        self.assertIsInstance(meth1, BoundMethod)
        self.failUnlessEqual(meth1.name, 'meth1')
        self.failUnlessEqual(meth1.parent.frame().name, 'C')
        self.failUnlessRaises(StopIteration, infered.next)

    def test_args_default_inference1(self):
        optarg = get_name_node(self.astng['C']['meth1'], 'optarg')
        infered = optarg.infer()
        obj1 = infered.next()
        self.assertIsInstance(obj1, nodes.Const)
        self.failUnlessEqual(obj1.value, 0)
        obj1 = infered.next()
        self.assertIs(obj1, YES, obj1)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_args_default_inference2(self):
        infered = self.astng['C']['meth3'].ilookup('d')
        obj1 = infered.next()
        self.assertIsInstance(obj1, nodes.Const)
        self.failUnlessEqual(obj1.value, 4)
        obj1 = infered.next()
        self.assertIs(obj1, YES, obj1)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_inference_restrictions(self):
        infered = get_name_node(self.astng['C']['meth1'], 'arg1').infer()
        obj1 = infered.next()
        self.assertIs(obj1, YES, obj1)
        self.failUnlessRaises(StopIteration, infered.next)

    def test_ancestors_inference(self):
        code = '''
class A:
    pass

class A(A):
    pass
        '''
        astng = builder.string_build(code, __name__, __file__)
        a1 = astng.locals['A'][0]
        a2 = astng.locals['A'][1]
        a2_ancestors = list(a2.ancestors())
        self.failUnlessEqual(len(a2_ancestors), 1)
        self.failUnless(a2_ancestors[0] is a1)

    def test_ancestors_inference2(self):
        code = '''
class A:
    pass

class B(A): pass

class A(B):
    pass
        '''
        astng = builder.string_build(code, __name__, __file__)
        a1 = astng.locals['A'][0]
        a2 = astng.locals['A'][1]
        a2_ancestors = list(a2.ancestors())
        self.failUnlessEqual(len(a2_ancestors), 2)
        self.failUnless(a2_ancestors[0] is astng.locals['B'][0])
        self.failUnless(a2_ancestors[1] is a1, a2_ancestors[1])


    def test_f_arg_f(self):
        code = '''
def f(f=1):
    return f

a = f()
        '''
        astng = builder.string_build(code, __name__, __file__)
        a = astng['a']
        a_infered = a.infered()
        self.failUnlessEqual(a_infered[0].value, 1)
        self.assertEqual(len(a_infered), 1)

    def test_exc_ancestors(self):
        code = '''
def f():
    raise NotImplementedError
        '''
        astng = builder.string_build(code, __name__, __file__)
        error = astng.nodes_of_class(nodes.Name).next()
        nie = error.infered()[0]
        self.assertIsInstance(nie, nodes.Class)
        nie_ancestors = [c.name for c in nie.ancestors()]
        if sys.version_info < (3, 0):
            self.failUnlessEqual(nie_ancestors, ['RuntimeError', 'StandardError', 'Exception', 'BaseException', 'object'])
        else:
            self.failUnlessEqual(nie_ancestors, ['RuntimeError', 'Exception', 'BaseException', 'object'])

    def test_except_inference(self):
        code = '''
try:
    print (hop)
except NameError, ex:
    ex1 = ex
except Exception, ex:
    ex2 = ex
    raise
        '''
        if sys.version_info >= (3, 0):
            code = code.replace(', ex:', ' as ex:')
        astng = builder.string_build(code, __name__, __file__)
        ex1 = astng['ex1']
        ex1_infer = ex1.infer()
        ex1 = ex1_infer.next()
        self.assertIsInstance(ex1, Instance)
        self.failUnlessEqual(ex1.name, 'NameError')
        self.failUnlessRaises(StopIteration, ex1_infer.next)
        ex2 = astng['ex2']
        ex2_infer = ex2.infer()
        ex2 = ex2_infer.next()
        self.assertIsInstance(ex2, Instance)
        self.failUnlessEqual(ex2.name, 'Exception')
        self.failUnlessRaises(StopIteration, ex2_infer.next)

    def test_del1(self):
        code = '''
del undefined_attr
        '''
        delete = builder.string_build(code, __name__, __file__).body[0]
        self.failUnlessRaises(InferenceError, delete.infer)

    def test_del2(self):
        code = '''
a = 1
b = a
del a
c = a
a = 2
d = a
        '''
        astng = builder.string_build(code, __name__, __file__)
        n = astng['b']
        n_infer = n.infer()
        infered = n_infer.next()
        self.assertIsInstance(infered, nodes.Const)
        self.failUnlessEqual(infered.value, 1)
        self.failUnlessRaises(StopIteration, n_infer.next)
        n = astng['c']
        n_infer = n.infer()
        self.failUnlessRaises(InferenceError, n_infer.next)
        n = astng['d']
        n_infer = n.infer()
        infered = n_infer.next()
        self.assertIsInstance(infered, nodes.Const)
        self.failUnlessEqual(infered.value, 2)
        self.failUnlessRaises(StopIteration, n_infer.next)

    def test_builtin_types(self):
        code = '''
l = [1]
t = (2,)
d = {}
s = ''
s2 = '_'
        '''
        astng = builder.string_build(code, __name__, __file__)
        n = astng['l']
        infered = n.infer().next()
        self.assertIsInstance(infered, nodes.List)
        self.assertIsInstance(infered, Instance)
        self.failUnlessEqual(infered.getitem(0).value, 1)
        self.assertIsInstance(infered._proxied, nodes.Class)
        self.failUnlessEqual(infered._proxied.name, 'list')
        self.failUnless('append' in infered._proxied.locals)
        n = astng['t']
        infered = n.infer().next()
        self.assertIsInstance(infered, nodes.Tuple)
        self.assertIsInstance(infered, Instance)
        self.failUnlessEqual(infered.getitem(0).value, 2)
        self.assertIsInstance(infered._proxied, nodes.Class)
        self.failUnlessEqual(infered._proxied.name, 'tuple')
        n = astng['d']
        infered = n.infer().next()
        self.assertIsInstance(infered, nodes.Dict)
        self.assertIsInstance(infered, Instance)
        self.assertIsInstance(infered._proxied, nodes.Class)
        self.failUnlessEqual(infered._proxied.name, 'dict')
        self.failUnless('get' in infered._proxied.locals)
        n = astng['s']
        infered = n.infer().next()
        self.assertIsInstance(infered, nodes.Const)
        self.assertIsInstance(infered, Instance)
        self.failUnlessEqual(infered.name, 'str')
        self.failUnless('lower' in infered._proxied.locals)
        n = astng['s2']
        infered = n.infer().next()
        self.failUnlessEqual(infered.getitem(0).value, '_')

    def test_unicode_type(self):
        if sys.version_info >= (3, 0):
            self.skipTest('unicode removed on py >= 3.0')
        code = '''u = u""'''
        astng = builder.string_build(code, __name__, __file__)
        n = astng['u']
        infered = n.infer().next()
        self.assertIsInstance(infered, nodes.Const)
        self.assertIsInstance(infered, Instance)
        self.failUnlessEqual(infered.name, 'unicode')
        self.failUnless('lower' in infered._proxied.locals)

    def test_descriptor_are_callable(self):
        code = '''
class A:
    statm = staticmethod(open)
    clsm = classmethod('whatever')
        '''
        astng = builder.string_build(code, __name__, __file__)
        statm = astng['A'].igetattr('statm').next()
        self.failUnless(statm.callable())
        clsm = astng['A'].igetattr('clsm').next()
        self.failUnless(clsm.callable())

    def test_bt_ancestor_crash(self):
        code = '''
class Warning(Warning):
    pass
        '''
        astng = builder.string_build(code, __name__, __file__)
        w = astng['Warning']
        ancestors = w.ancestors()
        ancestor = ancestors.next()
        self.failUnlessEqual(ancestor.name, 'Warning')
        self.failUnlessEqual(ancestor.root().name, EXC_MODULE)
        ancestor = ancestors.next()
        self.failUnlessEqual(ancestor.name, 'Exception')
        self.failUnlessEqual(ancestor.root().name, EXC_MODULE)
        ancestor = ancestors.next()
        self.failUnlessEqual(ancestor.name, 'BaseException')
        self.failUnlessEqual(ancestor.root().name, EXC_MODULE)
        ancestor = ancestors.next()
        self.failUnlessEqual(ancestor.name, 'object')
        self.failUnlessEqual(ancestor.root().name, BUILTINS_NAME)
        self.failUnlessRaises(StopIteration, ancestors.next)

    def test_qqch(self):
        code = '''
from logilab.common.modutils import load_module_from_name
xxx = load_module_from_name('__pkginfo__')
        '''
        astng = builder.string_build(code, __name__, __file__)
        xxx = astng['xxx']
        self.assertSetEqual(set(n.__class__ for n in xxx.infered()),
                            set([nodes.Const, YES.__class__]))

    def test_method_argument(self):
        code = '''
class ErudiEntitySchema:
    """a entity has a type, a set of subject and or object relations"""
    def __init__(self, e_type, **kwargs):
        kwargs['e_type'] = e_type.capitalize().encode()

    def meth(self, e_type, *args, **kwargs):
        kwargs['e_type'] = e_type.capitalize().encode()
        print(args)
        '''
        astng = builder.string_build(code, __name__, __file__)
        arg = get_name_node(astng['ErudiEntitySchema']['__init__'], 'e_type')
        self.failUnlessEqual([n.__class__ for n in arg.infer()],
                             [YES.__class__])
        arg = get_name_node(astng['ErudiEntitySchema']['__init__'], 'kwargs')
        self.failUnlessEqual([n.__class__ for n in arg.infer()],
                             [nodes.Dict])
        arg = get_name_node(astng['ErudiEntitySchema']['meth'], 'e_type')
        self.failUnlessEqual([n.__class__ for n in arg.infer()],
                             [YES.__class__])
        arg = get_name_node(astng['ErudiEntitySchema']['meth'], 'args')
        self.failUnlessEqual([n.__class__ for n in arg.infer()],
                             [nodes.Tuple])
        arg = get_name_node(astng['ErudiEntitySchema']['meth'], 'kwargs')
        self.failUnlessEqual([n.__class__ for n in arg.infer()],
                             [nodes.Dict])


    def test_tuple_then_list(self):
        code = '''
def test_view(rql, vid, tags=()):
    tags = list(tags)
    tags.append(vid)
        '''
        astng = builder.string_build(code, __name__, __file__)
        name = get_name_node(astng['test_view'], 'tags', -1)
        it = name.infer()
        tags = it.next()
        self.failUnlessEqual(tags.__class__, Instance)
        self.failUnlessEqual(tags._proxied.name, 'list')
        self.failUnlessRaises(StopIteration, it.next)



    def test_mulassign_inference(self):
        code = '''

def first_word(line):
    """Return the first word of a line"""

    return line.split()[0]

def last_word(line):
    """Return last word of a line"""

    return line.split()[-1]

def process_line(word_pos):
    """Silly function: returns (ok, callable) based on argument.

       For test purpose only.
    """

    if word_pos > 0:
        return (True, first_word)
    elif word_pos < 0:
        return  (True, last_word)
    else:
        return (False, None)

if __name__ == '__main__':

    line_number = 0
    for a_line in file('test_callable.py'):
        tupletest  = process_line(line_number)
        (ok, fct)  = process_line(line_number)
        if ok:
            fct(a_line)
'''
        astng = builder.string_build(code, __name__, __file__)
        self.failUnlessEqual(len(list(astng['process_line'].infer_call_result(
                                                                None))), 3)
        self.failUnlessEqual(len(list(astng['tupletest'].infer())), 3)
        values = ['Function(first_word)', 'Function(last_word)', 'Const(NoneType)']
        self.failUnlessEqual([str(infered)
                              for infered in astng['fct'].infer()], values)

    def test_float_complex_ambiguity(self):
        code = '''
def no_conjugate_member(magic_flag):
    """should not raise E1101 on something.conjugate"""
    if magic_flag:
        something = 1.0
    else:
        something = 1.0j
    if isinstance(something, float):
        return something
    return something.conjugate()
        '''
        astng = builder.string_build(code, __name__, __file__)
        self.failUnlessEqual([i.value for i in
            astng['no_conjugate_member'].ilookup('something')], [1.0, 1.0j])
        self.failUnlessEqual([i.value for i in
                get_name_node(astng, 'something', -1).infer()], [1.0, 1.0j])

    def test_lookup_cond_branches(self):
        code = '''
def no_conjugate_member(magic_flag):
    """should not raise E1101 on something.conjugate"""
    something = 1.0
    if magic_flag:
        something = 1.0j
    return something.conjugate()
        '''
        astng = builder.string_build(code, __name__, __file__)
        self.failUnlessEqual([i.value for i in
                get_name_node(astng, 'something', -1).infer()], [1.0, 1.0j])


    def test_simple_subscript(self):
        code = '''
a = [1, 2, 3][0]
b = (1, 2, 3)[1]
c = (1, 2, 3)[-1]
d = a + b + c
print (d)
        '''
        astng = builder.string_build(code, __name__, __file__)
        self.failUnlessEqual([i.value for i in
                                get_name_node(astng, 'a', -1).infer()], [1])
        self.failUnlessEqual([i.value for i in
                                get_name_node(astng, 'b', -1).infer()], [2])
        self.failUnlessEqual([i.value for i in
                                get_name_node(astng, 'c', -1).infer()], [3])
        self.failUnlessEqual([i.value for i in
                                get_name_node(astng, 'd', -1).infer()], [6])

    #def test_simple_tuple(self):
        #"""test case for a simple tuple value"""
        ## XXX tuple inference is not implemented ...
        #code = """
#a = (1,)
#b = (22,)
#some = a + b
#"""
        #astng = builder.string_build(code, __name__, __file__)
        #self.failUnlessEqual(astng['some'].infer.next().as_string(), "(1, 22)")

    def test_simple_for(self):
        code = '''
for a in [1, 2, 3]:
    print (a)
for b,c in [(1,2), (3,4)]:
    print (b)
    print (c)

print ([(d,e) for e,d in ([1,2], [3,4])])
        '''
        astng = builder.string_build(code, __name__, __file__)
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'a', -1).infer()], [1, 2, 3])
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'b', -1).infer()], [1, 3])
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'c', -1).infer()], [2, 4])
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'd', -1).infer()], [2, 4])
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'e', -1).infer()], [1, 3])


    def test_simple_for_genexpr(self):
        code = '''
print ((d,e) for e,d in ([1,2], [3,4]))
        '''
        astng = builder.string_build(code, __name__, __file__)
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'd', -1).infer()], [2, 4])
        self.failUnlessEqual([i.value for i in
                            get_name_node(astng, 'e', -1).infer()], [1, 3])


    def test_builtin_help(self):
        code = '''
help()
        '''
        # XXX failing since __builtin__.help assignment has
        #     been moved into a function...
        astng = builder.string_build(code, __name__, __file__)
        node = get_name_node(astng, 'help', -1)
        infered = list(node.infer())
        self.failUnlessEqual(len(infered), 1, infered)
        self.assertIsInstance(infered[0], Instance)
        self.failUnlessEqual(str(infered[0]),
                             'Instance of site._Helper')

    def test_builtin_open(self):
        code = '''
open("toto.txt")
        '''
        astng = builder.string_build(code, __name__, __file__)
        node = get_name_node(astng, 'open', -1)
        infered = list(node.infer())
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Function)
        self.failUnlessEqual(infered[0].name, 'open')

    def test_callfunc_context_func(self):
        code = '''
def mirror(arg=None):
    return arg

un = mirror(1)
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng.igetattr('un'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Const)
        self.failUnlessEqual(infered[0].value, 1)

    def test_callfunc_context_lambda(self):
        code = '''
mirror = lambda x=None: x

un = mirror(1)
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng.igetattr('mirror'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Lambda)
        infered = list(astng.igetattr('un'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Const)
        self.failUnlessEqual(infered[0].value, 1)

    def test_factory_method(self):
        code = '''
class Super(object):
      @classmethod
      def instance(cls):
              return cls()

class Sub(Super):
      def method(self):
              print ('method called')

sub = Sub.instance()
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng.igetattr('sub'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], Instance)
        self.failUnlessEqual(infered[0]._proxied.name, 'Sub')


    def test_import_as(self):
        code = '''
import os.path as osp
print (osp.dirname(__file__))

from os.path import exists as e
assert e(__file__)

from new import code as make_code
print (make_code)
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng.igetattr('osp'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Module)
        self.failUnlessEqual(infered[0].name, 'os.path')
        infered = list(astng.igetattr('e'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Function)
        self.failUnlessEqual(infered[0].name, 'exists')
        if sys.version_info >= (3, 0):
            self.skipTest('<new> module has been removed')
        infered = list(astng.igetattr('make_code'))
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], Instance)
        self.failUnlessEqual(str(infered[0]),
                             'Instance of %s.type' % BUILTINS_NAME)

    def _test_const_infered(self, node, value):
        infered = list(node.infer())
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Const)
        self.failUnlessEqual(infered[0].value, value)

    def test_unary_not(self):
        for code in ('a = not (1,); b = not ()',
                     'a = not {1:2}; b = not {}'):
            astng = builder.string_build(code, __name__, __file__)
            self._test_const_infered(astng['a'], False)
            self._test_const_infered(astng['b'], True)

    def test_binary_op_int_add(self):
        astng = builder.string_build('a = 1 + 2', __name__, __file__)
        self._test_const_infered(astng['a'], 3)

    def test_binary_op_int_sub(self):
        astng = builder.string_build('a = 1 - 2', __name__, __file__)
        self._test_const_infered(astng['a'], -1)

    def test_binary_op_float_div(self):
        astng = builder.string_build('a = 1 / 2.', __name__, __file__)
        self._test_const_infered(astng['a'], 1 / 2.)

    def test_binary_op_str_mul(self):
        astng = builder.string_build('a = "*" * 40', __name__, __file__)
        self._test_const_infered(astng['a'], "*" * 40)

    def test_binary_op_bitand(self):
        astng = builder.string_build('a = 23&20', __name__, __file__)
        self._test_const_infered(astng['a'], 23&20)

    def test_binary_op_bitor(self):
        astng = builder.string_build('a = 23|8', __name__, __file__)
        self._test_const_infered(astng['a'], 23|8)

    def test_binary_op_bitxor(self):
        astng = builder.string_build('a = 23^9', __name__, __file__)
        self._test_const_infered(astng['a'], 23^9)

    def test_binary_op_shiftright(self):
        astng = builder.string_build('a = 23 >>1', __name__, __file__)
        self._test_const_infered(astng['a'], 23>>1)

    def test_binary_op_shiftleft(self):
        astng = builder.string_build('a = 23 <<1', __name__, __file__)
        self._test_const_infered(astng['a'], 23<<1)


    def test_binary_op_list_mul(self):
        for code in ('a = [[]] * 2', 'a = 2 * [[]]'):
            astng = builder.string_build(code, __name__, __file__)
            infered = list(astng['a'].infer())
            self.failUnlessEqual(len(infered), 1)
            self.assertIsInstance(infered[0], nodes.List)
            self.failUnlessEqual(len(infered[0].elts), 2)
            self.assertIsInstance(infered[0].elts[0], nodes.List)
            self.assertIsInstance(infered[0].elts[1], nodes.List)

    def test_binary_op_list_mul_none(self):
        'test correct handling on list multiplied by None'
        astng = builder.string_build( 'a = [1] * None\nb = [1] * "r"')
        infered = astng['a'].infered()
        self.assertEqual(len(infered), 1)
        self.assertEqual(infered[0], YES)
        infered = astng['b'].infered()
        self.assertEqual(len(infered), 1)
        self.assertEqual(infered[0], YES)


    def test_binary_op_tuple_add(self):
        astng = builder.string_build('a = (1,) + (2,)', __name__, __file__)
        infered = list(astng['a'].infer())
        self.failUnlessEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Tuple)
        self.failUnlessEqual(len(infered[0].elts), 2)
        self.failUnlessEqual(infered[0].elts[0].value, 1)
        self.failUnlessEqual(infered[0].elts[1].value, 2)

    def test_binary_op_custom_class(self):
        code = '''
class myarray:
    def __init__(self, array):
        self.array = array
    def __mul__(self, x):
        return myarray([2,4,6])
    def astype(self):
        return "ASTYPE"

def randint(maximum):
    if maximum is not None:
        return myarray([1,2,3]) * 2
    else:
        return int(5)

x = randint(1)
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng.igetattr('x'))
        self.failUnlessEqual(len(infered), 2)
        value = [str(v) for v in infered]
        # The __name__ trick here makes it work when invoked directly
        # (__name__ == '__main__') and through pytest (__name__ ==
        # 'unittest_inference')
        self.assertEqual(value, ['Instance of %s.myarray' % __name__,
                                 'Instance of %s.int' % BUILTINS_NAME])

    def test_nonregr_lambda_arg(self):
        code = '''
def f(g = lambda: None):
        g().x
'''
        astng = builder.string_build(code, __name__, __file__)
        callfuncnode = astng['f'].body[0].value.expr
        infered = list(callfuncnode.infer())
        self.failUnlessEqual(len(infered), 2, infered)
        infered.remove(YES)
        self.assertIsInstance(infered[0], nodes.Const)
        self.failUnlessEqual(infered[0].value, None)

    def test_nonregr_getitem_empty_tuple(self):
        code = '''
def f(x):
        a = ()[x]
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng['f'].ilookup('a'))
        self.failUnlessEqual(len(infered), 1)
        self.failUnlessEqual(infered[0], YES)

    def test_python25_generator_exit(self):
        sys.stderr = StringIO()
        data = "b = {}[str(0)+''].a"
        astng = builder.string_build(data, __name__, __file__)
        list(astng['b'].infer())
        output = sys.stderr.getvalue()
        # I have no idea how to test for this in another way...
        self.failIf("RuntimeError" in output, "Exception exceptions.RuntimeError: 'generator ignored GeneratorExit' in <generator object> ignored")
        sys.stderr = sys.__stderr__

    def test_python25_relative_import(self):
        data = "from ...common import date; print (date)"
        # !! FIXME also this relative import would not work 'in real' (no __init__.py in test/)
        # the test works since we pretend we have a package by passing the full modname
        astng = builder.string_build(data, 'logilab.astng.test.unittest_inference', __file__)
        infered = get_name_node(astng, 'date').infer().next()
        self.assertIsInstance(infered, nodes.Module)
        self.assertEqual(infered.name, 'logilab.common.date')

    def test_python25_no_relative_import(self):
        fname = join(abspath(dirname(__file__)), 'regrtest_data', 'package', 'absimport.py')
        astng = builder.file_build(fname, 'absimport')
        self.failUnless(astng.absolute_import_activated(), True)
        infered = get_name_node(astng, 'import_package_subpackage_module').infer().next()
        # failed to import since absolute_import is activated
        self.failUnless(infered is YES)

    def test_nonregr_absolute_import(self):
        fname = join(abspath(dirname(__file__)), 'regrtest_data', 'absimp', 'string.py')
        astng = builder.file_build(fname, 'absimp.string')
        self.failUnless(astng.absolute_import_activated(), True)
        infered = get_name_node(astng, 'string').infer().next()
        self.assertIsInstance(infered, nodes.Module)
        self.assertEqual(infered.name, 'string')
        self.failUnless('lower' in infered.locals)

    def test_mechanize_open(self):
        try:
            import mechanize
        except ImportError:
            self.skipTest('require mechanize installed')
        data = '''from mechanize import Browser
print (Browser)
b = Browser()
'''
        astng = builder.string_build(data, __name__, __file__)
        browser = get_name_node(astng, 'Browser').infer().next()
        self.assertIsInstance(browser, nodes.Class)
        bopen = list(browser.igetattr('open'))
        self.skipTest('the commit said: "huum, see that later"')
        self.assertEqual(len(bopen), 1)
        self.assertIsInstance(bopen[0], nodes.Function)
        self.failUnless(bopen[0].callable())
        b = get_name_node(astng, 'b').infer().next()
        self.assertIsInstance(b, Instance)
        bopen = list(b.igetattr('open'))
        self.assertEqual(len(bopen), 1)
        self.assertIsInstance(bopen[0], BoundMethod)
        self.failUnless(bopen[0].callable())

    def test_property(self):
        code = '''
from smtplib import SMTP
class SendMailController(object):

    @property
    def smtp(self):
        return SMTP(mailhost, port)

    @property
    def me(self):
        return self

my_smtp = SendMailController().smtp
my_me = SendMailController().me
'''
        decorators = set(['%s.property' % BUILTINS_NAME])
        astng = builder.string_build(code, __name__, __file__)
        self.assertEqual(astng['SendMailController']['smtp'].decoratornames(),
                          decorators)
        propinfered = list(astng.body[2].value.infer())
        self.assertEqual(len(propinfered), 1)
        propinfered = propinfered[0]
        self.assertIsInstance(propinfered, Instance)
        self.assertEqual(propinfered.name, 'SMTP')
        self.assertEqual(propinfered.root().name, 'smtplib')
        self.assertEqual(astng['SendMailController']['me'].decoratornames(),
                          decorators)
        propinfered = list(astng.body[3].value.infer())
        self.assertEqual(len(propinfered), 1)
        propinfered = propinfered[0]
        self.assertIsInstance(propinfered, Instance)
        self.assertEqual(propinfered.name, 'SendMailController')
        self.assertEqual(propinfered.root().name, __name__)


    def test_im_func_unwrap(self):
        code = '''
class EnvBasedTC:
    def pactions(self):
        pass
pactions = EnvBasedTC.pactions.im_func
print (pactions)

class EnvBasedTC2:
    pactions = EnvBasedTC.pactions.im_func
    print (pactions)

'''
        astng = builder.string_build(code, __name__, __file__)
        pactions = get_name_node(astng, 'pactions')
        infered = list(pactions.infer())
        self.assertEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Function)
        pactions = get_name_node(astng['EnvBasedTC2'], 'pactions')
        infered = list(pactions.infer())
        self.assertEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Function)

    def test_augassign(self):
        code = '''
a = 1
a += 2
print (a)
'''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(get_name_node(astng, 'a').infer())

        self.assertEqual(len(infered), 1)
        self.assertIsInstance(infered[0], nodes.Const)
        self.assertEqual(infered[0].value, 3)

    def test_nonregr_func_arg(self):
        code = '''
def foo(self, bar):
    def baz():
        pass
    def qux():
        return baz
    spam = bar(None, qux)
    print (spam)
'''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(get_name_node(astng['foo'], 'spam').infer())
        self.assertEqual(len(infered), 1)
        self.assertIs(infered[0], YES)

    def test_nonregr_func_global(self):
        code = '''
active_application = None

def get_active_application():
  global active_application
  return active_application

class Application(object):
  def __init__(self):
     global active_application
     active_application = self

class DataManager(object):
  def __init__(self, app=None):
     self.app = get_active_application()
  def test(self):
     p = self.app
     print (p)
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(Instance(astng['DataManager']).igetattr('app'))
        self.assertEqual(len(infered), 2, infered) # None / Instance(Application)
        infered = list(get_name_node(astng['DataManager']['test'], 'p').infer())
        self.assertEqual(len(infered), 2, infered)
        for node in infered:
            if isinstance(node, Instance) and node.name == 'Application':
                break
        else:
            self.fail('expected to find an instance of Application in %s' % infered)

    def test_list_inference(self):
        """#20464"""
        code = '''
import optparse

A = []
B = []

def test():
  xyz = [
    "foobar=%s" % options.ca,
  ] + A + B

  if options.bind is not None:
    xyz.append("bind=%s" % options.bind)
  return xyz

def main():
  global options

  parser = optparse.OptionParser()
  (options, args) = parser.parse_args()

Z = test()
        '''
        astng = builder.string_build(code, __name__, __file__)
        infered = list(astng['Z'].infer())
        self.assertEqual(len(infered), 1, infered)
        self.assertIsInstance(infered[0], Instance)
        self.assertIsInstance(infered[0]._proxied, nodes.Class)
        self.assertEqual(infered[0]._proxied.name, 'list')

    def test__new__(self):
        code = '''
class NewTest(object):
    "doc"
    def __new__(cls, arg):
        self = object.__new__(cls)
        self.arg = arg
        return self

n = NewTest()
        '''
        astng = builder.string_build(code, __name__, __file__)
        self.assertRaises(InferenceError, list, astng['NewTest'].igetattr('arg'))
        n = astng['n'].infer().next()
        infered = list(n.igetattr('arg'))
        self.assertEqual(len(infered), 1, infered)


    def test_two_parents_from_same_module(self):
        code = '''
from data import nonregr
class Xxx(nonregr.Aaa, nonregr.Ccc):
    "doc"
        '''
        astng = builder.string_build(code, __name__, __file__)
        parents = list(astng['Xxx'].ancestors())
        self.assertEqual(len(parents), 3, parents) # Aaa, Ccc, object

if __name__ == '__main__':
    unittest_main()
