# pylint: disable=W0511
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
""" Copyright (c) 2000-2010 LOGILAB S.A. (Paris, FRANCE).
 http://www.logilab.fr/ -- mailto:contact@logilab.fr

Check source code is ascii only or has an encoding declaration (PEP 263)
"""

import re

from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker


MSGS = {
    'W0511': ('%s',
              'fixme',
              'Used when a warning note as FIXME or XXX is detected.'),
    }

class EncodingChecker(BaseChecker):
    """checks for:
    * warning notes in the code like FIXME, XXX
    * PEP 263: source code with non ascii character but no encoding declaration
    """
    __implements__ = IRawChecker

    # configuration section name
    name = 'miscellaneous'
    msgs = MSGS

    options = (('notes',
                {'type' : 'csv', 'metavar' : '<comma separated values>',
                 'default' : ('FIXME', 'XXX', 'TODO'),
                 'help' : 'List of note tags to take in consideration, \
separated by a comma.'
                 }),
               )

    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)

    def process_module(self, node):
        """inspect the source file to found encoding problem or fixmes like
        notes
        """
        stream = node.file_stream
        stream.seek(0) # XXX may be removed with astng > 0.23
        # warning notes in the code
        notes = []
        for note in self.config.notes:
            notes.append(re.compile(note))
        linenum = 1
        for line in stream.readlines():
            for note in notes:
                match = note.search(line)
                if match:
                    self.add_message('W0511', args=line[match.start():-1],
                                     line=linenum)
                    break
            linenum += 1



def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(EncodingChecker(linter))
