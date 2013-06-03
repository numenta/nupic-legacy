# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""Classes to handle advanced configuration in simple to complex applications.

Allows to load the configuration from a file or from command line
options, to generate a sample configuration file or to display
program's usage. Fills the gap between optik/optparse and ConfigParser
by adding data types (which are also available as a standalone optik
extension in the `optik_ext` module).


Quick start: simplest usage
---------------------------

.. python ::

  >>> import sys
  >>> from logilab.common.configuration import Configuration
  >>> options = [('dothis', {'type':'yn', 'default': True, 'metavar': '<y or n>'}),
  ...            ('value', {'type': 'string', 'metavar': '<string>'}),
  ...            ('multiple', {'type': 'csv', 'default': ('yop',),
  ...                          'metavar': '<comma separated values>',
  ...                          'help': 'you can also document the option'}),
  ...            ('number', {'type': 'int', 'default':2, 'metavar':'<int>'}),
  ...           ]
  >>> config = Configuration(options=options, name='My config')
  >>> print config['dothis']
  True
  >>> print config['value']
  None
  >>> print config['multiple']
  ('yop',)
  >>> print config['number']
  2
  >>> print config.help()
  Usage:  [options]

  Options:
    -h, --help            show this help message and exit
    --dothis=<y or n>
    --value=<string>
    --multiple=<comma separated values>
                          you can also document the option [current: none]
    --number=<int>

  >>> f = open('myconfig.ini', 'w')
  >>> f.write('''[MY CONFIG]
  ... number = 3
  ... dothis = no
  ... multiple = 1,2,3
  ... ''')
  >>> f.close()
  >>> config.load_file_configuration('myconfig.ini')
  >>> print config['dothis']
  False
  >>> print config['value']
  None
  >>> print config['multiple']
  ['1', '2', '3']
  >>> print config['number']
  3
  >>> sys.argv = ['mon prog', '--value', 'bacon', '--multiple', '4,5,6',
  ...             'nonoptionargument']
  >>> print config.load_command_line_configuration()
  ['nonoptionargument']
  >>> print config['value']
  bacon
  >>> config.generate_config()
  # class for simple configurations which don't need the
  # manager / providers model and prefer delegation to inheritance
  #
  # configuration values are accessible through a dict like interface
  #
  [MY CONFIG]

  dothis=no

  value=bacon

  # you can also document the option
  multiple=4,5,6

  number=3
  >>>
"""
__docformat__ = "restructuredtext en"

__all__ = ('OptionsManagerMixIn', 'OptionsProviderMixIn',
           'ConfigurationMixIn', 'Configuration',
           'OptionsManager2ConfigurationAdapter')

import os
import sys
import re
from os.path import exists, expanduser
from copy import copy
from ConfigParser import ConfigParser, NoOptionError, NoSectionError, \
     DuplicateSectionError
from warnings import warn

from logilab.common.compat import callable, raw_input, str_encode as _encode

from logilab.common.textutils import normalize_text, unquote
from logilab.common import optik_ext as optparse

OptionError = optparse.OptionError

REQUIRED = []

class UnsupportedAction(Exception):
    """raised by set_option when it doesn't know what to do for an action"""


def _get_encoding(encoding, stream):
    encoding = encoding or getattr(stream, 'encoding', None)
    if not encoding:
        import locale
        encoding = locale.getpreferredencoding()
    return encoding


# validation functions ########################################################

def choice_validator(optdict, name, value):
    """validate and return a converted value for option of type 'choice'
    """
    if not value in optdict['choices']:
        msg = "option %s: invalid value: %r, should be in %s"
        raise optparse.OptionValueError(msg % (name, value, optdict['choices']))
    return value

def multiple_choice_validator(optdict, name, value):
    """validate and return a converted value for option of type 'choice'
    """
    choices = optdict['choices']
    values = optparse.check_csv(None, name, value)
    for value in values:
        if not value in choices:
            msg = "option %s: invalid value: %r, should be in %s"
            raise optparse.OptionValueError(msg % (name, value, choices))
    return values

def csv_validator(optdict, name, value):
    """validate and return a converted value for option of type 'csv'
    """
    return optparse.check_csv(None, name, value)

def yn_validator(optdict, name, value):
    """validate and return a converted value for option of type 'yn'
    """
    return optparse.check_yn(None, name, value)

def named_validator(optdict, name, value):
    """validate and return a converted value for option of type 'named'
    """
    return optparse.check_named(None, name, value)

def file_validator(optdict, name, value):
    """validate and return a filepath for option of type 'file'"""
    return optparse.check_file(None, name, value)

def color_validator(optdict, name, value):
    """validate and return a valid color for option of type 'color'"""
    return optparse.check_color(None, name, value)

def password_validator(optdict, name, value):
    """validate and return a string for option of type 'password'"""
    return optparse.check_password(None, name, value)

def date_validator(optdict, name, value):
    """validate and return a mx DateTime object for option of type 'date'"""
    return optparse.check_date(None, name, value)

def time_validator(optdict, name, value):
    """validate and return a time object for option of type 'time'"""
    return optparse.check_time(None, name, value)

def bytes_validator(optdict, name, value):
    """validate and return an integer for option of type 'bytes'"""
    return optparse.check_bytes(None, name, value)


VALIDATORS = {'string': unquote,
              'int': int,
              'float': float,
              'file': file_validator,
              'font': unquote,
              'color': color_validator,
              'regexp': re.compile,
              'csv': csv_validator,
              'yn': yn_validator,
              'bool': yn_validator,
              'named': named_validator,
              'password': password_validator,
              'date': date_validator,
              'time': time_validator,
              'bytes': bytes_validator,
              'choice': choice_validator,
              'multiple_choice': multiple_choice_validator,
              }

def _call_validator(opttype, optdict, option, value):
    if opttype not in VALIDATORS:
        raise Exception('Unsupported type "%s"' % opttype)
    try:
        return VALIDATORS[opttype](optdict, option, value)
    except TypeError:
        try:
            return VALIDATORS[opttype](value)
        except optparse.OptionValueError:
            raise
        except:
            raise optparse.OptionValueError('%s value (%r) should be of type %s' %
                                   (option, value, opttype))

# user input functions ########################################################

def input_password(optdict, question='password:'):
    from getpass import getpass
    while True:
        value = getpass(question)
        value2 = getpass('confirm: ')
        if value == value2:
            return value
        print 'password mismatch, try again'

def input_string(optdict, question):
    value = raw_input(question).strip()
    return value or None

def _make_input_function(opttype):
    def input_validator(optdict, question):
        while True:
            value = raw_input(question)
            if not value.strip():
                return None
            try:
                return _call_validator(opttype, optdict, None, value)
            except optparse.OptionValueError, ex:
                msg = str(ex).split(':', 1)[-1].strip()
                print 'bad value: %s' % msg
    return input_validator

INPUT_FUNCTIONS = {
    'string': input_string,
    'password': input_password,
    }

for opttype in VALIDATORS.keys():
    INPUT_FUNCTIONS.setdefault(opttype, _make_input_function(opttype))

def expand_default(self, option):
    """monkey patch OptionParser.expand_default since we have a particular
    way to handle defaults to avoid overriding values in the configuration
    file
    """
    if self.parser is None or not self.default_tag:
        return option.help
    optname = option._long_opts[0][2:]
    try:
        provider = self.parser.options_manager._all_options[optname]
    except KeyError:
        value = None
    else:
        optdict = provider.get_option_def(optname)
        optname = provider.option_name(optname, optdict)
        value = getattr(provider.config, optname, optdict)
        value = format_option_value(optdict, value)
    if value is optparse.NO_DEFAULT or not value:
        value = self.NO_DEFAULT_VALUE
    return option.help.replace(self.default_tag, str(value))


def convert(value, optdict, name=''):
    """return a validated value for an option according to its type

    optional argument name is only used for error message formatting
    """
    try:
        _type = optdict['type']
    except KeyError:
        # FIXME
        return value
    return _call_validator(_type, optdict, name, value)

def comment(string):
    """return string as a comment"""
    lines = [line.strip() for line in string.splitlines()]
    return '# ' + ('%s# ' % os.linesep).join(lines)

def format_time(value):
    if not value:
        return '0'
    if value != int(value):
        return '%.2fs' % value
    value = int(value)
    nbmin, nbsec = divmod(value, 60)
    if nbsec:
        return '%ss' % value
    nbhour, nbmin_ = divmod(nbmin, 60)
    if nbmin_:
        return '%smin' % nbmin
    nbday, nbhour_ = divmod(nbhour, 24)
    if nbhour_:
        return '%sh' % nbhour
    return '%sd' % nbday

def format_bytes(value):
    if not value:
        return '0'
    if value != int(value):
        return '%.2fB' % value
    value = int(value)
    prevunit = 'B'
    for unit in ('KB', 'MB', 'GB', 'TB'):
        next, remain = divmod(value, 1024)
        if remain:
            return '%s%s' % (value, prevunit)
        prevunit = unit
        value = next
    return '%s%s' % (value, unit)

def format_option_value(optdict, value):
    """return the user input's value from a 'compiled' value"""
    if isinstance(value, (list, tuple)):
        value = ','.join(value)
    elif isinstance(value, dict):
        value = ','.join(['%s:%s' % (k, v) for k, v in value.items()])
    elif hasattr(value, 'match'): # optdict.get('type') == 'regexp'
        # compiled regexp
        value = value.pattern
    elif optdict.get('type') == 'yn':
        value = value and 'yes' or 'no'
    elif isinstance(value, (str, unicode)) and value.isspace():
        value = "'%s'" % value
    elif optdict.get('type') == 'time' and isinstance(value, (float, int, long)):
        value = format_time(value)
    elif optdict.get('type') == 'bytes' and hasattr(value, '__int__'):
        value = format_bytes(value)
    return value

def ini_format_section(stream, section, options, encoding=None, doc=None):
    """format an options section using the INI format"""
    encoding = _get_encoding(encoding, stream)
    if doc:
        print >> stream, _encode(comment(doc), encoding)
    print >> stream, '[%s]' % section
    ini_format(stream, options, encoding)

def ini_format(stream, options, encoding):
    """format options using the INI format"""
    for optname, optdict, value in options:
        value = format_option_value(optdict, value)
        help = optdict.get('help')
        if help:
            help = normalize_text(help, line_len=79, indent='# ')
            print >> stream
            print >> stream, _encode(help, encoding)
        else:
            print >> stream
        if value is None:
            print >> stream, '#%s=' % optname
        else:
            value = _encode(value, encoding).strip()
            print >> stream, '%s=%s' % (optname, value)

format_section = ini_format_section

def rest_format_section(stream, section, options, encoding=None, doc=None):
    """format an options section using the INI format"""
    encoding = _get_encoding(encoding, stream)
    if section:
        print >> stream, '%s\n%s' % (section, "'"*len(section))
    if doc:
        print >> stream, _encode(normalize_text(doc, line_len=79, indent=''),
                                 encoding)
        print >> stream
    for optname, optdict, value in options:
        help = optdict.get('help')
        print >> stream, ':%s:' % optname
        if help:
            help = normalize_text(help, line_len=79, indent='  ')
            print >> stream, _encode(help, encoding)
        if value:
            value = _encode(format_option_value(optdict, value), encoding)
            print >> stream, ''
            print >> stream, '  Default: ``%s``' % value.replace("`` ", "```` ``")


class OptionsManagerMixIn(object):
    """MixIn to handle a configuration from both a configuration file and
    command line options
    """

    def __init__(self, usage, config_file=None, version=None, quiet=0):
        self.config_file = config_file
        self.reset_parsers(usage, version=version)
        # list of registered options providers
        self.options_providers = []
        # dictionary associating option name to checker
        self._all_options = {}
        self._short_options = {}
        self._nocallback_options = {}
        self._mygroups = dict()
        # verbosity
        self.quiet = quiet
        self._maxlevel = 0

    def reset_parsers(self, usage='', version=None):
        # configuration file parser
        self.cfgfile_parser = ConfigParser()
        # command line parser
        self.cmdline_parser = optparse.OptionParser(usage=usage, version=version)
        self.cmdline_parser.options_manager = self
        self._optik_option_attrs = set(self.cmdline_parser.option_class.ATTRS)

    def register_options_provider(self, provider, own_group=True):
        """register an options provider"""
        assert provider.priority <= 0, "provider's priority can't be >= 0"
        for i in range(len(self.options_providers)):
            if provider.priority > self.options_providers[i].priority:
                self.options_providers.insert(i, provider)
                break
        else:
            self.options_providers.append(provider)
        non_group_spec_options = [option for option in provider.options
                                  if 'group' not in option[1]]
        groups = getattr(provider, 'option_groups', ())
        if own_group and non_group_spec_options:
            self.add_option_group(provider.name.upper(), provider.__doc__,
                                  non_group_spec_options, provider)
        else:
            for opt, optdict in non_group_spec_options:
                self.add_optik_option(provider, self.cmdline_parser, opt, optdict)
        for gname, gdoc in groups:
            gname = gname.upper()
            goptions = [option for option in provider.options
                        if option[1].get('group', '').upper() == gname]
            self.add_option_group(gname, gdoc, goptions, provider)

    def add_option_group(self, group_name, doc, options, provider):
        """add an option group including the listed options
        """
        assert options
        # add option group to the command line parser
        if group_name in self._mygroups:
            group = self._mygroups[group_name]
        else:
            group = optparse.OptionGroup(self.cmdline_parser,
                                         title=group_name.capitalize())
            self.cmdline_parser.add_option_group(group)
            group.level = provider.level
            self._mygroups[group_name] = group
            # add section to the config file
            if group_name != "DEFAULT":
                self.cfgfile_parser.add_section(group_name)
        # add provider's specific options
        for opt, optdict in options:
            self.add_optik_option(provider, group, opt, optdict)

    def add_optik_option(self, provider, optikcontainer, opt, optdict):
        if 'inputlevel' in optdict:
            warn('[0.50] "inputlevel" in option dictionary for %s is deprecated,'
                 ' use "level"' % opt, DeprecationWarning)
            optdict['level'] = optdict.pop('inputlevel')
        args, optdict = self.optik_option(provider, opt, optdict)
        option = optikcontainer.add_option(*args, **optdict)
        self._all_options[opt] = provider
        self._maxlevel = max(self._maxlevel, option.level or 0)

    def optik_option(self, provider, opt, optdict):
        """get our personal option definition and return a suitable form for
        use with optik/optparse
        """
        optdict = copy(optdict)
        others = {}
        if 'action' in optdict:
            self._nocallback_options[provider] = opt
        else:
            optdict['action'] = 'callback'
            optdict['callback'] = self.cb_set_provider_option
        # default is handled here and *must not* be given to optik if you
        # want the whole machinery to work
        if 'default' in optdict:
            if (optparse.OPTPARSE_FORMAT_DEFAULT and 'help' in optdict and
                optdict.get('default') is not None and
                not optdict['action'] in ('store_true', 'store_false')):
                optdict['help'] += ' [current: %default]'
            del optdict['default']
        args = ['--' + str(opt)]
        if 'short' in optdict:
            self._short_options[optdict['short']] = opt
            args.append('-' + optdict['short'])
            del optdict['short']
        # cleanup option definition dict before giving it to optik
        for key in optdict.keys():
            if not key in self._optik_option_attrs:
                optdict.pop(key)
        return args, optdict

    def cb_set_provider_option(self, option, opt, value, parser):
        """optik callback for option setting"""
        if opt.startswith('--'):
            # remove -- on long option
            opt = opt[2:]
        else:
            # short option, get its long equivalent
            opt = self._short_options[opt[1:]]
        # trick since we can't set action='store_true' on options
        if value is None:
            value = 1
        self.global_set_option(opt, value)

    def global_set_option(self, opt, value):
        """set option on the correct option provider"""
        self._all_options[opt].set_option(opt, value)

    def generate_config(self, stream=None, skipsections=(), encoding=None):
        """write a configuration file according to the current configuration
        into the given stream or stdout
        """
        options_by_section = {}
        sections = []
        for provider in self.options_providers:
            for section, options in provider.options_by_section():
                if section is None:
                    section = provider.name
                if section in skipsections:
                    continue
                options = [(n, d, v) for (n, d, v) in options
                           if d.get('type') is not None]
                if not options:
                    continue
                if not section in sections:
                    sections.append(section)
                alloptions = options_by_section.setdefault(section, [])
                alloptions += options
        stream = stream or sys.stdout
        encoding = _get_encoding(encoding, stream)
        printed = False
        for section in sections:
            if printed:
                print >> stream, '\n'
            format_section(stream, section.upper(), options_by_section[section],
                           encoding)
            printed = True

    def generate_manpage(self, pkginfo, section=1, stream=None):
        """write a man page for the current configuration into the given
        stream or stdout
        """
        self._monkeypatch_expand_default()
        try:
            optparse.generate_manpage(self.cmdline_parser, pkginfo,
                                      section, stream=stream or sys.stdout,
                                      level=self._maxlevel)
        finally:
            self._unmonkeypatch_expand_default()

    # initialization methods ##################################################

    def load_provider_defaults(self):
        """initialize configuration using default values"""
        for provider in self.options_providers:
            provider.load_defaults()

    def load_file_configuration(self, config_file=None):
        """load the configuration from file"""
        self.read_config_file(config_file)
        self.load_config_file()

    def read_config_file(self, config_file=None):
        """read the configuration file but do not load it (i.e. dispatching
        values to each options provider)
        """
        helplevel = 1
        while helplevel <= self._maxlevel:
            opt = '-'.join(['long'] * helplevel) + '-help'
            if opt in self._all_options:
                break # already processed
            def helpfunc(option, opt, val, p, level=helplevel):
                print self.help(level)
                sys.exit(0)
            helpmsg = '%s verbose help.' % ' '.join(['more'] * helplevel)
            optdict = {'action' : 'callback', 'callback' : helpfunc,
                       'help' : helpmsg}
            provider = self.options_providers[0]
            self.add_optik_option(provider, self.cmdline_parser, opt, optdict)
            provider.options += ( (opt, optdict), )
            helplevel += 1
        if config_file is None:
            config_file = self.config_file
        if config_file is not None:
            config_file = expanduser(config_file)
        if config_file and exists(config_file):
            parser = self.cfgfile_parser
            parser.read([config_file])
            # normalize sections'title
            for sect, values in parser._sections.items():
                if not sect.isupper() and values:
                    parser._sections[sect.upper()] = values
        elif not self.quiet:
            msg = 'No config file found, using default configuration'
            print >> sys.stderr, msg
            return

    def input_config(self, onlysection=None, inputlevel=0, stream=None):
        """interactively get configuration values by asking to the user and generate
        a configuration file
        """
        if onlysection is not None:
            onlysection = onlysection.upper()
        for provider in self.options_providers:
            for section, option, optdict in provider.all_options():
                if onlysection is not None and section != onlysection:
                    continue
                if not 'type' in optdict:
                    # ignore action without type (callback, store_true...)
                    continue
                provider.input_option(option, optdict, inputlevel)
        # now we can generate the configuration file
        if stream is not None:
            self.generate_config(stream)

    def load_config_file(self):
        """dispatch values previously read from a configuration file to each
        options provider)
        """
        parser = self.cfgfile_parser
        for provider in self.options_providers:
            for section, option, optdict in provider.all_options():
                try:
                    value = parser.get(section, option)
                    provider.set_option(option, value, optdict=optdict)
                except (NoSectionError, NoOptionError), ex:
                    continue

    def load_configuration(self, **kwargs):
        """override configuration according to given parameters
        """
        for opt, opt_value in kwargs.items():
            opt = opt.replace('_', '-')
            provider = self._all_options[opt]
            provider.set_option(opt, opt_value)

    def load_command_line_configuration(self, args=None):
        """override configuration according to command line parameters

        return additional arguments
        """
        self._monkeypatch_expand_default()
        try:
            if args is None:
                args = sys.argv[1:]
            else:
                args = list(args)
            (options, args) = self.cmdline_parser.parse_args(args=args)
            for provider in self._nocallback_options.keys():
                config = provider.config
                for attr in config.__dict__.keys():
                    value = getattr(options, attr, None)
                    if value is None:
                        continue
                    setattr(config, attr, value)
            return args
        finally:
            self._unmonkeypatch_expand_default()


    # help methods ############################################################

    def add_help_section(self, title, description, level=0):
        """add a dummy option section for help purpose """
        group = optparse.OptionGroup(self.cmdline_parser,
                                     title=title.capitalize(),
                                     description=description)
        group.level = level
        self._maxlevel = max(self._maxlevel, level)
        self.cmdline_parser.add_option_group(group)

    def _monkeypatch_expand_default(self):
        # monkey patch optparse to deal with our default values
        try:
            self.__expand_default_backup = optparse.HelpFormatter.expand_default
            optparse.HelpFormatter.expand_default = expand_default
        except AttributeError:
            # python < 2.4: nothing to be done
            pass
    def _unmonkeypatch_expand_default(self):
        # remove monkey patch
        if hasattr(optparse.HelpFormatter, 'expand_default'):
            # unpatch optparse to avoid side effects
            optparse.HelpFormatter.expand_default = self.__expand_default_backup

    def help(self, level=0):
        """return the usage string for available options """
        self.cmdline_parser.formatter.output_level = level
        self._monkeypatch_expand_default()
        try:
            return self.cmdline_parser.format_help()
        finally:
            self._unmonkeypatch_expand_default()


class Method(object):
    """used to ease late binding of default method (so you can define options
    on the class using default methods on the configuration instance)
    """
    def __init__(self, methname):
        self.method = methname
        self._inst = None

    def bind(self, instance):
        """bind the method to its instance"""
        if self._inst is None:
            self._inst = instance

    def __call__(self, *args, **kwargs):
        assert self._inst, 'unbound method'
        return getattr(self._inst, self.method)(*args, **kwargs)


class OptionsProviderMixIn(object):
    """Mixin to provide options to an OptionsManager"""

    # those attributes should be overridden
    priority = -1
    name = 'default'
    options = ()
    level = 0

    def __init__(self):
        self.config = optparse.Values()
        for option in self.options:
            try:
                option, optdict = option
            except ValueError:
                raise Exception('Bad option: %r' % option)
            if isinstance(optdict.get('default'), Method):
                optdict['default'].bind(self)
            elif isinstance(optdict.get('callback'), Method):
                optdict['callback'].bind(self)
        self.load_defaults()

    def load_defaults(self):
        """initialize the provider using default values"""
        for opt, optdict in self.options:
            action = optdict.get('action')
            if action != 'callback':
                # callback action have no default
                default = self.option_default(opt, optdict)
                if default is REQUIRED:
                    continue
                self.set_option(opt, default, action, optdict)

    def option_default(self, opt, optdict=None):
        """return the default value for an option"""
        if optdict is None:
            optdict = self.get_option_def(opt)
        default = optdict.get('default')
        if callable(default):
            default = default()
        return default

    def option_name(self, opt, optdict=None):
        """get the config attribute corresponding to opt
        """
        if optdict is None:
            optdict = self.get_option_def(opt)
        return optdict.get('dest', opt.replace('-', '_'))

    def option_value(self, opt):
        """get the current value for the given option"""
        return getattr(self.config, self.option_name(opt), None)

    def set_option(self, opt, value, action=None, optdict=None):
        """method called to set an option (registered in the options list)
        """
        # print "************ setting option", opt," to value", value
        if optdict is None:
            optdict = self.get_option_def(opt)
        if value is not None:
            value = convert(value, optdict, opt)
        if action is None:
            action = optdict.get('action', 'store')
        if optdict.get('type') == 'named': # XXX need specific handling
            optname = self.option_name(opt, optdict)
            currentvalue = getattr(self.config, optname, None)
            if currentvalue:
                currentvalue.update(value)
                value = currentvalue
        if action == 'store':
            setattr(self.config, self.option_name(opt, optdict), value)
        elif action in ('store_true', 'count'):
            setattr(self.config, self.option_name(opt, optdict), 0)
        elif action == 'store_false':
            setattr(self.config, self.option_name(opt, optdict), 1)
        elif action == 'append':
            opt = self.option_name(opt, optdict)
            _list = getattr(self.config, opt, None)
            if _list is None:
                if isinstance(value, (list, tuple)):
                    _list = value
                elif value is not None:
                    _list = []
                    _list.append(value)
                setattr(self.config, opt, _list)
            elif isinstance(_list, tuple):
                setattr(self.config, opt, _list + (value,))
            else:
                _list.append(value)
        elif action == 'callback':
            optdict['callback'](None, opt, value, None)
        else:
            raise UnsupportedAction(action)

    def input_option(self, option, optdict, inputlevel=99):
        default = self.option_default(option, optdict)
        if default is REQUIRED:
            defaultstr = '(required): '
        elif optdict.get('level', 0) > inputlevel:
            return
        elif optdict['type'] == 'password' or default is None:
            defaultstr = ': '
        else:
            defaultstr = '(default: %s): ' % format_option_value(optdict, default)
        print ':%s:' % option
        print optdict.get('help') or option
        inputfunc = INPUT_FUNCTIONS[optdict['type']]
        value = inputfunc(optdict, defaultstr)
        while default is REQUIRED and not value:
            print 'please specify a value'
            value = inputfunc(optdict, '%s: ' % option)
        if value is None and default is not None:
            value = default
        self.set_option(option, value, optdict=optdict)

    def get_option_def(self, opt):
        """return the dictionary defining an option given it's name"""
        assert self.options
        for option in self.options:
            if option[0] == opt:
                return option[1]
        raise OptionError('no such option %s in section %r'
                          % (opt, self.name), opt)


    def all_options(self):
        """return an iterator on available options for this provider
        option are actually described by a 3-uple:
        (section, option name, option dictionary)
        """
        for section, options in self.options_by_section():
            if section is None:
                if self.name is None:
                    continue
                section = self.name.upper()
            for option, optiondict, value in options:
                yield section, option, optiondict

    def options_by_section(self):
        """return an iterator on options grouped by section

        (section, [list of (optname, optdict, optvalue)])
        """
        sections = {}
        for optname, optdict in self.options:
            sections.setdefault(optdict.get('group'), []).append(
                (optname, optdict, self.option_value(optname)))
        if None in sections:
            yield None, sections.pop(None)
        for section, options in sections.items():
            yield section.upper(), options

    def options_and_values(self, options=None):
        if options is None:
            options = self.options
        for optname, optdict in options:
            yield (optname, optdict, self.option_value(optname))


class ConfigurationMixIn(OptionsManagerMixIn, OptionsProviderMixIn):
    """basic mixin for simple configurations which don't need the
    manager / providers model
    """
    def __init__(self, *args, **kwargs):
        if not args:
            kwargs.setdefault('usage', '')
        kwargs.setdefault('quiet', 1)
        OptionsManagerMixIn.__init__(self, *args, **kwargs)
        OptionsProviderMixIn.__init__(self)
        if not getattr(self, 'option_groups', None):
            self.option_groups = []
            for option, optdict in self.options:
                try:
                    gdef = (optdict['group'].upper(), '')
                except KeyError:
                    continue
                if not gdef in self.option_groups:
                    self.option_groups.append(gdef)
        self.register_options_provider(self, own_group=0)

    def register_options(self, options):
        """add some options to the configuration"""
        options_by_group = {}
        for optname, optdict in options:
            options_by_group.setdefault(optdict.get('group', self.name.upper()), []).append((optname, optdict))
        for group, options in options_by_group.items():
            self.add_option_group(group, None, options, self)
        self.options += tuple(options)

    def load_defaults(self):
        OptionsProviderMixIn.load_defaults(self)

    def __iter__(self):
        return iter(self.config.__dict__.iteritems())

    def __getitem__(self, key):
        try:
            return getattr(self.config, self.option_name(key))
        except (optparse.OptionValueError, AttributeError):
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.set_option(key, value)

    def get(self, key, default=None):
        try:
            return getattr(self.config, self.option_name(key))
        except (OptionError, AttributeError):
            return default


class Configuration(ConfigurationMixIn):
    """class for simple configurations which don't need the
    manager / providers model and prefer delegation to inheritance

    configuration values are accessible through a dict like interface
    """

    def __init__(self, config_file=None, options=None, name=None,
                 usage=None, doc=None, version=None):
        if options is not None:
            self.options = options
        if name is not None:
            self.name = name
        if doc is not None:
            self.__doc__ = doc
        super(Configuration, self).__init__(config_file=config_file, usage=usage, version=version)


class OptionsManager2ConfigurationAdapter(object):
    """Adapt an option manager to behave like a
    `logilab.common.configuration.Configuration` instance
    """
    def __init__(self, provider):
        self.config = provider

    def __getattr__(self, key):
        return getattr(self.config, key)

    def __getitem__(self, key):
        provider = self.config._all_options[key]
        try:
            return getattr(provider.config, provider.option_name(key))
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self.config.global_set_option(self.config.option_name(key), value)

    def get(self, key, default=None):
        provider = self.config._all_options[key]
        try:
            return getattr(provider.config, provider.option_name(key))
        except AttributeError:
            return default


def read_old_config(newconfig, changes, configfile):
    """initialize newconfig from a deprecated configuration file

    possible changes:
    * ('renamed', oldname, newname)
    * ('moved', option, oldgroup, newgroup)
    * ('typechanged', option, oldtype, newvalue)
    """
    # build an index of changes
    changesindex = {}
    for action in changes:
        if action[0] == 'moved':
            option, oldgroup, newgroup = action[1:]
            changesindex.setdefault(option, []).append((action[0], oldgroup, newgroup))
            continue
        if action[0] == 'renamed':
            oldname, newname = action[1:]
            changesindex.setdefault(newname, []).append((action[0], oldname))
            continue
        if action[0] == 'typechanged':
            option, oldtype, newvalue = action[1:]
            changesindex.setdefault(option, []).append((action[0], oldtype, newvalue))
            continue
        if action[1] in ('added', 'removed'):
            continue # nothing to do here
        raise Exception('unknown change %s' % action[0])
    # build a config object able to read the old config
    options = []
    for optname, optdef in newconfig.options:
        for action in changesindex.pop(optname, ()):
            if action[0] == 'moved':
                oldgroup, newgroup = action[1:]
                optdef = optdef.copy()
                optdef['group'] = oldgroup
            elif action[0] == 'renamed':
                optname = action[1]
            elif action[0] == 'typechanged':
                oldtype = action[1]
                optdef = optdef.copy()
                optdef['type'] = oldtype
        options.append((optname, optdef))
    if changesindex:
        raise Exception('unapplied changes: %s' % changesindex)
    oldconfig = Configuration(options=options, name=newconfig.name)
    # read the old config
    oldconfig.load_file_configuration(configfile)
    # apply values reverting changes
    changes.reverse()
    done = set()
    for action in changes:
        if action[0] == 'renamed':
            oldname, newname = action[1:]
            newconfig[newname] = oldconfig[oldname]
            done.add(newname)
        elif action[0] == 'typechanged':
            optname, oldtype, newvalue = action[1:]
            newconfig[optname] = newvalue
            done.add(optname)
    for optname, optdef in newconfig.options:
        if optdef.get('type') and not optname in done:
            newconfig.set_option(optname, oldconfig[optname], optdict=optdef)


def merge_options(options, optgroup=None):
    """preprocess a list of options and remove duplicates, returning a new list
    (tuple actually) of options.

    Options dictionaries are copied to avoid later side-effect. Also, if
    `otpgroup` argument is specified, ensure all options are in the given group.
    """
    alloptions = {}
    options = list(options)
    for i in range(len(options)-1, -1, -1):
        optname, optdict = options[i]
        if optname in alloptions:
            options.pop(i)
            alloptions[optname].update(optdict)
        else:
            optdict = optdict.copy()
            options[i] = (optname, optdict)
            alloptions[optname] = optdict
        if optgroup is not None:
            alloptions[optname]['group'] = optgroup
    return tuple(options)
