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
"""some various utilities and helper classes, most of them used in the
main pylint class
"""

import sys
from warnings import warn
from os.path import dirname, basename, splitext, exists, isdir, join, normpath

from logilab.common.modutils import modpath_from_file, get_module_files, \
                                    file_from_modpath
from logilab.common.textutils import normalize_text
from logilab.common.configuration import rest_format_section
from logilab.common.ureports import Section

from logilab.astng import nodes, Module

from pylint.checkers import EmptyReport


class UnknownMessage(Exception):
    """raised when a unregistered message id is encountered"""


MSG_TYPES = {
    'I' : 'info',
    'C' : 'convention',
    'R' : 'refactor',
    'W' : 'warning',
    'E' : 'error',
    'F' : 'fatal'
    }
MSG_TYPES_LONG = dict([(v, k) for k, v in MSG_TYPES.iteritems()])

MSG_TYPES_STATUS = {
    'I' : 0,
    'C' : 16,
    'R' : 8,
    'W' : 4,
    'E' : 2,
    'F' : 1
    }

_MSG_ORDER = 'EWRCIF'

def sort_msgs(msgids):
    """sort message identifiers according to their category first"""
    msgs = {}
    for msg in msgids:
        msgs.setdefault(msg[0], []).append(msg)
    result = []
    for m_id in _MSG_ORDER:
        if m_id in msgs:
            result.extend( sorted(msgs[m_id]) )
    return result

def get_module_and_frameid(node):
    """return the module name and the frame id in the module"""
    frame = node.frame()
    module, obj = '', []
    while frame:
        if isinstance(frame, Module):
            module = frame.name
        else:
            obj.append(getattr(frame, 'name', '<lambda>'))
        try:
            frame = frame.parent.frame()
        except AttributeError:
            frame = None
    obj.reverse()
    return module, '.'.join(obj)

def category_id(id):
    id = id.upper()
    if id in MSG_TYPES:
        return id
    return MSG_TYPES_LONG.get(id)


class Message:
    def __init__(self, checker, msgid, msg, descr, symbol):
        assert len(msgid) == 5, 'Invalid message id %s' % msgid
        assert msgid[0] in MSG_TYPES, \
               'Bad message type %s in %r' % (msgid[0], msgid)
        self.msgid = msgid
        self.msg = msg
        self.descr = descr
        self.checker = checker
        self.symbol = symbol

class MessagesHandlerMixIn:
    """a mix-in class containing all the messages related methods for the main
    lint class
    """

    def __init__(self):
        # dictionary of registered messages
        self._messages = {}
        # dictionary from string symbolic id to Message object.
        self._messages_by_symbol = {}
        self._msgs_state = {}
        self._module_msgs_state = {} # None
        self._msgs_by_category = {}
        self.msg_status = 0

    def register_messages(self, checker):
        """register a dictionary of messages

        Keys are message ids, values are a 2-uple with the message type and the
        message itself

        message ids should be a string of len 4, where the two first characters
        are the checker id and the two last the message id in this checker
        """
        msgs_dict = checker.msgs
        chkid = None
        for msgid, msg_tuple in msgs_dict.iteritems():
            if len(msg_tuple) == 3:
                (msg, msgsymbol, msgdescr) = msg_tuple
                assert msgsymbol not in self._messages_by_symbol, \
                    'Message symbol %r is already defined' % msgsymbol
            else:
                # messages should have a symbol, but for backward compatibility
                # they may not.
                (msg, msgdescr) = msg_tuple
                warn("[pylint 0.26] description of message %s doesn't include "
                     "a symbolic name" % msgid, DeprecationWarning)
                msgsymbol = None
            # avoid duplicate / malformed ids
            assert msgid not in self._messages, \
                   'Message id %r is already defined' % msgid
            assert chkid is None or chkid == msgid[1:3], \
                   'Inconsistent checker part in message id %r' % msgid
            chkid = msgid[1:3]
            msg = Message(checker, msgid, msg, msgdescr, msgsymbol)
            self._messages[msgid] = msg
            self._messages_by_symbol[msgsymbol] = msg
            self._msgs_by_category.setdefault(msgid[0], []).append(msgid)

    def get_message_help(self, msgid, checkerref=False):
        """return the help string for the given message id"""
        msg = self.check_message_id(msgid)
        desc = normalize_text(' '.join(msg.descr.split()), indent='  ')
        if checkerref:
            desc += ' This message belongs to the %s checker.' % \
                   msg.checker.name
        title = msg.msg
        if msg.symbol:
            symbol_part = ' (%s)' % msg.symbol
        else:
            symbol_part = ''
        if title != '%s':
            title = title.splitlines()[0]
            return ':%s%s: *%s*\n%s' % (msg.msgid, symbol_part, title, desc)
        return ':%s%s:\n%s' % (msg.msgid, symbol_part, desc)

    def disable(self, msgid, scope='package', line=None):
        """don't output message of the given id"""
        assert scope in ('package', 'module')
        # msgid is a category?
        catid = category_id(msgid)
        if catid is not None:
            for _msgid in self._msgs_by_category.get(catid):
                self.disable(_msgid, scope, line)
            return
        # msgid is a checker name?
        if msgid.lower() in self._checkers:
            for checker in self._checkers[msgid.lower()]:
                for _msgid in checker.msgs:
                    self.disable(_msgid, scope, line)
            return
        # msgid is report id?
        if msgid.lower().startswith('rp'):
            self.disable_report(msgid)
            return
        # msgid is a symbolic or numeric msgid.
        msg = self.check_message_id(msgid)
        if scope == 'module':
            assert line > 0
            try:
                self._module_msgs_state[msg.msgid][line] = False
            except KeyError:
                self._module_msgs_state[msg.msgid] = {line: False}
                if msgid != 'I0011':
                    self.add_message('I0011', line=line, args=msg.msgid)

        else:
            msgs = self._msgs_state
            msgs[msg.msgid] = False
            # sync configuration object
            self.config.disable_msg = [mid for mid, val in msgs.iteritems()
                                       if not val]

    def enable(self, msgid, scope='package', line=None):
        """reenable message of the given id"""
        assert scope in ('package', 'module')
        catid = category_id(msgid)
        # msgid is a category?
        if catid is not None:
            for msgid in self._msgs_by_category.get(catid):
                self.enable(msgid, scope, line)
            return
        # msgid is a checker name?
        if msgid.lower() in self._checkers:
            for checker in self._checkers[msgid.lower()]:
                for msgid in checker.msgs:
                    self.enable(msgid, scope, line)
            return
        # msgid is report id?
        if msgid.lower().startswith('rp'):
            self.enable_report(msgid)
            return
        # msgid is a symbolic or numeric msgid.
        msg = self.check_message_id(msgid)
        if scope == 'module':
            assert line > 0
            try:
                self._module_msgs_state[msg.msgid][line] = True
            except KeyError:
                self._module_msgs_state[msg.msgid] = {line: True}
                self.add_message('I0012', line=line, args=msg.msgid)
        else:
            msgs = self._msgs_state
            msgs[msg.msgid] = True
            # sync configuration object
            self.config.enable = [mid for mid, val in msgs.iteritems() if val]

    def check_message_id(self, msgid):
        """returns the Message object for this message.

        msgid may be either a numeric or symbolic id.

        Raises UnknownMessage if the message id is not defined.
        """
        if msgid in self._messages_by_symbol:
            return self._messages_by_symbol[msgid]
        msgid = msgid.upper()
        try:
            return self._messages[msgid]
        except KeyError:
            raise UnknownMessage('No such message id %s' % msgid)

    def is_message_enabled(self, msgid, line=None):
        """return true if the message associated to the given message id is
        enabled

        msgid may be either a numeric or symbolic message id.
        """
        if msgid in self._messages_by_symbol:
            msgid = self._messages_by_symbol[msgid].msgid
        if line is None:
            return self._msgs_state.get(msgid, True)
        try:
            return self._module_msgs_state[msgid][line]
        except (KeyError, TypeError):
            return self._msgs_state.get(msgid, True)

    def add_message(self, msgid, line=None, node=None, args=None):
        """add the message corresponding to the given id.

        If provided, msg is expanded using args

        astng checkers should provide the node argument, raw checkers should
        provide the line argument.
        """
        if line is None and node is not None:
            line = node.fromlineno
        if hasattr(node, 'col_offset'):
            col_offset = node.col_offset # XXX measured in bytes for utf-8, divide by two for chars?
        else:
            col_offset = None
        # should this message be displayed
        if not self.is_message_enabled(msgid, line):
            return
        # update stats
        msg_cat = MSG_TYPES[msgid[0]]
        self.msg_status |= MSG_TYPES_STATUS[msgid[0]]
        self.stats[msg_cat] += 1
        self.stats['by_module'][self.current_name][msg_cat] += 1
        try:
            self.stats['by_msg'][msgid] += 1
        except KeyError:
            self.stats['by_msg'][msgid] = 1
        msg = self._messages[msgid].msg
        # expand message ?
        if args:
            msg %= args
        # get module and object
        if node is None:
            module, obj = self.current_name, ''
            path = self.current_file
        else:
            module, obj = get_module_and_frameid(node)
            path = node.root().file
        # add the message
        self.reporter.add_message(msgid, (path, module, obj, line or 1, col_offset or 0), msg)

    def help_message(self, msgids):
        """display help messages for the given message identifiers"""
        for msgid in msgids:
            try:
                print self.get_message_help(msgid, True)
                print
            except UnknownMessage, ex:
                print ex
                print
                continue

    def print_full_documentation(self):
        """output a full documentation in ReST format"""
        by_checker = {}
        for checker in self.get_checkers():
            if checker.name == 'master':
                prefix = 'Main '
                print "Options"
                print '-------\n'
                if checker.options:
                    for section, options in checker.options_by_section():
                        if section is None:
                            title = 'General options'
                        else:
                            title = '%s options' % section.capitalize()
                        print title
                        print '~' * len(title)
                        rest_format_section(sys.stdout, None, options)
                        print
            else:
                try:
                    by_checker[checker.name][0] += checker.options_and_values()
                    by_checker[checker.name][1].update(checker.msgs)
                    by_checker[checker.name][2] += checker.reports
                except KeyError:
                    by_checker[checker.name] = [list(checker.options_and_values()),
                                                dict(checker.msgs),
                                                list(checker.reports)]
        for checker, (options, msgs, reports) in by_checker.iteritems():
            prefix = ''
            title = '%s checker' % checker
            print title
            print '-' * len(title)
            print
            if options:
                title = 'Options'
                print title
                print '~' * len(title)
                rest_format_section(sys.stdout, None, options)
                print
            if msgs:
                title = ('%smessages' % prefix).capitalize()
                print title
                print '~' * len(title)
                for msgid in sort_msgs(msgs.iterkeys()):
                    print self.get_message_help(msgid, False)
                print
            if reports:
                title = ('%sreports' % prefix).capitalize()
                print title
                print '~' * len(title)
                for report in reports:
                    print ':%s: %s' % report[:2]
                print
            print

    def list_messages(self):
        """output full messages list documentation in ReST format"""
        msgids = []
        for checker in self.get_checkers():
            for msgid in checker.msgs.iterkeys():
                msgids.append(msgid)
        msgids.sort()
        for msgid in msgids:
            print self.get_message_help(msgid, False)
        print


class ReportsHandlerMixIn:
    """a mix-in class containing all the reports and stats manipulation
    related methods for the main lint class
    """
    def __init__(self):
        self._reports = {}
        self._reports_state = {}

    def register_report(self, reportid, r_title, r_cb, checker):
        """register a report

        reportid is the unique identifier for the report
        r_title the report's title
        r_cb the method to call to make the report
        checker is the checker defining the report
        """
        reportid = reportid.upper()
        self._reports.setdefault(checker, []).append( (reportid, r_title, r_cb) )

    def enable_report(self, reportid):
        """disable the report of the given id"""
        reportid = reportid.upper()
        self._reports_state[reportid] = True

    def disable_report(self, reportid):
        """disable the report of the given id"""
        reportid = reportid.upper()
        self._reports_state[reportid] = False

    def report_is_enabled(self, reportid):
        """return true if the report associated to the given identifier is
        enabled
        """
        return self._reports_state.get(reportid, True)

    def make_reports(self, stats, old_stats):
        """render registered reports"""
        sect = Section('Report',
                       '%s statements analysed.'% (self.stats['statement']))
        for checker in self._reports:
            for reportid, r_title, r_cb in self._reports[checker]:
                if not self.report_is_enabled(reportid):
                    continue
                report_sect = Section(r_title)
                try:
                    r_cb(report_sect, stats, old_stats)
                except EmptyReport:
                    continue
                report_sect.report_id = reportid
                sect.append(report_sect)
        return sect

    def add_stats(self, **kwargs):
        """add some stats entries to the statistic dictionary
        raise an AssertionError if there is a key conflict
        """
        for key, value in kwargs.iteritems():
            if key[-1] == '_':
                key = key[:-1]
            assert key not in self.stats
            self.stats[key] = value
        return self.stats


def expand_modules(files_or_modules, black_list):
    """take a list of files/modules/packages and return the list of tuple
    (file, module name) which have to be actually checked
    """
    result = []
    errors = []
    for something in files_or_modules:
        if exists(something):
            # this is a file or a directory
            try:
                modname = '.'.join(modpath_from_file(something))
            except ImportError:
                modname = splitext(basename(something))[0]
            if isdir(something):
                filepath = join(something, '__init__.py')
            else:
                filepath = something
        else:
            # suppose it's a module or package
            modname = something
            try:
                filepath = file_from_modpath(modname.split('.'))
                if filepath is None:
                    errors.append( {'key' : 'F0003', 'mod': modname} )
                    continue
            except (ImportError, SyntaxError), ex:
                # FIXME p3k : the SyntaxError is a Python bug and should be
                # removed as soon as possible http://bugs.python.org/issue10588
                errors.append( {'key': 'F0001', 'mod': modname, 'ex': ex} )
                continue
        filepath = normpath(filepath)
        result.append( {'path': filepath, 'name': modname,
                        'basepath': filepath, 'basename': modname} )
        if not (modname.endswith('.__init__') or modname == '__init__') \
                and '__init__.py' in filepath:
            for subfilepath in get_module_files(dirname(filepath), black_list):
                if filepath == subfilepath:
                    continue
                submodname = '.'.join(modpath_from_file(subfilepath))
                result.append( {'path': subfilepath, 'name': submodname,
                                'basepath': filepath, 'basename': modname} )
    return result, errors


class PyLintASTWalker(object):

    def __init__(self, linter):
        # callbacks per node types
        self.nbstatements = 1
        self.visit_events = {}
        self.leave_events = {}
        self.linter = linter

    def add_checker(self, checker):
        """walk to the checker's dir and collect visit and leave methods"""
        # XXX : should be possible to merge needed_checkers and add_checker
        vcids = set()
        lcids = set()
        visits = self.visit_events
        leaves = self.leave_events
        msgs = self.linter._msgs_state
        for member in dir(checker):
            cid = member[6:]
            if cid == 'default':
                continue
            if member.startswith('visit_'):
                v_meth = getattr(checker, member)
                # don't use visit_methods with no activated message:
                if hasattr(v_meth, 'checks_msgs'):
                    if not any(msgs.get(m, True) for m in v_meth.checks_msgs):
                        continue
                visits.setdefault(cid, []).append(v_meth)
                vcids.add(cid)
            elif member.startswith('leave_'):
                l_meth = getattr(checker, member)
                # don't use leave_methods with no activated message:
                if hasattr(l_meth, 'checks_msgs'):
                    if not any(msgs.get(m, True) for m in l_meth.checks_msgs):
                        continue
                leaves.setdefault(cid, []).append(l_meth)
                lcids.add(cid)
        visit_default = getattr(checker, 'visit_default', None)
        if visit_default:
            for cls in nodes.ALL_NODE_CLASSES:
                cid = cls.__name__.lower()
                if cid not in vcids:
                    visits.setdefault(cid, []).append(visit_default)
        # for now we have no "leave_default" method in Pylint

    def walk(self, astng):
        """call visit events of astng checkers for the given node, recurse on
        its children, then leave events.
        """
        cid = astng.__class__.__name__.lower()
        if astng.is_statement:
            self.nbstatements += 1
        # generate events for this node on each checker
        for cb in self.visit_events.get(cid, ()):
            cb(astng)
        # recurse on children
        for child in astng.get_children():
            self.walk(child)
        for cb in self.leave_events.get(cid, ()):
            cb(astng)
