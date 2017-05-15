# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------


print """
This program shows how to access the Temporal Memory directly by demonstrating
how to create a TM instance, train it with vectors, get predictions, and
inspect the state.

The code here runs a very simple version of sequence learning, with one
cell per column. The TM is trained with the simple sequence A->B->C->D->E

HOMEWORK: once you have understood exactly what is going on here, try changing
cellsPerColumn to 4. What is the difference between once cell per column and 4
cells per column?

PLEASE READ THROUGH THE CODE COMMENTS - THEY EXPLAIN THE OUTPUT IN DETAIL

"""

# Can't live without numpy
import numpy
from itertools import izip as zip, count

from nupic.algorithms.temporal_memory import TemporalMemory as TM


# Utility routine for printing the input vector
def formatRow(x):
  s = ''
  for c in range(len(x)):
    if c > 0 and c % 10 == 0:
      s += ' '
    s += str(x[c])
  s += ' '
  return s


# Step 1: create Temporal Pooler instance with appropriate parameters

tm = TM(columnDimensions = (50,),
        cellsPerColumn=2,
        initialPermanence=0.5,
        connectedPermanence=0.5,
        minThreshold=8,
        maxNewSynapseCount=20,
        permanenceIncrement=0.1,
        permanenceDecrement=0.0,
        activationThreshold=8,
        )


# Step 2: create input vectors to feed to the temporal memory. Each input vector
# must be numberOfCols wide. Here we create a simple sequence of 5 vectors
# representing the sequence A -> B -> C -> D -> E
x = numpy.zeros((5, tm.numberOfColumns()), dtype="uint32")
x[0, 0:10] = 1    # Input SDR representing "A", corresponding to columns 0-9
x[1, 10:20] = 1   # Input SDR representing "B", corresponding to columns 10-19
x[2, 20:30] = 1   # Input SDR representing "C", corresponding to columns 20-29
x[3, 30:40] = 1   # Input SDR representing "D", corresponding to columns 30-39
x[4, 40:50] = 1   # Input SDR representing "E", corresponding to columns 40-49


# Step 3: send this simple sequence to the temporal memory for learning
# We repeat the sequence 10 times
for i in range(10):

  # Send each letter in the sequence in order
  for j in range(5):
    activeColumns = set([i for i, j in zip(count(), x[j]) if j == 1])

    # The compute method performs one step of learning and/or inference. Note:
    # here we just perform learning but you can perform prediction/inference and
    # learning in the same step if you want (online learning).
    tm.compute(activeColumns, learn = True)

    # The following print statements can be ignored.
    # Useful for tracing internal states
    print("active cells " + str(tm.getActiveCells()))
    print("predictive cells " + str(tm.getPredictiveCells()))
    print("winner cells " + str(tm.getWinnerCells()))
    print("# of active segments " + str(tm.connections.numSegments()))

  # The reset command tells the TM that a sequence just ended and essentially
  # zeros out all the states. It is not strictly necessary but it's a bit
  # messier without resets, and the TM learns quicker with resets.
  tm.reset()


#######################################################################
#
# Step 3: send the same sequence of vectors and look at predictions made by
# temporal memory
for j in range(5):
  print "\n\n--------","ABCDE"[j],"-----------"
  print "Raw input vector : " + formatRow(x[j])
  activeColumns = set([i for i, j in zip(count(), x[j]) if j == 1])
  # Send each vector to the TM, with learning turned off
  tm.compute(activeColumns, learn = False)

  # The following print statements prints out the active cells, predictive
  # cells, active segments and winner cells.
  #
  # What you should notice is that the columns where active state is 1
  # represent the SDR for the current input pattern and the columns where
  # predicted state is 1 represent the SDR for the next expected pattern
  print "\nAll the active and predicted cells:"

  print("active cells " + str(tm.getActiveCells()))
  print("predictive cells " + str(tm.getPredictiveCells()))
  print("winner cells " + str(tm.getWinnerCells()))
  print("# of active segments " + str(tm.connections.numSegments()))

  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]


  # Reconstructing the active and inactive columns with 1 as active and 0 as
  # inactive representation.

  actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
  actColStr = ("".join(actColState))
  predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
  predColStr = ("".join(predColState))

  # For convenience the cells are grouped
  # 10 at a time. When there are multiple cells per column the printout
  # is arranged so the cells in a column are stacked together
  print "Active columns:    " + formatRow(actColStr)
  print "Predicted columns: " + formatRow(predColStr)

  # predictedCells[c][i] represents the state of the i'th cell in the c'th
  # column. To see if a column is predicted, we can simply take the OR
  # across all the cells in that column. In numpy we can do this by taking
  # the max along axis 1.
