# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
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
