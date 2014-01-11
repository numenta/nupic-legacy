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

"""
This file defines VerticalPictureExplorer, an explorer for
PictureSensor.
"""

# Third-party imports
import numpy

# Local imports
from nupic.regions.PictureSensorExplorers.random import RandomPictureExplorer

#+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# VerticalPictureExplorer

class VerticalPictureExplorer(RandomPictureExplorer):
  """
  Specialization of 'random' explorer that allows vertical
  sweeps only.
  """

  def initSequence(self, state, params):
    # Invoke base class
    super(VerticalPictureExplorer, self).initSequence(state, params)
    # Force horizontal velocity to be zero
    state['velocityX'] = 0
    # Make sure we don't allow stationary (no velocity)
    if state['velocityY'] == 0:
      state['velocityY'] = self._rng.choice(numpy.array([-1, 1], dtype=int) \
                         * max(1, params['minVelocity']))
