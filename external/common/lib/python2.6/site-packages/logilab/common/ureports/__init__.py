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
"""Universal report objects and some formatting drivers.

A way to create simple reports using python objects, primarily designed to be
formatted as text and html.
"""
from __future__ import generators
__docformat__ = "restructuredtext en"

import sys
from cStringIO import StringIO
from StringIO import StringIO as UStringIO

from logilab.common.textutils import linesep


def get_nodes(node, klass):
    """return an iterator on all children node of the given klass"""
    for child in node.children:
        if isinstance(child, klass):
            yield child
        # recurse (FIXME: recursion controled by an option)
        for grandchild in get_nodes(child, klass):
            yield grandchild

def layout_title(layout):
    """try to return the layout's title as string, return None if not found
    """
    for child in layout.children:
        if isinstance(child, Title):
            return ' '.join([node.data for node in get_nodes(child, Text)])

def build_summary(layout, level=1):
    """make a summary for the report, including X level"""
    assert level > 0
    level -= 1
    summary = List(klass='summary')
    for child in layout.children:
        if not isinstance(child, Section):
            continue
        label = layout_title(child)
        if not label and not child.id:
            continue
        if not child.id:
            child.id = label.replace(' ', '-')
        node = Link('#'+child.id, label=label or child.id)
        # FIXME: Three following lines produce not very compliant
        # docbook: there are some useless <para><para>. They might be
        # replaced by the three commented lines but this then produces
        # a bug in html display...
        if level and [n for n in child.children if isinstance(n, Section)]:
            node = Paragraph([node, build_summary(child, level)])
        summary.append(node)
#         summary.append(node)
#         if level and [n for n in child.children if isinstance(n, Section)]:
#             summary.append(build_summary(child, level))
    return summary


class BaseWriter(object):
    """base class for ureport writers"""

    def format(self, layout, stream=None, encoding=None):
        """format and write the given layout into the stream object

        unicode policy: unicode strings may be found in the layout;
        try to call stream.write with it, but give it back encoded using
        the given encoding if it fails
        """
        if stream is None:
            stream = sys.stdout
        if not encoding:
            encoding = getattr(stream, 'encoding', 'UTF-8')
        self.encoding = encoding or 'UTF-8'
        self.__compute_funcs = []
        self.out = stream
        self.begin_format(layout)
        layout.accept(self)
        self.end_format(layout)

    def format_children(self, layout):
        """recurse on the layout children and call their accept method
        (see the Visitor pattern)
        """
        for child in getattr(layout, 'children', ()):
            child.accept(self)

    def writeln(self, string=''):
        """write a line in the output buffer"""
        self.write(string + linesep)

    def write(self, string):
        """write a string in the output buffer"""
        try:
            self.out.write(string)
        except UnicodeEncodeError:
            self.out.write(string.encode(self.encoding))

    def begin_format(self, layout):
        """begin to format a layout"""
        self.section = 0

    def end_format(self, layout):
        """finished to format a layout"""

    def get_table_content(self, table):
        """trick to get table content without actually writing it

        return an aligned list of lists containing table cells values as string
        """
        result = [[]]
        cols = table.cols
        for cell in self.compute_content(table):
            if cols == 0:
                result.append([])
                cols = table.cols
            cols -= 1
            result[-1].append(cell)
        # fill missing cells
        while len(result[-1]) < cols:
            result[-1].append('')
        return result

    def compute_content(self, layout):
        """trick to compute the formatting of children layout before actually
        writing it

        return an iterator on strings (one for each child element)
        """
        # use cells !
        def write(data):
            try:
                stream.write(data)
            except UnicodeEncodeError:
                stream.write(data.encode(self.encoding))
        def writeln(data=''):
            try:
                stream.write(data+linesep)
            except UnicodeEncodeError:
                stream.write(data.encode(self.encoding)+linesep)
        self.write = write
        self.writeln = writeln
        self.__compute_funcs.append((write, writeln))
        for child in layout.children:
            stream = UStringIO()
            child.accept(self)
            yield stream.getvalue()
        self.__compute_funcs.pop()
        try:
            self.write, self.writeln = self.__compute_funcs[-1]
        except IndexError:
            del self.write
            del self.writeln


from logilab.common.ureports.nodes import *
from logilab.common.ureports.text_writer import TextWriter
from logilab.common.ureports.html_writer import HTMLWriter
