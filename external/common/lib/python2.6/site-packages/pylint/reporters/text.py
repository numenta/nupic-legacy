# Copyright (c) 2003-2007 Sylvain Thenault (thenault@gmail.com).
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
"""Plain text reporters:

:text: the default one grouping messages by module
:parseable:
  standard parseable output with full module path on each message (for
  editor integration)
:colorized: an ANSI colorized text reporter

"""

import os
import sys

from logilab.common.ureports import TextWriter
from logilab.common.textutils import colorize_ansi

from pylint.interfaces import IReporter
from pylint.reporters import BaseReporter

TITLE_UNDERLINES = ['', '=', '-', '.']


class TextReporter(BaseReporter):
    """reports messages and layouts in plain text
    """

    __implements__ = IReporter
    extension = 'txt'

    def __init__(self, output=sys.stdout):
        BaseReporter.__init__(self, output)
        self._modules = {}

    def add_message(self, msg_id, location, msg):
        """manage message of different type and in the context of path"""
        module, obj, line, col_offset = location[1:]
        if module not in self._modules:
            if module:
                self.writeln('************* Module %s' % module)
                self._modules[module] = 1
            else:
                self.writeln('************* %s' % module)
        if obj:
            obj = ':%s' % obj
        sigle = self.make_sigle(msg_id)
        self.writeln('%s:%3s,%s%s: %s' % (sigle, line, col_offset, obj, msg))

    def _display(self, layout):
        """launch layouts display"""
        print >> self.out
        TextWriter().format(layout, self.out)


class ParseableTextReporter(TextReporter):
    """a reporter very similar to TextReporter, but display messages in a form
    recognized by most text editors :

    <filename>:<linenum>:<msg>
    """
    line_format = '%(path)s:%(line)s: [%(sigle)s%(obj)s] %(msg)s'

    def __init__(self, output=sys.stdout, relative=True):
        TextReporter.__init__(self, output)
        if relative:
            self._prefix = os.getcwd() + os.sep
        else:
            self._prefix = ''

    def add_message(self, msg_id, location, msg):
        """manage message of different type and in the context of path"""
        path, _, obj, line, _ = location
        if obj:
            obj = ', %s' % obj
        sigle = self.make_sigle(msg_id)
        if self._prefix:
            path = path.replace(self._prefix, '')
        self.writeln(self.line_format % locals())


class VSTextReporter(ParseableTextReporter):
    """Visual studio text reporter"""
    line_format = '%(path)s(%(line)s): [%(sigle)s%(obj)s] %(msg)s'

class ColorizedTextReporter(TextReporter):
    """Simple TextReporter that colorizes text output"""

    COLOR_MAPPING = {
        "I" : ("green", None),
        'C' : (None, "bold"),
        'R' : ("magenta", "bold, italic"),
        'W' : ("blue", None),
        'E' : ("red", "bold"),
        'F' : ("red", "bold, underline"),
        'S' : ("yellow", "inverse"), # S stands for module Separator
    }

    def __init__(self, output=sys.stdout, color_mapping = None):
        TextReporter.__init__(self, output)
        self.color_mapping = color_mapping or \
                             dict(ColorizedTextReporter.COLOR_MAPPING)


    def _get_decoration(self, msg_id):
        """Returns the tuple color, style associated with msg_id as defined
        in self.color_mapping
        """
        try:
            return self.color_mapping[msg_id[0]]
        except KeyError:
            return None, None

    def add_message(self, msg_id, location, msg):
        """manage message of different types, and colorize output
        using ansi escape codes
        """
        module, obj, line, _ = location[1:]
        if module not in self._modules:
            color, style = self._get_decoration('S')
            if module:
                modsep = colorize_ansi('************* Module %s' % module,
                                       color, style)
            else:
                modsep = colorize_ansi('************* %s' % module,
                                       color, style)
            self.writeln(modsep)
            self._modules[module] = 1
        if obj:
            obj = ':%s' % obj
        sigle = self.make_sigle(msg_id)
        color, style = self._get_decoration(sigle)
        msg = colorize_ansi(msg, color, style)
        sigle = colorize_ansi(sigle, color, style)
        self.writeln('%s:%3s%s: %s' % (sigle, line, obj, msg))
