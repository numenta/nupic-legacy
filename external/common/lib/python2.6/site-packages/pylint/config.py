# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
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
"""utilities for PyLint configuration :

* pylintrc
* pylint.d (PYLINTHOME)
"""

import pickle
import os
import sys
from os.path import exists, isfile, join, expanduser, abspath, dirname

# pylint home is used to save old runs results ################################

USER_HOME = expanduser('~')
if 'PYLINTHOME' in os.environ:
    PYLINT_HOME = os.environ['PYLINTHOME']
    if USER_HOME == '~':
        USER_HOME = dirname(PYLINT_HOME)
elif USER_HOME == '~':
    PYLINT_HOME = ".pylint.d"
else:
    PYLINT_HOME = join(USER_HOME, '.pylint.d')

if not exists(PYLINT_HOME):
    try:
        os.mkdir(PYLINT_HOME)
    except OSError:
        print >> sys.stderr, 'Unable to create directory %s' % PYLINT_HOME

def get_pdata_path(base_name, recurs):
    """return the path of the file which should contain old search data for the
    given base_name with the given options values
    """
    base_name = base_name.replace(os.sep, '_')
    return join(PYLINT_HOME, "%s%s%s"%(base_name, recurs, '.stats'))

def load_results(base):
    """try to unpickle and return data from file if it exists and is not
    corrupted

    return an empty dictionary if it doesn't exists
    """
    data_file = get_pdata_path(base, 1)
    try:
        return pickle.load(open(data_file))
    except:
        return {}

if sys.version_info < (3, 0):
    _PICK_MOD = 'w'
else:
    _PICK_MOD = 'wb'

def save_results(results, base):
    """pickle results"""
    data_file = get_pdata_path(base, 1)
    try:
        pickle.dump(results, open(data_file, _PICK_MOD))
    except (IOError, OSError), ex:
        print >> sys.stderr, 'Unable to create file %s: %s' % (data_file, ex)

# location of the configuration file ##########################################


def find_pylintrc():
    """search the pylint rc file and return its path if it find it, else None
    """
    # is there a pylint rc file in the current directory ?
    if exists('pylintrc'):
        return abspath('pylintrc')
    if isfile('__init__.py'):
        curdir = abspath(os.getcwd())
        while isfile(join(curdir, '__init__.py')):
            curdir = abspath(join(curdir, '..'))
            if isfile(join(curdir, 'pylintrc')):
                return join(curdir, 'pylintrc')
    if 'PYLINTRC' in os.environ and exists(os.environ['PYLINTRC']):
        pylintrc = os.environ['PYLINTRC']
    else:
        user_home = expanduser('~')
        if user_home == '~' or user_home == '/root':
            pylintrc = ".pylintrc"
        else:
            pylintrc = join(user_home, '.pylintrc')
    if not isfile(pylintrc):
        if isfile('/etc/pylintrc'):
            pylintrc = '/etc/pylintrc'
        else:
            pylintrc = None
    return pylintrc

PYLINTRC = find_pylintrc()

ENV_HELP = '''
The following environment variables are used:                                   
    * PYLINTHOME                                                                
    path to the directory where data of persistent run will be stored. If not 
found, it defaults to ~/.pylint.d/ or .pylint.d (in the current working 
directory).                                                                     
    * PYLINTRC                                                                  
    path to the configuration file. If not found, it will use the first         
existing file among (~/.pylintrc, /etc/pylintrc).
''' % globals()

# evaluation messages #########################################################

def get_note_message(note):
    """return a message according to note
    note is a float < 10  (10 is the highest note)
    """
    assert note <= 10, "Note is %.2f. Either you cheated, or pylint's \
broken!" % note
    if note < 0:
        msg = 'You have to do something quick !'
    elif note < 1:
        msg = 'Hey! This is really dreadful. Or maybe pylint is buggy?'
    elif note < 2:
        msg = "Come on! You can't be proud of this code"
    elif note < 3:
        msg = 'Hum... Needs work.'
    elif note < 4:
        msg = 'Wouldn\'t you be a bit lazy?'
    elif note < 5:
        msg = 'A little more work would make it acceptable.'
    elif note < 6:
        msg = 'Just the bare minimum. Give it a bit more polish. '
    elif note < 7:
        msg = 'This is okay-ish, but I\'m sure you can do better.'
    elif note < 8:
        msg = 'If you commit now, people should not be making nasty \
comments about you on c.l.py'
    elif note < 9:
        msg = 'That\'s pretty good. Good work mate.'
    elif note < 10:
        msg = 'So close to being perfect...'
    else:
        msg = 'Wow ! Now this deserves our uttermost respect.\nPlease send \
your code to python-projects@logilab.org'
    return msg
