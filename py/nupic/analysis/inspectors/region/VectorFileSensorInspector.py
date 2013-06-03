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
from nupic.ui.enthought import alignCenter, FileOrDirectoryEditor

class _DataTab(ParametersTab):

  # Traits which aren't added by ParametersTab
  loadFile = File
  appendFile = File

  def _createView(self):
    """Set up the view for the traits."""

    self.traits_view = View(
      Group(
        Group(
          alignCenter(
            Item('loadFile', show_label=False,
              editor=FileOrDirectoryEditor(buttonLabel="Load file...")),
            Item('appendFile', show_label=False,
              editor=FileOrDirectoryEditor(buttonLabel="Append file..."))
          ),
          label='Data',
          show_border=True
        ),
        Group(
          Item('position'),
          Item('repeatCount'),
          Item('scalingMode'),
          Item('activeOutputCount', style='readonly'),
          Item('maxOutputVectorCount', style='readonly'),
          Item('vectorCount', style='readonly'),
          Item('recentFile', style='readonly'),
          label='Parameters',
          show_border=True
        )
      ),
      title='Data'
    )

class VectorFileSensorInspector(RegionInspector):
  def __init__(self, parent, region, tabChangeCallback=None):
    tabs = [_DataTab, OutputsTab, HelpTab]
    RegionInspector.__init__(self, parent, region, tabChangeCallback, tabs)