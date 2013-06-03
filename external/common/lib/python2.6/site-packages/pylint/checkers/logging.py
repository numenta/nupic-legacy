# Copyright (c) 2009-2010 Google, Inc.
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
"""checker for use of Python logging
"""

from logilab import astng
from pylint import checkers
from pylint import interfaces
from pylint.checkers import utils


MSGS = {
    'W1201': ('Specify string format arguments as logging function parameters',
             'logging-not-lazy',
             'Used when a logging statement has a call form of '
             '"logging.<logging method>(format_string % (format_args...))". '
             'Such calls should leave string interpolation to the logging '
             'method itself and be written '
             '"logging.<logging method>(format_string, format_args...)" '
             'so that the program may avoid incurring the cost of the '
             'interpolation in those cases in which no message will be '
             'logged. For more, see '
             'http://www.python.org/dev/peps/pep-0282/.'),
    'E1200': ('Unsupported logging format character %r (%#02x) at index %d',
              'logging-unsupported-format',
              'Used when an unsupported format character is used in a logging\
              statement format string.'),
    'E1201': ('Logging format string ends in middle of conversion specifier',
              'logging-format-truncated',
              'Used when a logging statement format string terminates before\
              the end of a conversion specifier.'),
    'E1205': ('Too many arguments for logging format string',
              'logging-too-many-args',
              'Used when a logging format string is given too few arguments.'),
    'E1206': ('Not enough arguments for logging format string',
              'logging-too-few-args',
              'Used when a logging format string is given too many arguments'),
    }


CHECKED_CONVENIENCE_FUNCTIONS = set([
    'critical', 'debug', 'error', 'exception', 'fatal', 'info', 'warn',
    'warning'])


class LoggingChecker(checkers.BaseChecker):
    """Checks use of the logging module."""

    __implements__ = interfaces.IASTNGChecker
    name = 'logging'
    msgs = MSGS

    def visit_module(self, unused_node):
        """Clears any state left in this checker from last module checked."""
        # The code being checked can just as easily "import logging as foo",
        # so it is necessary to process the imports and store in this field
        # what name the logging module is actually given.
        self._logging_name = None

    def visit_import(self, node):
        """Checks to see if this module uses Python's built-in logging."""
        for module, as_name in node.names:
            if module == 'logging':
                if as_name:
                    self._logging_name = as_name
                else:
                    self._logging_name = 'logging'

    def visit_callfunc(self, node):
        """Checks calls to (simple forms of) logging methods."""
        if (not isinstance(node.func, astng.Getattr)
            or not isinstance(node.func.expr, astng.Name)
            or node.func.expr.name != self._logging_name):
            return
        self._check_convenience_methods(node)
        self._check_log_methods(node)

    def _check_convenience_methods(self, node):
        """Checks calls to logging convenience methods (like logging.warn)."""
        if node.func.attrname not in CHECKED_CONVENIENCE_FUNCTIONS:
            return
        if node.starargs or node.kwargs or not node.args:
            # Either no args, star args, or double-star args. Beyond the
            # scope of this checker.
            return
        if isinstance(node.args[0], astng.BinOp) and node.args[0].op == '%':
            self.add_message('W1201', node=node)
        elif isinstance(node.args[0], astng.Const):
            self._check_format_string(node, 0)

    def _check_log_methods(self, node):
        """Checks calls to logging.log(level, format, *format_args)."""
        if node.func.attrname != 'log':
            return
        if node.starargs or node.kwargs or len(node.args) < 2:
            # Either a malformed call, star args, or double-star args. Beyond
            # the scope of this checker.
            return
        if isinstance(node.args[1], astng.BinOp) and node.args[1].op == '%':
            self.add_message('W1201', node=node)
        elif isinstance(node.args[1], astng.Const):
            self._check_format_string(node, 1)

    def _check_format_string(self, node, format_arg):
        """Checks that format string tokens match the supplied arguments.

        Args:
          node: AST node to be checked.
          format_arg: Index of the format string in the node arguments.
        """
        num_args = self._count_supplied_tokens(node.args[format_arg + 1:])
        if not num_args:
            # If no args were supplied, then all format strings are valid -
            # don't check any further.
            return
        format_string = node.args[format_arg].value
        if not isinstance(format_string, basestring):
            # If the log format is constant non-string (e.g. logging.debug(5)),
            # ensure there are no arguments.
            required_num_args = 0
        else:
            try:
                keyword_args, required_num_args = \
                    utils.parse_format_string(format_string)
                if keyword_args:
                    # Keyword checking on logging strings is complicated by
                    # special keywords - out of scope.
                    return
            except utils.UnsupportedFormatCharacter, e:
                c = format_string[e.index]
                self.add_message('E1200', node=node, args=(c, ord(c), e.index))
                return
            except utils.IncompleteFormatString:
                self.add_message('E1201', node=node)
                return
        if num_args > required_num_args:
            self.add_message('E1205', node=node)
        elif num_args < required_num_args:
            self.add_message('E1206', node=node)

    def _count_supplied_tokens(self, args):
        """Counts the number of tokens in an args list.

        The Python log functions allow for special keyword arguments: func,
        exc_info and extra. To handle these cases correctly, we only count
        arguments that aren't keywords.

        Args:
          args: List of AST nodes that are arguments for a log format string.

        Returns:
          Number of AST nodes that aren't keywords.
        """
        return sum(1 for arg in args if not isinstance(arg, astng.Keyword))


def register(linter):
    """Required method to auto-register this checker."""
    linter.register_checker(LoggingChecker(linter))
