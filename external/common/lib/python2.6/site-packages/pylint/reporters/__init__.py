# Copyright (c) 2003-2010 Sylvain Thenault (thenault@gmail.com).
# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
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
"""utilities methods and classes for reporters"""

import sys, locale

CMPS = ['=', '-', '+']

def diff_string(old, new):
    """given a old and new int value, return a string representing the
    difference
    """
    diff = abs(old - new)
    diff_str = "%s%s" % (CMPS[cmp(old, new)], diff and ('%.2f' % diff) or '')
    return diff_str


class EmptyReport(Exception):
    """raised when a report is empty and so should not be displayed"""

class BaseReporter:
    """base class for reporters

    symbols: show short symbolic names for messages.
    """

    extension = ''

    def __init__(self, output=None):
        self.linter = None
        self.include_ids = None
        self.symbols = None
        self.section = 0
        self.out = None
        self.out_encoding = None
        self.set_output(output)

    def make_sigle(self, msg_id):
        """generate a short prefix for a message.

        The sigle can include the id, the symbol, or both, or it can just be
        the message class.
        """
        if self.include_ids:
            sigle = msg_id
        else:
            sigle = msg_id[0]
        if self.symbols:
            symbol = self.linter.check_message_id(msg_id).symbol
            if symbol:
                sigle += '(%s)' % symbol
        return sigle

    def set_output(self, output=None):
        """set output stream"""
        self.out = output or sys.stdout
        # py3k streams handle their encoding :
        if sys.version_info >= (3, 0):
            self.encode = lambda x: x
            return

        def encode(string):
            if not isinstance(string, unicode):
                return string
            encoding = (getattr(self.out, 'encoding', None) or
                        locale.getdefaultlocale()[1] or
                        sys.getdefaultencoding())
            return string.encode(encoding)
        self.encode = encode

    def writeln(self, string=''):
        """write a line in the output buffer"""
        print >> self.out, self.encode(string)

    def display_results(self, layout):
        """display results encapsulated in the layout tree"""
        self.section = 0
        if self.include_ids and hasattr(layout, 'report_id'):
            layout.children[0].children[0].data += ' (%s)' % layout.report_id
        self._display(layout)

    def _display(self, layout):
        """display the layout"""
        raise NotImplementedError()

    # Event callbacks

    def on_set_current_module(self, module, filepath):
        """starting analyzis of a module"""
        pass

    def on_close(self, stats, previous_stats):
        """global end of analyzis"""
        pass


