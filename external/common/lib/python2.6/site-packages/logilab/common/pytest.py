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
"""pytest is a tool that eases test running and debugging.

To be able to use pytest, you should either write tests using
the logilab.common.testlib's framework or the unittest module of the
Python's standard library.

You can customize pytest's behaviour by defining a ``pytestconf.py`` file
somewhere in your test directory. In this file, you can add options or
change the way tests are run.

To add command line options, you must define a ``update_parser`` function in
your ``pytestconf.py`` file. The function must accept a single parameter
that will be the OptionParser's instance to customize.

If you wish to customize the tester, you'll have to define a class named
``CustomPyTester``. This class should extend the default `PyTester` class
defined in the pytest module. Take a look at the `PyTester` and `DjangoTester`
classes for more information about what can be done.

For instance, if you wish to add a custom -l option to specify a loglevel, you
could define the following ``pytestconf.py`` file ::

    import logging
    from logilab.common.pytest import PyTester

    def update_parser(parser):
        parser.add_option('-l', '--loglevel', dest='loglevel', action='store',
                          choices=('debug', 'info', 'warning', 'error', 'critical'),
                          default='critical', help="the default log level possible choices are "
                          "('debug', 'info', 'warning', 'error', 'critical')")
        return parser


    class CustomPyTester(PyTester):
        def __init__(self, cvg, options):
            super(CustomPyTester, self).__init__(cvg, options)
            loglevel = options.loglevel.upper()
            logger = logging.getLogger('erudi')
            logger.setLevel(logging.getLevelName(loglevel))


In your TestCase class you can then get the value of a specific option with
the ``optval`` method::

    class MyTestCase(TestCase):
        def test_foo(self):
            loglevel = self.optval('loglevel')
            # ...


You can also tag your tag your test for fine filtering

With those tag::

    from logilab.common.testlib import tag, TestCase

    class Exemple(TestCase):

        @tag('rouge', 'carre')
        def toto(self):
            pass

        @tag('carre', 'vert')
        def tata(self):
            pass

        @tag('rouge')
        def titi(test):
            pass

you can filter the function with a simple python expression

 * ``toto`` and ``titi`` match ``rouge``
 * ``toto``, ``tata`` and ``titi``, match ``rouge or carre``
 * ``tata`` and ``titi`` match``rouge ^ carre``
 * ``titi`` match ``rouge and not carre``
"""
__docformat__ = "restructuredtext en"

PYTEST_DOC = """%prog [OPTIONS] [testfile [testpattern]]

examples:

pytest path/to/mytests.py
pytest path/to/mytests.py TheseTests
pytest path/to/mytests.py TheseTests.test_thisone
pytest path/to/mytests.py -m '(not long and database) or regr'

pytest one (will run both test_thisone and test_thatone)
pytest path/to/mytests.py -s not (will skip test_notthisone)

pytest --coverage test_foo.py
  (only if logilab.devtools is available)
"""

ENABLE_DBC = False
FILE_RESTART = ".pytest.restart"

import os, sys, re
import os.path as osp
from time import time, clock
import warnings
import types

from logilab.common.fileutils import abspath_listdir
from logilab.common import textutils
from logilab.common import testlib, STD_BLACKLIST
# use the same unittest module as testlib
from logilab.common.testlib import unittest, start_interactive_mode
from logilab.common.compat import any
import doctest

import unittest as unittest_legacy
if not getattr(unittest_legacy, "__package__", None):
    try:
        import unittest2.suite as unittest_suite
    except ImportError:
        sys.exit("You have to install python-unittest2 to use this module")
else:
    import unittest.suite as unittest_suite

try:
    import django
    from logilab.common.modutils import modpath_from_file, load_module_from_modpath
    DJANGO_FOUND = True
except ImportError:
    DJANGO_FOUND = False

CONF_FILE = 'pytestconf.py'

## coverage hacks, do not read this, do not read this, do not read this

# hey, but this is an aspect, right ?!!!
class TraceController(object):
    nesting = 0

    def pause_tracing(cls):
        if not cls.nesting:
            cls.tracefunc = staticmethod(getattr(sys, '__settrace__', sys.settrace))
            cls.oldtracer = getattr(sys, '__tracer__', None)
            sys.__notrace__ = True
            cls.tracefunc(None)
        cls.nesting += 1
    pause_tracing = classmethod(pause_tracing)

    def resume_tracing(cls):
        cls.nesting -= 1
        assert cls.nesting >= 0
        if not cls.nesting:
            cls.tracefunc(cls.oldtracer)
            delattr(sys, '__notrace__')
    resume_tracing = classmethod(resume_tracing)


pause_tracing = TraceController.pause_tracing
resume_tracing = TraceController.resume_tracing


def nocoverage(func):
    if hasattr(func, 'uncovered'):
        return func
    func.uncovered = True
    def not_covered(*args, **kwargs):
        pause_tracing()
        try:
            return func(*args, **kwargs)
        finally:
            resume_tracing()
    not_covered.uncovered = True
    return not_covered


## end of coverage hacks


TESTFILE_RE = re.compile("^((unit)?test.*|smoketest)\.py$")
def this_is_a_testfile(filename):
    """returns True if `filename` seems to be a test file"""
    return TESTFILE_RE.match(osp.basename(filename))

TESTDIR_RE = re.compile("^(unit)?tests?$")
def this_is_a_testdir(dirpath):
    """returns True if `filename` seems to be a test directory"""
    return TESTDIR_RE.match(osp.basename(dirpath))


def load_pytest_conf(path, parser):
    """loads a ``pytestconf.py`` file and update default parser
    and / or tester.
    """
    namespace = {}
    execfile(path, namespace)
    if 'update_parser' in namespace:
        namespace['update_parser'](parser)
    return namespace.get('CustomPyTester', PyTester)


def project_root(parser, projdir=os.getcwd()):
    """try to find project's root and add it to sys.path"""
    previousdir = curdir = osp.abspath(projdir)
    testercls = PyTester
    conf_file_path = osp.join(curdir, CONF_FILE)
    if osp.isfile(conf_file_path):
        testercls = load_pytest_conf(conf_file_path, parser)
    while this_is_a_testdir(curdir) or \
              osp.isfile(osp.join(curdir, '__init__.py')):
        newdir = osp.normpath(osp.join(curdir, os.pardir))
        if newdir == curdir:
            break
        previousdir = curdir
        curdir = newdir
        conf_file_path = osp.join(curdir, CONF_FILE)
        if osp.isfile(conf_file_path):
            testercls = load_pytest_conf(conf_file_path, parser)
    return previousdir, testercls


class GlobalTestReport(object):
    """this class holds global test statistics"""
    def __init__(self):
        self.ran = 0
        self.skipped = 0
        self.failures = 0
        self.errors = 0
        self.ttime = 0
        self.ctime = 0
        self.modulescount = 0
        self.errmodules = []

    def feed(self, filename, testresult, ttime, ctime):
        """integrates new test information into internal statistics"""
        ran = testresult.testsRun
        self.ran += ran
        self.skipped += len(getattr(testresult, 'skipped', ()))
        self.failures += len(testresult.failures)
        self.errors += len(testresult.errors)
        self.ttime += ttime
        self.ctime += ctime
        self.modulescount += 1
        if not testresult.wasSuccessful():
            problems = len(testresult.failures) + len(testresult.errors)
            self.errmodules.append((filename[:-3], problems, ran))

    def failed_to_test_module(self, filename):
        """called when the test module could not be imported by unittest
        """
        self.errors += 1
        self.modulescount += 1
        self.ran += 1
        self.errmodules.append((filename[:-3], 1, 1))

    def skip_module(self, filename):
        self.modulescount += 1
        self.ran += 1
        self.errmodules.append((filename[:-3], 0, 0))

    def __str__(self):
        """this is just presentation stuff"""
        line1 = ['Ran %s test cases in %.2fs (%.2fs CPU)'
                 % (self.ran, self.ttime, self.ctime)]
        if self.errors:
            line1.append('%s errors' % self.errors)
        if self.failures:
            line1.append('%s failures' % self.failures)
        if self.skipped:
            line1.append('%s skipped' % self.skipped)
        modulesok = self.modulescount - len(self.errmodules)
        if self.errors or self.failures:
            line2 = '%s modules OK (%s failed)' % (modulesok,
                                                   len(self.errmodules))
            descr = ', '.join(['%s [%s/%s]' % info for info in self.errmodules])
            line3 = '\nfailures: %s' % descr
        elif modulesok:
            line2 = 'All %s modules OK' % modulesok
            line3 = ''
        else:
            return ''
        return '%s\n%s%s' % (', '.join(line1), line2, line3)



def remove_local_modules_from_sys(testdir):
    """remove all modules from cache that come from `testdir`

    This is used to avoid strange side-effects when using the
    testall() mode of pytest.
    For instance, if we run pytest on this tree::

      A/test/test_utils.py
      B/test/test_utils.py

    we **have** to clean sys.modules to make sure the correct test_utils
    module is ran in B
    """
    for modname, mod in sys.modules.items():
        if mod is None:
            continue
        if not hasattr(mod, '__file__'):
            # this is the case of some built-in modules like sys, imp, marshal
            continue
        modfile = mod.__file__
        # if modfile is not an absolute path, it was probably loaded locally
        # during the tests
        if not osp.isabs(modfile) or modfile.startswith(testdir):
            del sys.modules[modname]



class PyTester(object):
    """encapsulates testrun logic"""

    def __init__(self, cvg, options):
        self.report = GlobalTestReport()
        self.cvg = cvg
        self.options = options
        self.firstwrite = True
        self._errcode = None

    def show_report(self):
        """prints the report and returns appropriate exitcode"""
        # everything has been ran, print report
        print "*" * 79
        print self.report

    def get_errcode(self):
        # errcode set explicitly
        if self._errcode is not None:
            return self._errcode
        return self.report.failures + self.report.errors

    def set_errcode(self, errcode):
        self._errcode = errcode
    errcode = property(get_errcode, set_errcode)

    def testall(self, exitfirst=False):
        """walks through current working directory, finds something
        which can be considered as a testdir and runs every test there
        """
        here = os.getcwd()
        for dirname, dirs, _ in os.walk(here):
            for skipped in STD_BLACKLIST:
                if skipped in dirs:
                    dirs.remove(skipped)
            basename = osp.basename(dirname)
            if this_is_a_testdir(basename):
                print "going into", dirname
                # we found a testdir, let's explore it !
                if not self.testonedir(dirname, exitfirst):
                    break
                dirs[:] = []
        if self.report.ran == 0:
            print "no test dir found testing here:", here
            # if no test was found during the visit, consider
            # the local directory as a test directory even if
            # it doesn't have a traditional test directory name
            self.testonedir(here)

    def testonedir(self, testdir, exitfirst=False):
        """finds each testfile in the `testdir` and runs it

        return true when all tests has been executed, false if exitfirst and
        some test has failed.
        """
        for filename in abspath_listdir(testdir):
            if this_is_a_testfile(filename):
                if self.options.exitfirst and not self.options.restart:
                    # overwrite restart file
                    try:
                        restartfile = open(FILE_RESTART, "w")
                        restartfile.close()
                    except Exception, e:
                        print >> sys.__stderr__, "Error while overwriting \
succeeded test file :", osp.join(os.getcwd(), FILE_RESTART)
                        raise e
                # run test and collect information
                prog = self.testfile(filename, batchmode=True)
                if exitfirst and (prog is None or not prog.result.wasSuccessful()):
                    return False
                self.firstwrite = True
        # clean local modules
        remove_local_modules_from_sys(testdir)
        return True

    def testfile(self, filename, batchmode=False):
        """runs every test in `filename`

        :param filename: an absolute path pointing to a unittest file
        """
        here = os.getcwd()
        dirname = osp.dirname(filename)
        if dirname:
            os.chdir(dirname)
        # overwrite restart file if it has not been done already
        if self.options.exitfirst and not self.options.restart and self.firstwrite:
            try:
                restartfile = open(FILE_RESTART, "w")
                restartfile.close()
            except Exception, e:
                print >> sys.__stderr__, "Error while overwriting \
succeeded test file :", osp.join(os.getcwd(), FILE_RESTART)
                raise e
        modname = osp.basename(filename)[:-3]
        try:
            print >> sys.stderr, ('  %s  ' % osp.basename(filename)).center(70, '=')
        except TypeError: # < py 2.4 bw compat
            print >> sys.stderr, ('  %s  ' % osp.basename(filename)).center(70)
        try:
            tstart, cstart = time(), clock()
            try:
                testprog = SkipAwareTestProgram(modname, batchmode=batchmode, cvg=self.cvg,
                                                 options=self.options, outstream=sys.stderr)
            except KeyboardInterrupt:
                raise
            except SystemExit, exc:
                self.errcode = exc.code
                raise
            except testlib.SkipTest:
                print "Module skipped:", filename
                self.report.skip_module(filename)
                return None
            except Exception:
                self.report.failed_to_test_module(filename)
                print >> sys.stderr, 'unhandled exception occurred while testing', modname
                import traceback
                traceback.print_exc(file=sys.stderr)
                return None

            tend, cend = time(), clock()
            ttime, ctime = (tend - tstart), (cend - cstart)
            self.report.feed(filename, testprog.result, ttime, ctime)
            return testprog
        finally:
            if dirname:
                os.chdir(here)



class DjangoTester(PyTester):

    def load_django_settings(self, dirname):
        """try to find project's setting and load it"""
        curdir = osp.abspath(dirname)
        previousdir = curdir
        while not osp.isfile(osp.join(curdir, 'settings.py')) and \
                  osp.isfile(osp.join(curdir, '__init__.py')):
            newdir = osp.normpath(osp.join(curdir, os.pardir))
            if newdir == curdir:
                raise AssertionError('could not find settings.py')
            previousdir = curdir
            curdir = newdir
        # late django initialization
        settings = load_module_from_modpath(modpath_from_file(osp.join(curdir, 'settings.py')))
        from django.core.management import setup_environ
        setup_environ(settings)
        settings.DEBUG = False
        self.settings = settings
        # add settings dir to pythonpath since it's the project's root
        if curdir not in sys.path:
            sys.path.insert(1, curdir)

    def before_testfile(self):
        # Those imports must be done **after** setup_environ was called
        from django.test.utils import setup_test_environment
        from django.test.utils import create_test_db
        setup_test_environment()
        create_test_db(verbosity=0)
        self.dbname = self.settings.TEST_DATABASE_NAME

    def after_testfile(self):
        # Those imports must be done **after** setup_environ was called
        from django.test.utils import teardown_test_environment
        from django.test.utils import destroy_test_db
        teardown_test_environment()
        print 'destroying', self.dbname
        destroy_test_db(self.dbname, verbosity=0)

    def testall(self, exitfirst=False):
        """walks through current working directory, finds something
        which can be considered as a testdir and runs every test there
        """
        for dirname, dirs, files in os.walk(os.getcwd()):
            for skipped in ('CVS', '.svn', '.hg'):
                if skipped in dirs:
                    dirs.remove(skipped)
            if 'tests.py' in files:
                if not self.testonedir(dirname, exitfirst):
                    break
                dirs[:] = []
            else:
                basename = osp.basename(dirname)
                if basename in ('test', 'tests'):
                    print "going into", dirname
                    # we found a testdir, let's explore it !
                    if not self.testonedir(dirname, exitfirst):
                        break
                    dirs[:] = []

    def testonedir(self, testdir, exitfirst=False):
        """finds each testfile in the `testdir` and runs it

        return true when all tests has been executed, false if exitfirst and
        some test has failed.
        """
        # special django behaviour : if tests are splitted in several files,
        # remove the main tests.py file and tests each test file separately
        testfiles = [fpath for fpath in abspath_listdir(testdir)
                     if this_is_a_testfile(fpath)]
        if len(testfiles) > 1:
            try:
                testfiles.remove(osp.join(testdir, 'tests.py'))
            except ValueError:
                pass
        for filename in testfiles:
            # run test and collect information
            prog = self.testfile(filename, batchmode=True)
            if exitfirst and (prog is None or not prog.result.wasSuccessful()):
                return False
        # clean local modules
        remove_local_modules_from_sys(testdir)
        return True

    def testfile(self, filename, batchmode=False):
        """runs every test in `filename`

        :param filename: an absolute path pointing to a unittest file
        """
        here = os.getcwd()
        dirname = osp.dirname(filename)
        if dirname:
            os.chdir(dirname)
        self.load_django_settings(dirname)
        modname = osp.basename(filename)[:-3]
        print >>sys.stderr, ('  %s  ' % osp.basename(filename)).center(70, '=')
        try:
            try:
                tstart, cstart = time(), clock()
                self.before_testfile()
                testprog = SkipAwareTestProgram(modname, batchmode=batchmode, cvg=self.cvg)
                tend, cend = time(), clock()
                ttime, ctime = (tend - tstart), (cend - cstart)
                self.report.feed(filename, testprog.result, ttime, ctime)
                return testprog
            except SystemExit:
                raise
            except Exception, exc:
                import traceback
                traceback.print_exc()
                self.report.failed_to_test_module(filename)
                print 'unhandled exception occurred while testing', modname
                print 'error: %s' % exc
                return None
        finally:
            self.after_testfile()
            if dirname:
                os.chdir(here)


def make_parser():
    """creates the OptionParser instance
    """
    from optparse import OptionParser
    parser = OptionParser(usage=PYTEST_DOC)

    parser.newargs = []
    def rebuild_cmdline(option, opt, value, parser):
        """carry the option to unittest_main"""
        parser.newargs.append(opt)

    def rebuild_and_store(option, opt, value, parser):
        """carry the option to unittest_main and store
        the value on current parser
        """
        parser.newargs.append(opt)
        setattr(parser.values, option.dest, True)

    def capture_and_rebuild(option, opt, value, parser):
        warnings.simplefilter('ignore', DeprecationWarning)
        rebuild_cmdline(option, opt, value, parser)

    # pytest options
    parser.add_option('-t', dest='testdir', default=None,
                      help="directory where the tests will be found")
    parser.add_option('-d', dest='dbc', default=False,
                      action="store_true", help="enable design-by-contract")
    # unittest_main options provided and passed through pytest
    parser.add_option('-v', '--verbose', callback=rebuild_cmdline,
                      action="callback", help="Verbose output")
    parser.add_option('-i', '--pdb', callback=rebuild_and_store,
                      dest="pdb", action="callback",
                      help="Enable test failure inspection (conflicts with --coverage)")
    parser.add_option('-x', '--exitfirst', callback=rebuild_and_store,
                      dest="exitfirst", default=False,
                      action="callback", help="Exit on first failure "
                      "(only make sense when pytest run one test file)")
    parser.add_option('-R', '--restart', callback=rebuild_and_store,
                      dest="restart", default=False,
                      action="callback",
                      help="Restart tests from where it failed (implies exitfirst) "
                        "(only make sense if tests previously ran with exitfirst only)")
    parser.add_option('--color', callback=rebuild_cmdline,
                      action="callback",
                      help="colorize tracebacks")
    parser.add_option('-s', '--skip',
                      # XXX: I wish I could use the callback action but it
                      #      doesn't seem to be able to get the value
                      #      associated to the option
                      action="store", dest="skipped", default=None,
                      help="test names matching this name will be skipped "
                      "to skip several patterns, use commas")
    parser.add_option('-q', '--quiet', callback=rebuild_cmdline,
                      action="callback", help="Minimal output")
    parser.add_option('-P', '--profile', default=None, dest='profile',
                      help="Profile execution and store data in the given file")
    parser.add_option('-m', '--match', default=None, dest='tags_pattern',
                      help="only execute test whose tag match the current pattern")

    try:
        from logilab.devtools.lib.coverage import Coverage
        parser.add_option('--coverage', dest="coverage", default=False,
                          action="store_true",
                          help="run tests with pycoverage (conflicts with --pdb)")
    except ImportError:
        pass

    if DJANGO_FOUND:
        parser.add_option('-J', '--django', dest='django', default=False,
                          action="store_true",
                          help='use pytest for django test cases')
    return parser


def parseargs(parser):
    """Parse the command line and return (options processed), (options to pass to
    unittest_main()), (explicitfile or None).
    """
    # parse the command line
    options, args = parser.parse_args()
    if options.pdb and getattr(options, 'coverage', False):
        parser.error("'pdb' and 'coverage' options are exclusive")
    filenames = [arg for arg in args if arg.endswith('.py')]
    if filenames:
        if len(filenames) > 1:
            parser.error("only one filename is acceptable")
        explicitfile = filenames[0]
        args.remove(explicitfile)
    else:
        explicitfile = None
    # someone wants DBC
    testlib.ENABLE_DBC = options.dbc
    newargs = parser.newargs
    if options.skipped:
        newargs.extend(['--skip', options.skipped])
    # restart implies exitfirst
    if options.restart:
        options.exitfirst = True
    # append additional args to the new sys.argv and let unittest_main
    # do the rest
    newargs += args
    return options, explicitfile



def run():
    parser = make_parser()
    rootdir, testercls = project_root(parser)
    options, explicitfile = parseargs(parser)
    # mock a new command line
    sys.argv[1:] = parser.newargs
    covermode = getattr(options, 'coverage', None)
    cvg = None
    if not '' in sys.path:
        sys.path.insert(0, '')
    if covermode:
        # control_import_coverage(rootdir)
        from logilab.devtools.lib.coverage import Coverage
        cvg = Coverage([rootdir])
        cvg.erase()
        cvg.start()
    if DJANGO_FOUND and options.django:
        tester = DjangoTester(cvg, options)
    else:
        tester = testercls(cvg, options)
    if explicitfile:
        cmd, args = tester.testfile, (explicitfile,)
    elif options.testdir:
        cmd, args = tester.testonedir, (options.testdir, options.exitfirst)
    else:
        cmd, args = tester.testall, (options.exitfirst,)
    try:
        try:
            if options.profile:
                import hotshot
                prof = hotshot.Profile(options.profile)
                prof.runcall(cmd, *args)
                prof.close()
                print 'profile data saved in', options.profile
            else:
                cmd(*args)
        except SystemExit:
            raise
        except:
            import traceback
            traceback.print_exc()
    finally:
        if covermode:
            cvg.stop()
            cvg.save()
        tester.show_report()
        if covermode:
            print 'coverage information stored, use it with pycoverage -ra'
        sys.exit(tester.errcode)

class SkipAwareTestProgram(unittest.TestProgram):
    # XXX: don't try to stay close to unittest.py, use optparse
    USAGE = """\
Usage: %(progName)s [options] [test] [...]

Options:
  -h, --help       Show this message
  -v, --verbose    Verbose output
  -i, --pdb        Enable test failure inspection
  -x, --exitfirst  Exit on first failure
  -s, --skip       skip test matching this pattern (no regexp for now)
  -q, --quiet      Minimal output
  --color          colorize tracebacks

  -m, --match      Run only test whose tag match this pattern

  -P, --profile    FILE: Run the tests using cProfile and saving results
                   in FILE

Examples:
  %(progName)s                               - run default set of tests
  %(progName)s MyTestSuite                   - run suite 'MyTestSuite'
  %(progName)s MyTestCase.testSomething      - run MyTestCase.testSomething
  %(progName)s MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
"""
    def __init__(self, module='__main__', defaultTest=None, batchmode=False,
                 cvg=None, options=None, outstream=sys.stderr):
        self.batchmode = batchmode
        self.cvg = cvg
        self.options = options
        self.outstream = outstream
        super(SkipAwareTestProgram, self).__init__(
            module=module, defaultTest=defaultTest,
            testLoader=NonStrictTestLoader())

    def parseArgs(self, argv):
        self.pdbmode = False
        self.exitfirst = False
        self.skipped_patterns = []
        self.test_pattern = None
        self.tags_pattern = None
        self.colorize = False
        self.profile_name = None
        import getopt
        try:
            options, args = getopt.getopt(argv[1:], 'hHvixrqcp:s:m:P:',
                                          ['help', 'verbose', 'quiet', 'pdb',
                                           'exitfirst', 'restart',
                                           'skip=', 'color', 'match=', 'profile='])
            for opt, value in options:
                if opt in ('-h', '-H', '--help'):
                    self.usageExit()
                if opt in ('-i', '--pdb'):
                    self.pdbmode = True
                if opt in ('-x', '--exitfirst'):
                    self.exitfirst = True
                if opt in ('-r', '--restart'):
                    self.restart = True
                    self.exitfirst = True
                if opt in ('-q', '--quiet'):
                    self.verbosity = 0
                if opt in ('-v', '--verbose'):
                    self.verbosity = 2
                if opt in ('-s', '--skip'):
                    self.skipped_patterns = [pat.strip() for pat in
                                             value.split(', ')]
                if opt == '--color':
                    self.colorize = True
                if opt in ('-m', '--match'):
                    #self.tags_pattern = value
                    self.options["tag_pattern"] = value
                if opt in ('-P', '--profile'):
                    self.profile_name = value
            self.testLoader.skipped_patterns = self.skipped_patterns
            if len(args) == 0 and self.defaultTest is None:
                suitefunc = getattr(self.module, 'suite', None)
                if isinstance(suitefunc, (types.FunctionType,
                        types.MethodType)):
                    self.test = self.module.suite()
                else:
                    self.test = self.testLoader.loadTestsFromModule(self.module)
                return
            if len(args) > 0:
                self.test_pattern = args[0]
                self.testNames = args
            else:
                self.testNames = (self.defaultTest, )
            self.createTests()
        except getopt.error, msg:
            self.usageExit(msg)

    def runTests(self):
        if self.profile_name:
            import cProfile
            cProfile.runctx('self._runTests()', globals(), locals(), self.profile_name )
        else:
            return self._runTests()

    def _runTests(self):
        self.testRunner = SkipAwareTextTestRunner(verbosity=self.verbosity,
                                                  stream=self.outstream,
                                                  exitfirst=self.exitfirst,
                                                  pdbmode=self.pdbmode,
                                                  cvg=self.cvg,
                                                  test_pattern=self.test_pattern,
                                                  skipped_patterns=self.skipped_patterns,
                                                  colorize=self.colorize,
                                                  batchmode=self.batchmode,
                                                  options=self.options)

        def removeSucceededTests(obj, succTests):
            """ Recursive function that removes succTests from
            a TestSuite or TestCase
            """
            if isinstance(obj, unittest.TestSuite):
                removeSucceededTests(obj._tests, succTests)
            if isinstance(obj, list):
                for el in obj[:]:
                    if isinstance(el, unittest.TestSuite):
                        removeSucceededTests(el, succTests)
                    elif isinstance(el, unittest.TestCase):
                        descr = '.'.join((el.__class__.__module__,
                                el.__class__.__name__,
                                el._testMethodName))
                        if descr in succTests:
                            obj.remove(el)
        # take care, self.options may be None
        if getattr(self.options, 'restart', False):
            # retrieve succeeded tests from FILE_RESTART
            try:
                restartfile = open(FILE_RESTART, 'r')
                try:
                    succeededtests = list(elem.rstrip('\n\r') for elem in
                                          restartfile.readlines())
                    removeSucceededTests(self.test, succeededtests)
                finally:
                    restartfile.close()
            except Exception, ex:
                raise Exception("Error while reading succeeded tests into %s: %s"
                                % (osp.join(os.getcwd(), FILE_RESTART), ex))

        result = self.testRunner.run(self.test)
        # help garbage collection: we want TestSuite, which hold refs to every
        # executed TestCase, to be gc'ed
        del self.test
        if getattr(result, "debuggers", None) and \
           getattr(self, "pdbmode", None):
            start_interactive_mode(result)
        if not getattr(self, "batchmode", None):
            sys.exit(not result.wasSuccessful())
        self.result = result


class SkipAwareTextTestRunner(unittest.TextTestRunner):

    def __init__(self, stream=sys.stderr, verbosity=1,
                 exitfirst=False, pdbmode=False, cvg=None, test_pattern=None,
                 skipped_patterns=(), colorize=False, batchmode=False,
                 options=None):
        super(SkipAwareTextTestRunner, self).__init__(stream=stream,
                                                      verbosity=verbosity)
        self.exitfirst = exitfirst
        self.pdbmode = pdbmode
        self.cvg = cvg
        self.test_pattern = test_pattern
        self.skipped_patterns = skipped_patterns
        self.colorize = colorize
        self.batchmode = batchmode
        self.options = options

    def _this_is_skipped(self, testedname):
        return any([(pat in testedname) for pat in self.skipped_patterns])

    def _runcondition(self, test, skipgenerator=True):
        if isinstance(test, testlib.InnerTest):
            testname = test.name
        else:
            if isinstance(test, testlib.TestCase):
                meth = test._get_test_method()
                func = meth.im_func
                testname = '%s.%s' % (meth.im_class.__name__, func.__name__)
            elif isinstance(test, types.FunctionType):
                func = test
                testname = func.__name__
            elif isinstance(test, types.MethodType):
                func = test.im_func
                testname = '%s.%s' % (test.im_class.__name__, func.__name__)
            else:
                return True # Not sure when this happens
            if testlib.is_generator(test) and skipgenerator:
                return self.does_match_tags(test) # Let inner tests decide at run time
        if self._this_is_skipped(testname):
            return False # this was explicitly skipped
        if self.test_pattern is not None:
            try:
                classpattern, testpattern = self.test_pattern.split('.')
                klass, name = testname.split('.')
                if classpattern not in klass or testpattern not in name:
                    return False
            except ValueError:
                if self.test_pattern not in testname:
                    return False

        return self.does_match_tags(test)

    def does_match_tags(self, test):
        if self.options is not None:
            tags_pattern = getattr(self.options, 'tags_pattern', None)
            if tags_pattern is not None:
                tags = getattr(test, 'tags', testlib.Tags())
                if tags.inherit and isinstance(test, types.MethodType):
                    tags = tags | getattr(test.im_class, 'tags', testlib.Tags())
                return tags.match(tags_pattern)
        return True # no pattern

    def _makeResult(self):
        return testlib.SkipAwareTestResult(self.stream, self.descriptions,
                                   self.verbosity, self.exitfirst,
                                   self.pdbmode, self.cvg, self.colorize)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        startTime = time()
        test(result, runcondition=self._runcondition, options=self.options)
        stopTime = time()
        timeTaken = stopTime - startTime
        result.printErrors()
        if not self.batchmode:
            self.stream.writeln(result.separator2)
            run = result.testsRun
            self.stream.writeln("Ran %d test%s in %.3fs" %
                                (run, run != 1 and "s" or "", timeTaken))
            self.stream.writeln()
            if not result.wasSuccessful():
                if self.colorize:
                    self.stream.write(textutils.colorize_ansi("FAILED", color='red'))
                else:
                    self.stream.write("FAILED")
            else:
                if self.colorize:
                    self.stream.write(textutils.colorize_ansi("OK", color='green'))
                else:
                    self.stream.write("OK")
            failed, errored, skipped = map(len, (result.failures,
                                                 result.errors,
                                                 result.skipped))

            det_results = []
            for name, value in (("failures", result.failures),
                                ("errors",result.errors),
                                ("skipped", result.skipped)):
                if value:
                    det_results.append("%s=%i" % (name, len(value)))
            if det_results:
                self.stream.write(" (")
                self.stream.write(', '.join(det_results))
                self.stream.write(")")
            self.stream.writeln("")
        return result

class NonStrictTestLoader(unittest.TestLoader):
    """
    Overrides default testloader to be able to omit classname when
    specifying tests to run on command line.

    For example, if the file test_foo.py contains ::

        class FooTC(TestCase):
            def test_foo1(self): # ...
            def test_foo2(self): # ...
            def test_bar1(self): # ...

        class BarTC(TestCase):
            def test_bar2(self): # ...

    'python test_foo.py' will run the 3 tests in FooTC
    'python test_foo.py FooTC' will run the 3 tests in FooTC
    'python test_foo.py test_foo' will run test_foo1 and test_foo2
    'python test_foo.py test_foo1' will run test_foo1
    'python test_foo.py test_bar' will run FooTC.test_bar1 and BarTC.test_bar2
    """

    def __init__(self):
        self.skipped_patterns = ()

    # some magic here to accept empty list by extending
    # and to provide callable capability
    def loadTestsFromNames(self, names, module=None):
        suites = []
        for name in names:
            suites.extend(self.loadTestsFromName(name, module))
        return self.suiteClass(suites)

    def _collect_tests(self, module):
        tests = {}
        for obj in vars(module).values():
            if (issubclass(type(obj), (types.ClassType, type)) and
                 issubclass(obj, unittest.TestCase)):
                classname = obj.__name__
                if classname[0] == '_' or self._this_is_skipped(classname):
                    continue
                methodnames = []
                # obj is a TestCase class
                for attrname in dir(obj):
                    if attrname.startswith(self.testMethodPrefix):
                        attr = getattr(obj, attrname)
                        if callable(attr):
                            methodnames.append(attrname)
                # keep track of class (obj) for convenience
                tests[classname] = (obj, methodnames)
        return tests

    def loadTestsFromSuite(self, module, suitename):
        try:
            suite = getattr(module, suitename)()
        except AttributeError:
            return []
        assert hasattr(suite, '_tests'), \
               "%s.%s is not a valid TestSuite" % (module.__name__, suitename)
        # python2.3 does not implement __iter__ on suites, we need to return
        # _tests explicitly
        return suite._tests

    def loadTestsFromName(self, name, module=None):
        parts = name.split('.')
        if module is None or len(parts) > 2:
            # let the base class do its job here
            return [super(NonStrictTestLoader, self).loadTestsFromName(name)]
        tests = self._collect_tests(module)
        collected = []
        if len(parts) == 1:
            pattern = parts[0]
            if callable(getattr(module, pattern, None)
                    )  and pattern not in tests:
                # consider it as a suite
                return self.loadTestsFromSuite(module, pattern)
            if pattern in tests:
                # case python unittest_foo.py MyTestTC
                klass, methodnames = tests[pattern]
                for methodname in methodnames:
                    collected = [klass(methodname)
                        for methodname in methodnames]
            else:
                # case python unittest_foo.py something
                for klass, methodnames in tests.values():
                    # skip methodname if matched by skipped_patterns
                    for skip_pattern in self.skipped_patterns:
                        methodnames = [methodname
                                      for methodname in methodnames
                                      if skip_pattern not in methodname]
                    collected += [klass(methodname)
                                  for methodname in methodnames
                                  if pattern in methodname]
        elif len(parts) == 2:
            # case "MyClass.test_1"
            classname, pattern = parts
            klass, methodnames = tests.get(classname, (None, []))
            for methodname in methodnames:
                collected = [klass(methodname) for methodname in methodnames
                            if pattern in methodname]
        return collected

    def _this_is_skipped(self, testedname):
        return any([(pat in testedname) for pat in self.skipped_patterns])

    def getTestCaseNames(self, testCaseClass):
        """Return a sorted sequence of method names found within testCaseClass
        """
        is_skipped = self._this_is_skipped
        classname = testCaseClass.__name__
        if classname[0] == '_' or is_skipped(classname):
            return []
        testnames = super(NonStrictTestLoader, self).getTestCaseNames(
                testCaseClass)
        return [testname for testname in testnames if not is_skipped(testname)]

def _ts_run(self, result, runcondition=None, options=None):
    self._wrapped_run(result,runcondition=runcondition, options=options)
    self._tearDownPreviousClass(None, result)
    self._handleModuleTearDown(result)
    return result

def _ts_wrapped_run(self, result, debug=False, runcondition=None, options=None):
    for test in self:
        if result.shouldStop:
            break
        if unittest_suite._isnotsuite(test):
            self._tearDownPreviousClass(test, result)
            self._handleModuleFixture(test, result)
            self._handleClassSetUp(test, result)
            result._previousTestClass = test.__class__
            if (getattr(test.__class__, '_classSetupFailed', False) or 
                getattr(result, '_moduleSetUpFailed', False)):
                continue

        if hasattr(test, '_wrapped_run'):
            try:
                test._wrapped_run(result, debug, runcondition=runcondition, options=options)
            except TypeError:
                test._wrapped_run(result, debug)
        elif not debug:
            try:
                test(result, runcondition, options)
            except TypeError:
                test(result)
        else:
            test.debug()


def enable_dbc(*args):
    """
    Without arguments, return True if contracts can be enabled and should be
    enabled (see option -d), return False otherwise.

    With arguments, return False if contracts can't or shouldn't be enabled,
    otherwise weave ContractAspect with items passed as arguments.
    """
    if not ENABLE_DBC:
        return False
    try:
        from logilab.aspects.weaver import weaver
        from logilab.aspects.lib.contracts import ContractAspect
    except ImportError:
        sys.stderr.write(
            'Warning: logilab.aspects is not available. Contracts disabled.')
        return False
    for arg in args:
        weaver.weave_module(arg, ContractAspect)
    return True


# monkeypatch unittest and doctest (ouch !)
unittest._TextTestResult = testlib.SkipAwareTestResult
unittest.TextTestRunner = SkipAwareTextTestRunner
unittest.TestLoader = NonStrictTestLoader
unittest.TestProgram = SkipAwareTestProgram

if sys.version_info >= (2, 4):
    doctest.DocTestCase.__bases__ = (testlib.TestCase,)
    # XXX check python2.6 compatibility
    #doctest.DocTestCase._cleanups = []
    #doctest.DocTestCase._out = []
else:
    unittest.FunctionTestCase.__bases__ = (testlib.TestCase,)
unittest.TestSuite.run = _ts_run
unittest.TestSuite._wrapped_run = _ts_wrapped_run
