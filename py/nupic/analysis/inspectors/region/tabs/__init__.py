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
This file exports all the RegionInspector tabs. It also exports defaultTabs, a
sorted list of all the tab classes. The sorting is based on 'order',
defined here, which specifies the default order for tabs to
appear in an inspector. Tabs that don't appear in the list will still be
used, and they will appear at the front of the tab list.
"""

import os
import glob

# This is a list of names used to sort the tabs.
# It is okay if some of the files are not present in a particular distribution.
# This module will find all the tabs it can (including ones that aren't in this
# list), and then use the list to sort them.
# Tabs that do not appear in this list will be placed at the front.
order = ['ParametersTab',
         'PCATab',
         'InputsTab',
         'OutputsTab',
         #'SpColumnActivityTab',
         #'TpColumnActivityTab',
         'MasterCoincsTab',
         'InputCoverageTab',
         'OutputImagesTab',
         'TimeSeriesTab',
         'LocalTAMTab',
         'HelpTab']

# Import all tabs that are present in this distribution
names = []
import nupic
suffix = '*Tab.py'

tabs = [os.path.splitext(os.path.split(x)[1])[0] for x in
           glob.glob(os.path.join(os.path.split(__file__)[0], suffix))]

from nupic.analysis.inspectors.region.tabs.RegionInspectorTab import *
tabs.remove('RegionInspectorTab')
tabs = [(t, t) for t in tabs]

for t in tabs:
  exec('from nupic.analysis.inspectors.region.tabs.%s import %s' % t)
  names.append(t[1])

# Sort the tabs and set up defaultTabs as list of classes
orderDict = {}
for name in names:
  if name in order:
    orderDict[name] = order.index(name)

#names.sort(key=lambda name: orderDict.get(name, -1))
names = order
defaultTabs = map(eval, names)