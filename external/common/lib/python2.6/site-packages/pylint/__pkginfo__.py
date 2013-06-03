# pylint: disable=W0622,C0103
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
"""pylint packaging information"""

modname = distname = 'pylint'

numversion = (0, 26, 0)
version = '.'.join([str(num) for num in numversion])

install_requires = ['logilab-common >= 0.53.0', 'logilab-astng >= 0.21.1']

license = 'GPL'
copyright = 'Logilab S.A.'
description = "python code static checker"
web = "http://www.logilab.org/project/%s" % distname
ftp = "ftp://ftp.logilab.org/pub/%s" % modname
mailinglist = "mailto://python-projects@lists.logilab.org"
author = 'Logilab'
author_email = 'python-projects@lists.logilab.org'

classifiers =  ['Development Status :: 4 - Beta',
                'Environment :: Console',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 3',
                'Topic :: Software Development :: Debuggers',
                'Topic :: Software Development :: Quality Assurance',
                'Topic :: Software Development :: Testing',
                ]


long_desc = """\
 Pylint is a Python source code analyzer which looks for programming
 errors, helps enforcing a coding standard and sniffs for some code
 smells (as defined in Martin Fowler's Refactoring book)
 .
 Pylint can be seen as another PyChecker since nearly all tests you
 can do with PyChecker can also be done with Pylint. However, Pylint
 offers some more features, like checking length of lines of code,
 checking if variable names are well-formed according to your coding
 standard, or checking if declared interfaces are truly implemented,
 and much more.
 .
 Additionally, it is possible to write plugins to add your own checks.
 .
 Pylint is shipped with "pylint-gui", "pyreverse" (UML diagram generator)
 and "symilar" (an independent similarities checker)."""

from os.path import join
scripts = [join('bin', filename)
           for filename in ('pylint', 'pylint-gui', "symilar", "epylint",
                            "pyreverse")]

