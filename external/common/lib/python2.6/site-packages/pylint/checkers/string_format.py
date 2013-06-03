# Copyright (c) 2009-2010 Arista Networks, Inc. - James Lingard
# Copyright (c) 2004-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""Checker for string formatting operations.
"""

from logilab import astng
from pylint.interfaces import IASTNGChecker
from pylint.checkers import BaseChecker
from pylint.checkers import utils


MSGS = {
    'E1300': ("Unsupported format character %r (%#02x) at index %d",
              "bad-format-character",
              "Used when a unsupported format character is used in a format\
              string."),
    'E1301': ("Format string ends in middle of conversion specifier",
              "truncated-format-string",
              "Used when a format string terminates before the end of a \
              conversion specifier."),
    'E1302': ("Mixing named and unnamed conversion specifiers in format string",
              "mixed-format-string",
              "Used when a format string contains both named (e.g. '%(foo)d') \
              and unnamed (e.g. '%d') conversion specifiers.  This is also \
              used when a named conversion specifier contains * for the \
              minimum field width and/or precision."),
    'E1303': ("Expected mapping for format string, not %s",
              "format-needs-mapping",
              "Used when a format string that uses named conversion specifiers \
              is used with an argument that is not a mapping."),
    'W1300': ("Format string dictionary key should be a string, not %s",
              "bad-format-string-key",
              "Used when a format string that uses named conversion specifiers \
              is used with a dictionary whose keys are not all strings."),
    'W1301': ("Unused key %r in format string dictionary",
              "unused-format-string-key",
              "Used when a format string that uses named conversion specifiers \
              is used with a dictionary that conWtains keys not required by the \
              format string."),
    'E1304': ("Missing key %r in format string dictionary",
              "missing-format-string-key",
              "Used when a format string that uses named conversion specifiers \
              is used with a dictionary that doesn't contain all the keys \
              required by the format string."),
    'E1305': ("Too many arguments for format string",
              "too-many-format-args",
              "Used when a format string that uses unnamed conversion \
              specifiers is given too few arguments."),
    'E1306': ("Not enough arguments for format string",
              "too-few-format-args",
              "Used when a format string that uses unnamed conversion \
              specifiers is given too many arguments"),
    }

OTHER_NODES = (astng.Const, astng.List, astng.Backquote,
               astng.Lambda, astng.Function,
               astng.ListComp, astng.SetComp, astng.GenExpr)

class StringFormatChecker(BaseChecker):
    """Checks string formatting operations to ensure that the format string
    is valid and the arguments match the format string.
    """

    __implements__ = (IASTNGChecker,)
    name = 'string_format'
    msgs = MSGS

    def visit_binop(self, node):
        if node.op != '%':
            return
        left = node.left
        args = node.right

        if not (isinstance(left, astng.Const)
            and isinstance(left.value, basestring)):
            return
        format_string = left.value
        try:
            required_keys, required_num_args = \
                utils.parse_format_string(format_string)
        except utils.UnsupportedFormatCharacter, e:
            c = format_string[e.index]
            self.add_message('E1300', node=node, args=(c, ord(c), e.index))
            return
        except utils.IncompleteFormatString:
            self.add_message('E1301', node=node)
            return
        if required_keys and required_num_args:
            # The format string uses both named and unnamed format
            # specifiers.
            self.add_message('E1302', node=node)
        elif required_keys:
            # The format string uses only named format specifiers.
            # Check that the RHS of the % operator is a mapping object
            # that contains precisely the set of keys required by the
            # format string.
            if isinstance(args, astng.Dict):
                keys = set()
                unknown_keys = False
                for k, _ in args.items:
                    if isinstance(k, astng.Const):
                        key = k.value
                        if isinstance(key, basestring):
                            keys.add(key)
                        else:
                            self.add_message('W1300', node=node, args=key)
                    else:
                        # One of the keys was something other than a
                        # constant.  Since we can't tell what it is,
                        # supress checks for missing keys in the
                        # dictionary.
                        unknown_keys = True
                if not unknown_keys:
                    for key in required_keys:
                        if key not in keys:
                            self.add_message('E1304', node=node, args=key)
                for key in keys:
                    if key not in required_keys:
                        self.add_message('W1301', node=node, args=key)
            elif isinstance(args, OTHER_NODES + (astng.Tuple,)):
                type_name = type(args).__name__
                self.add_message('E1303', node=node, args=type_name)
            # else:
                # The RHS of the format specifier is a name or
                # expression.  It may be a mapping object, so
                # there's nothing we can check.
        else:
            # The format string uses only unnamed format specifiers.
            # Check that the number of arguments passed to the RHS of
            # the % operator matches the number required by the format
            # string.
            if isinstance(args, astng.Tuple):
                num_args = len(args.elts)
            elif isinstance(args, OTHER_NODES + (astng.Dict, astng.DictComp)):
                num_args = 1
            else:
                # The RHS of the format specifier is a name or
                # expression.  It could be a tuple of unknown size, so
                # there's nothing we can check.
                num_args = None
            if num_args is not None:
                if num_args > required_num_args:
                    self.add_message('E1305', node=node)
                elif num_args < required_num_args:
                    self.add_message('E1306', node=node)


def register(linter):
    """required method to auto register this checker """
    linter.register_checker(StringFormatChecker(linter))
