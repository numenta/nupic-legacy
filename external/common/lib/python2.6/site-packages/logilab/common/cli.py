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
"""Command line interface helper classes.

It provides some default commands, a help system, a default readline
configuration with completion and persistent history.

Example::

    class BookShell(CLIHelper):

        def __init__(self):
            # quit and help are builtins
            # CMD_MAP keys are commands, values are topics
            self.CMD_MAP['pionce'] = _("Sommeil")
            self.CMD_MAP['ronfle'] = _("Sommeil")
            CLIHelper.__init__(self)

        help_do_pionce = ("pionce", "pionce duree", _("met ton corps en veille"))
        def do_pionce(self):
            print 'nap is good'

        help_do_ronfle = ("ronfle", "ronfle volume", _("met les autres en veille"))
        def do_ronfle(self):
            print 'fuuuuuuuuuuuu rhhhhhrhrhrrh'

    cl = BookShell()
"""

__docformat__ = "restructuredtext en"

from logilab.common.compat import raw_input, builtins
if not hasattr(builtins, '_'):
    builtins._ = str


def init_readline(complete_method, histfile=None):
    """Init the readline library if available."""
    try:
        import readline
        readline.parse_and_bind("tab: complete")
        readline.set_completer(complete_method)
        string = readline.get_completer_delims().replace(':', '')
        readline.set_completer_delims(string)
        if histfile is not None:
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            import atexit
            atexit.register(readline.write_history_file, histfile)
    except:
        print 'readline is not available :-('


class Completer :
    """Readline completer."""

    def __init__(self, commands):
        self.list = commands

    def complete(self, text, state):
        """Hook called by readline when <tab> is pressed."""
        n = len(text)
        matches = []
        for cmd in self.list :
            if cmd[:n] == text :
                matches.append(cmd)
        try:
            return matches[state]
        except IndexError:
            return None


class CLIHelper:
    """An abstract command line interface client which recognize commands
    and provide an help system.
    """

    CMD_MAP = {'help': _("Others"),
               'quit': _("Others"),
               }
    CMD_PREFIX = ''

    def __init__(self, histfile=None) :
        self._topics = {}
        self.commands = None
        self._completer = Completer(self._register_commands())
        init_readline(self._completer.complete, histfile)

    def run(self):
        """loop on user input, exit on EOF"""
        while True:
            try:
                line = raw_input('>>> ')
            except EOFError:
                print
                break
            s_line = line.strip()
            if not s_line:
                continue
            args = s_line.split()
            if args[0] in self.commands:
                try:
                    cmd = 'do_%s' % self.commands[args[0]]
                    getattr(self, cmd)(*args[1:])
                except EOFError:
                    break
                except:
                    import traceback
                    traceback.print_exc()
            else:
                try:
                    self.handle_line(s_line)
                except:
                    import traceback
                    traceback.print_exc()

    def handle_line(self, stripped_line):
        """Method to overload in the concrete class (should handle
        lines which are not commands).
        """
        raise NotImplementedError()


    # private methods #########################################################

    def _register_commands(self):
        """ register available commands method and return the list of
        commands name
        """
        self.commands = {}
        self._command_help = {}
        commands = [attr[3:] for attr in dir(self) if attr[:3] == 'do_']
        for command in commands:
            topic = self.CMD_MAP[command]
            help_method = getattr(self, 'help_do_%s' % command)
            self._topics.setdefault(topic, []).append(help_method)
            self.commands[self.CMD_PREFIX + command] = command
            self._command_help[command] = help_method
        return self.commands.keys()

    def _print_help(self, cmd, syntax, explanation):
        print _('Command %s') % cmd
        print _('Syntax: %s') % syntax
        print '\t', explanation
        print


    # predefined commands #####################################################

    def do_help(self, command=None) :
        """base input of the help system"""
        if command in self._command_help:
            self._print_help(*self._command_help[command])
        elif command is None or command not in self._topics:
            print _("Use help <topic> or help <command>.")
            print _("Available topics are:")
            topics = sorted(self._topics.keys())
            for topic in topics:
                print '\t', topic
            print
            print _("Available commands are:")
            commands = self.commands.keys()
            commands.sort()
            for command in commands:
                print '\t', command[len(self.CMD_PREFIX):]

        else:
            print _('Available commands about %s:') % command
            print
            for command_help_method in self._topics[command]:
                try:
                    if callable(command_help_method):
                        self._print_help(*command_help_method())
                    else:
                        self._print_help(*command_help_method)
                except:
                    import traceback
                    traceback.print_exc()
                    print 'ERROR in help method %s'% (
                        command_help_method.func_name)

    help_do_help = ("help", "help [topic|command]",
                    _("print help message for the given topic/command or \
available topics when no argument"))

    def do_quit(self):
        """quit the CLI"""
        raise EOFError()

    def help_do_quit(self):
        return ("quit", "quit", _("quit the application"))
