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

from enthought.traits.api import *
from enthought.traits.ui.api import *

from nupic.analysis.inspectors.region.RegionInspector import RegionInspector
from nupic.analysis.inspectors.region.tabs import *
from nupic.ui.enthought import alignCenter


class _DataTab(RegionInspectorTab):

  # Traits
  outputFile = File(label='Output File')
  flushFile = Button(label='Flush File')
  closeFile = Button(label='Close File')

  def __init__(self, region):

    RegionInspectorTab.__init__(self, region)

    self.traits_view = View(
      Group(
        Item('outputFile', style='text'),
        alignCenter(
          Item('flushFile', show_label=False),
          Item('closeFile', show_label=False)
        )
      ),
      title='Data'
    )


class VectorFileEffectorInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = [_DataTab, InputsTab, HelpTab]
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)