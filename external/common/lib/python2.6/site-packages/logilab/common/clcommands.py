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
"""Helper functions to support command line tools providing more than
one command.

e.g called as "tool command [options] args..." where <options> and <args> are
command'specific
"""

__docformat__ = "restructuredtext en"

import sys
import logging
from os.path import basename

from logilab.common.configuration import Configuration
from logilab.common.logging_ext import init_log, get_threshold
from logilab.common.deprecation import deprecated


class BadCommandUsage(Exception):
    """Raised when an unknown command is used or when a command is not
    correctly used (bad options, too much / missing arguments...).

    Trigger display of command usage.
    """

class CommandError(Exception):
    """Raised when a command can't be processed and we want to display it and
    exit, without traceback nor usage displayed.
    """


# command line access point ####################################################

class CommandLine(dict):
    """Usage:

    >>> LDI = cli.CommandLine('ldi', doc='Logilab debian installer',
                              version=version, rcfile=RCFILE)
    >>> LDI.register(MyCommandClass)
    >>> LDI.register(MyOtherCommandClass)
    >>> LDI.run(sys.argv[1:])

    Arguments:

    * `pgm`, the program name, default to `basename(sys.argv[0])`

    * `doc`, a short description of the command line tool

    * `copyright`, additional doc string that will be appended to the generated
      doc

    * `version`, version number of string of the tool. If specified, global
      --version option will be available.

    * `rcfile`, path to a configuration file. If specified, global --C/--rc-file
      option will be available?  self.rcfile = rcfile

    * `logger`, logger to propagate to commands, default to
      `logging.getLogger(self.pgm))`
    """
    def __init__(self, pgm=None, doc=None, copyright=None, version=None,
                 rcfile=None, logthreshold=logging.ERROR,
                 check_duplicated_command=True):
        if pgm is None:
            pgm = basename(sys.argv[0])
        self.pgm = pgm
        self.doc = doc
        self.copyright = copyright
        self.version = version
        self.rcfile = rcfile
        self.logger = None
        self.logthreshold = logthreshold
        self.check_duplicated_command = check_duplicated_command

    def register(self, cls, force=False):
        """register the given :class:`Command` subclass"""
        assert not self.check_duplicated_command or force or not cls.name in self, \
               'a command %s is already defined' % cls.name
        self[cls.name] = cls
        return cls

    def run(self, args):
        """main command line access point:
        * init logging
        * handle global options (-h/--help, --version, -C/--rc-file)
        * check command
        * run command

        Terminate by :exc:`SystemExit`
        """
        init_log(debug=True, # so that we use StreamHandler
                 logthreshold=self.logthreshold,
                 logformat='%(levelname)s: %(message)s')
        try:
            arg = args.pop(0)
        except IndexError:
            self.usage_and_exit(1)
        if arg in ('-h', '--help'):
            self.usage_and_exit(0)
        if self.version is not None and arg in ('--version'):
            print self.version
            sys.exit(0)
        rcfile = self.rcfile
        if rcfile is not None and arg in ('-C', '--rc-file'):
            try:
                rcfile = args.pop(0)
                arg = args.pop(0)
            except IndexError:
                self.usage_and_exit(1)
        try:
            command = self.get_command(arg)
        except KeyError:
            print 'ERROR: no %s command' % arg
            print
            self.usage_and_exit(1)
        try:
            sys.exit(command.main_run(args, rcfile))
        except KeyboardInterrupt, exc:
            print 'Interrupted',
            if str(exc):
                print ': %s' % exc,
            print
            sys.exit(4)
        except BadCommandUsage, err:
            print 'ERROR:', err
            print
            print command.help()
            sys.exit(1)

    def create_logger(self, handler, logthreshold=None):
        logger = logging.Logger(self.pgm)
        logger.handlers = [handler]
        if logthreshold is None:
            logthreshold = get_threshold(self.logthreshold)
        logger.setLevel(logthreshold)
        return logger

    def get_command(self, cmd, logger=None):
        if logger is None:
            logger = self.logger
        if logger is None:
            logger = self.logger = logging.getLogger(self.pgm)
            logger.setLevel(get_threshold(self.logthreshold))
        return self[cmd](logger)

    def usage(self):
        """display usage for the main program (i.e. when no command supplied)
        and exit
        """
        print 'usage:', self.pgm,
        if self.rcfile:
            print '[--rc-file=<configuration file>]',
        print '<command> [options] <command argument>...'
        if self.doc:
            print '\n%s' % self.doc
        print  '''
Type "%(pgm)s <command> --help" for more information about a specific
command. Available commands are :\n''' % self.__dict__
        max_len = max([len(cmd) for cmd in self])
        padding = ' ' * max_len
        for cmdname, cmd in sorted(self.items()):
            if not cmd.hidden:
                print ' ', (cmdname + padding)[:max_len], cmd.short_description()
        if self.rcfile:
            print '''
Use --rc-file=<configuration file> / -C <configuration file> before the command
to specify a configuration file. Default to %s.
''' % self.rcfile
        print  '''%(pgm)s -h/--help
      display this usage information and exit''' % self.__dict__
        if self.version:
            print  '''%(pgm)s -v/--version
      display version configuration and exit''' % self.__dict__
        if self.copyright:
            print '\n', self.copyright

    def usage_and_exit(self, status):
        self.usage()
        sys.exit(status)


# base command classes #########################################################

class Command(Configuration):
    """Base class for command line commands.

    Class attributes:

    * `name`, the name of the command

    * `min_args`, minimum number of arguments, None if unspecified

    * `max_args`, maximum number of arguments, None if unspecified

    * `arguments`, string describing arguments, used in command usage

    * `hidden`, boolean flag telling if the command should be hidden, e.g. does
      not appear in help's commands list

    * `options`, options list, as allowed by :mod:configuration
    """

    arguments = ''
    name = ''
    # hidden from help ?
    hidden = False
    # max/min args, None meaning unspecified
    min_args = None
    max_args = None

    @classmethod
    def description(cls):
        return cls.__doc__.replace('    ', '')

    @classmethod
    def short_description(cls):
        return cls.description().split('.')[0]

    def __init__(self, logger):
        usage = '%%prog %s %s\n\n%s' % (self.name, self.arguments,
                                        self.description())
        Configuration.__init__(self, usage=usage)
        self.logger = logger

    def check_args(self, args):
        """check command's arguments are provided"""
        if self.min_args is not None and len(args) < self.min_args:
            raise BadCommandUsage('missing argument')
        if self.max_args is not None and len(args) > self.max_args:
            raise BadCommandUsage('too many arguments')

    def main_run(self, args, rcfile=None):
        """Run the command and return status 0 if everything went fine.

        If :exc:`CommandError` is raised by the underlying command, simply log
        the error and return status 2.

        Any other exceptions, including :exc:`BadCommandUsage` will be
        propagated.
        """
        if rcfile:
            self.load_file_configuration(rcfile)
        args = self.load_command_line_configuration(args)
        try:
            self.check_args(args)
            self.run(args)
        except CommandError, err:
            self.logger.error(err)
            return 2
        return 0

    def run(self, args):
        """run the command with its specific arguments"""
        raise NotImplementedError()


class ListCommandsCommand(Command):
    """list available commands, useful for bash completion."""
    name = 'listcommands'
    arguments = '[command]'
    hidden = True

    def run(self, args):
        """run the command with its specific arguments"""
        if args:
            command = args.pop()
            cmd = _COMMANDS[command]
            for optname, optdict in cmd.options:
                print '--help'
                print '--' + optname
        else:
            commands = sorted(_COMMANDS.keys())
            for command in commands:
                cmd = _COMMANDS[command]
                if not cmd.hidden:
                    print command


# deprecated stuff #############################################################

_COMMANDS = CommandLine()

DEFAULT_COPYRIGHT = '''\
Copyright (c) 2004-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
http://www.logilab.fr/ -- mailto:contact@logilab.fr'''

@deprecated('use cls.register(cli)')
def register_commands(commands):
    """register existing commands"""
    for command_klass in commands:
        _COMMANDS.register(command_klass)

@deprecated('use args.pop(0)')
def main_run(args, doc=None, copyright=None, version=None):
    """command line tool: run command specified by argument list (without the
    program name). Raise SystemExit with status 0 if everything went fine.

    >>> main_run(sys.argv[1:])
    """
    _COMMANDS.doc = doc
    _COMMANDS.copyright = copyright
    _COMMANDS.version = version
    _COMMANDS.run(args)

@deprecated('use args.pop(0)')
def pop_arg(args_list, expected_size_after=None, msg="Missing argument"):
    """helper function to get and check command line arguments"""
    try:
        value = args_list.pop(0)
    except IndexError:
        raise BadCommandUsage(msg)
    if expected_size_after is not None and len(args_list) > expected_size_after:
        raise BadCommandUsage('too many arguments')
    return value

