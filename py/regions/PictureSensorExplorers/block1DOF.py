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
This file defines Block1DOFPictureExplorer, an explorer for
PictureSensor.
"""

from nupic.regions.PictureSensor import PictureSensor

#+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# Block1DOFPictureExplorer

class Block1DOFPictureExplorer(PictureSensor.PictureExplorer):
  """
  Presents each category at an Nx1 "block" of shifted positions
  centered upon the centroid of the canvas, where N is 2R+1
  (where R is the radialLength); each such presentation is
  spaced radialStep pixels apart in both X and Y dimensions.
  """

  @classmethod
  def queryRelevantParams(klass):
    """
    Returns a sequence of parameter names that are relevant to
    the operation of the explorer.

    May be extended or overridden by sub-classes as appropriate.
    """
    return ( 'radialLength', 'radialStep', )

  def initSequence(self, state, params):
    self._presentNextBlockPosn(state, params)

  def updateSequence(self, state, params):
    self._presentNextBlockPosn(state, params)


  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # Internal helper method(s)

  def _presentNextBlockPosn(self, state, params):
    """
    Compute the appropriate category and block position
    deterministically based on the current iteration count.
    """
    # Compute iteration indices
    edgeLen = 2 * params['radialLength'] + 1
    numBlocksPerCat = edgeLen
    numCats = self._getNumCategories()
    numBlocks = numBlocksPerCat * numCats
    blockCounter = self._getIterCount() % numBlocks
    catIndex = blockCounter // numBlocksPerCat
    blockCatIndex = blockCounter % numBlocksPerCat
    # Compute position within onion block
    posnX = ((blockCatIndex % edgeLen) - params['radialLength']) * params['radialStep']

    # Override default state
    state['posnX'] = posnX
    state['posnY'] = 0
    state['velocityX'] = 0
    state['velocityY'] = 0
    state['angularPosn'] = 0
    state['angularVelocity'] = 0
    state['catIndex'] = catIndex
