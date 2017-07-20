# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
from nupic.encoders.base import Encoder
from nupic.encoders import (DeltaEncoder,
                            AdaptiveScalarEncoder)


class ScalarSpaceEncoder(Encoder):
  """
  An encoder that can be used to permute the encodings through different spaces
  These include absolute value, delta, log space, etc.

  :param space: (string) if "absolute", an :class:`.AdaptiveScalarEncoder` is
                returned. Otherwise, a :class:`.DeltaEncoder` is returned.
  """

  SPACE_ABSOLUTE = "absolute"
  SPACE_DELTA = "delta"


  def __init__(self):
    pass


  def __new__(self, w, minval=None, maxval=None, periodic=False, n=0, radius=0,
              resolution=0, name=None, verbosity=0, clipInput=False,
              space="absolute", forced=False):
    self._encoder = None

    if space == "absolute":
      ret = AdaptiveScalarEncoder(w, minval, maxval, periodic, n, radius,
                                  resolution, name, verbosity, clipInput,
                                  forced=forced)
    else:
      ret = DeltaEncoder(w, minval, maxval, periodic, n, radius, resolution,
                         name, verbosity, clipInput, forced=forced)
    return ret
