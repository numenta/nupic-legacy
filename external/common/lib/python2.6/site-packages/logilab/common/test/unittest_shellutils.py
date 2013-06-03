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
"""unit tests for logilab.common.shellutils"""

import sys, os, tempfile, shutil
from os.path import join, dirname, abspath
import datetime, time
from StringIO import StringIO

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.shellutils import (globfind, find, ProgressBar,
                                       acquire_lock, release_lock,
                                       RawInput)
from logilab.common.compat import str_to_bytes
from logilab.common.proc import NoSuchProcess

DATA_DIR = join(dirname(abspath(__file__)), 'data', 'find_test')

class FindTC(TestCase):
    def test_include(self):
        files = set(find(DATA_DIR, '.py'))
        self.assertSetEqual(files,
                            set([join(DATA_DIR, f) for f in ['__init__.py', 'module.py',
                                                       'module2.py', 'noendingnewline.py',
                                                       'nonregr.py', join('sub', 'momo.py')]]))
        files = set(find(DATA_DIR, ('.py',), blacklist=('sub',)))
        self.assertSetEqual(files,
                            set([join(DATA_DIR, f) for f in ['__init__.py', 'module.py',
                                                       'module2.py', 'noendingnewline.py',
                                                       'nonregr.py']]))

    def test_exclude(self):
        files = set(find(DATA_DIR, ('.py', '.pyc'), exclude=True))
        self.assertSetEqual(files,
                            set([join(DATA_DIR, f) for f in ['foo.txt',
                                                       'newlines.txt',
                                                       'normal_file.txt',
                                                       'test.ini',
                                                       'test1.msg',
                                                       'test2.msg',
                                                       'spam.txt',
                                                       join('sub', 'doc.txt'),
                                                       'write_protected_file.txt',
                                                       ]]))

    def test_globfind(self):
        files = set(globfind(DATA_DIR, '*.py'))
        self.assertSetEqual(files,
                            set([join(DATA_DIR, f) for f in ['__init__.py', 'module.py',
                                                       'module2.py', 'noendingnewline.py',
                                                       'nonregr.py', join('sub', 'momo.py')]]))
        files = set(globfind(DATA_DIR, 'mo*.py'))
        self.assertSetEqual(files,
                            set([join(DATA_DIR, f) for f in ['module.py', 'module2.py',
                                                             join('sub', 'momo.py')]]))
        files = set(globfind(DATA_DIR, 'mo*.py', blacklist=('sub',)))
        self.assertSetEqual(files,
                            set([join(DATA_DIR, f) for f in ['module.py', 'module2.py']]))


class ProgressBarTC(TestCase):
    def test_refresh(self):
        pgb_stream = StringIO()
        expected_stream = StringIO()
        pgb = ProgressBar(20, stream=pgb_stream)
        self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue()) # nothing print before refresh
        pgb.refresh()
        expected_stream.write("\r["+' '*20+"]")
        self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue())

    def test_refresh_g_size(self):
        pgb_stream = StringIO()
        expected_stream = StringIO()
        pgb = ProgressBar(20, 35, stream=pgb_stream)
        pgb.refresh()
        expected_stream.write("\r["+' '*35+"]")
        self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue())

    def test_refresh_l_size(self):
        pgb_stream = StringIO()
        expected_stream = StringIO()
        pgb = ProgressBar(20, 3, stream=pgb_stream)
        pgb.refresh()
        expected_stream.write("\r["+' '*3+"]")
        self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue())

    def _update_test(self, nbops, expected, size = None):
        pgb_stream = StringIO()
        expected_stream = StringIO()
        if size is None:
            pgb = ProgressBar(nbops, stream=pgb_stream)
            size=20
        else:
            pgb = ProgressBar(nbops, size, stream=pgb_stream)
        last = 0
        for round in expected:
            if not hasattr(round, '__int__'):
                dots, update = round
            else:
                dots, update = round, None
            pgb.update()
            if update or (update is None and dots != last):
                last = dots
                expected_stream.write("\r["+('='*dots)+(' '*(size-dots))+"]")
            self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue())

    def test_default(self):
        self._update_test(20, xrange(1, 21))

    def test_nbops_gt_size(self):
        """Test the progress bar for nbops > size"""
        def half(total):
            for counter in range(1, total+1):
                yield counter // 2
        self._update_test(40, half(40))

    def test_nbops_lt_size(self):
        """Test the progress bar for nbops < size"""
        def double(total):
            for counter in range(1, total+1):
                yield counter * 2
        self._update_test(10, double(10))

    def test_nbops_nomul_size(self):
        """Test the progress bar for size % nbops !=0 (non int number of dots per update)"""
        self._update_test(3, (6, 13, 20))

    def test_overflow(self):
        self._update_test(5, (8, 16, 25, 33, 42, (42, True)), size=42)

    def test_update_exact(self):
        pgb_stream = StringIO()
        expected_stream = StringIO()
        size=20
        pgb = ProgressBar(100, size, stream=pgb_stream)
        last = 0
        for dots in xrange(10, 105, 15):
            pgb.update(dots, exact=True)
            dots //= 5
            expected_stream.write("\r["+('='*dots)+(' '*(size-dots))+"]")
            self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue())

    def test_update_relative(self):
        pgb_stream = StringIO()
        expected_stream = StringIO()
        size=20
        pgb = ProgressBar(100, size, stream=pgb_stream)
        last = 0
        for dots in xrange(5, 105, 5):
            pgb.update(5, exact=False)
            dots //= 5
            expected_stream.write("\r["+('='*dots)+(' '*(size-dots))+"]")
            self.assertEqual(pgb_stream.getvalue(), expected_stream.getvalue())


class AcquireLockTC(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.lock = join(self.tmpdir, 'LOCK')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_acquire_normal(self):
        self.assertTrue(acquire_lock(self.lock, 1, 1))
        self.assertTrue(os.path.exists(self.lock))
        release_lock(self.lock)
        self.assertFalse(os.path.exists(self.lock))

    def test_no_possible_acquire(self):
        self.assertRaises(Exception, acquire_lock, self.lock, 0)

    def test_wrong_process(self):
        fd = os.open(self.lock, os.O_EXCL | os.O_RDWR | os.O_CREAT)
        os.write(fd, str_to_bytes('1111111111'))
        os.close(fd)
        self.assertTrue(os.path.exists(self.lock))
        self.assertRaises(Exception, acquire_lock, self.lock, 1, 1)

    def test_wrong_process_and_continue(self):
        fd = os.open(self.lock, os.O_EXCL | os.O_RDWR | os.O_CREAT)
        os.write(fd, str_to_bytes('1111111111'))
        os.close(fd)
        self.assertTrue(os.path.exists(self.lock))
        self.assertTrue(acquire_lock(self.lock))

    def test_locked_for_one_hour(self):
        self.assertTrue(acquire_lock(self.lock))
        touch = datetime.datetime.fromtimestamp(time.time() - 3601).strftime("%m%d%H%M")
        os.system("touch -t %s %s" % (touch, self.lock))
        self.assertRaises(UserWarning, acquire_lock, self.lock, max_try=2, delay=1)

class RawInputTC(TestCase):

    def auto_input(self, *args):
        self.input_args = args
        return self.input_answer

    def setUp(self):
        null_printer = lambda x: None
        self.qa = RawInput(self.auto_input, null_printer)

    def test_ask_default(self):
        self.input_answer = ''
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'yes')
        self.input_answer = '  '
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'yes')

    def test_ask_case(self):
        self.input_answer = 'no'
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'no')
        self.input_answer = 'No'
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'no')
        self.input_answer = 'NO'
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'no')
        self.input_answer = 'nO'
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'no')
        self.input_answer = 'YES'
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(answer, 'yes')

    def test_ask_prompt(self):
        self.input_answer = ''
        answer = self.qa.ask('text', ('yes', 'no'), 'yes')
        self.assertEqual(self.input_args[0], 'text [Y(es)/n(o)]: ')
        answer = self.qa.ask('text', ('y', 'n'), 'y')
        self.assertEqual(self.input_args[0], 'text [Y/n]: ')
        answer = self.qa.ask('text', ('n', 'y'), 'y')
        self.assertEqual(self.input_args[0], 'text [n/Y]: ')
        answer = self.qa.ask('text', ('yes', 'no', 'maybe', '1'), 'yes')
        self.assertEqual(self.input_args[0], 'text [Y(es)/n(o)/m(aybe)/1]: ')

    def test_ask_ambiguous(self):
        self.input_answer = 'y'
        self.assertRaises(Exception, self.qa.ask, 'text', ('yes', 'yep'), 'yes')

    def test_confirm(self):
        self.input_answer = 'y'
        self.assertEqual(self.qa.confirm('Say yes'), True)
        self.assertEqual(self.qa.confirm('Say yes', default_is_yes=False), True)
        self.input_answer = 'n'
        self.assertEqual(self.qa.confirm('Say yes'), False)
        self.assertEqual(self.qa.confirm('Say yes', default_is_yes=False), False)
        self.input_answer = ''
        self.assertEqual(self.qa.confirm('Say default'), True)
        self.assertEqual(self.qa.confirm('Say default', default_is_yes=False), False)

if __name__ == '__main__':
    unittest_main()
