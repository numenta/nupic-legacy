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
from __future__ import with_statement

from os.path import join, dirname
from cStringIO import StringIO

from logilab.common.testlib import TestCase, unittest_main

from logilab.common.changelog import ChangeLog

class ChangeLogTC(TestCase):
    cl_class = ChangeLog
    cl_file = join(dirname(__file__), 'data', 'ChangeLog')

    def test_round_trip(self):
        cl = self.cl_class(self.cl_file)
        out = StringIO()
        cl.write(out)
        with open(self.cl_file) as stream:
            self.assertMultiLineEqual(stream.read(), out.getvalue())


if __name__ == '__main__':
    unittest_main()
