# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

"""
A simple tutorial that shows some features of the Spatial Pooler.

The following program has the purpose of presenting some
basic properties of the Spatial Pooler. It reproduces Figs.
5, 7 and 9 from this paper: http://arxiv.org/abs/1505.02142
To learn more about the Spatial Pooler have a look at BAMI:
http://numenta.com/biological-and-machine-intelligence/
or at its class reference in the NuPIC documentation:
http://numenta.org/docs/nupic/classnupic_1_1research_1_1spatial__pooler_1_1_spatial_pooler.html
The purpose of the Spatial Pooler is to create a sparse representation
of its inputs in such a way that similar inputs will be mapped to similar
sparse representations. Thus, the Spatial Pooler should exhibit some resilience
to noise in its input.
"""

import numpy as np
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nupic.research.spatial_pooler import SpatialPooler as SP

def percentOverlap(x1, x2, size):
  """
  Computes the percentage of overlap between vectors x1 and x2.

  @param x1   (array) binary vector
  @param x2   (array) binary vector
  @param size (int)   length of binary vectors
  
  @return percentOverlap (float) percentage overlap between x1 and x2
  """
  nonZeroX1 = np.count_nonzero(x1)
  nonZeroX2 = np.count_nonzero(x2)
  minX1X2 = min(nonZeroX1, nonZeroX2)
  percentOverlap = 0
  if minX1X2 > 0:
    percentOverlap = float(np.dot(x1, x2))/float(minX1X2)
  return percentOverlap



def corruptVector(vector, noiseLevel):
  """
  Corrupts a binary vector by inverting noiseLevel percent of its bits.

  @param vector     (array) binary vector to be corrupted
  @param noiseLevel (float) amount of noise to be applied on the vector. 
  """
  size = len(vector)
  for i in range(size):
    rnd = random.random()
    if rnd < noiseLevel:
      if vector[i] == 1:
        vector[i] = 0
      else:
        vector[i] = 1 


    
def resetVector(x1, x2):
  """
  Copies the contents of vector x1 into vector x2.
  
  @param x1 (array) binary vector to be copied
  @param x2 (array) binary vector where x1 is copied
  """
  size = len(x1)
  for i in range(size):
    x2[i] = x1[i]

random.seed(1)
uintType = "uint32"
inputDimensions = (1000,1)
columnDimensions = (2048,1)
inputSize = np.array(inputDimensions).prod()
columnNumber = np.array(columnDimensions).prod()
inputArray = np.zeros(inputSize, dtype=uintType)

for i in range(inputSize):
  inputArray[i] = random.randrange(2)
  
activeCols = np.zeros(columnNumber, dtype=uintType)
sp = SP(inputDimensions, 
  columnDimensions, 
  potentialRadius = int(0.5*inputSize),
  numActiveColumnsPerInhArea = int(0.02*columnNumber),
  globalInhibition = True,
  seed = 1,
  synPermActiveInc = 0.01,
  synPermInactiveDec = 0.008
   )

# Part 1: 
# -------
# A column connects to a subset of the input vector (specified
# by both the potentialRadius and potentialPct). The overlap score
# for a column is the number of connections to the input that become
# active when presented with a vector. When learning is 'on' in the SP,
# the active connections are reinforced, whereas those inactive are
# depressed (according to parameters synPermActiveInc and synPermInactiveDec.
# In order for the SP to create a sparse representation of the input, it
# will select a small percentage (usually 2%) of its most active columns,
# ie. columns with the largest overlap score.
# In this first part, we will create a histogram showing the overlap scores
# of the Spatial Pooler (SP) after feeding it with a random binary
# input. As well, the histogram will show the scores of those columns
# that are chosen to build the sparse representation of the input.

sp.compute(inputArray, False, activeCols)
overlaps = sp.getOverlaps()
activeColsScores = []
for i in activeCols.nonzero():
  activeColsScores.append(overlaps[i])

print ""
print "---------------------------------"
print "Figure 1 shows an histogram of the overlap scores"
print "from all the columns in the spatial pooler, as well as the"
print "overlap scores of those columns that were selected to build a"
print "sparse representation of the input (shown in green)."
print "The SP chooses 2% of the columns with the largest overlap score"
print "to make such sparse representation."
print "---------------------------------"
print ""

bins = np.linspace(min(overlaps), max(overlaps), 28)
plt.hist(overlaps, bins, alpha=0.5, label='All cols')
plt.hist(activeColsScores, bins, alpha=0.5, label='Active cols')
plt.legend(loc='upper right')
plt.xlabel("Overlap scores")
plt.ylabel("Frequency")
plt.title("Figure 1: Column overlap of a SP with random input.")
plt.savefig("figure_1")
plt.close()

# Part 2a: 
# -------
# The input overlap between two binary vectors is defined as their dot product. In order
# to normalize this value we divide by the minimum number of active inputs
# (in either vector). This means we are considering the sparser vector as reference.
# Two identical binary vectors will have an input overlap of 1, whereas two completely 
# different vectors (one is the logical NOT of the other) will yield an overlap of 0.
# In this section we will see how the input overlap of two binary vectors decrease as we
# add noise to one of them.
	
inputX1 = np.zeros(inputSize, dtype=uintType)
inputX2 = np.zeros(inputSize, dtype=uintType)
outputX1 = np.zeros(columnNumber, dtype=uintType)
outputX2 = np.zeros(columnNumber, dtype=uintType)

for i in range(inputSize):
  inputX1[i] = random.randrange(2)

x = []
y = []   
for noiseLevel in np.arange(0, 1.1, 0.1):
  resetVector(inputX1, inputX2)
  corruptVector(inputX2, noiseLevel)
  x.append(noiseLevel)
  y.append(percentOverlap(inputX1, inputX2, inputSize))

print ""
print "---------------------------------"
print "Figure 2 shows the input overlap between 2 identical binary"
print "vectors in function of the noise applied to one of them."
print "0 noise level means that the vector remains the same, whereas"
print "1 means that the vector is the logical negation of the original"
print "vector."
print "The relationship between overlap and noise level is practically"
print "linear and monotonically decreasing."
print "---------------------------------"
print ""

plt.plot(x, y)
plt.xlabel("Noise level")
plt.ylabel("Input overlap")
plt.title("Figure 2: Input overlap between 2 identical vectors in function of noiseLevel.")
plt.savefig("figure_2")
plt.close()

# Part 2b: 
# -------
# The output overlap between two binary input vectors is the overlap of the
# columns that become active once they are fed to the SP. In this part we
# turn learning off, and observe the output of the SP as we input two binary 
# input vectors with varying level of noise.
# Starting from two identical vectors (that yield the same active columns)
# we would expect that as we add noise to one of them their output overlap
# decreases.
# In this part we will show how the output overlap behaves in function of the
# input overlap between two vectors.
# Even with an untrained spatial pooler, we see some noise resilience. 
# Note that due to the non-linear properties of high dimensional SDRs, overlaps 
# greater than 10 bits, or 25% in this example, are considered significant.

x = []
y = []   
for noiseLevel in np.arange(0, 1.1, 0.1):
  resetVector(inputX1, inputX2)
  corruptVector(inputX2, noiseLevel)
  
  sp.compute(inputX1, False, outputX1)
  sp.compute(inputX2, False, outputX2)  
  
  x.append(percentOverlap(inputX1, inputX2, inputSize))
  y.append(percentOverlap(outputX1, outputX2, columnNumber))

print ""
print "---------------------------------"
print "Figure 3 shows the output overlap between two sparse representations" 
print "in function of their input overlap. Starting from two identical binary vectors"
print "(which yield the same active columns) we add noise two one of them"
print "feed it to the SP, and estimate the output overlap between the two"
print "representations in terms of the common active columns between them."
print "As expected, as the input overlap decrease, so does the output overlap."
print "---------------------------------"
print ""

plt.plot(x, y)
plt.xlabel("Input overlap")
plt.ylabel("Output overlap")
plt.title("Figure 3: Output overlap in function of input overlap in a SP without training")
plt.savefig("figure_3")
plt.close()

# Part 3: 
# -------
# After training, a SP can become less sensitive to noise. For this purpose, we train the SP by
# turning learning on, and by exposing it to a variety of random binary vectors.
# We will expose the SP to a repetition of input patterns in order to make it learn and distinguish
# them once learning is over. This will result in robustness to noise in the inputs.
# In this section we will reproduce the plot in the last section after the SP has learned a series
# of inputs. Here we will see how the SP exhibits increased resilience to noise after learning.

# We will present 10 random vectors to the SP, and repeat this 30 times.
# Later you can try changing the number of times we do this to see how it changes the last plot.
# Then, you could also modify the number of examples to see how the SP behaves.
# Is there a relationship between the number of examples and the number of times that
# we expose them to the SP?

numExamples = 10
inputVectors = np.zeros((numExamples, inputSize), dtype=uintType)
outputColumns = np.zeros((numExamples, columnNumber), dtype=uintType)

for i in range(numExamples):
  for j in range(inputSize):
    inputVectors[i][j] = random.randrange(2)

# This is the number of times that we will present the input vectors to the SP
epochs = 30

for _ in range(epochs):
  for i in range(numExamples):
    #Feed the examples to the SP
    sp.compute(inputVectors[i][:], True, outputColumns[i][:])

inputVectorsCorrupted = np.zeros((numExamples, inputSize), dtype=uintType)
outputColumnsCorrupted = np.zeros((numExamples, columnNumber), dtype=uintType)

x = []
y = []
# We will repeat the experiment in the last section for only one input vector
# in the set of input vectors
for noiseLevel in np.arange(0, 1.1, 0.1):
  resetVector(inputVectors[0][:], inputVectorsCorrupted[0][:])
  corruptVector(inputVectorsCorrupted[0][:], noiseLevel)
  
  sp.compute(inputVectors[0][:], False, outputColumns[0][:])
  sp.compute(inputVectorsCorrupted[0][:], False, outputColumnsCorrupted[0][:])  
  
  x.append(percentOverlap(inputVectors[0][:], inputVectorsCorrupted[0][:], inputSize))
  y.append(percentOverlap(outputColumns[0][:], outputColumnsCorrupted[0][:], columnNumber))

print ""
print "---------------------------------"
print "How robust is the SP to noise after learning?"
print "Figure 4 shows again the output overlap between two binary vectors in function"
print "of their input overlap. After training, the SP exhibits more robustness to noise"
print "in its input, resulting in a -almost- sigmoid curve. This implies that even if a"
print "previous input is presented again with a certain amount of noise its sparse"
print "representation still resembles its original."
print "---------------------------------"
print ""

plt.plot(x, y)
plt.xlabel("Input overlap")
plt.ylabel("Output overlap")
plt.title("Figure 4: Output overlap in function of input overlap in a SP after training")
plt.savefig("figure_4")
plt.close()

print ""
print "+++++++++++++++++++++++++++++++++++++++++++++++++++"
print " All images generated by this script will be saved"
print " in your current working directory."
print "+++++++++++++++++++++++++++++++++++++++++++++++++++"
print ""

