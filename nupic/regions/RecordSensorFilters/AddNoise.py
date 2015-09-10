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

"""
This file defines the 'starBlock' explorer.

"""

import numpy



class AddNoise:
  """
  This RecordSensor filter adds noise to the input

  """


  def __init__(self, noise=0.0, seed=-1):
    """ Construct the filter

    Parameters:
    -------------------------------------------------
    noise: Amount of noise to add, from 0 to 1.0

    """
    self.noise = noise
    if seed != -1:
      numpy.random.seed(seed)


  def process(self, encoder, data):
    """ Modify the data in place, adding noise
    """

    if self.noise == 0:
      return

    inputSize = data.size
    flipBits = numpy.random.randint(0, inputSize, self.noise*inputSize)
    data[flipBits] = numpy.logical_not(data[flipBits])
