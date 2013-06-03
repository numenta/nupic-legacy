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
"""Add an abstraction level to transparently import optik classes from optparse
(python >= 2.3) or the optik package.

It also defines three new types for optik/optparse command line parser :

  * regexp
    argument of this type will be converted using re.compile
  * csv
    argument of this type will be converted using split(',')
  * yn
    argument of this type will be true if 'y' or 'yes', false if 'n' or 'no'
  * named
    argument of this type are in the form <NAME>=<VALUE> or <NAME>:<VALUE>
  * password
    argument of this type wont be converted but this is used by other tools
    such as interactive prompt for configuration to double check value and
    use an invisible field
  * multiple_choice
    same as default "choice" type but multiple choices allowed
  * file
    argument of this type wont be converted but checked that the given file exists
  * color
    argument of this type wont be converted but checked its either a
    named color or a color specified using hexadecimal notation (preceded by a #)
  * time
    argument of this type will be converted to a float value in seconds
    according to time units (ms, s, min, h, d)
  * bytes
    argument of this type will be converted to a float value in bytes
    according to byte units (b, kb, mb, gb, tb)
"""
__docformat__ = "restructuredtext en"

import re
import sys
import time
from copy import copy
from os.path import exists

# python >= 2.3
from optparse import OptionParser as BaseParser, Option as BaseOption, \
     OptionGroup, OptionContainer, OptionValueError, OptionError, \
     Values, HelpFormatter, NO_DEFAULT, SUPPRESS_HELP

try:
    from mx import DateTime
    HAS_MX_DATETIME = True
except ImportError:
    HAS_MX_DATETIME = False


OPTPARSE_FORMAT_DEFAULT = sys.version_info >= (2, 4)

from logilab.common.textutils import splitstrip

def check_regexp(option, opt, value):
    """check a regexp value by trying to compile it
    return the compiled regexp
    """
    if hasattr(value, 'pattern'):
        return value
    try:
        return re.compile(value)
    except ValueError:
        raise OptionValueError(
            "option %s: invalid regexp value: %r" % (opt, value))

def check_csv(option, opt, value):
    """check a csv value by trying to split it
    return the list of separated values
    """
    if isinstance(value, (list, tuple)):
        return value
    try:
        return splitstrip(value)
    except ValueError:
        raise OptionValueError(
            "option %s: invalid csv value: %r" % (opt, value))

def check_yn(option, opt, value):
    """check a yn value
    return true for yes and false for no
    """
    if isinstance(value, int):
        return bool(value)
    if value in ('y', 'yes'):
        return True
    if value in ('n', 'no'):
        return False
    msg = "option %s: invalid yn value %r, should be in (y, yes, n, no)"
    raise OptionValueError(msg % (opt, value))

def check_named(option, opt, value):
    """check a named value
    return a dictionary containing (name, value) associations
    """
    if isinstance(value, dict):
        return value
    values = []
    for value in check_csv(option, opt, value):
        if value.find('=') != -1:
            values.append(value.split('=', 1))
        elif value.find(':') != -1:
            values.append(value.split(':', 1))
    if values:
        return dict(values)
    msg = "option %s: invalid named value %r, should be <NAME>=<VALUE> or \
<NAME>:<VALUE>"
    raise OptionValueError(msg % (opt, value))

def check_password(option, opt, value):
    """check a password value (can't be empty)
    """
    # no actual checking, monkey patch if you want more
    return value

def check_file(option, opt, value):
    """check a file value
    return the filepath
    """
    if exists(value):
        return value
    msg = "option %s: file %r does not exist"
    raise OptionValueError(msg % (opt, value))

# XXX use python datetime
def check_date(option, opt, value):
    """check a file value
    return the filepath
    """
    try:
        return DateTime.strptime(value, "%Y/%m/%d")
    except DateTime.Error :
        raise OptionValueError(
            "expected format of %s is yyyy/mm/dd" % opt)

def check_color(option, opt, value):
    """check a color value and returns it
    /!\ does *not* check color labels (like 'red', 'green'), only
    checks hexadecimal forms
    """
    # Case (1) : color label, we trust the end-user
    if re.match('[a-z0-9 ]+$', value, re.I):
        return value
    # Case (2) : only accepts hexadecimal forms
    if re.match('#[a-f0-9]{6}', value, re.I):
        return value
    # Else : not a color label neither a valid hexadecimal form => error
    msg = "option %s: invalid color : %r, should be either hexadecimal \
    value or predefined color"
    raise OptionValueError(msg % (opt, value))

def check_time(option, opt, value):
    from logilab.common.textutils import TIME_UNITS, apply_units
    if isinstance(value, (int, long, float)):
        return value
    return apply_units(value, TIME_UNITS)

def check_bytes(option, opt, value):
    from logilab.common.textutils import BYTE_UNITS, apply_units
    if hasattr(value, '__int__'):
        return value
    return apply_units(value, BYTE_UNITS)

import types

class Option(BaseOption):
    """override optik.Option to add some new option types
    """
    TYPES = BaseOption.TYPES + ('regexp', 'csv', 'yn', 'named', 'password',
                                'multiple_choice', 'file', 'color',
                                'time', 'bytes')
    ATTRS = BaseOption.ATTRS + ['hide', 'level']
    TYPE_CHECKER = copy(BaseOption.TYPE_CHECKER)
    TYPE_CHECKER['regexp'] = check_regexp
    TYPE_CHECKER['csv'] = check_csv
    TYPE_CHECKER['yn'] = check_yn
    TYPE_CHECKER['named'] = check_named
    TYPE_CHECKER['multiple_choice'] = check_csv
    TYPE_CHECKER['file'] = check_file
    TYPE_CHECKER['color'] = check_color
    TYPE_CHECKER['password'] = check_password
    TYPE_CHECKER['time'] = check_time
    TYPE_CHECKER['bytes'] = check_bytes
    if HAS_MX_DATETIME:
        TYPES += ('date',)
        TYPE_CHECKER['date'] = check_date

    def __init__(self, *opts, **attrs):
        BaseOption.__init__(self, *opts, **attrs)
        if hasattr(self, "hide") and self.hide:
            self.help = SUPPRESS_HELP

    def _check_choice(self):
        """FIXME: need to override this due to optik misdesign"""
        if self.type in ("choice", "multiple_choice"):
            if self.choices is None:
                raise OptionError(
                    "must supply a list of choices for type 'choice'", self)
            elif type(self.choices) not in (types.TupleType, types.ListType):
                raise OptionError(
                    "choices must be a list of strings ('%s' supplied)"
                    % str(type(self.choices)).split("'")[1], self)
        elif self.choices is not None:
            raise OptionError(
                "must not supply choices for type %r" % self.type, self)
    BaseOption.CHECK_METHODS[2] = _check_choice


    def process(self, opt, value, values, parser):
        # First, convert the value(s) to the right type.  Howl if any
        # value(s) are bogus.
        try:
            value = self.convert_value(opt, value)
        except AttributeError: # py < 2.4
            value = self.check_value(opt, value)
        if self.type == 'named':
            existant = getattr(values, self.dest)
            if existant:
                existant.update(value)
                value = existant
       # And then take whatever action is expected of us.
        # This is a separate method to make life easier for
        # subclasses to add new actions.
        return self.take_action(
            self.action, self.dest, opt, value, values, parser)


class OptionParser(BaseParser):
    """override optik.OptionParser to use our Option class
    """
    def __init__(self, option_class=Option, *args, **kwargs):
        BaseParser.__init__(self, option_class=Option, *args, **kwargs)

    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        outputlevel = getattr(formatter, 'output_level', 0)
        formatter.store_option_strings(self)
        result = []
        result.append(formatter.format_heading("Options"))
        formatter.indent()
        if self.option_list:
            result.append(OptionContainer.format_option_help(self, formatter))
            result.append("\n")
        for group in self.option_groups:
            if group.level <= outputlevel and (
                group.description or level_options(group, outputlevel)):
                result.append(group.format_help(formatter))
                result.append("\n")
        formatter.dedent()
        # Drop the last "\n", or the header if no options or option groups:
        return "".join(result[:-1])


OptionGroup.level = 0

def level_options(group, outputlevel):
    return [option for option in group.option_list
            if (getattr(option, 'level', 0) or 0) <= outputlevel
            and not option.help is SUPPRESS_HELP]

def format_option_help(self, formatter):
    result = []
    outputlevel = getattr(formatter, 'output_level', 0) or 0
    for option in level_options(self, outputlevel):
        result.append(formatter.format_option(option))
    return "".join(result)
OptionContainer.format_option_help = format_option_help


class ManHelpFormatter(HelpFormatter):
    """Format help using man pages ROFF format"""

    def __init__ (self,
                  indent_increment=0,
                  max_help_position=24,
                  width=79,
                  short_first=0):
        HelpFormatter.__init__ (
            self, indent_increment, max_help_position, width, short_first)

    def format_heading(self, heading):
        return '.SH %s\n' % heading.upper()

    def format_description(self, description):
        return description

    def format_option(self, option):
        try:
            optstring = option.option_strings
        except AttributeError:
            optstring = self.format_option_strings(option)
        if option.help:
            help_text = self.expand_default(option)
            help = ' '.join([l.strip() for l in help_text.splitlines()])
        else:
            help = ''
        return '''.IP "%s"
%s
''' % (optstring, help)

    def format_head(self, optparser, pkginfo, section=1):
        long_desc = ""
        try:
            pgm = optparser._get_prog_name()
        except AttributeError:
            # py >= 2.4.X (dunno which X exactly, at least 2)
            pgm = optparser.get_prog_name()
        short_desc = self.format_short_description(pgm, pkginfo.description)
        if hasattr(pkginfo, "long_desc"):
            long_desc = self.format_long_description(pgm, pkginfo.long_desc)
        return '%s\n%s\n%s\n%s' % (self.format_title(pgm, section),
                                   short_desc, self.format_synopsis(pgm),
                                   long_desc)

    def format_title(self, pgm, section):
        date = '-'.join([str(num) for num in time.localtime()[:3]])
        return '.TH %s %s "%s" %s' % (pgm, section, date, pgm)

    def format_short_description(self, pgm, short_desc):
        return '''.SH NAME
.B %s
\- %s
''' % (pgm, short_desc.strip())

    def format_synopsis(self, pgm):
        return '''.SH SYNOPSIS
.B  %s
[
.I OPTIONS
] [
.I <arguments>
]
''' % pgm

    def format_long_description(self, pgm, long_desc):
        long_desc = '\n'.join([line.lstrip()
                               for line in long_desc.splitlines()])
        long_desc = long_desc.replace('\n.\n', '\n\n')
        if long_desc.lower().startswith(pgm):
            long_desc = long_desc[len(pgm):]
        return '''.SH DESCRIPTION
.B %s
%s
''' % (pgm, long_desc.strip())

    def format_tail(self, pkginfo):
        tail = '''.SH SEE ALSO
/usr/share/doc/pythonX.Y-%s/

.SH BUGS
Please report bugs on the project\'s mailing list:
%s

.SH AUTHOR
%s <%s>
''' % (getattr(pkginfo, 'debian_name', pkginfo.modname),
       pkginfo.mailinglist, pkginfo.author, pkginfo.author_email)

        if hasattr(pkginfo, "copyright"):
            tail += '''
.SH COPYRIGHT
%s
''' % pkginfo.copyright

        return tail

def generate_manpage(optparser, pkginfo, section=1, stream=sys.stdout, level=0):
    """generate a man page from an optik parser"""
    formatter = ManHelpFormatter()
    formatter.output_level = level
    formatter.parser = optparser
    print >> stream, formatter.format_head(optparser, pkginfo, section)
    print >> stream, optparser.format_option_help(formatter)
    print >> stream, formatter.format_tail(pkginfo)


__all__ = ('OptionParser', 'Option', 'OptionGroup', 'OptionValueError',
           'Values')
