# -*- coding: utf-8 -*-
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
"""Run tests.

This will find all modules whose name match a given prefix in the test
directory, and run them. Various command line options provide
additional facilities.

Command line options:

 -v  verbose -- run tests in verbose mode with output to stdout
 -q  quiet   -- don't print anything except if a test fails
 -t  testdir -- directory where the tests will be found
 -x  exclude -- add a test to exclude
 -p  profile -- profiled execution
 -d  dbc     -- enable design-by-contract
 -m  match   -- only run test matching the tag pattern which follow

If no non-option arguments are present, prefixes used are 'test',
'regrtest', 'smoketest' and 'unittest'.

"""
__docformat__ = "restructuredtext en"
# modified copy of some functions from test/regrtest.py from PyXml
# disable camel case warning
# pylint: disable=C0103

import sys
import os, os.path as osp
import re
import traceback
import inspect
import difflib
import tempfile
import math
import warnings
from shutil import rmtree
from operator import itemgetter
from ConfigParser import ConfigParser
from itertools import dropwhile

from logilab.common.deprecation import deprecated
from logilab.common.compat import builtins

import unittest as unittest_legacy
if not getattr(unittest_legacy, "__package__", None):
    try:
        import unittest2 as unittest
        from unittest2 import SkipTest
    except ImportError:
        raise ImportError("You have to install python-unittest2 to use %s" % __name__)
else:
    import unittest
    from unittest import SkipTest

try:
    from functools import wraps
except ImportError:
    def wraps(wrapped):
        def proxy(callable):
            callable.__name__ = wrapped.__name__
            return callable
        return proxy
try:
    from test import test_support
except ImportError:
    # not always available
    class TestSupport:
        def unload(self, test):
            pass
    test_support = TestSupport()

# pylint: disable=W0622
from logilab.common.compat import any, InheritableSet, callable
# pylint: enable=W0622
from logilab.common.debugger import Debugger, colorize_source
from logilab.common.decorators import cached, classproperty
from logilab.common import textutils


__all__ = ['main', 'unittest_main', 'find_tests', 'run_test', 'spawn']

DEFAULT_PREFIXES = ('test', 'regrtest', 'smoketest', 'unittest',
                    'func', 'validation')


if sys.version_info >= (2, 6):
    # FIXME : this does not work as expected / breaks tests on testlib
    # however testlib does not work on py3k for many reasons ...
    from inspect import CO_GENERATOR
else:
    from compiler.consts import CO_GENERATOR

if sys.version_info >= (3, 0):
    def is_generator(function):
        flags = function.__code__.co_flags
        return flags & CO_GENERATOR

else:
    def is_generator(function):
        flags = function.func_code.co_flags
        return flags & CO_GENERATOR

# used by unittest to count the number of relevant levels in the traceback
__unittest = 1


def with_tempdir(callable):
    """A decorator ensuring no temporary file left when the function return
    Work only for temporary file create with the tempfile module"""
    @wraps(callable)
    def proxy(*args, **kargs):

        old_tmpdir = tempfile.gettempdir()
        new_tmpdir = tempfile.mkdtemp(prefix="temp-lgc-")
        tempfile.tempdir = new_tmpdir
        try:
            return callable(*args, **kargs)
        finally:
            try:
                rmtree(new_tmpdir, ignore_errors=True)
            finally:
                tempfile.tempdir = old_tmpdir
    return proxy

def in_tempdir(callable):
    """A decorator moving the enclosed function inside the tempfile.tempfdir
    """
    @wraps(callable)
    def proxy(*args, **kargs):

        old_cwd = os.getcwd()
        os.chdir(tempfile.tempdir)
        try:
            return callable(*args, **kargs)
        finally:
            os.chdir(old_cwd)
    return proxy

def within_tempdir(callable):
    """A decorator run the enclosed function inside a tmpdir removed after execution
    """
    proxy = with_tempdir(in_tempdir(callable))
    proxy.__name__ = callable.__name__
    return proxy

def find_tests(testdir,
               prefixes=DEFAULT_PREFIXES, suffix=".py",
               excludes=(),
               remove_suffix=True):
    """
    Return a list of all applicable test modules.
    """
    tests = []
    for name in os.listdir(testdir):
        if not suffix or name.endswith(suffix):
            for prefix in prefixes:
                if name.startswith(prefix):
                    if remove_suffix and name.endswith(suffix):
                        name = name[:-len(suffix)]
                    if name not in excludes:
                        tests.append(name)
    tests.sort()
    return tests


## PostMortem Debug facilities #####
def start_interactive_mode(result):
    """starts an interactive shell so that the user can inspect errors
    """
    debuggers = result.debuggers
    descrs = result.error_descrs + result.fail_descrs
    if len(debuggers) == 1:
        # don't ask for test name if there's only one failure
        debuggers[0].start()
    else:
        while True:
            testindex = 0
            print "Choose a test to debug:"
            # order debuggers in the same way than errors were printed
            print "\n".join(['\t%s : %s' % (i, descr) for i, (_, descr)
                in enumerate(descrs)])
            print "Type 'exit' (or ^D) to quit"
            print
            try:
                todebug = raw_input('Enter a test name: ')
                if todebug.strip().lower() == 'exit':
                    print
                    break
                else:
                    try:
                        testindex = int(todebug)
                        debugger = debuggers[descrs[testindex][0]]
                    except (ValueError, IndexError):
                        print "ERROR: invalid test number %r" % (todebug, )
                    else:
                        debugger.start()
            except (EOFError, KeyboardInterrupt):
                print
                break


# test utils ##################################################################

class SkipAwareTestResult(unittest._TextTestResult):

    def __init__(self, stream, descriptions, verbosity,
                 exitfirst=False, pdbmode=False, cvg=None, colorize=False):
        super(SkipAwareTestResult, self).__init__(stream,
                                                  descriptions, verbosity)
        self.skipped = []
        self.debuggers = []
        self.fail_descrs = []
        self.error_descrs = []
        self.exitfirst = exitfirst
        self.pdbmode = pdbmode
        self.cvg = cvg
        self.colorize = colorize
        self.pdbclass = Debugger
        self.verbose = verbosity > 1

    def descrs_for(self, flavour):
        return getattr(self, '%s_descrs' % flavour.lower())

    def _create_pdb(self, test_descr, flavour):
        self.descrs_for(flavour).append( (len(self.debuggers), test_descr) )
        if self.pdbmode:
            self.debuggers.append(self.pdbclass(sys.exc_info()[2]))

    def _iter_valid_frames(self, frames):
        """only consider non-testlib frames when formatting  traceback"""
        lgc_testlib = osp.abspath(__file__)
        std_testlib = osp.abspath(unittest.__file__)
        invalid = lambda fi: osp.abspath(fi[1]) in (lgc_testlib, std_testlib)
        for frameinfo in dropwhile(invalid, frames):
            yield frameinfo

    def _exc_info_to_string(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string.

        This method is overridden here because we want to colorize
        lines if --color is passed, and display local variables if
        --verbose is passed
        """
        exctype, exc, tb = err
        output = ['Traceback (most recent call last)']
        frames = inspect.getinnerframes(tb)
        colorize = self.colorize
        frames = enumerate(self._iter_valid_frames(frames))
        for index, (frame, filename, lineno, funcname, ctx, ctxindex) in frames:
            filename = osp.abspath(filename)
            if ctx is None: # pyc files or C extensions for instance
                source = '<no source available>'
            else:
                source = ''.join(ctx)
            if colorize:
                filename = textutils.colorize_ansi(filename, 'magenta')
                source = colorize_source(source)
            output.append('  File "%s", line %s, in %s' % (filename, lineno, funcname))
            output.append('    %s' % source.strip())
            if self.verbose:
                output.append('%r == %r' % (dir(frame), test.__module__))
                output.append('')
                output.append('    ' + ' local variables '.center(66, '-'))
                for varname, value in sorted(frame.f_locals.items()):
                    output.append('    %s: %r' % (varname, value))
                    if varname == 'self': # special handy processing for self
                        for varname, value in sorted(vars(value).items()):
                            output.append('      self.%s: %r' % (varname, value))
                output.append('    ' + '-' * 66)
                output.append('')
        output.append(''.join(traceback.format_exception_only(exctype, exc)))
        return '\n'.join(output)

    def addError(self, test, err):
        """err ->  (exc_type, exc, tcbk)"""
        exc_type, exc, _ = err
        if isinstance(exc, SkipTest):
            assert exc_type == SkipTest
            self.addSkip(test, exc)
        else:
            if self.exitfirst:
                self.shouldStop = True
            descr = self.getDescription(test)
            super(SkipAwareTestResult, self).addError(test, err)
            self._create_pdb(descr, 'error')

    def addFailure(self, test, err):
        if self.exitfirst:
            self.shouldStop = True
        descr = self.getDescription(test)
        super(SkipAwareTestResult, self).addFailure(test, err)
        self._create_pdb(descr, 'fail')

    def addSkip(self, test, reason):
        self.skipped.append((test, reason))
        if self.showAll:
            self.stream.writeln("SKIPPED")
        elif self.dots:
            self.stream.write('S')

    def printErrors(self):
        super(SkipAwareTestResult, self).printErrors()
        self.printSkippedList()

    def printSkippedList(self):
        # format (test, err) compatible with unittest2
        for test, err in self.skipped:
            descr = self.getDescription(test)
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % ('SKIPPED', descr))
            self.stream.writeln("\t%s" % err)

    def printErrorList(self, flavour, errors):
        for (_, descr), (test, err) in zip(self.descrs_for(flavour), errors):
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour, descr))
            self.stream.writeln(self.separator2)
            self.stream.writeln(err)
            self.stream.writeln('no stdout'.center(len(self.separator2)))
            self.stream.writeln('no stderr'.center(len(self.separator2)))

# Add deprecation warnings about new api used by module level fixtures in unittest2
# http://www.voidspace.org.uk/python/articles/unittest2.shtml#setupmodule-and-teardownmodule
class _DebugResult(object): # simplify import statement among unittest flavors..
    "Used by the TestSuite to hold previous class when running in debug."
    _previousTestClass = None
    _moduleSetUpFailed = False
    shouldStop = False

from logilab.common.decorators import monkeypatch
@monkeypatch(unittest.TestSuite)
def _handleModuleTearDown(self, result):
    previousModule = self._get_previous_module(result)
    if previousModule is None:
        return
    if result._moduleSetUpFailed:
        return
    try:
        module = sys.modules[previousModule]
    except KeyError:
        return
    # add testlib specific deprecation warning and switch to new api
    if hasattr(module, 'teardown_module'):
        warnings.warn('Please rename teardown_module() to tearDownModule() instead.',
                      DeprecationWarning)
        setattr(module, 'tearDownModule', module.teardown_module)
    # end of monkey-patching
    tearDownModule = getattr(module, 'tearDownModule', None)
    if tearDownModule is not None:
        try:
            tearDownModule()
        except Exception, e:
            if isinstance(result, _DebugResult):
                raise
            errorName = 'tearDownModule (%s)' % previousModule
            self._addClassOrModuleLevelException(result, e, errorName)

@monkeypatch(unittest.TestSuite)
def _handleModuleFixture(self, test, result):
    previousModule = self._get_previous_module(result)
    currentModule = test.__class__.__module__
    if currentModule == previousModule:
        return
    self._handleModuleTearDown(result)
    result._moduleSetUpFailed = False
    try:
        module = sys.modules[currentModule]
    except KeyError:
        return
    # add testlib specific deprecation warning and switch to new api
    if hasattr(module, 'setup_module'):
        warnings.warn('Please rename setup_module() to setUpModule() instead.',
                      DeprecationWarning)
        setattr(module, 'setUpModule', module.setup_module)
    # end of monkey-patching
    setUpModule = getattr(module, 'setUpModule', None)
    if setUpModule is not None:
        try:
            setUpModule()
        except Exception, e:
            if isinstance(result, _DebugResult):
                raise
            result._moduleSetUpFailed = True
            errorName = 'setUpModule (%s)' % currentModule
            self._addClassOrModuleLevelException(result, e, errorName)

# backward compatibility: TestSuite might be imported from lgc.testlib
TestSuite = unittest.TestSuite

class keywords(dict):
    """Keyword args (**kwargs) support for generative tests."""

class starargs(tuple):
    """Variable arguments (*args) for generative tests."""
    def __new__(cls, *args):
        return tuple.__new__(cls, args)

unittest_main = unittest.main


class InnerTestSkipped(SkipTest):
    """raised when a test is skipped"""
    pass

def parse_generative_args(params):
    args = []
    varargs = ()
    kwargs = {}
    flags = 0 # 2 <=> starargs, 4 <=> kwargs
    for param in params:
        if isinstance(param, starargs):
            varargs = param
            if flags:
                raise TypeError('found starargs after keywords !')
            flags |= 2
            args += list(varargs)
        elif isinstance(param, keywords):
            kwargs = param
            if flags & 4:
                raise TypeError('got multiple keywords parameters')
            flags |= 4
        elif flags & 2 or flags & 4:
            raise TypeError('found parameters after kwargs or args')
        else:
            args.append(param)

    return args, kwargs


class InnerTest(tuple):
    def __new__(cls, name, *data):
        instance = tuple.__new__(cls, data)
        instance.name = name
        return instance

class Tags(InheritableSet): # 2.4 compat
    """A set of tag able validate an expression"""

    def __init__(self, *tags, **kwargs):
        self.inherit = kwargs.pop('inherit', True)
        if kwargs:
           raise TypeError("%s are an invalid keyword argument for this function" % kwargs.keys())

        if len(tags) == 1 and not isinstance(tags[0], basestring):
            tags = tags[0]
        super(Tags, self).__init__(tags, **kwargs)

    def __getitem__(self, key):
        return key in self

    def match(self, exp):
        return eval(exp, {}, self)


# duplicate definition from unittest2 of the _deprecate decorator
def _deprecate(original_func):
    def deprecated_func(*args, **kwargs):
        warnings.warn(
            ('Please use %s instead.' % original_func.__name__),
            DeprecationWarning, 2)
        return original_func(*args, **kwargs)
    return deprecated_func

class TestCase(unittest.TestCase):
    """A unittest.TestCase extension with some additional methods."""
    maxDiff = None
    pdbclass = Debugger
    tags = Tags()

    def __init__(self, methodName='runTest'):
        super(TestCase, self).__init__(methodName)
        # internal API changed in python2.4 and needed by DocTestCase
        if sys.version_info >= (2, 4):
            self.__exc_info = sys.exc_info
            self.__testMethodName = self._testMethodName
        else:
            # let's give easier access to _testMethodName to every subclasses
            if hasattr(self, "__testMethodName"):
                self._testMethodName = self.__testMethodName
        self._current_test_descr = None
        self._options_ = None

    @classproperty
    @cached
    def datadir(cls): # pylint: disable=E0213
        """helper attribute holding the standard test's data directory

        NOTE: this is a logilab's standard
        """
        mod = __import__(cls.__module__)
        return osp.join(osp.dirname(osp.abspath(mod.__file__)), 'data')
    # cache it (use a class method to cache on class since TestCase is
    # instantiated for each test run)

    @classmethod
    def datapath(cls, *fname):
        """joins the object's datadir and `fname`"""
        return osp.join(cls.datadir, *fname)

    def set_description(self, descr):
        """sets the current test's description.
        This can be useful for generative tests because it allows to specify
        a description per yield
        """
        self._current_test_descr = descr

    # override default's unittest.py feature
    def shortDescription(self):
        """override default unittest shortDescription to handle correctly
        generative tests
        """
        if self._current_test_descr is not None:
            return self._current_test_descr
        return super(TestCase, self).shortDescription()

    def quiet_run(self, result, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            result.addError(self, self.__exc_info())
            return False
        return True

    def _get_test_method(self):
        """return the test method"""
        return getattr(self, self._testMethodName)

    def optval(self, option, default=None):
        """return the option value or default if the option is not define"""
        return getattr(self._options_, option, default)

    def __call__(self, result=None, runcondition=None, options=None):
        """rewrite TestCase.__call__ to support generative tests
        This is mostly a copy/paste from unittest.py (i.e same
        variable names, same logic, except for the generative tests part)
        """
        from logilab.common.pytest import FILE_RESTART
        if result is None:
            result = self.defaultTestResult()
        result.pdbclass = self.pdbclass
        self._options_ = options
        # if result.cvg:
        #     result.cvg.start()
        testMethod = self._get_test_method()
        if runcondition and not runcondition(testMethod):
            return # test is skipped
        result.startTest(self)
        try:
            if not self.quiet_run(result, self.setUp):
                return
            generative = is_generator(testMethod.im_func)
            # generative tests
            if generative:
                self._proceed_generative(result, testMethod,
                                         runcondition)
            else:
                status = self._proceed(result, testMethod)
                success = (status == 0)
            if not self.quiet_run(result, self.tearDown):
                return
            if not generative and success:
                if hasattr(options, "exitfirst") and options.exitfirst:
                    # add this test to restart file
                    try:
                        restartfile = open(FILE_RESTART, 'a')
                        try:
                            descr = '.'.join((self.__class__.__module__,
                                              self.__class__.__name__,
                                              self._testMethodName))
                            restartfile.write(descr+os.linesep)
                        finally:
                            restartfile.close()
                    except Exception, ex:
                        print >> sys.__stderr__, "Error while saving \
succeeded test into", osp.join(os.getcwd(), FILE_RESTART)
                        raise ex
                result.addSuccess(self)
        finally:
            # if result.cvg:
            #     result.cvg.stop()
            result.stopTest(self)

    def _proceed_generative(self, result, testfunc, runcondition=None):
        # cancel startTest()'s increment
        result.testsRun -= 1
        success = True
        try:
            for params in testfunc():
                if runcondition and not runcondition(testfunc,
                        skipgenerator=False):
                    if not (isinstance(params, InnerTest)
                            and runcondition(params)):
                        continue
                if not isinstance(params, (tuple, list)):
                    params = (params, )
                func = params[0]
                args, kwargs = parse_generative_args(params[1:])
                # increment test counter manually
                result.testsRun += 1
                status = self._proceed(result, func, args, kwargs)
                if status == 0:
                    result.addSuccess(self)
                    success = True
                else:
                    success = False
                    # XXX Don't stop anymore if an error occured
                    #if status == 2:
                    #    result.shouldStop = True
                if result.shouldStop: # either on error or on exitfirst + error
                    break
        except:
            # if an error occurs between two yield
            result.addError(self, self.__exc_info())
            success = False
        return success

    def _proceed(self, result, testfunc, args=(), kwargs=None):
        """proceed the actual test
        returns 0 on success, 1 on failure, 2 on error

        Note: addSuccess can't be called here because we have to wait
        for tearDown to be successfully executed to declare the test as
        successful
        """
        kwargs = kwargs or {}
        try:
            testfunc(*args, **kwargs)
        except self.failureException:
            result.addFailure(self, self.__exc_info())
            return 1
        except KeyboardInterrupt:
            raise
        except InnerTestSkipped, e:
            result.addSkip(self, e)
            return 1
        except SkipTest, e:
            result.addSkip(self, e)
            return 0
        except:
            result.addError(self, self.__exc_info())
            return 2
        return 0

    def defaultTestResult(self):
        """return a new instance of the defaultTestResult"""
        return SkipAwareTestResult()

    skip = _deprecate(unittest.TestCase.skipTest)
    assertEquals = _deprecate(unittest.TestCase.assertEqual)
    assertNotEquals = _deprecate(unittest.TestCase.assertNotEqual)
    assertAlmostEquals = _deprecate(unittest.TestCase.assertAlmostEqual)
    assertNotAlmostEquals = _deprecate(unittest.TestCase.assertNotAlmostEqual)

    def innerSkip(self, msg=None):
        """mark a generative test as skipped for the <msg> reason"""
        msg = msg or 'test was skipped'
        raise InnerTestSkipped(msg)

    @deprecated('Please use assertDictEqual instead.')
    def assertDictEquals(self, dict1, dict2, msg=None, context=None):
        """compares two dicts

        If the two dict differ, the first difference is shown in the error
        message
        :param dict1: a Python Dictionary
        :param dict2: a Python Dictionary
        :param msg: custom message (String) in case of failure
        """
        dict1 = dict(dict1)
        msgs = []
        for key, value in dict2.items():
            try:
                if dict1[key] != value:
                    msgs.append('%r != %r for key %r' % (dict1[key], value,
                        key))
                del dict1[key]
            except KeyError:
                msgs.append('missing %r key' % key)
        if dict1:
            msgs.append('dict2 is lacking %r' % dict1)
        if msg:
            self.failureException(msg)
        elif msgs:
            if context is not None:
                base = '%s\n' % context
            else:
                base = ''
            self.fail(base + '\n'.join(msgs))

    @deprecated('Please use assertItemsEqual instead.')
    def assertUnorderedIterableEquals(self, got, expected, msg=None):
        """compares two iterable and shows difference between both

        :param got: the unordered Iterable that we found
        :param expected: the expected unordered Iterable
        :param msg: custom message (String) in case of failure
        """
        got, expected = list(got), list(expected)
        self.assertSetEqual(set(got), set(expected), msg)
        if len(got) != len(expected):
            if msg is None:
                msg = ['Iterable have the same elements but not the same number',
                       '\t<element>\t<expected>i\t<got>']
                got_count = {}
                expected_count = {}
                for element in got:
                    got_count[element] = got_count.get(element, 0) + 1
                for element in expected:
                    expected_count[element] = expected_count.get(element, 0) + 1
                # we know that got_count.key() == expected_count.key()
                # because of assertSetEqual
                for element, count in got_count.iteritems():
                    other_count = expected_count[element]
                    if other_count != count:
                        msg.append('\t%s\t%s\t%s' % (element, other_count, count))

            self.fail(msg)

    assertUnorderedIterableEqual = assertUnorderedIterableEquals
    assertUnordIterEquals = assertUnordIterEqual = assertUnorderedIterableEqual

    @deprecated('Please use assertSetEqual instead.')
    def assertSetEquals(self,got,expected, msg=None):
        """compares two sets and shows difference between both

        Don't use it for iterables other than sets.

        :param got: the Set that we found
        :param expected: the second Set to be compared to the first one
        :param msg: custom message (String) in case of failure
        """

        if not(isinstance(got, set) and isinstance(expected, set)):
            warnings.warn("the assertSetEquals function if now intended for set only."\
                          "use assertUnorderedIterableEquals instead.",
                DeprecationWarning, 2)
            return self.assertUnorderedIterableEquals(got, expected, msg)

        items={}
        items['missing'] = expected - got
        items['unexpected'] = got - expected
        if any(items.itervalues()):
            if msg is None:
                msg = '\n'.join('%s:\n\t%s' % (key, "\n\t".join(str(value) for value in values))
                    for key, values in items.iteritems() if values)
            self.fail(msg)

    @deprecated('Please use assertListEqual instead.')
    def assertListEquals(self, list_1, list_2, msg=None):
        """compares two lists

        If the two list differ, the first difference is shown in the error
        message

        :param list_1: a Python List
        :param list_2: a second Python List
        :param msg: custom message (String) in case of failure
        """
        _l1 = list_1[:]
        for i, value in enumerate(list_2):
            try:
                if _l1[0] != value:
                    from pprint import pprint
                    pprint(list_1)
                    pprint(list_2)
                    self.fail('%r != %r for index %d' % (_l1[0], value, i))
                del _l1[0]
            except IndexError:
                if msg is None:
                    msg = 'list_1 has only %d elements, not %s '\
                        '(at least %r missing)'% (i, len(list_2), value)
                self.fail(msg)
        if _l1:
            if msg is None:
                msg = 'list_2 is lacking %r' % _l1
            self.fail(msg)

    @deprecated('Non-standard. Please use assertMultiLineEqual instead.')
    def assertLinesEquals(self, string1, string2, msg=None, striplines=False):
        """compare two strings and assert that the text lines of the strings
        are equal.

        :param string1: a String
        :param string2: a String
        :param msg: custom message (String) in case of failure
        :param striplines: Boolean to trigger line stripping before comparing
        """
        lines1 = string1.splitlines()
        lines2 = string2.splitlines()
        if striplines:
            lines1 = [l.strip() for l in lines1]
            lines2 = [l.strip() for l in lines2]
        self.assertListEqual(lines1, lines2, msg)
    assertLineEqual = assertLinesEquals

    @deprecated('Non-standard: please copy test method to your TestCase class')
    def assertXMLWellFormed(self, stream, msg=None, context=2):
        """asserts the XML stream is well-formed (no DTD conformance check)

        :param context: number of context lines in standard message
                        (show all data if negative).
                        Only available with element tree
        """
        try:
            from xml.etree.ElementTree import parse
            self._assertETXMLWellFormed(stream, parse, msg)
        except ImportError:
            from xml.sax import make_parser, SAXParseException
            parser = make_parser()
            try:
                parser.parse(stream)
            except SAXParseException, ex:
                if msg is None:
                    stream.seek(0)
                    for _ in xrange(ex.getLineNumber()):
                        line = stream.readline()
                    pointer = ('' * (ex.getLineNumber() - 1)) + '^'
                    msg = 'XML stream not well formed: %s\n%s%s' % (ex, line, pointer)
                self.fail(msg)

    @deprecated('Non-standard: please copy test method to your TestCase class')
    def assertXMLStringWellFormed(self, xml_string, msg=None, context=2):
        """asserts the XML string is well-formed (no DTD conformance check)

        :param context: number of context lines in standard message
                        (show all data if negative).
                        Only available with element tree
        """
        try:
            from xml.etree.ElementTree import fromstring
        except ImportError:
            from elementtree.ElementTree import fromstring
        self._assertETXMLWellFormed(xml_string, fromstring, msg)

    def _assertETXMLWellFormed(self, data, parse, msg=None, context=2):
        """internal function used by /assertXML(String)?WellFormed/ functions

        :param data: xml_data
        :param parse: appropriate parser function for this data
        :param msg: error message
        :param context: number of context lines in standard message
                        (show all data if negative).
                        Only available with element tree
        """
        from xml.parsers.expat import ExpatError
        try:
            from xml.etree.ElementTree import ParseError
        except ImportError:
            # compatibility for <python2.7
            ParseError = ExpatError
        try:
            parse(data)
        except (ExpatError, ParseError), ex:
            if msg is None:
                if hasattr(data, 'readlines'): #file like object
                    data.seek(0)
                    lines = data.readlines()
                else:
                    lines = data.splitlines(True)
                nb_lines = len(lines)
                context_lines = []

                # catch when ParseError doesn't set valid lineno
                if ex.lineno is not None:
                    if context < 0:
                        start = 1
                        end   = nb_lines
                    else:
                        start = max(ex.lineno-context, 1)
                        end   = min(ex.lineno+context, nb_lines)
                    line_number_length = len('%i' % end)
                    line_pattern = " %%%ii: %%s" % line_number_length

                    for line_no in xrange(start, ex.lineno):
                        context_lines.append(line_pattern % (line_no, lines[line_no-1]))
                    context_lines.append(line_pattern % (ex.lineno, lines[ex.lineno-1]))
                    context_lines.append('%s^\n' % (' ' * (1 + line_number_length + 2 +ex.offset)))
                    for line_no in xrange(ex.lineno+1, end+1):
                        context_lines.append(line_pattern % (line_no, lines[line_no-1]))

                rich_context = ''.join(context_lines)
                msg = 'XML stream not well formed: %s\n%s' % (ex, rich_context)
            self.fail(msg)

    @deprecated('Non-standard: please copy test method to your TestCase class')
    def assertXMLEqualsTuple(self, element, tup):
        """compare an ElementTree Element to a tuple formatted as follow:
        (tagname, [attrib[, children[, text[, tail]]]])"""
        # check tag
        self.assertTextEquals(element.tag, tup[0])
        # check attrib
        if len(element.attrib) or len(tup)>1:
            if len(tup)<=1:
                self.fail( "tuple %s has no attributes (%s expected)"%(tup,
                    dict(element.attrib)))
            self.assertDictEqual(element.attrib, tup[1])
        # check children
        if len(element) or len(tup)>2:
            if len(tup)<=2:
                self.fail( "tuple %s has no children (%i expected)"%(tup,
                    len(element)))
            if len(element) != len(tup[2]):
                self.fail( "tuple %s has %i children%s (%i expected)"%(tup,
                    len(tup[2]),
                        ('', 's')[len(tup[2])>1], len(element)))
            for index in xrange(len(tup[2])):
                self.assertXMLEqualsTuple(element[index], tup[2][index])
        #check text
        if element.text or len(tup)>3:
            if len(tup)<=3:
                self.fail( "tuple %s has no text value (%r expected)"%(tup,
                    element.text))
            self.assertTextEquals(element.text, tup[3])
        #check tail
        if element.tail or len(tup)>4:
            if len(tup)<=4:
                self.fail( "tuple %s has no tail value (%r expected)"%(tup,
                    element.tail))
            self.assertTextEquals(element.tail, tup[4])

    def _difftext(self, lines1, lines2, junk=None, msg_prefix='Texts differ'):
        junk = junk or (' ', '\t')
        # result is a generator
        result = difflib.ndiff(lines1, lines2, charjunk=lambda x: x in junk)
        read = []
        for line in result:
            read.append(line)
            # lines that don't start with a ' ' are diff ones
            if not line.startswith(' '):
                self.fail('\n'.join(['%s\n'%msg_prefix]+read + list(result)))

    @deprecated('Non-standard. Please use assertMultiLineEqual instead.')
    def assertTextEquals(self, text1, text2, junk=None,
            msg_prefix='Text differ', striplines=False):
        """compare two multiline strings (using difflib and splitlines())

        :param text1: a Python BaseString
        :param text2: a second Python Basestring
        :param junk: List of Caracters
        :param msg_prefix: String (message prefix)
        :param striplines: Boolean to trigger line stripping before comparing
        """
        msg = []
        if not isinstance(text1, basestring):
            msg.append('text1 is not a string (%s)'%(type(text1)))
        if not isinstance(text2, basestring):
            msg.append('text2 is not a string (%s)'%(type(text2)))
        if msg:
            self.fail('\n'.join(msg))
        lines1 = text1.strip().splitlines(True)
        lines2 = text2.strip().splitlines(True)
        if striplines:
            lines1 = [line.strip() for line in lines1]
            lines2 = [line.strip() for line in lines2]
        self._difftext(lines1, lines2, junk,  msg_prefix)
    assertTextEqual = assertTextEquals

    @deprecated('Non-standard: please copy test method to your TestCase class')
    def assertStreamEquals(self, stream1, stream2, junk=None,
            msg_prefix='Stream differ'):
        """compare two streams (using difflib and readlines())"""
        # if stream2 is stream2, readlines() on stream1 will also read lines
        # in stream2, so they'll appear different, although they're not
        if stream1 is stream2:
            return
        # make sure we compare from the beginning of the stream
        stream1.seek(0)
        stream2.seek(0)
        # compare
        self._difftext(stream1.readlines(), stream2.readlines(), junk,
             msg_prefix)

    assertStreamEqual = assertStreamEquals

    @deprecated('Non-standard: please copy test method to your TestCase class')
    def assertFileEquals(self, fname1, fname2, junk=(' ', '\t')):
        """compares two files using difflib"""
        self.assertStreamEqual(open(fname1), open(fname2), junk,
            msg_prefix='Files differs\n-:%s\n+:%s\n'%(fname1, fname2))

    assertFileEqual = assertFileEquals

    @deprecated('Non-standard: please copy test method to your TestCase class')
    def assertDirEquals(self, path_a, path_b):
        """compares two files using difflib"""
        assert osp.exists(path_a), "%s doesn't exists" % path_a
        assert osp.exists(path_b), "%s doesn't exists" % path_b

        all_a = [ (ipath[len(path_a):].lstrip('/'), idirs, ifiles)
                    for ipath, idirs, ifiles in os.walk(path_a)]
        all_a.sort(key=itemgetter(0))

        all_b = [ (ipath[len(path_b):].lstrip('/'), idirs, ifiles)
                    for ipath, idirs, ifiles in os.walk(path_b)]
        all_b.sort(key=itemgetter(0))

        iter_a, iter_b = iter(all_a), iter(all_b)
        partial_iter = True
        ipath_a, idirs_a, ifiles_a = data_a = None, None, None
        while True:
            try:
                ipath_a, idirs_a, ifiles_a = datas_a = iter_a.next()
                partial_iter = False
                ipath_b, idirs_b, ifiles_b = datas_b = iter_b.next()
                partial_iter = True


                self.assertTrue(ipath_a == ipath_b,
                    "unexpected %s in %s while looking %s from %s" %
                    (ipath_a, path_a, ipath_b, path_b))


                errors = {}
                sdirs_a = set(idirs_a)
                sdirs_b = set(idirs_b)
                errors["unexpected directories"] = sdirs_a - sdirs_b
                errors["missing directories"] = sdirs_b - sdirs_a

                sfiles_a = set(ifiles_a)
                sfiles_b = set(ifiles_b)
                errors["unexpected files"] = sfiles_a - sfiles_b
                errors["missing files"] = sfiles_b - sfiles_a


                msgs = [ "%s: %s"% (name, items)
                    for name, items in errors.iteritems() if items]

                if msgs:
                    msgs.insert(0, "%s and %s differ :" % (
                        osp.join(path_a, ipath_a),
                        osp.join(path_b, ipath_b),
                        ))
                    self.fail("\n".join(msgs))

                for files in (ifiles_a, ifiles_b):
                    files.sort()

                for index, path in enumerate(ifiles_a):
                    self.assertFileEquals(osp.join(path_a, ipath_a, path),
                        osp.join(path_b, ipath_b, ifiles_b[index]))

            except StopIteration:
                break

    assertDirEqual = assertDirEquals

    def assertIsInstance(self, obj, klass, msg=None, strict=False):
        """check if an object is an instance of a class

        :param obj: the Python Object to be checked
        :param klass: the target class
        :param msg: a String for a custom message
        :param strict: if True, check that the class of <obj> is <klass>;
                       else check with 'isinstance'
        """
        if strict:
            warnings.warn('[API] Non-standard. Strict parameter has vanished',
                          DeprecationWarning, stacklevel=2)
        if msg is None:
            if strict:
                msg = '%r is not of class %s but of %s'
            else:
                msg = '%r is not an instance of %s but of %s'
            msg = msg % (obj, klass, type(obj))
        if strict:
            self.assertTrue(obj.__class__ is klass, msg)
        else:
            self.assertTrue(isinstance(obj, klass), msg)

    @deprecated('Please use assertIsNone instead.')
    def assertNone(self, obj, msg=None):
        """assert obj is None

        :param obj: Python Object to be tested
        """
        if msg is None:
            msg = "reference to %r when None expected"%(obj,)
        self.assertTrue( obj is None, msg )

    @deprecated('Please use assertIsNotNone instead.')
    def assertNotNone(self, obj, msg=None):
        """assert obj is not None"""
        if msg is None:
            msg = "unexpected reference to None"
        self.assertTrue( obj is not None, msg )

    @deprecated('Non-standard. Please use assertAlmostEqual instead.')
    def assertFloatAlmostEquals(self, obj, other, prec=1e-5,
                                relative=False, msg=None):
        """compares if two floats have a distance smaller than expected
        precision.

        :param obj: a Float
        :param other: another Float to be comparted to <obj>
        :param prec: a Float describing the precision
        :param relative: boolean switching to relative/absolute precision
        :param msg: a String for a custom message
        """
        if msg is None:
            msg = "%r != %r" % (obj, other)
        if relative:
            prec = prec*math.fabs(obj)
        self.assertTrue(math.fabs(obj - other) < prec, msg)

    def failUnlessRaises(self, excClass, callableObj=None, *args, **kwargs):
        """override default failUnlessRaises method to return the raised
        exception instance.

        Fail unless an exception of class excClass is thrown
        by callableObj when invoked with arguments args and keyword
        arguments kwargs. If a different type of exception is
        thrown, it will not be caught, and the test case will be
        deemed to have suffered an error, exactly as for an
        unexpected exception.

        CAUTION! There are subtle differences between Logilab and unittest2
        - exc is not returned in standard version
        - context capabilities in standard version
        - try/except/else construction (minor)

        :param excClass: the Exception to be raised
        :param callableObj: a callable Object which should raise <excClass>
        :param args: a List of arguments for <callableObj>
        :param kwargs: a List of keyword arguments  for <callableObj>
        """
        # XXX cube vcslib : test_branches_from_app
        if callableObj is None:
            _assert = super(TestCase, self).assertRaises
            return _assert(excClass, callableObj, *args, **kwargs)
        try:
            callableObj(*args, **kwargs)
        except excClass, exc:
            class ProxyException:
                def __init__(self, obj):
                    self._obj = obj
                def __getattr__(self, attr):
                    warn_msg = ("This exception was retrieved with the old testlib way "
                                "`exc = self.assertRaises(Exc, callable)`, please use "
                                "the context manager instead'")
                    warnings.warn(warn_msg, DeprecationWarning, 2)
                    return self._obj.__getattribute__(attr)
            return ProxyException(exc)
        else:
            if hasattr(excClass, '__name__'):
                excName = excClass.__name__
            else:
                excName = str(excClass)
            raise self.failureException("%s not raised" % excName)

    assertRaises = failUnlessRaises

    if not hasattr(unittest.TestCase, 'assertItemsEqual'):
        # python 3.2 has deprecated assertSameElements and is missing
        # assertItemsEqual
        assertItemsEqual = unittest.TestCase.assertSameElements

import doctest

class SkippedSuite(unittest.TestSuite):
    def test(self):
        """just there to trigger test execution"""
        self.skipped_test('doctest module has no DocTestSuite class')


class DocTestFinder(doctest.DocTestFinder):

    def __init__(self, *args, **kwargs):
        self.skipped = kwargs.pop('skipped', ())
        doctest.DocTestFinder.__init__(self, *args, **kwargs)

    def _get_test(self, obj, name, module, globs, source_lines):
        """override default _get_test method to be able to skip tests
        according to skipped attribute's value

        Note: Python (<=2.4) use a _name_filter which could be used for that
              purpose but it's no longer available in 2.5
              Python 2.5 seems to have a [SKIP] flag
        """
        if getattr(obj, '__name__', '') in self.skipped:
            return None
        return doctest.DocTestFinder._get_test(self, obj, name, module,
                                               globs, source_lines)


class DocTest(TestCase):
    """trigger module doctest
    I don't know how to make unittest.main consider the DocTestSuite instance
    without this hack
    """
    skipped = ()
    def __call__(self, result=None, runcondition=None, options=None):\
        # pylint: disable=W0613
        try:
            finder = DocTestFinder(skipped=self.skipped)
            if sys.version_info >= (2, 4):
                suite = doctest.DocTestSuite(self.module, test_finder=finder)
                if sys.version_info >= (2, 5):
                    # XXX iirk
                    doctest.DocTestCase._TestCase__exc_info = sys.exc_info
            else:
                suite = doctest.DocTestSuite(self.module)
        except AttributeError:
            suite = SkippedSuite()
        # doctest may gork the builtins dictionnary
        # This happen to the "_" entry used by gettext
        old_builtins = builtins.__dict__.copy()
        try:
            return suite.run(result)
        finally:
            builtins.__dict__.clear()
            builtins.__dict__.update(old_builtins)
    run = __call__

    def test(self):
        """just there to trigger test execution"""

MAILBOX = None

class MockSMTP:
    """fake smtplib.SMTP"""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        global MAILBOX
        self.reveived = MAILBOX = []

    def set_debuglevel(self, debuglevel):
        """ignore debug level"""

    def sendmail(self, fromaddr, toaddres, body):
        """push sent mail in the mailbox"""
        self.reveived.append((fromaddr, toaddres, body))

    def quit(self):
        """ignore quit"""


class MockConfigParser(ConfigParser):
    """fake ConfigParser.ConfigParser"""

    def __init__(self, options):
        ConfigParser.__init__(self)
        for section, pairs in options.iteritems():
            self.add_section(section)
            for key, value in pairs.iteritems():
                self.set(section, key, value)
    def write(self, _):
        raise NotImplementedError()


class MockConnection:
    """fake DB-API 2.0 connexion AND cursor (i.e. cursor() return self)"""

    def __init__(self, results):
        self.received = []
        self.states = []
        self.results = results

    def cursor(self):
        """Mock cursor method"""
        return self
    def execute(self, query, args=None):
        """Mock execute method"""
        self.received.append( (query, args) )
    def fetchone(self):
        """Mock fetchone method"""
        return self.results[0]
    def fetchall(self):
        """Mock fetchall method"""
        return self.results
    def commit(self):
        """Mock commiy method"""
        self.states.append( ('commit', len(self.received)) )
    def rollback(self):
        """Mock rollback method"""
        self.states.append( ('rollback', len(self.received)) )
    def close(self):
        """Mock close method"""
        pass


def mock_object(**params):
    """creates an object using params to set attributes
    >>> option = mock_object(verbose=False, index=range(5))
    >>> option.verbose
    False
    >>> option.index
    [0, 1, 2, 3, 4]
    """
    return type('Mock', (), params)()


def create_files(paths, chroot):
    """Creates directories and files found in <path>.

    :param paths: list of relative paths to files or directories
    :param chroot: the root directory in which paths will be created

    >>> from os.path import isdir, isfile
    >>> isdir('/tmp/a')
    False
    >>> create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], '/tmp')
    >>> isdir('/tmp/a')
    True
    >>> isdir('/tmp/a/b/c')
    True
    >>> isfile('/tmp/a/b/c/d/e.py')
    True
    >>> isfile('/tmp/a/b/foo.py')
    True
    """
    dirs, files = set(), set()
    for path in paths:
        path = osp.join(chroot, path)
        filename = osp.basename(path)
        # path is a directory path
        if filename == '':
            dirs.add(path)
        # path is a filename path
        else:
            dirs.add(osp.dirname(path))
            files.add(path)
    for dirpath in dirs:
        if not osp.isdir(dirpath):
            os.makedirs(dirpath)
    for filepath in files:
        open(filepath, 'w').close()


class AttrObject: # XXX cf mock_object
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def tag(*args, **kwargs):
    """descriptor adding tag to a function"""
    def desc(func):
        assert not hasattr(func, 'tags')
        func.tags = Tags(*args, **kwargs)
        return func
    return desc

def require_version(version):
    """ Compare version of python interpreter to the given one. Skip the test
    if older.
    """
    def check_require_version(f):
        version_elements = version.split('.')
        try:
            compare = tuple([int(v) for v in version_elements])
        except ValueError:
            raise ValueError('%s is not a correct version : should be X.Y[.Z].' % version)
        current = sys.version_info[:3]
        if current < compare:
            def new_f(self, *args, **kwargs):
                self.skipTest('Need at least %s version of python. Current version is %s.' % (version, '.'.join([str(element) for element in current])))
            new_f.__name__ = f.__name__
            return new_f
        else:
            return f
    return check_require_version

def require_module(module):
    """ Check if the given module is loaded. Skip the test if not.
    """
    def check_require_module(f):
        try:
            __import__(module)
            return f
        except ImportError:
            def new_f(self, *args, **kwargs):
                self.skipTest('%s can not be imported.' % module)
            new_f.__name__ = f.__name__
            return new_f
    return check_require_module

