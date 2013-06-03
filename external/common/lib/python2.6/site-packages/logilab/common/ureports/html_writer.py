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
"""HTML formatting drivers for ureports"""
__docformat__ = "restructuredtext en"

from cgi import escape

from logilab.common.ureports import BaseWriter


class HTMLWriter(BaseWriter):
    """format layouts as HTML"""

    def __init__(self, snippet=None):
        super(HTMLWriter, self).__init__()
        self.snippet = snippet

    def handle_attrs(self, layout):
        """get an attribute string from layout member attributes"""
        attrs = ''
        klass = getattr(layout, 'klass', None)
        if klass:
            attrs += ' class="%s"' % klass
        nid = getattr(layout, 'id', None)
        if nid:
            attrs += ' id="%s"' % nid
        return attrs

    def begin_format(self, layout):
        """begin to format a layout"""
        super(HTMLWriter, self).begin_format(layout)
        if self.snippet is None:
            self.writeln('<html>')
            self.writeln('<body>')

    def end_format(self, layout):
        """finished to format a layout"""
        if self.snippet is None:
            self.writeln('</body>')
            self.writeln('</html>')


    def visit_section(self, layout):
        """display a section as html, using div + h[section level]"""
        self.section += 1
        self.writeln('<div%s>' % self.handle_attrs(layout))
        self.format_children(layout)
        self.writeln('</div>')
        self.section -= 1

    def visit_title(self, layout):
        """display a title using <hX>"""
        self.write('<h%s%s>' % (self.section, self.handle_attrs(layout)))
        self.format_children(layout)
        self.writeln('</h%s>' % self.section)

    def visit_table(self, layout):
        """display a table as html"""
        self.writeln('<table%s>' % self.handle_attrs(layout))
        table_content = self.get_table_content(layout)
        for i in range(len(table_content)):
            row = table_content[i]
            if i == 0 and layout.rheaders:
                self.writeln('<tr class="header">')
            elif i+1 == len(table_content) and layout.rrheaders:
                self.writeln('<tr class="header">')
            else:
                self.writeln('<tr class="%s">' % (i%2 and 'even' or 'odd'))
            for j in range(len(row)):
                cell = row[j] or '&#160;'
                if (layout.rheaders and i == 0) or \
                   (layout.cheaders and j == 0) or \
                   (layout.rrheaders and i+1 == len(table_content)) or \
                   (layout.rcheaders and j+1 == len(row)):
                    self.writeln('<th>%s</th>' % cell)
                else:
                    self.writeln('<td>%s</td>' % cell)
            self.writeln('</tr>')
        self.writeln('</table>')

    def visit_list(self, layout):
        """display a list as html"""
        self.writeln('<ul%s>' % self.handle_attrs(layout))
        for row in list(self.compute_content(layout)):
            self.writeln('<li>%s</li>' % row)
        self.writeln('</ul>')

    def visit_paragraph(self, layout):
        """display links (using <p>)"""
        self.write('<p>')
        self.format_children(layout)
        self.write('</p>')

    def visit_span(self, layout):
        """display links (using <p>)"""
        self.write('<span%s>' % self.handle_attrs(layout))
        self.format_children(layout)
        self.write('</span>')

    def visit_link(self, layout):
        """display links (using <a>)"""
        self.write(' <a href="%s"%s>%s</a>' % (layout.url,
                                               self.handle_attrs(layout),
                                               layout.label))
    def visit_verbatimtext(self, layout):
        """display verbatim text (using <pre>)"""
        self.write('<pre>')
        self.write(layout.data.replace('&', '&amp;').replace('<', '&lt;'))
        self.write('</pre>')

    def visit_text(self, layout):
        """add some text"""
        data = layout.data
        if layout.escaped:
            data = data.replace('&', '&amp;').replace('<', '&lt;')
        self.write(data)
