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

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab

class HelpTab(RegionInspectorTab):

  """
  Displays the RegionHelp text.
  """

  regionHelp = Str

  def __init__(self, region):

    RegionInspectorTab.__init__(self, region)

    #self.regionHelp = getRegionHelp(region)
    self.regionHelp = str(region.spec)
    self.traits_view = View(
      Item('regionHelp', style='custom', show_label=False),
      title='Help'
    )