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
'''unit tests utilities for ureports
'''

__revision__ = "$Id: utils.py,v 1.3 2005-05-27 12:27:08 syt Exp $"

from cStringIO import StringIO
from logilab.common.ureports.nodes import *

class WriterTC:
    def _test_output(self, test_id, layout, msg=None):
        buffer = StringIO()
        self.writer.format(layout, buffer)
        got = buffer.getvalue()
        expected = getattr(self, test_id)
        try:
            self.assertMultiLineEqual(got, expected)
        except:
            print '**** got for %s' % test_id
            print got
            print '**** while expected'
            print expected
            print '****'
            raise

    def test_section(self):
        layout = Section('Section title',
                         'Section\'s description.\nBlabla bla')
        self._test_output('section_base', layout)
        layout.append(Section('Subsection', 'Sub section description'))
        self._test_output('section_nested', layout)

    def test_verbatim(self):
        layout = VerbatimText('blablabla')
        self._test_output('verbatim_base', layout)


    def test_list(self):
        layout = List(children=('item1', 'item2', 'item3', 'item4'))
        self._test_output('list_base', layout)

    def test_nested_list(self):
        layout = List(children=(Paragraph(("blabla", List(children=('1', "2", "3")))),
                                "an other point"))
        self._test_output('nested_list', layout)


    def test_table(self):
        layout = Table(cols=2, children=('head1', 'head2', 'cell1', 'cell2'))
        self._test_output('table_base', layout)

    def test_field_table(self):
        table = Table(cols=2, klass='field', id='mytable')
        for field, value in (('f1', 'v1'), ('f22', 'v22'), ('f333', 'v333')):
            table.append(Text(field))
            table.append(Text(value))
        self._test_output('field_table', table)

    def test_advanced_table(self):
        table = Table(cols=2, klass='whatever', id='mytable', rheaders=1)
        for field, value in (('field', 'value'), ('f1', 'v1'), ('f22', 'v22'), ('f333', 'v333')):
            table.append(Text(field))
            table.append(Text(value))
        table.append(Link('http://www.perdu.com', 'toi perdu ?'))
        table.append(Text(''))
        self._test_output('advanced_table', table)


##     def test_image(self):
##         layout = Verbatim('blablabla')
##         self._test_output('verbatim_base', layout)
