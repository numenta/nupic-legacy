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

"""
Temporal Memory implementation in Python.
"""

from operator import mul

from nupic.bindings.math import Random



class TM(object):
  """
  Class implementing the Temporal Memory algorithm.
  """

  def __init__(self,
               seed=42):
    """
    TODO
    """
    pass



class Connections(object):
  """
  Class to hold data representing the connectivity of a layer of cells,
  that the TM operates on.
  """

  def __init__(self,
               columnDimensions,
               cellsPerColumn):
    """
    @param columnDimensions (list) Dimensions of the column space
    @param cellsPerColumn   (int)  Number of cells per column
    """
    # Error checking
    if not len(columnDimensions):
      raise ValueError("Number of column dimensions must be greater than 0")

    if not cellsPerColumn > 0:
      raise ValueError("Number of cells per column must be greater than 0")

    # Initialize member variables
    self.columnDimensions = columnDimensions
    self.cellsPerColumn = cellsPerColumn


  def cellsForColumn(self, column):
    """
    Returns the indices of cells that belong to a column.

    @param  column (int) Column index
    @return cell   (set) Cell indices
    """
    # Error checking
    if column >= self._numberOfColumns() or column < 0:
      raise IndexError("Invalid column")

    # Compute cells in column
    start = self.cellsPerColumn * column
    end = start + self.cellsPerColumn
    return {cell for cell in range(start, end)}


  def columnForCell(self, cell):
    """
    Returns the index of the column that a cell belongs to.

    @param  cell   (int) Cell index
    @return column (set) Column index
    """
    # Error checking
    numberOfCells = self._numberOfColumns() * self.cellsPerColumn
    if cell >= numberOfCells or cell < 0:
      raise IndexError("Invalid cell")

    # Compute column for cell
    return int(cell / self.cellsPerColumn)


  def _numberOfColumns(self):
    """
    Returns the number of columns in this layer.

    @return numberOfColumns (int) Number of columns
    """
    return reduce(mul, self.columnDimensions, 1)
