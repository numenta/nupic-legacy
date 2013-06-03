# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""logilab.astng packaging information"""

distname = 'logilab-astng'

modname = 'astng'
subpackage_of = 'logilab'

numversion = (0, 24, 1)
version = '.'.join([str(num) for num in numversion])

install_requires = ['logilab-common >= 0.53.0']

license = 'LGPL'

author = 'Logilab'
author_email = 'python-projects@lists.logilab.org'
mailinglist = "mailto://%s" % author_email
web = "http://www.logilab.org/project/%s" % distname
ftp = "ftp://ftp.logilab.org/pub/%s" % modname

description = "rebuild a new abstract syntax tree from Python's ast"

from os.path import join
include_dirs = ['brain',
                join('test', 'regrtest_data'),
                join('test', 'data'), join('test', 'data2')]

classifiers = ["Topic :: Software Development :: Libraries :: Python Modules",
               "Topic :: Software Development :: Quality Assurance",
               "Programming Language :: Python",
               "Programming Language :: Python :: 2",
               "Programming Language :: Python :: 3",
               ]
