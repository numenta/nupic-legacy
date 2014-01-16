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
This file defines InwardPictureExplorer, an explorer for
PictureSensor.
"""

from nupic.regions.PictureSensor import PictureSensor
from nupic.math.cross import cross

#+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# InwardPictureExplorer

class InwardPictureExplorer(PictureSensor.PictureExplorer):
  """
  A PictureSensor explorer that deterministically generates
  inward sweeps starting at each point along a square perimeter
  of side length 1+2*radialLength, with each such sweep
  taking the most expeditious route to the center position.
  """

  # Pre-computed table
  _inwardNeighbors = tuple([delta for delta in cross([-1,0,1],[-1,0,1])])

  @classmethod
  def queryRelevantParams(klass):
    """
    Returns a sequence of parameter names that are relevant to
    the operation of the explorer.

    May be extended or overridden by sub-classes as appropriate.
    """
    return ( 'radialLength',)

  def initSequence(self, state, params):
    """
    Initiate the next sequence at the appropriate point
    along the block perimeter.
    """

    radialLength = params['radialLength']

    # Take into account repetitions
    iterCount = self._getIterCount() // self._getNumRepetitions()

    # numRadials are all the positions on the boundary
    # Calculation 1) (2*radialLength+1)**2 - (2*radialLength-1)**2
    # Calculation 2) (2*randialLength+1)*4 - 4
    # numRadials, both ways is 8*radialLength
    # And each radial is radialLength + 1 iterations
    numRadialsPerCat = 8 * radialLength
    numItersPerCat = numRadialsPerCat * (radialLength + 1)
    numCats = self._getNumCategories()
    catIndex = iterCount // numItersPerCat
    catIterCount = iterCount % numItersPerCat
    radialIndex = catIterCount // (radialLength + 1)
    # Determine quadrants: 0 (top), 1 (right), 2 (bottom), 3 (left)
    quadrantIndex = radialIndex // (2 * radialLength)
    radialPosn = catIterCount % (radialLength + 1)
    quadrantPosn = radialIndex % (2 * radialLength)

    # Determine start position of this radial
    posnX, posnY = {
        0: (quadrantPosn - radialLength, -radialLength),
        1: (radialLength, quadrantPosn - radialLength),
        2: (radialLength - quadrantPosn, radialLength),
        3: (-radialLength, radialLength - quadrantPosn),
        }[quadrantIndex]

    # Override default state
    state['posnX'] = posnX
    state['posnY'] = posnY
    state['velocityX'] = 0
    state['velocityY'] = 0
    state['angularPosn'] = 0
    state['angularVelocity'] = 0
    state['catIndex'] = catIndex


  def updateSequence(self, state, params):
    """
    Move to the neighbor position closest to the center
    """
    posnX = state['posnX']
    posnY = state['posnY']
    # Compute neighbor with minimal euclidean distance to center
    neighbors = [(posnX + dx, posnY + dy) for dx, dy in self._inwardNeighbors]
    state['posnX'], state['posnY'] = min(neighbors, key=lambda a: a[0]**2+a[1]**2)
