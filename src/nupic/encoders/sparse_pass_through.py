# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2017, Numenta, Inc.  Unless you have an agreement
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

import numpy

from nupic.encoders import pass_through



class SparsePassThroughEncoder(pass_through.PassThroughEncoder):
  """
  Convert a bitmap encoded as array indices to an SDR.

  Each encoding is an SDR in which ``w`` out of ``n`` bits are turned on.
  The input should be an array or string of indices to turn on.

  **Note:** the value for ``n`` must equal input length * w, for example:

  .. code-block:: python

     for n=8 w=1 [0,2,5] => 101001000

  or:

  .. code-block:: python

    for n=8 w=1 "0,2,5" => 101001000

  and:

  .. code-block:: python

    for n=24 w=3 [0,2,5] => 111000111000000111000000000

  or:

  .. code-block:: python

    for n=24 w=3 "0,2,5" => 111000111000000111000000000

  """


  def __init__(self, n, w=None, name="sparse_pass_through", forced=False, verbosity=0):
    """
    n is the total bits in input
    w is the number of bits used to encode each input bit
    """
    super(SparsePassThroughEncoder, self).__init__(
        n, w, name, forced, verbosity)


  def encodeIntoArray(self, value, output):
    """ See method description in base.py """
    denseInput = numpy.zeros(output.shape)
    try:
      denseInput[value] = 1
    except IndexError:
      if isinstance(value, numpy.ndarray):
        raise ValueError(
            "Numpy array must have integer dtype but got {}".format(
                value.dtype))
      raise
    super(SparsePassThroughEncoder, self).encodeIntoArray(denseInput, output)
