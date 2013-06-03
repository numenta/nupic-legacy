# Copyright (c) 2003-2006 Sylvain Thenault (thenault@gmail.com).
# Copyright (c) 2003-2011 LOGILAB S.A. (Paris, FRANCE).
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
"""HTML reporter"""

import sys
from cgi import escape

from logilab.common.ureports import HTMLWriter, Section, Table

from pylint.interfaces import IReporter
from pylint.reporters import BaseReporter


class HTMLReporter(BaseReporter):
    """report messages and layouts in HTML"""

    __implements__ = IReporter
    extension = 'html'

    def __init__(self, output=sys.stdout):
        BaseReporter.__init__(self, output)
        self.msgs = []

    def add_message(self, msg_id, location, msg):
        """manage message of different type and in the context of path"""
        module, obj, line, col_offset = location[1:]
        sigle = self.make_sigle(msg_id)
        self.msgs += [sigle, module, obj, str(line), str(col_offset), escape(msg)]

    def set_output(self, output=None):
        """set output stream

        messages buffered for old output is processed first"""
        if self.out and self.msgs:
            self._display(Section())
        BaseReporter.set_output(self, output)

    def _display(self, layout):
        """launch layouts display

        overridden from BaseReporter to add insert the messages section
        (in add_message, message is not displayed, just collected so it
        can be displayed in an html table)
        """
        if self.msgs:
            # add stored messages to the layout
            msgs = ['type', 'module', 'object', 'line', 'col_offset', 'message']
            msgs += self.msgs
            sect = Section('Messages')
            layout.append(sect)
            sect.append(Table(cols=6, children=msgs, rheaders=1))
            self.msgs = []
        HTMLWriter().format(layout, self.out)

