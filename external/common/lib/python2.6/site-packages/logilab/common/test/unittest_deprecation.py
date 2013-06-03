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
"""unit tests for logilab.common.deprecation"""

import warnings

from logilab.common.testlib import TestCase, unittest_main
from logilab.common import deprecation


class RawInputTC(TestCase):

    # XXX with 2.6 we could test warnings
    # http://docs.python.org/library/warnings.html#testing-warnings
    # instead we just make sure it does not crash

    def mock_warn(self, *args, **kwargs):
        self.messages.append(args[0])

    def setUp(self):
        self.messages = []
        deprecation.warn = self.mock_warn

    def tearDown(self):
        deprecation.warn = warnings.warn

    def mk_func(self):
        def any_func():
            pass
        return any_func

    def test_class_deprecated(self):
        class AnyClass:
            __metaclass__ = deprecation.class_deprecated
        AnyClass()
        self.assertEqual(self.messages,
                         ['AnyClass is deprecated'])

    def test_deprecated_func(self):
        any_func = deprecation.deprecated()(self.mk_func())
        any_func()
        any_func = deprecation.deprecated('message')(self.mk_func())
        any_func()
        self.assertEqual(self.messages,
                         ['The function "any_func" is deprecated', 'message'])

    def test_deprecated_decorator(self):
        @deprecation.deprecated()
        def any_func():
            pass
        any_func()
        @deprecation.deprecated('message')
        def any_func():
            pass
        any_func()
        self.assertEqual(self.messages,
                         ['The function "any_func" is deprecated', 'message'])

    def test_moved(self):
        module = 'data.deprecation'
        any_func = deprecation.moved(module, 'moving_target')
        any_func()
        self.assertEqual(self.messages,
                         ['object moving_target has been moved to module data.deprecation'])

if __name__ == '__main__':
    unittest_main()
