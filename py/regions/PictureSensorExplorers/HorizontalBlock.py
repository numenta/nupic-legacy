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
This file defines HorizBlock a horizontal-only block explorer.
"""

from nupic.regions.PictureSensor import PictureSensor

#+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# BlockPictureExplorer

class BlockPictureExplorer(PictureSensor.PictureExplorer):
  """
  A base plugin class that implements "explorer" functionality for
  specific categories; this functionality controls the manner in
  which pictures are swept.

  To add support for a new type of explorer to the PictureSensor,
  perform the following:

  1. Derive a sub-class from this PictureExplorer base class;
  2. Implement the following mandatory methods:
     initSequence() - create initial state for a new sequence
     updateSequence()  - update state of an existing sequence
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
    self._presentNextPosn(state, params)

  def updateSequence(self, state, params):
    self._presentNextPosn(state, params)


  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # Internal helper method(s)

  def _presentNextPosn(self, state, params):
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
