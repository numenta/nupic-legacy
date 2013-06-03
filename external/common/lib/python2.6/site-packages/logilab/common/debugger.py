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
"""Customized version of pdb's default debugger.

- sets up a history file
- uses ipython if available to colorize lines of code
- overrides list command to search for current block instead
  of using 5 lines of context




"""
__docformat__ = "restructuredtext en"

try:
    import readline
except ImportError:
    readline = None
import os
import os.path as osp
import sys
from pdb import Pdb
from cStringIO import StringIO
import inspect

try:
    from IPython import PyColorize
except ImportError:
    def colorize(source, *args):
        """fallback colorize function"""
        return source
    def colorize_source(source, *args):
        return source
else:
    def colorize(source, start_lineno, curlineno):
        """colorize and annotate source with linenos
        (as in pdb's list command)
        """
        parser = PyColorize.Parser()
        output = StringIO()
        parser.format(source, output)
        annotated = []
        for index, line in enumerate(output.getvalue().splitlines()):
            lineno = index + start_lineno
            if lineno == curlineno:
                annotated.append('%4s\t->\t%s' % (lineno, line))
            else:
                annotated.append('%4s\t\t%s' % (lineno, line))
        return '\n'.join(annotated)

    def colorize_source(source):
        """colorize given source"""
        parser = PyColorize.Parser()
        output = StringIO()
        parser.format(source, output)
        return output.getvalue()


def getsource(obj):
    """Return the text of the source code for an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a single string.  An
    IOError is raised if the source code cannot be retrieved."""
    lines, lnum = inspect.getsourcelines(obj)
    return ''.join(lines), lnum


################################################################
class Debugger(Pdb):
    """custom debugger

    - sets up a history file
    - uses ipython if available to colorize lines of code
    - overrides list command to search for current block instead
      of using 5 lines of context
    """
    def __init__(self, tcbk=None):
        Pdb.__init__(self)
        self.reset()
        if tcbk:
            while tcbk.tb_next is not None:
                tcbk = tcbk.tb_next
        self._tcbk = tcbk
        self._histfile = os.path.expanduser("~/.pdbhist")

    def setup_history_file(self):
        """if readline is available, read pdb history file
        """
        if readline is not None:
            try:
                # XXX try..except shouldn't be necessary
                # read_history_file() can accept None
                readline.read_history_file(self._histfile)
            except IOError:
                pass

    def start(self):
        """starts the interactive mode"""
        self.interaction(self._tcbk.tb_frame, self._tcbk)

    def setup(self, frame, tcbk):
        """setup hook: set up history file"""
        self.setup_history_file()
        Pdb.setup(self, frame, tcbk)

    def set_quit(self):
        """quit hook: save commands in the history file"""
        if readline is not None:
            readline.write_history_file(self._histfile)
        Pdb.set_quit(self)

    def complete_p(self, text, line, begin_idx, end_idx):
        """provide variable names completion for the ``p`` command"""
        namespace = dict(self.curframe.f_globals)
        namespace.update(self.curframe.f_locals)
        if '.' in text:
            return self.attr_matches(text, namespace)
        return [varname for varname in namespace if varname.startswith(text)]


    def attr_matches(self, text, namespace):
        """implementation coming from rlcompleter.Completer.attr_matches
        Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluatable in self.namespace, it will be evaluated and its attributes
        (as revealed by dir()) are used as possible completions.  (For class
        instances, class members are also considered.)

        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.

        """
        import re
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            return
        expr, attr = m.group(1, 3)
        object = eval(expr, namespace)
        words = dir(object)
        if hasattr(object, '__class__'):
            words.append('__class__')
            words = words + self.get_class_members(object.__class__)
        matches = []
        n = len(attr)
        for word in words:
            if word[:n] == attr and word != "__builtins__":
                matches.append("%s.%s" % (expr, word))
        return matches

    def get_class_members(self, klass):
        """implementation coming from rlcompleter.get_class_members"""
        ret = dir(klass)
        if hasattr(klass, '__bases__'):
            for base in klass.__bases__:
                ret = ret + self.get_class_members(base)
        return ret

    ## specific / overridden commands
    def do_list(self, arg):
        """overrides default list command to display the surrounding block
        instead of 5 lines of context
        """
        self.lastcmd = 'list'
        if not arg:
            try:
                source, start_lineno = getsource(self.curframe)
                print colorize(''.join(source), start_lineno,
                               self.curframe.f_lineno)
            except KeyboardInterrupt:
                pass
            except IOError:
                Pdb.do_list(self, arg)
        else:
            Pdb.do_list(self, arg)
    do_l = do_list

    def do_open(self, arg):
        """opens source file corresponding to the current stack level"""
        filename = self.curframe.f_code.co_filename
        lineno = self.curframe.f_lineno
        cmd = 'emacsclient --no-wait +%s %s' % (lineno, filename)
        os.system(cmd)

    do_o = do_open

def pm():
    """use our custom debugger"""
    dbg = Debugger(sys.last_traceback)
    dbg.start()

def set_trace():
    Debugger().set_trace(sys._getframe().f_back)
