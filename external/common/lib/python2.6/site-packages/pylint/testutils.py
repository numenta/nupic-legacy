# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""functional/non regression tests for pylint"""

import sys
import re

from glob import glob
from os import linesep
from os.path import abspath, dirname, join, basename, splitext
from cStringIO import StringIO

from logilab.common import testlib

from pylint import checkers
from pylint.reporters import BaseReporter
from pylint.interfaces import IReporter
from pylint.lint import PyLinter


# Utils

SYS_VERS_STR = '%d%d' % sys.version_info[:2]
TITLE_UNDERLINES = ['', '=', '-', '.']
PREFIX = abspath(dirname(__file__))

def fix_path():
    sys.path.insert(0, PREFIX)

def get_tests_info(input_dir, msg_dir, prefix, suffix):
    """get python input examples and output messages

    We use following conventions for input files and messages:
    for different inputs:
        don't test for python  <   x.y    ->  input   =  <name>_pyxy.py
        don't test for python  >=  x.y    ->  input   =  <name>_py_xy.py
    for one input and different messages:
        message for python     <=  x.y    ->  message =  <name>_pyxy.txt
        higher versions                   ->  message with highest num
    """
    result = []
    for fname in glob(join(input_dir, prefix + '*' + suffix)):
        infile = basename(fname)
        fbase = splitext(infile)[0]
        # filter input files :
        pyrestr = fbase.rsplit('_py', 1)[-1] # like _26 or 26
        if pyrestr.isdigit(): # '24', '25'...
            if SYS_VERS_STR < pyrestr:
                continue
        if pyrestr.startswith('_') and  pyrestr[1:].isdigit():
            # skip test for higher python versions
            if SYS_VERS_STR >= pyrestr[1:]:
                continue
        messages = glob(join(msg_dir, fbase + '*.txt'))
        # the last one will be without ext, i.e. for all or upper versions:
        if messages:
            for outfile in sorted(messages, reverse=True):
                py_rest = outfile.rsplit('_py', 1)[-1][:-4]
                if py_rest.isdigit() and SYS_VERS_STR >= py_rest:
                    break
        else:
            outfile = None
        result.append((infile, outfile))
    return result


class TestReporter(BaseReporter):
    """reporter storing plain text messages"""

    __implements____ = IReporter

    def __init__(self):
        self.message_ids = {}
        self.reset()

    def reset(self):
        self.out = StringIO()
        self.messages = []

    def add_message(self, msg_id, location, msg):
        """manage message of different type and in the context of path """
        fpath, module, object, line, _ = location
        self.message_ids[msg_id] = 1
        if object:
            object = ':%s' % object
        sigle = msg_id[0]
        self.messages.append('%s:%3s%s: %s' % (sigle, line, object, msg))

    def finalize(self):
        self.messages.sort()
        for msg in self.messages:
            print >> self.out, msg
        result = self.out.getvalue()
        self.reset()
        return result

    def display_results(self, layout):
        """ignore layouts"""

# Init

test_reporter = TestReporter()
linter = PyLinter()
linter.set_reporter(test_reporter)
linter.config.persistent = 0
checkers.initialize(linter)
linter.global_set_option('required-attributes', ('__revision__',))

if linesep != '\n':
    LINE_RGX = re.compile(linesep)
    def ulines(string):
        return LINE_RGX.sub('\n', string)
else:
    def ulines(string):
        return string

INFO_TEST_RGX = re.compile('^func_i\d\d\d\d$')

def exception_str(self, ex):
    """function used to replace default __str__ method of exception instances"""
    return 'in %s\n:: %s' % (ex.file, ', '.join(ex.args))

# Test classes

class LintTestUsingModule(testlib.TestCase):
    INPUT_DIR = None
    DEFAULT_PACKAGE = 'input'
    package = DEFAULT_PACKAGE
    linter = linter
    module = None
    depends = None
    output = None
    _TEST_TYPE = 'module'

    def shortDescription(self):
        values = { 'mode' : self._TEST_TYPE,
                   'input': self.module,
                   'pkg':   self.package,
                   'cls':   self.__class__.__name__}

        if self.package == self.DEFAULT_PACKAGE:
            msg = '%(mode)s test of input file "%(input)s" (%(cls)s)'
        else:
            msg = '%(mode)s test of input file "%(input)s" in "%(pkg)s" (%(cls)s)'
        return msg % values

    def test_functionality(self):
        tocheck = [self.package+'.'+self.module]
        if self.depends:
            tocheck += [self.package+'.%s' % name.replace('.py', '')
                        for name, file in self.depends]
        self._test(tocheck)

    def _test(self, tocheck):
        if INFO_TEST_RGX.match(self.module):
            self.linter.enable('I')
        else:
            self.linter.disable('I')
        try:
            self.linter.check(tocheck)
        except Exception, ex:
            # need finalization to restore a correct state
            self.linter.reporter.finalize()
            ex.file = tocheck
            print ex
            ex.__str__ = exception_str
            raise
        got = self.linter.reporter.finalize()
        self.assertMultiLineEqual(got, self._get_expected())


    def _get_expected(self):
        if self.module.startswith('func_noerror_'):
            expected = ''
        else:
            output = open(self.output)
            expected = output.read().strip() + '\n'
            output.close()
        return expected

class LintTestUsingFile(LintTestUsingModule):

    _TEST_TYPE = 'file'

    def test_functionality(self):
        tocheck = [join(self.INPUT_DIR, self.module + '.py')]
        if self.depends:
            tocheck += [join(self.INPUT_DIR, name) for name, _file in self.depends]
        self._test(tocheck)

# Callback

def cb_test_gen(base_class):
    def call(input_dir, msg_dir, module_file, messages_file, dependencies):
        class LintTC(base_class):
            module = module_file.replace('.py', '')
            output = messages_file
            depends = dependencies or None
            tags = testlib.Tags(('generated', 'pylint_input_%s' % module))
            INPUT_DIR = input_dir
            MSG_DIR = msg_dir
        return LintTC
    return call

# Main function

def make_tests(input_dir, msg_dir, filter_rgx, callbacks):
    """generate tests classes from test info

    return the list of generated test classes
    """
    if filter_rgx:
        is_to_run = re.compile(filter_rgx).search
    else:
        is_to_run = lambda x: 1
    tests = []
    for module_file, messages_file in get_tests_info(input_dir, msg_dir,
            'func_', '.py'):
        if not is_to_run(module_file):
            continue
        base = module_file.replace('func_', '').replace('.py', '')

        dependencies = get_tests_info(input_dir, msg_dir, base, '.py')

        for callback in callbacks:
            test = callback(input_dir, msg_dir, module_file, messages_file,
                dependencies)
            if test:
                tests.append(test)


    return tests
