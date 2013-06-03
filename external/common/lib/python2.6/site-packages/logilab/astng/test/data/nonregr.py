# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
# copyright 2003-2010 Sylvain Thenault, all rights reserved.
# contact mailto:thenault@gmail.com
#
# This file is part of logilab-astng.
#
# logilab-astng is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# logilab-astng is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-astng. If not, see <http://www.gnu.org/licenses/>.
from __future__ import generators

try:
    enumerate = enumerate
except NameError:

    def enumerate(iterable):
        """emulates the python2.3 enumerate() function"""
        i = 0
        for val in iterable:
            yield i, val
            i += 1

def toto(value):
    for k, v in value:
        print v.get('yo')


import imp
fp, mpath, desc = imp.find_module('optparse',a)
s_opt = imp.load_module('std_optparse', fp, mpath, desc)

class OptionParser(s_opt.OptionParser):

    def parse_args(self, args=None, values=None, real_optparse=False):
        if real_optparse:
            pass
##          return super(OptionParser, self).parse_args()
        else:
            import optcomp
            optcomp.completion(self)


class Aaa(object):
    """docstring"""
    def __init__(self):
        self.__setattr__('a','b')
        pass

    def one_public(self):
        """docstring"""
        pass

    def another_public(self):
        """docstring"""
        pass

class Ccc(Aaa):
    """docstring"""

    class Ddd(Aaa):
        """docstring"""
        pass

    class Eee(Ddd):
        """docstring"""
        pass
