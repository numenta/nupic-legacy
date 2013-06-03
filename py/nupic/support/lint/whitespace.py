# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Pylint checker for trailing whitespace."""

from logilab import astng
from pylint.checkers import BaseChecker
from pylint.interfaces import IRawChecker


MSGS = {
    'W9810': ('Trailing whitespace', 'trailing-whitespace',
              'Used when there is trailing whitespace on a line.'),
    }


class TrailingWhitespaceChecker(BaseChecker):
  """Checks for trailing whitespace on every line of the file."""

  __implements__ = IRawChecker

  name = 'trailing_whitespace_raw'
  msgs = MSGS
  options = ()

  def process_module(self, node):
    """Process a module.

    The module's content is accessible via the node.file_stream object.
    """
    for lineno, line in enumerate(node.file_stream):
      lineno += 1
      if line.rstrip() != line.rstrip('\n') and len(line.strip()) > 0:
        self.add_message('W9810', line=lineno)


def register(linter):
  """Register the checker with the linter."""
  linter.register_checker(TrailingWhitespaceChecker(linter))
