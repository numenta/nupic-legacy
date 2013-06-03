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
"""logilab.common packaging information"""
__docformat__ = "restructuredtext en"
import sys
import os

distname = 'logilab-common'
modname = 'common'
subpackage_of = 'logilab'
subpackage_master = True

numversion = (0, 59, 0)
version = '.'.join([str(num) for num in numversion])

license = 'LGPL' # 2.1 or later
description = "collection of low-level Python packages and modules used by Logilab projects"
web = "http://www.logilab.org/project/%s" % distname
mailinglist = "mailto://python-projects@lists.logilab.org"
author = "Logilab"
author_email = "contact@logilab.fr"


from os.path import join
scripts = [join('bin', 'pytest')]
include_dirs = [join('test', 'data')]

install_requires = []
if sys.version_info < (2, 7):
    install_requires.append('unittest2 >= 0.5.1')
if os.name == 'nt':
    install_requires.append('colorama')

classifiers = ["Topic :: Utilities",
               "Programming Language :: Python",
               "Programming Language :: Python :: 2",
               "Programming Language :: Python :: 3",
               ]
