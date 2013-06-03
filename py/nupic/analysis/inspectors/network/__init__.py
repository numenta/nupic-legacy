# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
This file exports all NetworkInspectors.
"""

import os
import glob
import nupic

# Import NetworkInspector and NetworkInspectorHandler
from nupic.analysis.inspectors.network.NetworkInspector import *

# Create networkInspectors as a list of all network inspector subclasses

files = [os.path.splitext(os.path.split(x)[1])[0] for x in
             glob.glob(os.path.join(os.path.split(__file__)[0], '*.py'))]
files.remove('__init__')
files.remove('NetworkInspector')

#files = [(f, f[:-1]) for f in files if f.endswith('2')]
files = [(f, f) for f in files]

for f in files:
  exec('from nupic.analysis.inspectors.network.%s import %s' % (f[0], f[1]))
networkInspectors = map(eval, [f[1] for f in files])