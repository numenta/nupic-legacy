# -*- coding: utf-8 -*-
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
"""Extend OptionParser with commands.

Example:

>>> parser = OptionParser()
>>> parser.usage = '%prog COMMAND [options] <arg> ...'
>>> parser.add_command('build', 'mymod.build')
>>> parser.add_command('clean', run_clean, add_opt_clean)
>>> run, options, args = parser.parse_command(sys.argv[1:])
>>> return run(options, args[1:])

With mymod.build that defines two functions run and add_options
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('lgc.optparser module is deprecated, use lgc.clcommands instead', DeprecationWarning,
     stacklevel=2)

import sys
import optparse

class OptionParser(optparse.OptionParser):

    def __init__(self, *args, **kwargs):
        optparse.OptionParser.__init__(self, *args, **kwargs)
        self._commands = {}
        self.min_args, self.max_args = 0, 1

    def add_command(self, name, mod_or_funcs, help=''):
        """name of the command, name of module or tuple of functions
        (run, add_options)
        """
        assert isinstance(mod_or_funcs, str) or isinstance(mod_or_funcs, tuple), \
            "mod_or_funcs has to be a module name or a tuple of functions"
        self._commands[name] = (mod_or_funcs, help)

    def print_main_help(self):
        optparse.OptionParser.print_help(self)
        print '\ncommands:'
        for cmdname, (_, help) in self._commands.items():
            print '% 10s - %s' % (cmdname, help)

    def parse_command(self, args):
        if len(args) == 0:
            self.print_main_help()
            sys.exit(1)
        cmd = args[0]
        args = args[1:]
        if cmd not in self._commands:
            if cmd in ('-h', '--help'):
                self.print_main_help()
                sys.exit(0)
            elif self.version is not None and cmd == "--version":
                self.print_version()
                sys.exit(0)
            self.error('unknown command')
        self.prog = '%s %s' % (self.prog, cmd)
        mod_or_f, help = self._commands[cmd]
        # optparse inserts self.description between usage and options help
        self.description = help
        if isinstance(mod_or_f, str):
            exec 'from %s import run, add_options' % mod_or_f
        else:
            run, add_options = mod_or_f
        add_options(self)
        (options, args) = self.parse_args(args)
        if not (self.min_args <= len(args) <= self.max_args):
            self.error('incorrect number of arguments')
        return run, options, args


