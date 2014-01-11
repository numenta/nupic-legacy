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
This file defines RotatePictureExplorer, an explorer for
PictureSensor.
"""

from nupic.regions.PictureSensor import PictureSensor

#+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# RotatePictureExplorer

class RotatePictureExplorer(PictureSensor.PictureExplorer):

  @classmethod
  def queryRelevantParams(klass):
    """
    Returns a sequence of parameter names that are relevant to
    the operation of the explorer.

    May be extended or overridden by sub-classes as appropriate.
    """
    return super(RotatePictureExplorer, klass).queryRelevantParams() + \
           ( 'radialLength', 'radialStep' )

  def initSequence(self, state, params):
    self._presentNextRotation(state, params)


  def updateSequence(self, state, params):
    self._presentNextRotation(state, params)


  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # Internal helper method(s)

  def _presentNextRotation(self, state, params):
    """
    We will visit each grid position. For each grid position,
    we rotate the object in 2D
    """

    # Compute iteration indices
    numRotations = 1 + int((params['maxAngularPosn'] - params['minAngularPosn'])
                           / params['minAngularVelocity'])
    edgeLen = 2 * params['radialLength'] + 1
    numItersPerCat = edgeLen * edgeLen * numRotations
    numCats = self._getNumCategories()
    numIters = numItersPerCat * numCats
    catIndex = self._getIterCount() // numItersPerCat
    index = self._getIterCount() % numItersPerCat
    blockIndex = index / numRotations
    rotationIndex = index % numRotations

    # Compute position within onion block
    posnX = ((blockIndex % edgeLen) - params['radialLength']) * params['radialStep']
    posnY = ((blockIndex // edgeLen) - params['radialLength']) * params['radialStep']

    # Compute rotation angle
    angularPosn = params['maxAngularPosn'] - params['minAngularVelocity'] * rotationIndex

    # Update state
    state['posnX'] = posnX
    state['posnY'] = posnY
    state['velocityX'] = 0
    state['velocityY'] = 0
    state['angularVelocity'] = params['minAngularVelocity']
    state['angularPosn'] = angularPosn
    state['catIndex'] = catIndex
