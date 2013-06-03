# Copyright (c) 2003-2010 Sylvain Thenault (thenault@gmail.com).
# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
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
""" %prog [options] module_or_package

  Check that a module satisfy a coding standard (and more !).

    %prog --help

  Display this help message and exit.

    %prog --help-msg <msg-id>[,<msg-id>]

  Display help messages about given message identifiers and exit.
"""

# import this first to avoid builtin namespace pollution
from pylint.checkers import utils

import sys
import os
import re
import tokenize
from warnings import warn

from logilab.common.configuration import UnsupportedAction, OptionsManagerMixIn
from logilab.common.optik_ext import check_csv
from logilab.common.modutils import load_module_from_name, get_module_part
from logilab.common.interface import implements
from logilab.common.textutils import splitstrip
from logilab.common.ureports import Table, Text, Section
from logilab.common.__pkginfo__ import version as common_version

from logilab.astng import MANAGER, nodes, ASTNGBuildingException
from logilab.astng.__pkginfo__ import version as astng_version

from pylint.utils import (PyLintASTWalker, UnknownMessage, MessagesHandlerMixIn,
                          ReportsHandlerMixIn, MSG_TYPES, expand_modules)
from pylint.interfaces import ILinter, IRawChecker, IASTNGChecker
from pylint.checkers import (BaseRawChecker, EmptyReport,
                             table_lines_from_stats)
from pylint.reporters.text import (TextReporter, ParseableTextReporter,
                                   VSTextReporter, ColorizedTextReporter)
from pylint.reporters.html import HTMLReporter
from pylint import config

from pylint.__pkginfo__ import version


OPTION_RGX = re.compile(r'\s*#*\s*pylint:(.*)')
REPORTER_OPT_MAP = {'text': TextReporter,
                    'parseable': ParseableTextReporter,
                    'msvs': VSTextReporter,
                    'colorized': ColorizedTextReporter,
                    'html': HTMLReporter,}


def _get_python_path(filepath):
    dirname = os.path.dirname(os.path.realpath(
            os.path.expanduser(filepath)))
    while True:
        if not os.path.exists(os.path.join(dirname, "__init__.py")):
            return dirname
        old_dirname = dirname
        dirname = os.path.dirname(dirname)
        if old_dirname == dirname:
            return os.getcwd()


# Python Linter class #########################################################

MSGS = {
    'F0001': ('%s',
              'fatal',
              'Used when an error occurred preventing the analysis of a \
              module (unable to find it for instance).'),
    'F0002': ('%s: %s',
              'astng-error',
              'Used when an unexpected error occurred while building the ASTNG \
              representation. This is usually accompanied by a traceback. \
              Please report such errors !'),
    'F0003': ('ignored builtin module %s',
              'ignored-builtin-module',
              'Used to indicate that the user asked to analyze a builtin module\
              which has been skipped.'),
    'F0004': ('unexpected inferred value %s',
              'unexpected-inferred-value',
              'Used to indicate that some value of an unexpected type has been \
              inferred.'),
    'F0010': ('error while code parsing: %s',
              'parse-error',
              'Used when an exception occured while building the ASTNG \
               representation which could be handled by astng.'),

    'I0001': ('Unable to run raw checkers on built-in module %s',
              'raw-checker-failed',
              'Used to inform that a built-in module has not been checked \
              using the raw checkers.'),

    'I0010': ('Unable to consider inline option %r',
              'bad-inline-option',
              'Used when an inline option is either badly formatted or can\'t \
              be used inside modules.'),

    'I0011': ('Locally disabling %s',
              'locally-disabled',
              'Used when an inline option disables a message or a messages \
              category.'),
    'I0012': ('Locally enabling %s',
              'locally-enabled',
              'Used when an inline option enables a message or a messages \
              category.'),
    'I0013': ('Ignoring entire file',
              'file-ignored',
              'Used to inform that the file will not be checked'),


    'E0001': ('%s',
              'syntax-error',
              'Used when a syntax error is raised for a module.'),

    'E0011': ('Unrecognized file option %r',
              'unrecognized-inline-option',
              'Used when an unknown inline option is encountered.'),
    'E0012': ('Bad option value %r',
              'bad-option-value',
              'Used when a bad value for an inline option is encountered.'),
    }


class PyLinter(OptionsManagerMixIn, MessagesHandlerMixIn, ReportsHandlerMixIn,
               BaseRawChecker):
    """lint Python modules using external checkers.

    This is the main checker controlling the other ones and the reports
    generation. It is itself both a raw checker and an astng checker in order
    to:
    * handle message activation / deactivation at the module level
    * handle some basic but necessary stats'data (number of classes, methods...)

    IDE plugins developpers: you may have to call
    `logilab.astng.builder.MANAGER.astng_cache.clear()` accross run if you want
    to ensure the latest code version is actually checked.
    """

    __implements__ = (ILinter, IRawChecker)

    name = 'master'
    priority = 0
    level = 0
    msgs = MSGS
    may_be_disabled = False

    @staticmethod
    def make_options():
        return (('ignore',
                 {'type' : 'csv', 'metavar' : '<file>[,<file>...]',
                  'dest' : 'black_list', 'default' : ('CVS',),
                  'help' : 'Add files or directories to the blacklist. \
They should be base names, not paths.'}),
                ('persistent',
                 {'default': True, 'type' : 'yn', 'metavar' : '<y_or_n>',
                  'level': 1,
                  'help' : 'Pickle collected data for later comparisons.'}),

                ('load-plugins',
                 {'type' : 'csv', 'metavar' : '<modules>', 'default' : (),
                  'level': 1,
                  'help' : 'List of plugins (as comma separated values of \
python modules names) to load, usually to register additional checkers.'}),

                ('output-format',
                 {'default': 'text', 'type': 'string', 'metavar' : '<format>',
                  'short': 'f',
                  'group': 'Reports',
                  'help' : 'Set the output format. Available formats are text,'
                  ' parseable, colorized, msvs (visual studio) and html. You '
                  'can also give a reporter class, eg mypackage.mymodule.'
                  'MyReporterClass.'}),

                ('include-ids',
                 {'type' : 'yn', 'metavar' : '<y_or_n>', 'default' : 0,
                  'short': 'i',
                  'group': 'Reports',
                  'help' : 'Include message\'s id in output'}),

                ('symbols',
                 {'type' : 'yn', 'metavar' : '<y_or_n>', 'default' : 0,
                  'short': 's',
                  'group': 'Reports',
                  'help' : 'Include symbolic ids of messages in output'}),

                ('files-output',
                 {'default': 0, 'type' : 'yn', 'metavar' : '<y_or_n>',
                  'group': 'Reports', 'level': 1,
                  'help' : 'Put messages in a separate file for each module / \
package specified on the command line instead of printing them on stdout. \
Reports (if any) will be written in a file name "pylint_global.[txt|html]".'}),

                ('reports',
                 {'default': 1, 'type' : 'yn', 'metavar' : '<y_or_n>',
                  'short': 'r',
                  'group': 'Reports',
                  'help' : 'Tells whether to display a full report or only the\
 messages'}),

                ('evaluation',
                 {'type' : 'string', 'metavar' : '<python_expression>',
                  'group': 'Reports', 'level': 1,
                  'default': '10.0 - ((float(5 * error + warning + refactor + \
convention) / statement) * 10)',
                  'help' : 'Python expression which should return a note less \
than 10 (10 is the highest note). You have access to the variables errors \
warning, statement which respectively contain the number of errors / warnings\
 messages and the total number of statements analyzed. This is used by the \
 global evaluation report (RP0004).'}),

                ('comment',
                 {'default': 0, 'type' : 'yn', 'metavar' : '<y_or_n>',
                  'group': 'Reports', 'level': 1,
                  'help' : 'Add a comment according to your evaluation note. \
This is used by the global evaluation report (RP0004).'}),

                ('enable',
                 {'type' : 'csv', 'metavar': '<msg ids>',
                  'short': 'e',
                  'group': 'Messages control',
                  'help' : 'Enable the message, report, category or checker with the '
                  'given id(s). You can either give multiple identifier '
                  'separated by comma (,) or put this option multiple time.'}),

                ('disable',
                 {'type' : 'csv', 'metavar': '<msg ids>',
                  'short': 'd',
                  'group': 'Messages control',
                  'help' : 'Disable the message, report, category or checker '
                  'with the given id(s). You can either give multiple identifier'
                  ' separated by comma (,) or put this option multiple time '
                  '(only on the command line, not in the configuration file '
                  'where it should appear only once).'}),
               )

    option_groups = (
        ('Messages control', 'Options controling analysis messages'),
        ('Reports', 'Options related to output formating and reporting'),
        )

    def __init__(self, options=(), reporter=None, option_groups=(),
                 pylintrc=None):
        # some stuff has to be done before ancestors initialization...
        #
        # checkers / reporter / astng manager
        self.reporter = None
        self._checkers = {}
        self._ignore_file = False
        # visit variables
        self.base_name = None
        self.base_file = None
        self.current_name = None
        self.current_file = None
        self.stats = None
        # init options
        self.options = options + PyLinter.make_options()
        self.option_groups = option_groups + PyLinter.option_groups
        self._options_methods = {
            'enable': self.enable,
            'disable': self.disable}
        self._bw_options_methods = {'disable-msg': self.disable,
                                    'enable-msg': self.enable}
        full_version = '%%prog %s, \nastng %s, common %s\nPython %s' % (
            version, astng_version, common_version, sys.version)
        OptionsManagerMixIn.__init__(self, usage=__doc__,
                                     version=full_version,
                                     config_file=pylintrc or config.PYLINTRC)
        MessagesHandlerMixIn.__init__(self)
        ReportsHandlerMixIn.__init__(self)
        BaseRawChecker.__init__(self)
        # provided reports
        self.reports = (('RP0001', 'Messages by category',
                         report_total_messages_stats),
                        ('RP0002', '% errors / warnings by module',
                         report_messages_by_module_stats),
                        ('RP0003', 'Messages',
                         report_messages_stats),
                        ('RP0004', 'Global evaluation',
                         self.report_evaluation),
                        )
        self.register_checker(self)
        self._dynamic_plugins = []
        self.load_provider_defaults()
        self.set_reporter(reporter or TextReporter(sys.stdout))

    def load_default_plugins(self):
        from pylint import checkers
        checkers.initialize(self)

    def load_plugin_modules(self, modnames):
        """take a list of module names which are pylint plugins and load
        and register them
        """
        for modname in modnames:
            if modname in self._dynamic_plugins:
                continue
            self._dynamic_plugins.append(modname)
            module = load_module_from_name(modname)
            module.register(self)

    def set_reporter(self, reporter):
        """set the reporter used to display messages and reports"""
        self.reporter = reporter
        reporter.linter = self

    def set_option(self, optname, value, action=None, optdict=None):
        """overridden from configuration.OptionsProviderMixin to handle some
        special options
        """
        if optname in self._options_methods or optname in self._bw_options_methods:
            if value:
                try:
                    meth = self._options_methods[optname]
                except KeyError:
                    meth = self._bw_options_methods[optname]
                    warn('%s is deprecated, replace it by %s' % (
                        optname, optname.split('-')[0]), DeprecationWarning)
                value = check_csv(None, optname, value)
                if isinstance(value, (list, tuple)):
                    for _id in value :
                        meth(_id)
                else :
                    meth(value)
        elif optname == 'output-format':
            if value.lower() in REPORTER_OPT_MAP:
                self.set_reporter(REPORTER_OPT_MAP[value.lower()]())
            else:
                module = load_module_from_name(get_module_part(value))
                class_name = value.split('.')[-1]
                reporter_class = getattr(module, class_name)
                self.set_reporter(reporter_class())

        try:
            BaseRawChecker.set_option(self, optname, value, action, optdict)
        except UnsupportedAction:
            print >> sys.stderr, 'option %s can\'t be read from config file' % \
                  optname

    # checkers manipulation methods ############################################

    def register_checker(self, checker):
        """register a new checker

        checker is an object implementing IRawChecker or / and IASTNGChecker
        """
        assert checker.priority <= 0, 'checker priority can\'t be >= 0'
        self._checkers.setdefault(checker.name, []).append(checker)
        for r_id, r_title, r_cb in checker.reports:
            self.register_report(r_id, r_title, r_cb, checker)
        self.register_options_provider(checker)
        if hasattr(checker, 'msgs'):
            self.register_messages(checker)
        checker.load_defaults()

    def disable_noerror_messages(self):
        for msgcat, msgids in self._msgs_by_category.iteritems():
            if msgcat == 'E':
                for msgid in msgids:
                    self.enable(msgid)
            else:
                for msgid in msgids:
                    self.disable(msgid)

    def disable_reporters(self):
        """disable all reporters"""
        for reporters in self._reports.itervalues():
            for report_id, _title, _cb in reporters:
                self.disable_report(report_id)

    def error_mode(self):
        """error mode: enable only errors; no reports, no persistent"""
        self.disable_noerror_messages()
        self.disable('miscellaneous')
        self.set_option('reports', False)
        self.set_option('persistent', False)

    # block level option handling #############################################
    #
    # see func_block_disable_msg.py test case for expected behaviour

    def process_tokens(self, tokens):
        """process tokens from the current module to search for module/block
        level options
        """
        comment = tokenize.COMMENT
        newline = tokenize.NEWLINE
        for (tok_type, _, start, _, line) in tokens:
            if tok_type not in (comment, newline):
                continue
            match = OPTION_RGX.search(line)
            if match is None:
                continue
            if match.group(1).strip() == "disable-all":
                self.add_message('I0013', line=start[0])
                self._ignore_file = True
                return
            try:
                opt, value = match.group(1).split('=', 1)
            except ValueError:
                self.add_message('I0010', args=match.group(1).strip(),
                                 line=start[0])
                continue
            opt = opt.strip()
            if opt in self._options_methods or opt in self._bw_options_methods:
                try:
                    meth = self._options_methods[opt]
                except KeyError:
                    meth = self._bw_options_methods[opt]
                    warn('%s is deprecated, replace it by %s (%s, line %s)' % (
                        opt, opt.split('-')[0], self.current_file, line),
                         DeprecationWarning)
                for msgid in splitstrip(value):
                    try:
                        meth(msgid, 'module', start[0])
                    except UnknownMessage:
                        self.add_message('E0012', args=msgid, line=start[0])
            else:
                self.add_message('E0011', args=opt, line=start[0])

    def collect_block_lines(self, node, msg_state):
        """walk ast to collect block level options line numbers"""
        # recurse on children (depth first)
        for child in node.get_children():
            self.collect_block_lines(child, msg_state)
        first = node.fromlineno
        last = node.tolineno
        # first child line number used to distinguish between disable
        # which are the first child of scoped node with those defined later.
        # For instance in the code below:
        #
        # 1.   def meth8(self):
        # 2.        """test late disabling"""
        # 3.        # pylint: disable=E1102
        # 4.        print self.blip
        # 5.        # pylint: disable=E1101
        # 6.        print self.bla
        #
        # E1102 should be disabled from line 1 to 6 while E1101 from line 5 to 6
        #
        # this is necessary to disable locally messages applying to class /
        # function using their fromlineno
        if isinstance(node, (nodes.Module, nodes.Class, nodes.Function)) and node.body:
            firstchildlineno = node.body[0].fromlineno
        else:
            firstchildlineno = last
        for msgid, lines in msg_state.iteritems():
            for lineno, state in lines.items():
                if first <= lineno <= last:
                    if lineno > firstchildlineno:
                        state = True
                    # set state for all lines for this block
                    first, last = node.block_range(lineno)
                    for line in xrange(first, last+1):
                        # do not override existing entries
                        if not line in self._module_msgs_state.get(msgid, ()):
                            if line in lines: # state change in the same block
                                state = lines[line]
                            try:
                                self._module_msgs_state[msgid][line] = state
                            except KeyError:
                                self._module_msgs_state[msgid] = {line: state}
                    del lines[lineno]


    # code checking methods ###################################################

    def get_checkers(self):
        """return all available checkers as a list"""
        return [self] + [c for checkers in self._checkers.itervalues()
                         for c in checkers if c is not self]

    def prepare_checkers(self):
        """return checkers needed for activated messages and reports"""
        if not self.config.reports:
            self.disable_reporters()
        # get needed checkers
        neededcheckers = [self]
        for checker in self.get_checkers()[1:]:
            # fatal errors should not trigger enable / disabling a checker
            messages = set(msg for msg in checker.msgs
                           if msg[0] != 'F' and self.is_message_enabled(msg))
            if (messages or
                any(self.report_is_enabled(r[0]) for r in checker.reports)):
                neededcheckers.append(checker)
                checker.active_msgs = messages
        return neededcheckers

    def check(self, files_or_modules):
        """main checking entry: check a list of files or modules from their
        name.
        """
        self.reporter.include_ids = self.config.include_ids
        self.reporter.symbols = self.config.symbols
        if not isinstance(files_or_modules, (list, tuple)):
            files_or_modules = (files_or_modules,)
        walker = PyLintASTWalker(self)
        checkers = self.prepare_checkers()
        rawcheckers = [c for c in checkers if implements(c, IRawChecker)
                       and c is not self]
        # notify global begin
        for checker in checkers:
            checker.open()
            if implements(checker, IASTNGChecker):
                walker.add_checker(checker)
        # build ast and check modules or packages
        for descr in self.expand_files(files_or_modules):
            modname, filepath = descr['name'], descr['path']
            if self.config.files_output:
                reportfile = 'pylint_%s.%s' % (modname, self.reporter.extension)
                self.reporter.set_output(open(reportfile, 'w'))
            self.set_current_module(modname, filepath)
            # get the module representation
            astng = self.get_astng(filepath, modname)
            if astng is None:
                continue
            self.base_name = descr['basename']
            self.base_file = descr['basepath']
            self._ignore_file = False
            # fix the current file (if the source file was not available or
            # if it's actually a c extension)
            self.current_file = astng.file
            self.check_astng_module(astng, walker, rawcheckers)
        # notify global end
        self.set_current_module('')
        self.stats['statement'] = walker.nbstatements
        checkers.reverse()
        for checker in checkers:
            checker.close()

    def expand_files(self, modules):
        """get modules and errors from a list of modules and handle errors
        """
        result, errors = expand_modules(modules, self.config.black_list)
        for error in errors:
            message = modname = error["mod"]
            key = error["key"]
            self.set_current_module(modname)
            if key == "F0001":
                message = str(error["ex"]).replace(os.getcwd() + os.sep, '')
            self.add_message(key, args=message)
        return result

    def set_current_module(self, modname, filepath=None):
        """set the name of the currently analyzed module and
        init statistics for it
        """
        if not modname and filepath is None:
            return
        self.reporter.on_set_current_module(modname, filepath)
        self.current_name = modname
        self.current_file = filepath or modname
        self.stats['by_module'][modname] = {}
        self.stats['by_module'][modname]['statement'] = 0
        for msg_cat in MSG_TYPES.itervalues():
            self.stats['by_module'][modname][msg_cat] = 0
        # XXX hack, to be correct we need to keep module_msgs_state
        # for every analyzed module (the problem stands with localized
        # messages which are only detected in the .close step)
        if modname:
            self._module_msgs_state = {}
            self._module_msg_cats_state = {}

    def get_astng(self, filepath, modname):
        """return a astng representation for a module"""
        try:
            return MANAGER.astng_from_file(filepath, modname, source=True)
        except SyntaxError, ex:
            self.add_message('E0001', line=ex.lineno, args=ex.msg)
        except ASTNGBuildingException, ex:
            self.add_message('F0010', args=ex)
        except Exception, ex:
            import traceback
            traceback.print_exc()
            self.add_message('F0002', args=(ex.__class__, ex))

    def check_astng_module(self, astng, walker, rawcheckers):
        """check a module from its astng representation, real work"""
        # call raw checkers if possible
        if not astng.pure_python:
            self.add_message('I0001', args=astng.name)
        else:
            #assert astng.file.endswith('.py')
            # invoke IRawChecker interface on self to fetch module/block
            # level options
            self.process_module(astng)
            if self._ignore_file:
                return False
            # walk ast to collect line numbers
            orig_state = self._module_msgs_state.copy()
            self._module_msgs_state = {}
            self.collect_block_lines(astng, orig_state)
            for checker in rawcheckers:
                checker.process_module(astng)
        # generate events to astng checkers
        walker.walk(astng)
        return True

    # IASTNGChecker interface #################################################

    def open(self):
        """initialize counters"""
        self.stats = { 'by_module' : {},
                       'by_msg' : {},
                       }
        for msg_cat in MSG_TYPES.itervalues():
            self.stats[msg_cat] = 0

    def close(self):
        """close the whole package /module, it's time to make reports !

        if persistent run, pickle results for later comparison
        """
        if self.base_name is not None:
            # load previous results if any
            previous_stats = config.load_results(self.base_name)
            # XXX code below needs refactoring to be more reporter agnostic
            self.reporter.on_close(self.stats, previous_stats)
            if self.config.reports:
                sect = self.make_reports(self.stats, previous_stats)
                if self.config.files_output:
                    filename = 'pylint_global.' + self.reporter.extension
                    self.reporter.set_output(open(filename, 'w'))
            else:
                sect = Section()
            if self.config.reports or self.config.output_format == 'html':
                self.reporter.display_results(sect)
            # save results if persistent run
            if self.config.persistent:
                config.save_results(self.stats, self.base_name)

    # specific reports ########################################################

    def report_evaluation(self, sect, stats, previous_stats):
        """make the global evaluation report"""
        # check with at least check 1 statements (usually 0 when there is a
        # syntax error preventing pylint from further processing)
        if stats['statement'] == 0:
            raise EmptyReport()
        # get a global note for the code
        evaluation = self.config.evaluation
        try:
            note = eval(evaluation, {}, self.stats)
        except Exception, ex:
            msg = 'An exception occurred while rating: %s' % ex
        else:
            stats['global_note'] = note
            msg = 'Your code has been rated at %.2f/10' % note
            if 'global_note' in previous_stats:
                msg += ' (previous run: %.2f/10)' % previous_stats['global_note']
            if self.config.comment:
                msg = '%s\n%s' % (msg, config.get_note_message(note))
        sect.append(Text(msg))

# some reporting functions ####################################################

def report_total_messages_stats(sect, stats, previous_stats):
    """make total errors / warnings report"""
    lines = ['type', 'number', 'previous', 'difference']
    lines += table_lines_from_stats(stats, previous_stats,
                                    ('convention', 'refactor',
                                     'warning', 'error'))
    sect.append(Table(children=lines, cols=4, rheaders=1))

def report_messages_stats(sect, stats, _):
    """make messages type report"""
    if not stats['by_msg']:
        # don't print this report when we didn't detected any errors
        raise EmptyReport()
    in_order = sorted([(value, msg_id)
                       for msg_id, value in stats['by_msg'].iteritems()
                       if not msg_id.startswith('I')])
    in_order.reverse()
    lines = ('message id', 'occurrences')
    for value, msg_id in in_order:
        lines += (msg_id, str(value))
    sect.append(Table(children=lines, cols=2, rheaders=1))

def report_messages_by_module_stats(sect, stats, _):
    """make errors / warnings by modules report"""
    if len(stats['by_module']) == 1:
        # don't print this report when we are analysing a single module
        raise EmptyReport()
    by_mod = {}
    for m_type in ('fatal', 'error', 'warning', 'refactor', 'convention'):
        total = stats[m_type]
        for module in stats['by_module'].iterkeys():
            mod_total = stats['by_module'][module][m_type]
            if total == 0:
                percent = 0
            else:
                percent = float((mod_total)*100) / total
            by_mod.setdefault(module, {})[m_type] = percent
    sorted_result = []
    for module, mod_info in by_mod.iteritems():
        sorted_result.append((mod_info['error'],
                              mod_info['warning'],
                              mod_info['refactor'],
                              mod_info['convention'],
                              module))
    sorted_result.sort()
    sorted_result.reverse()
    lines = ['module', 'error', 'warning', 'refactor', 'convention']
    for line in sorted_result:
        if line[0] == 0 and line[1] == 0:
            break
        lines.append(line[-1])
        for val in line[:-1]:
            lines.append('%.2f' % val)
    if len(lines) == 5:
        raise EmptyReport()
    sect.append(Table(children=lines, cols=5, rheaders=1))


# utilities ###################################################################

# this may help to import modules using gettext
# XXX syt, actually needed since we don't import code?

from logilab.common.compat import builtins
builtins._ = str


class ArgumentPreprocessingError(Exception):
    """Raised if an error occurs during argument preprocessing."""


def preprocess_options(args, search_for):
    """look for some options (keys of <search_for>) which have to be processed
    before others

    values of <search_for> are callback functions to call when the option is
    found
    """
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('--'):
            try:
                option, val = arg[2:].split('=', 1)
            except ValueError:
                option, val = arg[2:], None
            try:
                cb, takearg = search_for[option]
                del args[i]
                if takearg and val is None:
                    if i >= len(args) or args[i].startswith('-'):
                        raise ArgumentPreprocessingError(arg)
                    val = args[i]
                    del args[i]
                cb(option, val)
            except KeyError:
                i += 1
        else:
            i += 1

class Run:
    """helper class to use as main for pylint :

    run(*sys.argv[1:])
    """
    LinterClass = PyLinter
    option_groups = (
        ('Commands', 'Options which are actually commands. Options in this \
group are mutually exclusive.'),
        )

    def __init__(self, args, reporter=None, exit=True):
        self._rcfile = None
        self._plugins = []
        try:
            preprocess_options(args, {
                # option: (callback, takearg)
                'rcfile':       (self.cb_set_rcfile, True),
                'load-plugins': (self.cb_add_plugins, True),
                })
        except ArgumentPreprocessingError, e:
            print >> sys.stderr, 'Argument %s expects a value.' % (e.args[0],)
            sys.exit(32)

        self.linter = linter = self.LinterClass((
            ('rcfile',
             {'action' : 'callback', 'callback' : lambda *args: 1,
              'type': 'string', 'metavar': '<file>',
              'help' : 'Specify a configuration file.'}),

            ('init-hook',
             {'action' : 'callback', 'type' : 'string', 'metavar': '<code>',
              'callback' : cb_init_hook, 'level': 1,
              'help' : 'Python code to execute, usually for sys.path \
manipulation such as pygtk.require().'}),

            ('help-msg',
             {'action' : 'callback', 'type' : 'string', 'metavar': '<msg-id>',
              'callback' : self.cb_help_message,
              'group': 'Commands',
              'help' : '''Display a help message for the given message id and \
exit. The value may be a comma separated list of message ids.'''}),

            ('list-msgs',
             {'action' : 'callback', 'metavar': '<msg-id>',
              'callback' : self.cb_list_messages,
              'group': 'Commands', 'level': 1,
              'help' : "Generate pylint's messages."}),

            ('full-documentation',
             {'action' : 'callback', 'metavar': '<msg-id>',
              'callback' : self.cb_full_documentation,
              'group': 'Commands', 'level': 1,
              'help' : "Generate pylint's full documentation."}),

            ('generate-rcfile',
             {'action' : 'callback', 'callback' : self.cb_generate_config,
              'group': 'Commands',
              'help' : '''Generate a sample configuration file according to \
the current configuration. You can put other options before this one to get \
them in the generated configuration.'''}),

            ('generate-man',
             {'action' : 'callback', 'callback' : self.cb_generate_manpage,
              'group': 'Commands',
              'help' : "Generate pylint's man page.",'hide': True}),

            ('errors-only',
             {'action' : 'callback', 'callback' : self.cb_error_mode,
              'short': 'E',
              'help' : '''In error mode, checkers without error messages are \
disabled and for others, only the ERROR messages are displayed, and no reports \
are done by default'''}),

            ('profile',
             {'type' : 'yn', 'metavar' : '<y_or_n>',
              'default': False, 'hide': True,
              'help' : 'Profiled execution.'}),

            ), option_groups=self.option_groups,
               reporter=reporter, pylintrc=self._rcfile)
        # register standard checkers
        linter.load_default_plugins()
        # load command line plugins
        linter.load_plugin_modules(self._plugins)
        # add some help section
        linter.add_help_section('Environment variables', config.ENV_HELP, level=1)
        linter.add_help_section('Output',
'Using the default text output, the message format is :                          \n'
'                                                                                \n'
'        MESSAGE_TYPE: LINE_NUM:[OBJECT:] MESSAGE                                \n'
'                                                                                \n'
'There are 5 kind of message types :                                             \n'
'    * (C) convention, for programming standard violation                        \n'
'    * (R) refactor, for bad code smell                                          \n'
'    * (W) warning, for python specific problems                                 \n'
'    * (E) error, for probable bugs in the code                                  \n'
'    * (F) fatal, if an error occurred which prevented pylint from doing further\n'
'processing.\n'
        , level=1)
        linter.add_help_section('Output status code',
'Pylint should leave with following status code:                                 \n'
'    * 0 if everything went fine                                                 \n'
'    * 1 if a fatal message was issued                                           \n'
'    * 2 if an error message was issued                                          \n'
'    * 4 if a warning message was issued                                         \n'
'    * 8 if a refactor message was issued                                        \n'
'    * 16 if a convention message was issued                                     \n'
'    * 32 on usage error                                                         \n'
'                                                                                \n'
'status 1 to 16 will be bit-ORed so you can know which different categories has\n'
'been issued by analysing pylint output status code\n',
        level=1)
        # read configuration
        linter.disable('W0704')
        linter.read_config_file()
        # is there some additional plugins in the file configuration, in
        config_parser = linter.cfgfile_parser
        if config_parser.has_option('MASTER', 'load-plugins'):
            plugins = splitstrip(config_parser.get('MASTER', 'load-plugins'))
            linter.load_plugin_modules(plugins)
        # now we can load file config and command line, plugins (which can
        # provide options) have been registered
        linter.load_config_file()
        if reporter:
            # if a custom reporter is provided as argument, it may be overridden
            # by file parameters, so re-set it here, but before command line
            # parsing so it's still overrideable by command line option
            linter.set_reporter(reporter)
        try:
            args = linter.load_command_line_configuration(args)
        except SystemExit, exc:
            if exc.code == 2: # bad options
                exc.code = 32
            raise
        if not args:
            print linter.help()
            sys.exit(32)
        # insert current working directory to the python path to have a correct
        # behaviour
        if len(args) == 1:
            sys.path.insert(0, _get_python_path(args[0]))
        else:
            sys.path.insert(0, os.getcwd())
        if self.linter.config.profile:
            print >> sys.stderr, '** profiled run'
            import cProfile, pstats
            cProfile.runctx('linter.check(%r)' % args, globals(), locals(), 'stones.prof' )
            data = pstats.Stats('stones.prof')
            data.strip_dirs()
            data.sort_stats('time', 'calls')
            data.print_stats(30)
        else:
            linter.check(args)
        sys.path.pop(0)
        if exit:
            sys.exit(self.linter.msg_status)

    def cb_set_rcfile(self, name, value):
        """callback for option preprocessing (i.e. before optik parsing)"""
        self._rcfile = value

    def cb_add_plugins(self, name, value):
        """callback for option preprocessing (i.e. before optik parsing)"""
        self._plugins.extend(splitstrip(value))

    def cb_error_mode(self, *args, **kwargs):
        """error mode:
        * disable all but error messages
        * disable the 'miscellaneous' checker which can be safely deactivated in
          debug
        * disable reports
        * do not save execution information
        """
        self.linter.error_mode()

    def cb_generate_config(self, *args, **kwargs):
        """optik callback for sample config file generation"""
        self.linter.generate_config(skipsections=('COMMANDS',))
        sys.exit(0)

    def cb_generate_manpage(self, *args, **kwargs):
        """optik callback for sample config file generation"""
        from pylint import __pkginfo__
        self.linter.generate_manpage(__pkginfo__)
        sys.exit(0)

    def cb_help_message(self, option, optname, value, parser):
        """optik callback for printing some help about a particular message"""
        self.linter.help_message(splitstrip(value))
        sys.exit(0)

    def cb_full_documentation(self, option, optname, value, parser):
        """optik callback for printing full documentation"""
        self.linter.print_full_documentation()
        sys.exit(0)

    def cb_list_messages(self, option, optname, value, parser): # FIXME
        """optik callback for printing available messages"""
        self.linter.list_messages()
        sys.exit(0)

def cb_init_hook(option, optname, value, parser):
    """exec arbitrary code to set sys.path for instance"""
    exec value


if __name__ == '__main__':
    Run(sys.argv[1:])
