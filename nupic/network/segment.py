# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

from nupic.network.synapse import Synapse



class Segment(object):

  def __init__(self, cell=None, column=None):
    self.cell = cell
    self.column = column
    self.synapses = set()


  def createSynapse(self, presynapticCell=None, presynapticCellIndex=None, permanence=None):
    """
    Creates a new synapse on a segment.
    
    @param presynapticCell      (Cell)  Source cell
    @param presynapticCellIndex (int)   Source cell index
    @param permanence           (float) Initial permanence

    @return (Synapse) New synapse
    """

    synapse = Synapse(self, presynapticCell, presynapticCellIndex, permanence)
    self.synapses.add(synapse)

    if presynapticCell is not None:
      presynapticCell.postsynapticCellsSynapses.add(synapse)

    return synapse


  def destroySynapse(self, synapse):
    """
    Destroys a synapse.

    @param synapse (Synapse) Synapse to destroy
    """
    self.synapses.remove(synapse)

    if synapse.presynapticCell is not None:
      synapse.presynapticCell.postsynapticCellsSynapses.remove(synapse)

    del synapse


  def destroyAllSynapses(self):
    """
    Destroys a synapse.

    @param synapse (Synapse) Synapse to destroy
    """
    while self.synapses:
      synapse = self.synapses.pop()
      if synapse.presynapticCell is not None:
        synapse.presynapticCell.postsynapticCellsSynapses.remove(synapse)
      del synapse
