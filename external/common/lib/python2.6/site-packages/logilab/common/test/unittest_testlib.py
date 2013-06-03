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
"""unittest module for logilab.comon.testlib"""

import os
import sys
from os.path import join, dirname, isdir, isfile, abspath, exists
from cStringIO import StringIO
import tempfile
import shutil

try:
    __file__
except NameError:
    __file__ = sys.argv[0]

from logilab.common.testlib import (unittest, TestSuite, unittest_main, Tags,
    TestCase, mock_object, create_files, InnerTest, with_tempdir, tag,
    require_version, require_module)
from logilab.common.pytest  import SkipAwareTextTestRunner, NonStrictTestLoader


class MockTestCase(TestCase):
    def __init__(self):
        # Do not call unittest.TestCase's __init__
        pass

    def fail(self, msg):
        raise AssertionError(msg)

class UtilTC(TestCase):

    def test_mockobject(self):
        obj = mock_object(foo='bar', baz='bam')
        self.assertEqual(obj.foo, 'bar')
        self.assertEqual(obj.baz, 'bam')

    def test_create_files(self):
        chroot = tempfile.mkdtemp()
        path_to = lambda path: join(chroot, path)
        dircontent = lambda path: sorted(os.listdir(join(chroot, path)))
        try:
            self.assertFalse(isdir(path_to('a/')))
            create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], chroot)
            # make sure directories exist
            self.assertTrue(isdir(path_to('a')))
            self.assertTrue(isdir(path_to('a/b')))
            self.assertTrue(isdir(path_to('a/b/c')))
            self.assertTrue(isdir(path_to('a/b/c/d')))
            # make sure files exist
            self.assertTrue(isfile(path_to('a/b/foo.py')))
            self.assertTrue(isfile(path_to('a/b/c/d/e.py')))
            # make sure only asked files were created
            self.assertEqual(dircontent('a'), ['b'])
            self.assertEqual(dircontent('a/b'), ['c', 'foo.py'])
            self.assertEqual(dircontent('a/b/c'), ['d'])
            self.assertEqual(dircontent('a/b/c/d'), ['e.py'])
        finally:
            shutil.rmtree(chroot)


class TestlibTC(TestCase):

    def mkdir(self, path):
        if not exists(path):
            self._dirs.add(path)
            os.mkdir(path)

    def setUp(self):
        self.tc = MockTestCase()
        self._dirs = set()

    def tearDown(self):
        while(self._dirs):
            shutil.rmtree(self._dirs.pop(), ignore_errors=True)

    def test_dict_equals(self):
        """tests TestCase.assertDictEqual"""
        d1 = {'a' : 1, 'b' : 2}
        d2 = {'a' : 1, 'b' : 3}
        d3 = dict(d1)
        self.assertRaises(AssertionError, self.tc.assertDictEqual, d1, d2)
        self.tc.assertDictEqual(d1, d3)
        self.tc.assertDictEqual(d3, d1)
        self.tc.assertDictEqual(d1, d1)

    def test_list_equals(self):
        """tests TestCase.assertListEqual"""
        l1 = range(10)
        l2 = range(5)
        l3 = range(10)
        self.assertRaises(AssertionError, self.tc.assertListEqual, l1, l2)
        self.tc.assertListEqual(l1, l1)
        self.tc.assertListEqual(l1, l3)
        self.tc.assertListEqual(l3, l1)

    def test_xml_valid(self):
        """tests xml is valid"""
        valid = """<root>
        <hello />
        <world>Logilab</world>
        </root>"""
        invalid = """<root><h2> </root>"""
        self.tc.assertXMLStringWellFormed(valid)
        self.assertRaises(AssertionError, self.tc.assertXMLStringWellFormed, invalid)
        invalid = """<root><h2 </h2> </root>"""
        self.assertRaises(AssertionError, self.tc.assertXMLStringWellFormed, invalid)

    def test_equality_for_sets(self):
        s1 = set('ab')
        s2 = set('a')
        self.assertRaises(AssertionError, self.tc.assertSetEqual, s1, s2)
        self.tc.assertSetEqual(s1, s1)
        self.tc.assertSetEqual(set(), set())

    def test_file_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')
        self.assertRaises(AssertionError, self.tc.assertFileEqual, foo, spam)
        self.tc.assertFileEqual(foo, foo)

    def test_dir_equality(self):
        ref = join(dirname(__file__), 'data', 'reference_dir')
        same = join(dirname(__file__), 'data', 'same_dir')
        subdir_differ = join(dirname(__file__), 'data', 'subdir_differ_dir')
        file_differ = join(dirname(__file__), 'data', 'file_differ_dir')
        content_differ = join(dirname(__file__), 'data', 'content_differ_dir')
        ed1 = join(dirname(__file__), 'data', 'empty_dir_1')
        ed2 = join(dirname(__file__), 'data', 'empty_dir_2')

        for path in (ed1, ed2, join(subdir_differ, 'unexpected')):
            self.mkdir(path)

        self.assertDirEqual(ed1, ed2)
        self.assertDirEqual(ref, ref)
        self.assertDirEqual( ref, same)
        self.assertRaises(AssertionError, self.assertDirEqual, ed1, ref)
        self.assertRaises(AssertionError, self.assertDirEqual, ref, ed2)
        self.assertRaises(AssertionError, self.assertDirEqual, subdir_differ, ref)
        self.assertRaises(AssertionError, self.assertDirEqual, file_differ, ref)
        self.assertRaises(AssertionError, self.assertDirEqual, ref, content_differ)

    def test_stream_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')
        stream1 = open(foo)
        self.tc.assertStreamEqual(stream1, stream1)
        stream1 = open(foo)
        stream2 = open(spam)
        self.assertRaises(AssertionError, self.tc.assertStreamEqual, stream1, stream2)

    def test_text_equality(self):
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, "toto", 12)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, "toto", 12)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, "toto", None)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, "toto", None)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, 3.12, u"toto")
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, 3.12, u"toto")
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, None, u"toto")
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, None, u"toto")
        self.tc.assertMultiLineEqual('toto\ntiti', 'toto\ntiti')
        self.tc.assertMultiLineEqual('toto\ntiti', 'toto\ntiti')
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, 'toto\ntiti', 'toto\n titi\n')
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, 'toto\ntiti', 'toto\n titi\n')
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')
        text1 = open(foo).read()
        self.tc.assertMultiLineEqual(text1, text1)
        self.tc.assertMultiLineEqual(text1, text1)
        text2 = open(spam).read()
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, text1, text2)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, text1, text2)

    def test_default_datadir(self):
        expected_datadir = join(dirname(abspath(__file__)), 'data')
        self.assertEqual(self.datadir, expected_datadir)
        self.assertEqual(self.datapath('foo'), join(expected_datadir, 'foo'))

    def test_multiple_args_datadir(self):
        expected_datadir = join(dirname(abspath(__file__)), 'data')
        self.assertEqual(self.datadir, expected_datadir)
        self.assertEqual(self.datapath('foo', 'bar'), join(expected_datadir, 'foo', 'bar'))

    def test_custom_datadir(self):
        class MyTC(TestCase):
            datadir = 'foo'
            def test_1(self): pass

        # class' custom datadir
        tc = MyTC('test_1')
        self.assertEqual(tc.datapath('bar'), join('foo', 'bar'))

    def test_cached_datadir(self):
        """test datadir is cached on the class"""
        class MyTC(TestCase):
            def test_1(self): pass

        expected_datadir = join(dirname(abspath(__file__)), 'data')
        tc = MyTC('test_1')
        self.assertEqual(tc.datadir, expected_datadir)
        # changing module should not change the datadir
        MyTC.__module__ = 'os'
        self.assertEqual(tc.datadir, expected_datadir)
        # even on new instances
        tc2 = MyTC('test_1')
        self.assertEqual(tc2.datadir, expected_datadir)

    def test_is(self):
        obj_1 = []
        obj_2 = []
        self.assertIs(obj_1, obj_1)
        self.assertRaises(AssertionError, self.assertIs, obj_1, obj_2)

    def test_isnot(self):
        obj_1 = []
        obj_2 = []
        self.assertIsNot(obj_1, obj_2)
        self.assertRaises(AssertionError, self.assertIsNot, obj_1, obj_1)

    def test_none(self):
        self.assertIsNone(None)
        self.assertRaises(AssertionError, self.assertIsNone, object())

    def test_not_none(self):
        self.assertIsNotNone(object())
        self.assertRaises(AssertionError, self.assertIsNotNone, None)

    def test_in(self):
        self.assertIn("a", "dsqgaqg")
        obj, seq = 'a', ('toto', "azf", "coin")
        self.assertRaises(AssertionError, self.assertIn, obj, seq)

    def test_not_in(self):
        self.assertNotIn('a', ('toto', "azf", "coin"))
        self.assertRaises(AssertionError, self.assertNotIn, 'a', "dsqgaqg")


class GenerativeTestsTC(TestCase):

    def setUp(self):
        output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=output)

    def test_generative_ok(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEqual, i, i
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)

    def test_generative_half_bad(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEqual, i%2, 0
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 5)
        self.assertEqual(len(result.errors), 0)

    def test_generative_error(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    if i == 5:
                        raise ValueError('STOP !')
                    yield self.assertEqual, i, i

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 5)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_error2(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    if i == 5:
                        yield self.ouch
                    yield self.assertEqual, i, i
            def ouch(self): raise ValueError('stop !')
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 11)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_setup(self):
        class FooTC(TestCase):
            def setUp(self):
                raise ValueError('STOP !')
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEqual, i, i

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_inner_skip(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    self.innerSkip("no 5")
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.skipped), 1)

    def test_generative_skip(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    self.skipTest("no 5")
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.skipped), 1)

    def test_generative_inner_error(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    raise ValueError("no 5")
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.skipped), 0)

    def test_generative_inner_failure(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    self.assertEqual(val, val+1)
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.skipped), 0)


class ExitFirstTC(TestCase):
    def setUp(self):
        output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=output, exitfirst=True)

    def test_failure_exit_first(self):
        class FooTC(TestCase):
            def test_1(self): pass
            def test_2(self): assert False
            def test_3(self): pass
        tests = [FooTC('test_1'), FooTC('test_2')]
        result = self.runner.run(TestSuite(tests))
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)

    def test_error_exit_first(self):
        class FooTC(TestCase):
            def test_1(self): pass
            def test_2(self): raise ValueError()
            def test_3(self): pass
        tests = [FooTC('test_1'), FooTC('test_2'), FooTC('test_3')]
        result = self.runner.run(TestSuite(tests))
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_exit_first(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assert_, False
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)


class TestLoaderTC(TestCase):
    ## internal classes for test purposes ########
    class FooTC(TestCase):
        def test_foo1(self): pass
        def test_foo2(self): pass
        def test_bar1(self): pass

    class BarTC(TestCase):
        def test_bar2(self): pass
    ##############################################

    def setUp(self):
        self.loader = NonStrictTestLoader()
        self.module = TestLoaderTC # mock_object(FooTC=TestLoaderTC.FooTC, BarTC=TestLoaderTC.BarTC)
        self.output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=self.output)

    def assertRunCount(self, pattern, module, expected_count, skipped=()):
        self.loader.test_pattern = pattern
        self.loader.skipped_patterns = skipped
        if pattern:
            suite = self.loader.loadTestsFromNames([pattern], module)
        else:
            suite = self.loader.loadTestsFromModule(module)
        result = self.runner.run(suite)
        self.loader.test_pattern = None
        self.loader.skipped_patterns = ()
        self.assertEqual(result.testsRun, expected_count)

    def test_collect_everything(self):
        """make sure we don't change the default behaviour
        for loadTestsFromModule() and loadTestsFromTestCase
        """
        testsuite = self.loader.loadTestsFromModule(self.module)
        self.assertEqual(len(testsuite._tests), 2)
        suite1, suite2 = testsuite._tests
        self.assertEqual(len(suite1._tests) + len(suite2._tests), 4)

    def test_collect_with_classname(self):
        self.assertRunCount('FooTC', self.module, 3)
        self.assertRunCount('BarTC', self.module, 1)

    def test_collect_with_classname_and_pattern(self):
        data = [('FooTC.test_foo1', 1), ('FooTC.test_foo', 2), ('FooTC.test_fo', 2),
                ('FooTC.foo1', 1), ('FooTC.foo', 2), ('FooTC.whatever', 0)
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, self.module, expected_count

    def test_collect_with_pattern(self):
        data = [('test_foo1', 1), ('test_foo', 2), ('test_bar', 2),
                ('foo1', 1), ('foo', 2), ('bar', 2), ('ba', 2),
                ('test', 4), ('ab', 0),
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, self.module, expected_count

    def test_testcase_with_custom_metaclass(self):
        class mymetaclass(type): pass
        class MyMod:
            class MyTestCase(TestCase):
                __metaclass__ = mymetaclass
                def test_foo1(self): pass
                def test_foo2(self): pass
                def test_bar(self): pass
        data = [('test_foo1', 1), ('test_foo', 2), ('test_bar', 1),
                ('foo1', 1), ('foo', 2), ('bar', 1), ('ba', 1),
                ('test', 3), ('ab', 0),
                ('MyTestCase.test_foo1', 1), ('MyTestCase.test_foo', 2),
                ('MyTestCase.test_fo', 2), ('MyTestCase.foo1', 1),
                ('MyTestCase.foo', 2), ('MyTestCase.whatever', 0)
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, MyMod, expected_count

    def test_collect_everything_and_skipped_patterns(self):
        testdata = [ (['foo1'], 3), (['foo'], 2),
                     (['foo', 'bar'], 0), ]
        for skipped, expected_count in testdata:
            yield self.assertRunCount, None, self.module, expected_count, skipped

    def test_collect_specific_pattern_and_skip_some(self):
        testdata = [ ('bar', ['foo1'], 2), ('bar', [], 2),
                     ('bar', ['bar'], 0), ]
        for runpattern, skipped, expected_count in testdata:
            yield self.assertRunCount, runpattern, self.module, expected_count, skipped

    def test_skip_classname(self):
        testdata = [ (['BarTC'], 3), (['FooTC'], 1), ]
        for skipped, expected_count in testdata:
            yield self.assertRunCount, None, self.module, expected_count, skipped

    def test_skip_classname_and_specific_collect(self):
        testdata = [ ('bar', ['BarTC'], 1), ('foo', ['FooTC'], 0), ]
        for runpattern, skipped, expected_count in testdata:
            yield self.assertRunCount, runpattern, self.module, expected_count, skipped

    def test_nonregr_dotted_path(self):
        self.assertRunCount('FooTC.test_foo', self.module, 2)

    def test_inner_tests_selection(self):
        class MyMod:
            class MyTestCase(TestCase):
                def test_foo(self): pass
                def test_foobar(self):
                    for i in xrange(5):
                        if i%2 == 0:
                            yield InnerTest('even', lambda: None)
                        else:
                            yield InnerTest('odd', lambda: None)
                    yield lambda: None

        # FIXME InnerTest masked by pattern usage
        # data = [('foo', 7), ('test_foobar', 6), ('even', 3), ('odd', 2), ]
        data = [('foo', 7), ('test_foobar', 6), ('even', 0), ('odd', 0), ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, MyMod, expected_count

    def test_nonregr_class_skipped_option(self):
        class MyMod:
            class MyTestCase(TestCase):
                def test_foo(self): pass
                def test_bar(self): pass
            class FooTC(TestCase):
                def test_foo(self): pass
        self.assertRunCount('foo', MyMod, 2)
        self.assertRunCount(None, MyMod, 3)
        self.assertRunCount('foo', MyMod, 1, ['FooTC'])
        self.assertRunCount(None, MyMod, 2, ['FooTC'])

    def test__classes_are_ignored(self):
        class MyMod:
            class _Base(TestCase):
                def test_1(self): pass
            class MyTestCase(_Base):
                def test_2(self): pass
        self.assertRunCount(None, MyMod, 2)


class DecoratorTC(TestCase):

    @with_tempdir
    def test_tmp_dir_normal_1(self):
        tempdir = tempfile.gettempdir()
        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempdir)),
            [(tempdir, [], [])])

        witness = []

        @with_tempdir
        def createfile(list):
            fd1, fn1 = tempfile.mkstemp()
            fd2, fn2 = tempfile.mkstemp()
            dir = tempfile.mkdtemp()
            fd3, fn3 = tempfile.mkstemp(dir=dir)
            tempfile.mkdtemp()
            list.append(True)
            for fd in (fd1, fd2, fd3):
                os.close(fd)

        self.assertFalse(witness)
        createfile(witness)
        self.assertTrue(witness)

        self.assertEqual(tempfile.gettempdir(), tempdir)

        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempdir)),
            [(tempdir, [], [])])

    @with_tempdir
    def test_tmp_dir_normal_2(self):
        tempdir = tempfile.gettempdir()
        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempfile.tempdir)),
            [(tempfile.tempdir, [], [])])


        class WitnessException(Exception):
            pass

        @with_tempdir
        def createfile():
            fd1, fn1 = tempfile.mkstemp()
            fd2, fn2 = tempfile.mkstemp()
            dir = tempfile.mkdtemp()
            fd3, fn3 = tempfile.mkstemp(dir=dir)
            tempfile.mkdtemp()
            for fd in (fd1, fd2, fd3):
                os.close(fd)
            raise WitnessException()

        self.assertRaises(WitnessException, createfile)

        # assert tempdir didn't change
        self.assertEqual(tempfile.gettempdir(), tempdir)

        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempdir)),
            [(tempdir, [], [])])

    def setUp(self):
        self.pyversion = sys.version_info

    def tearDown(self):
        sys.version_info = self.pyversion

    def test_require_version_good(self):
        """ should return the same function
        """
        def func() :
            pass
        sys.version_info = (2, 5, 5, 'final', 4)
        current = sys.version_info[:3]
        compare = ('2.4', '2.5', '2.5.4', '2.5.5')
        for version in compare:
            decorator = require_version(version)
            self.assertEqual(func, decorator(func), '%s =< %s : function \
                return by the decorator should be the same.' % (version,
                '.'.join([str(element) for element in current])))

    def test_require_version_bad(self):
        """ should return a different function : skipping test
        """
        def func() :
            pass
        sys.version_info = (2, 5, 5, 'final', 4)
        current = sys.version_info[:3]
        compare = ('2.5.6', '2.6', '2.6.5')
        for version in compare:
            decorator = require_version(version)
            self.assertNotEqual(func, decorator(func), '%s >= %s : function \
                 return by the decorator should NOT be the same.'
                 % ('.'.join([str(element) for element in current]), version))

    def test_require_version_exception(self):
        """ should throw a ValueError exception
        """
        def func() :
            pass
        compare = ('2.5.a', '2.a', 'azerty')
        for version in compare:
            decorator = require_version(version)
            self.assertRaises(ValueError, decorator, func)

    def test_require_module_good(self):
        """ should return the same function
        """
        def func() :
            pass
        module = 'sys'
        decorator = require_module(module)
        self.assertEqual(func, decorator(func), 'module %s exists : function \
            return by the decorator should be the same.' % module)

    def test_require_module_bad(self):
        """ should return a different function : skipping test
        """
        def func() :
            pass
        modules = ('bla', 'blo', 'bli')
        for module in modules:
            try:
                __import__(module)
                pass
            except ImportError:
                decorator = require_module(module)
                self.assertNotEqual(func, decorator(func), 'module %s does \
                    not exist : function return by the decorator should \
                    NOT be the same.' % module)
                return
        print 'all modules in %s exist. Could not test %s' % (', '.join(modules),
            sys._getframe().f_code.co_name)

class TagTC(TestCase):

    def setUp(self):
        @tag('testing', 'bob')
        def bob(a, b, c):
            return (a + b) * c

        self.func = bob

        class TagTestTC(TestCase):
            tags = Tags('one', 'two')

            def test_one(self):
                self.assertTrue(True)

            @tag('two', 'three')
            def test_two(self):
                self.assertTrue(True)

            @tag('three', inherit=False)
            def test_three(self):
                self.assertTrue(True)
        self.cls = TagTestTC

    def test_tag_decorator(self):
        bob = self.func

        self.assertEqual(bob(2, 3, 7), 35)
        self.assertTrue(hasattr(bob, 'tags'))
        self.assertSetEqual(bob.tags, set(['testing', 'bob']))

    def test_tags_class(self):
        tags = self.func.tags

        self.assertTrue(tags['testing'])
        self.assertFalse(tags['Not inside'])

    def test_tags_match(self):
        tags = self.func.tags

        self.assertTrue(tags.match('testing'))
        self.assertFalse(tags.match('other'))

        self.assertFalse(tags.match('testing and coin'))
        self.assertTrue(tags.match('testing or other'))

        self.assertTrue(tags.match('not other'))

        self.assertTrue(tags.match('not other or (testing and bibi)'))
        self.assertTrue(tags.match('other or (testing and bob)'))

    def test_tagged_class(self):
        if sys.version_info > (3, 0):
            self.skipTest('fix me for py3k')

        def options(tags):
            class Options(object):
                tags_pattern = tags
            return Options()

        cls = self.cls

        runner = SkipAwareTextTestRunner()
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertTrue(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('one'))
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertFalse(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('two'))
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertFalse(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('three'))
        self.assertFalse(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertTrue(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('two or three'))
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertTrue(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('two and three'))
        self.assertFalse(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertFalse(runner.does_match_tags(cls.test_three))



if __name__ == '__main__':
    unittest_main()
