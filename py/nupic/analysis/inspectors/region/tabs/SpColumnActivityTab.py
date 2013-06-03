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

# Python imports...

# Local imports...
from ColumnActivityTab import ColumnActivityTab
from ColumnActivityTab import kShowSpColumns

################################################################################
class SpColumnActivityTab(ColumnActivityTab):
  """ColumnActivityTab subclass showing SP outputs."""

  ####################################################################
  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise.

    @return isRegionSupported  True if this is a supported region.
    """
    return 'CLARegion' in region.type and (not region.getParameter('disableSpatial'))

  ####################################################################
  def __init__(self, region):
    """SpColumnActivityTab constructor.

    @param  region  The RuntimeRegion.
    """
    # Call superclass.  This will init, among other things, self.region...
    super(SpColumnActivityTab, self).__init__(region, kShowSpColumns)