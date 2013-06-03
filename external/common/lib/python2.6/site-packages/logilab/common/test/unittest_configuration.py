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
import tempfile
import os
from os.path import join, dirname, abspath

from cStringIO import StringIO
from sys import version_info

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.optik_ext import OptionValueError
from logilab.common.configuration import Configuration, \
     OptionsManagerMixIn, OptionsProviderMixIn, Method, read_old_config

DATA = join(dirname(abspath(__file__)), 'data')

options = [('dothis', {'type':'yn', 'action': 'store', 'default': True, 'metavar': '<y or n>'}),
           ('value', {'type': 'string', 'metavar': '<string>', 'short': 'v'}),
           ('multiple', {'type': 'csv', 'default': ('yop', 'yep'),
                         'metavar': '<comma separated values>',
                         'help': 'you can also document the option'}),
           ('number', {'type': 'int', 'default':2, 'metavar':'<int>', 'help': 'boom'}),
           ('choice', {'type': 'choice', 'default':'yo', 'choices': ('yo', 'ye'),
                       'metavar':'<yo|ye>'}),
           ('multiple-choice', {'type': 'multiple_choice', 'default':('yo', 'ye'),
                                'choices': ('yo', 'ye', 'yu', 'yi', 'ya'),
                                'metavar':'<yo|ye>'}),
           ('named', {'type':'named', 'default':Method('get_named'),
                      'metavar': '<key=val>'}),

           ('diffgroup', {'type':'string', 'default':'pouet', 'metavar': '<key=val>',
                          'group': 'agroup'}),

           ]

class MyConfiguration(Configuration):
    """test configuration"""
    def get_named(self):
        return {'key': 'val'}

class ConfigurationTC(TestCase):

    def setUp(self):
        self.cfg = MyConfiguration(name='test', options=options, usage='Just do it ! (tm)')

    def test_default(self):
        cfg = self.cfg
        self.assertEqual(cfg['dothis'], True)
        self.assertEqual(cfg['value'], None)
        self.assertEqual(cfg['multiple'], ('yop', 'yep'))
        self.assertEqual(cfg['number'], 2)
        self.assertEqual(cfg['choice'], 'yo')
        self.assertEqual(cfg['multiple-choice'], ('yo', 'ye'))
        self.assertEqual(cfg['named'], {'key': 'val'})

    def test_base(self):
        cfg = self.cfg
        cfg.set_option('number', '0')
        self.assertEqual(cfg['number'], 0)
        self.assertRaises(OptionValueError, cfg.set_option, 'number', 'youpi')
        self.assertRaises(OptionValueError, cfg.set_option, 'choice', 'youpi')
        self.assertRaises(OptionValueError, cfg.set_option, 'multiple-choice', ('yo', 'y', 'ya'))
        cfg.set_option('multiple-choice', 'yo, ya')
        self.assertEqual(cfg['multiple-choice'], ['yo', 'ya'])
        self.assertEqual(cfg.get('multiple-choice'), ['yo', 'ya'])
        self.assertEqual(cfg.get('whatever'), None)

    def test_load_command_line_configuration(self):
        cfg = self.cfg
        args = cfg.load_command_line_configuration(['--choice', 'ye', '--number', '4',
                                                    '--multiple=1,2,3', '--dothis=n',
                                                    'other', 'arguments'])
        self.assertEqual(args, ['other', 'arguments'])
        self.assertEqual(cfg['dothis'], False)
        self.assertEqual(cfg['multiple'], ['1', '2', '3'])
        self.assertEqual(cfg['number'], 4)
        self.assertEqual(cfg['choice'], 'ye')
        self.assertEqual(cfg['value'], None)
        args = cfg.load_command_line_configuration(['-v', 'duh'])
        self.assertEqual(args, [])
        self.assertEqual(cfg['value'], 'duh')
        self.assertEqual(cfg['dothis'], False)
        self.assertEqual(cfg['multiple'], ['1', '2', '3'])
        self.assertEqual(cfg['number'], 4)
        self.assertEqual(cfg['choice'], 'ye')

    def test_load_configuration(self):
        cfg = self.cfg
        args = cfg.load_configuration(choice='ye', number='4',
                                      multiple='1,2,3', dothis='n',
                                      multiple_choice=('yo', 'ya'))
        self.assertEqual(cfg['dothis'], False)
        self.assertEqual(cfg['multiple'], ['1', '2', '3'])
        self.assertEqual(cfg['number'], 4)
        self.assertEqual(cfg['choice'], 'ye')
        self.assertEqual(cfg['value'], None)
        self.assertEqual(cfg['multiple-choice'], ('yo', 'ya'))

    def test_load_configuration_file_case_insensitive(self):
        file = tempfile.mktemp()
        stream = open(file, 'w')
        try:
            stream.write("""[Test]

dothis=no

#value=

# you can also document the option
multiple=yop,yepii

# boom
number=3

choice=yo

multiple-choice=yo,ye

named=key:val


[agroup]

diffgroup=zou
""")
            stream.close()
            self.cfg.load_file_configuration(file)
            self.assertEqual(self.cfg['dothis'], False)
            self.assertEqual(self.cfg['value'], None)
            self.assertEqual(self.cfg['multiple'], ['yop', 'yepii'])
            self.assertEqual(self.cfg['diffgroup'], 'zou')
        finally:
            os.remove(file)

    def test_generate_config(self):
        stream = StringIO()
        self.cfg.generate_config(stream)
        self.assertMultiLineEqual(stream.getvalue().strip(), """[TEST]

dothis=yes

#value=

# you can also document the option
multiple=yop,yep

# boom
number=2

choice=yo

multiple-choice=yo,ye

named=key:val


[AGROUP]

diffgroup=pouet""")

    def test_generate_config_with_space_string(self):
        self.cfg['value'] = '    '
        stream = StringIO()
        self.cfg.generate_config(stream)
        self.assertMultiLineEqual(stream.getvalue().strip(), """[TEST]

dothis=yes

value='    '

# you can also document the option
multiple=yop,yep

# boom
number=2

choice=yo

multiple-choice=yo,ye

named=key:val


[AGROUP]

diffgroup=pouet""")


    def test_loopback(self):
        cfg = self.cfg
        f = tempfile.mktemp()
        stream = open(f, 'w')
        try:
            cfg.generate_config(stream)
            stream.close()
            new_cfg = MyConfiguration(name='testloop', options=options)
            new_cfg.load_file_configuration(f)
            self.assertEqual(cfg['dothis'], new_cfg['dothis'])
            self.assertEqual(cfg['multiple'], new_cfg['multiple'])
            self.assertEqual(cfg['number'], new_cfg['number'])
            self.assertEqual(cfg['choice'], new_cfg['choice'])
            self.assertEqual(cfg['value'], new_cfg['value'])
            self.assertEqual(cfg['multiple-choice'], new_cfg['multiple-choice'])
        finally:
            os.remove(f)

    def test_setitem(self):
        self.assertRaises(OptionValueError,
                          self.cfg.__setitem__, 'multiple-choice', ('a', 'b'))
        self.cfg['multiple-choice'] = ('yi', 'ya')
        self.assertEqual(self.cfg['multiple-choice'], ('yi', 'ya'))

    def test_help(self):
        self.cfg.add_help_section('bonus', 'a nice additional help')
        help = self.cfg.help().strip()
        # at least in python 2.4.2 the output is:
        # '  -v <string>, --value=<string>'
        # it is not unlikely some optik/optparse versions do print -v<string>
        # so accept both
        help = help.replace(' -v <string>, ', ' -v<string>, ')
        USAGE = """Usage: Just do it ! (tm)

Options:
  -h, --help            show this help message and exit
  --dothis=<y or n>     
  -v<string>, --value=<string>
  --multiple=<comma separated values>
                        you can also document the option [current: yop,yep]
  --number=<int>        boom [current: 2]
  --choice=<yo|ye>      
  --multiple-choice=<yo|ye>
  --named=<key=val>     

  Agroup:
    --diffgroup=<key=val>

  Bonus:
    a nice additional help"""
        if version_info < (2, 5):
            # 'usage' header is not capitalized in this version
            USAGE = USAGE.replace('Usage: ', 'usage: ')
        elif version_info < (2, 4):
            USAGE = """usage: Just do it ! (tm)

options:
  -h, --help            show this help message and exit
  --dothis=<y or n>
  -v<string>, --value=<string>
  --multiple=<comma separated values>
                        you can also document the option
  --number=<int>
  --choice=<yo|ye>
  --multiple-choice=<yo|ye>
  --named=<key=val>

  Bonus:
    a nice additional help
"""
        self.assertMultiLineEqual(help, USAGE)


    def test_manpage(self):
        from logilab.common import __pkginfo__
        self.cfg.generate_manpage(__pkginfo__, stream=StringIO())

    def test_rewrite_config(self):
        changes = [('renamed', 'renamed', 'choice'),
                   ('moved', 'named', 'old', 'test'),
                   ]
        read_old_config(self.cfg, changes, join(DATA, 'test.ini'))
        stream = StringIO()
        self.cfg.generate_config(stream)
        self.assertMultiLineEqual(stream.getvalue().strip(), """[TEST]

dothis=yes

value='    '

# you can also document the option
multiple=yop

# boom
number=2

choice=yo

multiple-choice=yo,ye

named=key:val


[AGROUP]

diffgroup=pouet""")

class Linter(OptionsManagerMixIn, OptionsProviderMixIn):
    options = (
        ('profile', {'type' : 'yn', 'metavar' : '<y_or_n>',
                     'default': False,
                     'help' : 'Profiled execution.'}),
        )
    def __init__(self):
        OptionsManagerMixIn.__init__(self, usage="")
        OptionsProviderMixIn.__init__(self)
        self.register_options_provider(self)
        self.load_provider_defaults()

class RegrTC(TestCase):

    def setUp(self):
        self.linter = Linter()

    def test_load_defaults(self):
        self.linter.load_command_line_configuration([])
        self.assertEqual(self.linter.config.profile, False)


if __name__ == '__main__':
    unittest_main()
