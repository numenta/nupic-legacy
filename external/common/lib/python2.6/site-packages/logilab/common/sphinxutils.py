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
"""Sphinx utils

ModuleGenerator: Generate a file that lists all the modules of a list of
packages in order to pull all the docstring.
This should not be used in a makefile to systematically generate sphinx
documentation!

Typical usage:

>>> from logilab.common.sphinxutils import ModuleGenerator
>>> mgen = ModuleGenerator('logilab common', '/home/adim/src/logilab/common')
>>> mgen.generate('api_logilab_common.rst', exclude_dirs=('test',))
"""

import os, sys
import os.path as osp
import inspect

from logilab.common import STD_BLACKLIST
from logilab.common.shellutils import globfind
from logilab.common.modutils import load_module_from_file, modpath_from_file

def module_members(module):
    members = []
    for name, value in inspect.getmembers(module):
        if getattr(value, '__module__', None) == module.__name__:
            members.append( (name, value) )
    return sorted(members)


def class_members(klass):
    return sorted([name for name in vars(klass)
                   if name not in ('__doc__', '__module__',
                                   '__dict__', '__weakref__')])

class ModuleGenerator:
    file_header = """.. -*- coding: utf-8 -*-\n\n%s\n"""
    module_def = """
:mod:`%s`
=======%s

.. automodule:: %s
   :members: %s
"""
    class_def = """

.. autoclass:: %s
   :members: %s

"""

    def __init__(self, project_title, code_dir):
        self.title = project_title
        self.code_dir = osp.abspath(code_dir)

    def generate(self, dest_file, exclude_dirs=STD_BLACKLIST):
        """make the module file"""
        self.fn = open(dest_file, 'w')
        num = len(self.title) + 6
        title = "=" * num + "\n %s API\n" % self.title + "=" * num
        self.fn.write(self.file_header % title)
        self.gen_modules(exclude_dirs=exclude_dirs)
        self.fn.close()

    def gen_modules(self, exclude_dirs):
        """generate all modules"""
        for module in self.find_modules(exclude_dirs):
            modname = module.__name__
            classes = []
            modmembers = []
            for objname, obj in module_members(module):
                if inspect.isclass(obj):
                    classmembers = class_members(obj)
                    classes.append( (objname, classmembers) )
                else:
                    modmembers.append(objname)
            self.fn.write(self.module_def % (modname, '=' * len(modname),
                                             modname,
                                             ', '.join(modmembers)))
            for klass, members in classes:
                self.fn.write(self.class_def % (klass, ', '.join(members)))

    def find_modules(self, exclude_dirs):
        basepath = osp.dirname(self.code_dir)
        basedir = osp.basename(basepath) + osp.sep
        if basedir not in sys.path:
            sys.path.insert(1, basedir)
        for filepath in globfind(self.code_dir, '*.py', exclude_dirs):
            if osp.basename(filepath) in ('setup.py', '__pkginfo__.py'):
                continue
            try:
                module = load_module_from_file(filepath)
            except: # module might be broken or magic
                dotted_path = modpath_from_file(filepath)
                module = type('.'.join(dotted_path), (), {}) # mock it
            yield module


if __name__ == '__main__':
    # example :
    title, code_dir, outfile = sys.argv[1:]
    generator = ModuleGenerator(title, code_dir)
    # XXX modnames = ['logilab']
    generator.generate(outfile, ('test', 'tests', 'examples',
                             'data', 'doc', '.hg', 'migration'))
