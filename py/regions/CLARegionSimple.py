# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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


from nupic.regions.CLARegion import CLARegion, _getAdditionalSpecs

gDefaultTemporalImp = 'simple'

class CLARegionSimple(CLARegion):

  """
  Subclass of CLARegion that uses the simple TP
  """

  #############################################################################
  def __init__(self,
                temporalImp='simple',
               **kwargs):

    # Call parent
    CLARegion.__init__(self, temporalImp=temporalImp, **kwargs)


  #############################################################################
  @classmethod
  def getSpec(cls):
    """Return the Spec for CLARegion.

    The parameters collection is constructed based on the parameters specified
    by the variosu components (spatialSpec, temporalSpec and otherSpec)
    """

    spec = cls.getBaseSpec()
    s, t, o = _getAdditionalSpecs(temporalImp=gDefaultTemporalImp)
    spec['parameters'].update(s)
    spec['parameters'].update(t)
    spec['parameters'].update(o)

    #from dbgp.client import brk; brk(port=9011)
    return spec
