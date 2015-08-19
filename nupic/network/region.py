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

import numpy

from nupic.network.cell import Cell
from nupic.network.column import Column
from nupic.network.segment import Segment



class Region(object):

  def __init__(self, columnDimensions=(64,64), numCellsPerColumn=None):
    """
    Parameters:
    ----------------------------
    @param columnDimensions (list): 
      A list representing the dimensions of the columns in the region. Format is
      [height, width, depth, ...], where each value represents the size of the
      dimension.  For a topology of one dimension with 2000 columns use 2000, or
      [2000]. For a three dimensional topology of 32x64x16 use [32, 64, 16].
    @param cellsPerColumn   (int):
      Number of cells per column
    """
    # Error checking
    if not len(columnDimensions):
      raise ValueError("Number of column dimensions must be greater than 0")

    if numCellsPerColumn is not None and not numCellsPerColumn > 0:
      raise ValueError("Number of cells per column must be greater than 0")
    
    self.columnDimensions = numpy.array(columnDimensions, ndmin=1)
    self.numColumns = self.columnDimensions.prod()
    self.numCellsPerColumn = numCellsPerColumn
    
    self.columns = [None] * self.numColumns
    for i in xrange(self.numColumns):
      self.columns[i] = Column()
      if self.numCellsPerColumn is not None:
        self.columns[i].cells = [None] * self.numCellsPerColumn
        for j in xrange(self.numCellsPerColumn):
          self.columns[i].cells[j] = Cell(self.columns[i])

  def numberOfColumns(self):
    """
    Returns the number of columns in this layer.

    @return (int) Number of columns
    """
    return self.numColumns


  def numberOfCells(self):
    """
    Returns the number of cells in this layer.

    @return (int) Number of cells
    """
    return self.numColumns * self.numCellsPerColumn