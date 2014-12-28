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
  pass
