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

from nupic.encoders.random_distributed_scalar import RandomDistributedScalarEncoder as RDSE
from nupic.encoders.simple_scalar import SimpleScalarEncoder

############################################################################
class ScalarEncoder(RDSE):
  """
  A scalar encoder encodes a numeric (floating point) value into an array
  of bits.

  This is a META class that defines the default implementation of "scalar encoder". 
  Options:
    RandomDistributedScalarEncoder (default)
    SimpleScalarEncoder

  Other encoders that use scalar encoder (extend/instantiate) will use this implementation.

  WARNING: no logic should be written in this class, it only defines (extends) the chosen implementation!
  """
  
  def __init__(self, resolution, w=21, n=400, name=None, offset = None,
               seed=42, verbosity=0):
    """this is the default constructor from RDSE class"""
    super(ScalarEncoder, self).__init__(resolution,
                                        w=w,
                                        n=n,
                                        name=name,
                                        offset=offset,
                                        seed=seed,
                                        verbosity=verbosity)


  def __init__(self,
               w,
               minval,
               maxval,
               periodic=False,
               n=0,
               radius=0,
               resolution=0,
               name=None,
               verbosity=0,
               clipInput=False,
               forced=False):
    """backwards compatibility constructor - from SimpleScalarEncoder"""
 
    "get resolution by constructing a dummy SimpleScalar encoder and asking its resolution"
    dummySimpleScalar = SimpleScalarEncoder(w, minval, maxval, periodic=periodic,
                                            n=n, radius=radius, resolution=resolution,
                                            name=name, verbosity=verbosity,
                                            clipInput=clipInput, forced=forced)
    res = dummySimpleScalar.resolution
    super(ScalarEncoder, self).__init__(res,
                                   #     w=w, #TODO should we: a) add 'forced' to RDSE and allow given w,n; or
                                              #                b) pass only resolution and not w,n from former SimpleScalar to RDSE ?
                                   #     n=n,
                                        name=name,
                                        verbosity=verbosity)
