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
'''unit tests for ureports.text_writer
'''

__revision__ = "$Id: unittest_ureports_text.py,v 1.4 2005-05-27 12:27:08 syt Exp $"

from utils import WriterTC
from logilab.common.testlib import TestCase, unittest_main
from logilab.common.ureports.text_writer import TextWriter

class TextWriterTC(TestCase, WriterTC):
    def setUp(self):
        self.writer = TextWriter()

    # Section tests ###########################################################
    section_base = '''
Section title
=============
Section\'s description.
Blabla bla

'''
    section_nested = '''
Section title
=============
Section\'s description.
Blabla bla

Subsection
----------
Sub section description


'''

    # List tests ##############################################################
    list_base = '''
* item1
* item2
* item3
* item4'''

    nested_list = '''
* blabla
  - 1
  - 2
  - 3

* an other point'''

    # Table tests #############################################################
    table_base = '''
+------+------+
|head1 |head2 |
+------+------+
|cell1 |cell2 |
+------+------+

'''
    field_table = '''
f1  : v1
f22 : v22
f333: v333
'''
    advanced_table = '''
+---------------+------+
|field          |value |
+===============+======+
|f1             |v1    |
+---------------+------+
|f22            |v22   |
+---------------+------+
|f333           |v333  |
+---------------+------+
|`toi perdu ?`_ |      |
+---------------+------+

'''


    # VerbatimText tests ######################################################
    verbatim_base = '''::

    blablabla

'''

if __name__ == '__main__':
    unittest_main()
