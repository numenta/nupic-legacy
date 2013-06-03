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
"""tests for specific behaviour of astng nodes
"""
import sys

from logilab.common import testlib
from logilab.astng.node_classes import unpack_infer
from logilab.astng.bases import YES, InferenceContext
from logilab.astng.exceptions import ASTNGBuildingException, NotFoundError
from logilab.astng import BUILTINS_MODULE, builder, nodes
from logilab.astng.as_string import as_string

from data import module as test_module

from os.path import join, abspath, dirname

DATA = join(dirname(abspath(__file__)), 'data')

abuilder = builder.ASTNGBuilder()

class AsString(testlib.TestCase):

    def test_varargs_kwargs_as_string(self):
        ast = abuilder.string_build( 'raise_string(*args, **kwargs)').body[0]
        self.assertEqual(as_string(ast), 'raise_string(*args, **kwargs)')

    def test_module_as_string(self):
        """check as_string on a whole module prepared to be returned identically
        """
        data = open(join(DATA, 'module.py')).read()
        self.assertMultiLineEqual(as_string(MODULE), data)
        data = open(join(DATA, 'module2.py')).read()
        self.assertMultiLineEqual(as_string(MODULE2), data)

    def test_2_7_as_string(self):
        """check as_string for python syntax >= 2.7"""
        if sys.version_info < (2, 7):
            self.skipTest("test python >= 2.7 specific")
        code = '''one_two = {1, 2}
b = {v: k for (k, v) in enumerate('string')}
cdd = {k for k in b}\n\n'''
        ast = abuilder.string_build(code)
        self.assertMultiLineEqual(as_string(ast), code)

    def test_3k_as_string(self):
        """check as_string for python 3k syntax"""
        if sys.version_info < (3, 0):
            self.skipTest("test python 3k specific")
        code = '''print()

def function(var):
    nonlocal counter
    try:
        hello
    except NameError as nexc:
        (*hell, o) = b'hello'
        raise AttributeError from nexc
\n'''
        # TODO : annotations and keywords for class definition are not yet implemented
        _todo = '''
def function(var:int):
    nonlocal counter

class Language(metaclass=Natural):
    """natural language"""
        '''
        ast = abuilder.string_build(code)
        self.assertEqual(as_string(ast), code)


class _NodeTC(testlib.TestCase):
    """test transformation of If Node"""
    CODE = None
    @property
    def astng(self):
        try:
            return self.__class__.__dict__['CODE_ASTNG']
        except KeyError:
            astng = abuilder.string_build(self.CODE)
            self.__class__.CODE_ASTNG = astng
            return astng


class IfNodeTC(_NodeTC):
    """test transformation of If Node"""
    CODE = """
if 0:
    print()

if True:
    print()
else:
    pass

if "":
    print()
elif []:
    raise

if 1:
    print()
elif True:
    print()
elif func():
    pass
else:
    raise
    """

    def test_if_elif_else_node(self):
        """test transformation for If node"""
        self.assertEqual(len(self.astng.body), 4)
        for stmt in self.astng.body:
            self.assertIsInstance( stmt, nodes.If)
        self.failIf(self.astng.body[0].orelse) # simple If
        self.assertIsInstance(self.astng.body[1].orelse[0], nodes.Pass) # If / else
        self.assertIsInstance(self.astng.body[2].orelse[0], nodes.If) # If / elif
        self.assertIsInstance(self.astng.body[3].orelse[0].orelse[0], nodes.If)

    def test_block_range(self):
        # XXX ensure expected values
        self.assertEqual(self.astng.block_range(1), (0, 22))
        self.assertEqual(self.astng.block_range(10), (0, 22)) # XXX (10, 22) ?
        self.assertEqual(self.astng.body[1].block_range(5), (5, 6))
        self.assertEqual(self.astng.body[1].block_range(6), (6, 6))
        self.assertEqual(self.astng.body[1].orelse[0].block_range(7), (7, 8))
        self.assertEqual(self.astng.body[1].orelse[0].block_range(8), (8, 8))


class TryExceptNodeTC(_NodeTC):
    CODE = """
try:
    print ('pouet')
except IOError:
    pass
except UnicodeError:
    print()
else:
    print()
    """
    def test_block_range(self):
        # XXX ensure expected values
        self.assertEqual(self.astng.body[0].block_range(1), (1, 8))
        self.assertEqual(self.astng.body[0].block_range(2), (2, 2))
        self.assertEqual(self.astng.body[0].block_range(3), (3, 8))
        self.assertEqual(self.astng.body[0].block_range(4), (4, 4))
        self.assertEqual(self.astng.body[0].block_range(5), (5, 5))
        self.assertEqual(self.astng.body[0].block_range(6), (6, 6))
        self.assertEqual(self.astng.body[0].block_range(7), (7, 7))
        self.assertEqual(self.astng.body[0].block_range(8), (8, 8))


class TryFinallyNodeTC(_NodeTC):
    CODE = """
try:
    print ('pouet')
finally:
    print ('pouet')
    """
    def test_block_range(self):
        # XXX ensure expected values
        self.assertEqual(self.astng.body[0].block_range(1), (1, 4))
        self.assertEqual(self.astng.body[0].block_range(2), (2, 2))
        self.assertEqual(self.astng.body[0].block_range(3), (3, 4))
        self.assertEqual(self.astng.body[0].block_range(4), (4, 4))


class TryFinally25NodeTC(_NodeTC):
    CODE = """
try:
    print('pouet')
except Exception:
    print ('oops')
finally:
    print ('pouet')
    """
    def test_block_range(self):
        # XXX ensure expected values
        self.assertEqual(self.astng.body[0].block_range(1), (1, 6))
        self.assertEqual(self.astng.body[0].block_range(2), (2, 2))
        self.assertEqual(self.astng.body[0].block_range(3), (3, 4))
        self.assertEqual(self.astng.body[0].block_range(4), (4, 4))
        self.assertEqual(self.astng.body[0].block_range(5), (5, 5))
        self.assertEqual(self.astng.body[0].block_range(6), (6, 6))


class TryExcept2xNodeTC(_NodeTC):
    CODE = """
try:
    hello
except AttributeError, (retval, desc):
    pass
    """
    def test_tuple_attribute(self):
        if sys.version_info >= (3, 0):
            self.skipTest('syntax removed from py3.x')
        handler = self.astng.body[0].handlers[0]
        self.assertIsInstance(handler.name, nodes.Tuple)


MODULE = abuilder.module_build(test_module)
MODULE2 = abuilder.file_build(join(DATA, 'module2.py'), 'data.module2')


class ImportNodeTC(testlib.TestCase):

    def test_import_self_resolve(self):
        myos = MODULE2.igetattr('myos').next()
        self.failUnless(isinstance(myos, nodes.Module), myos)
        self.failUnlessEqual(myos.name, 'os')
        self.failUnlessEqual(myos.qname(), 'os')
        self.failUnlessEqual(myos.pytype(), '%s.module' % BUILTINS_MODULE)

    def test_from_self_resolve(self):
        spawn = MODULE.igetattr('spawn').next()
        self.failUnless(isinstance(spawn, nodes.Class), spawn)
        self.failUnlessEqual(spawn.root().name, 'logilab.common.shellutils')
        self.failUnlessEqual(spawn.qname(), 'logilab.common.shellutils.Execute')
        self.failUnlessEqual(spawn.pytype(), '%s.classobj' % BUILTINS_MODULE)
        abspath = MODULE2.igetattr('abspath').next()
        self.failUnless(isinstance(abspath, nodes.Function), abspath)
        self.failUnlessEqual(abspath.root().name, 'os.path')
        self.failUnlessEqual(abspath.qname(), 'os.path.abspath')
        self.failUnlessEqual(abspath.pytype(), '%s.function' % BUILTINS_MODULE)

    def test_real_name(self):
        from_ = MODULE['spawn']
        self.assertEqual(from_.real_name('spawn'), 'Execute')
        imp_ = MODULE['os']
        self.assertEqual(imp_.real_name('os'), 'os')
        self.assertRaises(NotFoundError, imp_.real_name, 'os.path')
        imp_ = MODULE['spawn']
        self.assertEqual(imp_.real_name('spawn'), 'Execute')
        self.assertRaises(NotFoundError, imp_.real_name, 'Execute')
        imp_ = MODULE2['YO']
        self.assertEqual(imp_.real_name('YO'), 'YO')
        self.assertRaises(NotFoundError, imp_.real_name, 'data')

    def test_as_string(self):
        ast = MODULE['modutils']
        self.assertEqual(as_string(ast), "from logilab.common import modutils")
        ast = MODULE['spawn']
        self.assertEqual(as_string(ast), "from logilab.common.shellutils import Execute as spawn")
        ast = MODULE['os']
        self.assertEqual(as_string(ast), "import os.path")
        code = """from . import here
from .. import door
from .store import bread
from ..cave import wine\n\n"""
        ast = abuilder.string_build(code)
        self.assertMultiLineEqual(ast.as_string(), code)

    def test_bad_import_inference(self):
        # Explication of bug
        '''When we import PickleError from nonexistent, a call to the infer
        method of this From node will be made by unpack_infer.
        inference.infer_from will try to import this module, which will fail and
        raise a InferenceException (by mixins.do_import_module). The infer_name
        will catch this exception and yield and YES instead.
        '''

        code = '''try:
    from pickle import PickleError
except ImportError:
    from nonexistent import PickleError

try:
    pass
except PickleError:
    pass
        '''

        astng = abuilder.string_build(code)
        from_node = astng.body[1].handlers[0].body[0]
        handler_type = astng.body[1].handlers[0].type

        excs = list(unpack_infer(handler_type))

    def test_absolute_import(self):
        astng = abuilder.file_build(self.datapath('absimport.py'))
        ctx = InferenceContext()
        ctx.lookupname = 'message'
        # will fail if absolute import failed
        astng['message'].infer(ctx).next()
        ctx.lookupname = 'email'
        m = astng['email'].infer(ctx).next()
        self.assertFalse(m.file.startswith(self.datapath('email.py')))


class CmpNodeTC(testlib.TestCase):
    def test_as_string(self):
        ast = abuilder.string_build("a == 2").body[0]
        self.assertEqual(as_string(ast), "a == 2")


class ConstNodeTC(testlib.TestCase):

    def _test(self, value):
        node = nodes.const_factory(value)
        self.assertIsInstance(node._proxied, nodes.Class)
        self.assertEqual(node._proxied.name, value.__class__.__name__)
        self.assertIs(node.value, value)
        self.failUnless(node._proxied.parent)
        self.assertEqual(node._proxied.root().name, value.__class__.__module__)

    def test_none(self):
        self._test(None)

    def test_bool(self):
        self._test(True)

    def test_int(self):
        self._test(1)

    def test_float(self):
        self._test(1.0)

    def test_complex(self):
        self._test(1.0j)

    def test_str(self):
        self._test('a')

    def test_unicode(self):
        self._test(u'a')


class NameNodeTC(testlib.TestCase):
    def test_assign_to_True(self):
        """test that True and False assignements don't crash"""
        code = """True = False
def hello(False):
    pass
del True
    """
        if sys.version_info >= (3, 0):
            self.assertRaises(SyntaxError,#might become ASTNGBuildingException
                              abuilder.string_build, code)
        else:
            ast = abuilder.string_build(code)
            ass_true = ast['True']
            self.assertIsInstance(ass_true, nodes.AssName)
            self.assertEqual(ass_true.name, "True")
            del_true = ast.body[2].targets[0]
            self.assertIsInstance(del_true, nodes.DelName)
            self.assertEqual(del_true.name, "True")


class ArgumentsNodeTC(testlib.TestCase):
    def test_linenumbering(self):
        ast = abuilder.string_build('''
def func(a,
    b): pass
x = lambda x: None
        ''')
        self.assertEqual(ast['func'].args.fromlineno, 2)
        self.failIf(ast['func'].args.is_statement)
        xlambda = ast['x'].infer().next()
        self.assertEqual(xlambda.args.fromlineno, 4)
        self.assertEqual(xlambda.args.tolineno, 4)
        self.failIf(xlambda.args.is_statement)
        if sys.version_info < (3, 0):
            self.assertEqual(ast['func'].args.tolineno, 3)
        else:
            self.skipTest('FIXME  http://bugs.python.org/issue10445 '
                          '(no line number on function args)')


class SliceNodeTC(testlib.TestCase):
    def test(self):
        for code in ('a[0]', 'a[1:3]', 'a[:-1:step]', 'a[:,newaxis]',
                     'a[newaxis,:]', 'del L[::2]', 'del A[1]', 'del Br[:]'):
            ast = abuilder.string_build(code).body[0]
            self.assertEqual(ast.as_string(), code)

    def test_slice_and_subscripts(self):
        code = """a[:1] = bord[2:]
a[:1] = bord[2:]
del bree[3:d]
bord[2:]
del av[d::f], a[df:]
a[:1] = bord[2:]
del SRC[::1,newaxis,1:]
tous[vals] = 1010
del thousand[key]
del a[::2], a[:-1:step]
del Fee.form[left:]
aout.vals = miles.of_stuff
del (ccok, (name.thing, foo.attrib.value)), Fee.form[left:]
if all[1] == bord[0:]:
    pass\n\n"""
        ast = abuilder.string_build(code)
        self.assertEqual(ast.as_string(), code)

class EllipsisNodeTC(testlib.TestCase):
    def test(self):
        ast = abuilder.string_build('a[...]').body[0]
        self.assertEqual(ast.as_string(), 'a[...]')

if __name__ == '__main__':
    testlib.unittest_main()
