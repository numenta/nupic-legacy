#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

print """
This program shows how to access the Temporal Pooler directly by demonstrating
how to create a TP instance, train it with vectors, get predictions, and inspect
the state.

The code here runs a very simple version of sequence learning, with one
cell per column. The TP is trained with the simple sequence A->B->C->D->E

HOMEWORK: once you have understood exactly what is going on here, try changing
cellsPerColumn to 4. What is the difference between once cell per column and 4
cells per column?

PLEASE READ THROUGH THE CODE COMMENTS - THEY EXPLAIN THE OUTPUT IN DETAIL

"""

# Can't live without numpy
import numpy

# This is the class correspondingn to the C++ optimized Temporal Pooler
from nupic.research.TP10X2 import TP10X2


# Utility routine for printing the input vector
def formatRow(x):
  s = ''
  for c in range(len(x)):
    if c > 0 and c % 10 == 0:
      s += ' '
    s += str(x[c])
  s += ' '
  return s



#######################################################################
#
# Step 1: create Temporal Pooler instance with appropriate parameters
tp = TP10X2(numberOfCols=50, cellsPerColumn=1,
                initialPerm=0.5, connectedPerm=0.5,
                minThreshold=10, newSynapseCount=10,
                permanenceInc=0.1, permanenceDec=0.0,
                activationThreshold=8,
                globalDecay=0, burnIn=1,
                checkSynapseConsistency=False,
                pamLength=10)


#######################################################################
#
# Step 2: create input vectors to feed to the temporal pooler. Each input vector
# must be numberOfCols wide. Here we create a simple sequence of 5 vectors
# representing the sequence A -> B -> C -> D -> E
x = numpy.zeros((5,tp.numberOfCols), dtype="uint32")
x[0,0:10]  = 1   # Input SDR representing "A"
x[1,10:20] = 1   # Input SDR representing "B"
x[2,20:30] = 1   # Input SDR representing "C"
x[3,30:40] = 1   # Input SDR representing "D"
x[4,40:50] = 1   # Input SDR representing "E"


#######################################################################
#
# Step 3: send this simple sequence to the temporal pooler for learning
# We repeat the sequence 10 times
for i in range(10):

  # Send each letter in the sequence in order
  for j in range(5):

    # The compute method performs one step of learning and/or inference. Note:
    # here we just perform learning but you can perform prediction/inference and
    # learning in the same step if you want (online learning).
    tp.compute(x[j], enableLearn = True, computeInfOutput = False)

  # The reset command tells the TP that a sequence just ended and essentially
  # zeros out all the states. It is not strictly necessary but it's a bit
  # messier without resets, and the TP learns quicker with resets.
  tp.reset()
  

#######################################################################
#
# Step 3: send the same sequence of vectors and look at predictions made by
# temporal pooler
for j in range(5):
  print "\n\n--------","ABCDE"[j],"-----------"
  print "Raw input vector\n",formatRow(x[j])
  
  # Send each vector to the TP, with learning turned off
  tp.compute(x[j], enableLearn = False, computeInfOutput = True)
  
  # This method prints out the active state of each cell followed by the
  # predicted state of each cell. For convenience the cells are grouped
  # 10 at a time. When there are multiple cells per column the printout
  # is arranged so the cells in a column are stacked together
  #
  # What you should notice is that the columns where active state is 1
  # represent the SDR for the current input pattern and the columns where
  # predicted state is 1 represent the SDR for the next expected pattern
  tp.printStates(printPrevious = False, printLearnState = False)


#######################################################################
#
# This command prints the segments associated with every single cell
# This is commented out because it prints a ton of stuff.
#tp.printCells()

