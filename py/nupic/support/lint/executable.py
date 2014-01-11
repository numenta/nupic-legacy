# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

"""Pylint checker for executable scripts."""

import os

from pylint.checkers import BaseChecker
from pylint.interfaces import IRawChecker


MSGS = {
    'W9820': ('Non-executable script - script has __main__ block, but the '
              'executable bit is not set. Set the executable bit on the '
              'script or remove the __main__ block.', 'non-executable',
              'Used when a script has a __main__ block but is not executable.'),
    'W9821': ('Missing shebang or improper shebang (should be "#!/usr/bin/env '
              'python") for script that has __main__ block. Add the shebang '
              'line or remove the __main__ block.', 'no-shebang',
              'Used when a script has has a __main__ block but is missing a '
              'shebang line.'),
    'W9822': ('Script has the executable bit set but there is no __main__ '
              'block. Unset the executable bit or add a __main__ block for the '
              'executable code.', 'no-main-executable',
              'Used when a script has no __main__ block but is executable.'),
    'W9823': ('File has a shebang line at the top, but has no __main__ block. '
              'Remove the shebang line or add a __main__ conditional.',
              'no-main-shebang',
              'Used when a script has executable permissions or has a __main__ '
              'block but is missing a shebang line.'),
    }


class ExecutableChecker(BaseChecker):
  """Checks for executable scripts."""

  __implements__ = IRawChecker

  name = 'executable_raw'
  msgs = MSGS
  options = ()

  def process_module(self, node):
    """Process a module.

    The module's content is accessible via the node.file_stream object.
    """
    isExecutable = os.access(node.path, os.X_OK)
    hasShebang = False
    hasMainProtection = False
    for lineno, line in enumerate(node.file_stream):
      lineno += 1
      line = line.strip()
      if lineno == 1 and (line == '#!/usr/bin/env python' or
                          line == '#! /usr/bin/env python'):
        hasShebang = True
      # Keep the checks on separate lines so this file doesn't appear as an
      # executable script.
      if ('__name__' in line and
          '__main__' in line):
        hasMainProtection = True
        break

    if hasMainProtection:
      if not isExecutable:
        self.add_message('W9820', line=1)
      if not hasShebang:
        self.add_message('W9821', line=1)
    else:
      if isExecutable:
        self.add_message('W9822', line=1)
      if hasShebang:
        self.add_message('W9823', line=1)


def register(linter):
  """Register the checker with the linter."""
  linter.register_checker(ExecutableChecker(linter))
