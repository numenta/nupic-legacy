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

from nupic.network.segment import Segment



class Cell(object):

  def __init__(self, column=None):
    self.column = column
    self.segments = set()
    self.postsynapticCellsSynapses = set()
    

  def createSegment(self):
    """
    Adds a new segment on a cell.

    @return (Segment) New segment
    """

    segment = Segment(self)
    self.segments.add(segment)

    return segment


  def destroySegment(self, segment):
    """
    Destroys a segment.

    @param segment (Segment) Segment to destroy
    """
    segment.destroyAllSynapses()

    self.segments.remove(segment)
    del segment
