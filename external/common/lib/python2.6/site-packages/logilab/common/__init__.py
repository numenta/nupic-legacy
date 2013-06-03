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
"""Logilab common library (aka Logilab's extension to the standard library).

:type STD_BLACKLIST: tuple
:var STD_BLACKLIST: directories ignored by default by the functions in
  this package which have to recurse into directories

:type IGNORED_EXTENSIONS: tuple
:var IGNORED_EXTENSIONS: file extensions that may usually be ignored
"""
__docformat__ = "restructuredtext en"
from logilab.common.__pkginfo__ import version as __version__

STD_BLACKLIST = ('CVS', '.svn', '.hg', 'debian', 'dist', 'build')

IGNORED_EXTENSIONS = ('.pyc', '.pyo', '.elc', '~', '.swp', '.orig')

# set this to False if you've mx DateTime installed but you don't want your db
# adapter to use it (should be set before you got a connection)
USE_MX_DATETIME = True


class attrdict(dict):
    """A dictionary for which keys are also accessible as attributes."""
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

class dictattr(dict):
    def __init__(self, proxy):
        self.__proxy = proxy

    def __getitem__(self, attr):
        try:
            return getattr(self.__proxy, attr)
        except AttributeError:
            raise KeyError(attr)

class nullobject(object):
    def __repr__(self):
        return '<nullobject>'
    def __nonzero__(self):
        return False

class tempattr(object):
    def __init__(self, obj, attr, value):
        self.obj = obj
        self.attr = attr
        self.value = value

    def __enter__(self):
        self.oldvalue = getattr(self.obj, self.attr)
        setattr(self.obj, self.attr, self.value)
        return self.obj

    def __exit__(self, exctype, value, traceback):
        setattr(self.obj, self.attr, self.oldvalue)



# flatten -----
# XXX move in a specific module and use yield instead
# do not mix flatten and translate
#
# def iterable(obj):
#    try: iter(obj)
#    except: return False
#    return True
#
# def is_string_like(obj):
#    try: obj +''
#    except (TypeError, ValueError): return False
#    return True
#
#def is_scalar(obj):
#    return is_string_like(obj) or not iterable(obj)
#
#def flatten(seq):
#    for item in seq:
#        if is_scalar(item):
#            yield item
#        else:
#            for subitem in flatten(item):
#               yield subitem

def flatten(iterable, tr_func=None, results=None):
    """Flatten a list of list with any level.

    If tr_func is not None, it should be a one argument function that'll be called
    on each final element.

    :rtype: list

    >>> flatten([1, [2, 3]])
    [1, 2, 3]
    """
    if results is None:
        results = []
    for val in iterable:
        if isinstance(val, (list, tuple)):
            flatten(val, tr_func, results)
        elif tr_func is None:
            results.append(val)
        else:
            results.append(tr_func(val))
    return results


# XXX is function below still used ?

def make_domains(lists):
    """
    Given a list of lists, return a list of domain for each list to produce all
    combinations of possibles values.

    :rtype: list

    Example:

    >>> make_domains(['a', 'b'], ['c','d', 'e'])
    [['a', 'b', 'a', 'b', 'a', 'b'], ['c', 'c', 'd', 'd', 'e', 'e']]
    """
    domains = []
    for iterable in lists:
        new_domain = iterable[:]
        for i in range(len(domains)):
            domains[i] = domains[i]*len(iterable)
        if domains:
            missing = (len(domains[0]) - len(iterable)) / len(iterable)
            i = 0
            for j in range(len(iterable)):
                value = iterable[j]
                for dummy in range(missing):
                    new_domain.insert(i, value)
                    i += 1
                i += 1
        domains.append(new_domain)
    return domains


# private stuff ################################################################

def _handle_blacklist(blacklist, dirnames, filenames):
    """remove files/directories in the black list

    dirnames/filenames are usually from os.walk
    """
    for norecurs in blacklist:
        if norecurs in dirnames:
            dirnames.remove(norecurs)
        elif norecurs in filenames:
            filenames.remove(norecurs)

