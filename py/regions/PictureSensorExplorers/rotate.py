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
    return ( 'numRepetitions',
             'minAngularPosn', 'maxAngularPosn',
             'minAngularVelocity', 'maxAngularVelocity',
           )

  def notifyParamUpdate(self, params):
    """
    A callback that will be invoked if/when any of the explorer's
    relevant parameters have their values changed.

    @param params: a dict containing the new values of all parameters
                   that are relevant to the explorer's operation
                   (as specified by a call to queryRelevantParams()).
    """
    # Parameter checks
    if params['minAngularVelocity'] != params['maxAngularVelocity']:
      raise NotImplementedError("'rotate' explorer currently supports " \
            "only a fixed angular velocity; i.e., 'minAngularVelocity' (%d) " \
            "must be identical to 'maxAngularVelocity' (%d)" \
            % (params['minAngularVelocity'], params['maxAngularVelocity']))
    super(RotatePictureExplorer, self).notifyParamUpdate(params)

  def initSequence(self, state, params):
    self._presentNextRotation(state, params)

  def updateSequence(self, state, params):
    self._presentNextRotation(state, params)


  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  # Internal helper method(s)

  def _presentNextRotation(self, state, params):
    """
    Compute the appropriate category and rotational angle
    deterministically based on the current iteration count.
    """

    # These don't change
    state['posnX'] = 0
    state['posnY'] = 0
    state['velocityX'] = 0
    state['velocityY'] = 0
    state['angularVelocity'] = params['minAngularVelocity']

    # These do change
    sequenceLength = 1 + int((params['maxAngularPosn'] - params['minAngularPosn'])
                             / params['minAngularVelocity'])
    state['catIndex'] = self._getIterCount() / (sequenceLength * params['numRepetitions'])
    seqIndex = self._getIterCount() % (sequenceLength * params['numRepetitions'])
    state['angularPosn'] = params['maxAngularPosn'] \
                           - state['angularVelocity'] * seqIndex
