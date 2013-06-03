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
""" Copyright (c) 2002-2003 LOGILAB S.A. (Paris, FRANCE).
 http://www.logilab.fr/ -- mailto:contact@logilab.fr

Interfaces for PyLint objects
"""

__revision__ = "$Id: interfaces.py,v 1.9 2004-04-24 12:14:53 syt Exp $"

from logilab.common.interface import Interface


class IChecker(Interface):
    """This is an base interface, not designed to be used elsewhere than for
    sub interfaces definition.
    """

    def open(self):
        """called before visiting project (i.e set of modules)"""

    def close(self):
        """called after visiting project (i.e set of modules)"""

##     def open_module(self):
##         """called before visiting a module"""

##     def close_module(self):
##         """called after visiting a module"""


class IRawChecker(IChecker):
    """interface for checker which need to parse the raw file
    """

    def process_module(self, astng):
        """ process a module

        the module's content is accessible via astng.file_stream
        """


class IASTNGChecker(IChecker):
    """ interface for checker which prefers receive events according to
    statement type
    """


class ILinter(Interface):
    """interface for the linter class

    the linter class will generate events to its registered checkers.
    Each checker may interact with the linter instance using this API
    """

    def register_checker(self, checker):
        """register a new checker class

        checker is a class implementing IrawChecker or / and IASTNGChecker
        """

    def add_message(self, msg_id, line=None, node=None, args=None):
        """add the message corresponding to the given id.

        If provided, msg is expanded using args

        astng checkers should provide the node argument,
        raw checkers should provide the line argument.
        """


class IReporter(Interface):
    """ reporter collect messages and display results encapsulated in a layout
    """
    def add_message(self, msg_id, location, msg):
        """add a message of a given type

        msg_id is a message identifier
        location is a 3-uple (module, object, line)
        msg is the actual message
        """

    def display_results(self, layout):
        """display results encapsulated in the layout tree
        """


__all__ = ('IRawChecker', 'ILinter', 'IReporter')
