#!/usr/bin/env python
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
A simple tutorial that shows some features of the Temporal Memory.

The following program has the purpose of presenting some
basic properties of the Temporal Memory, in particular when it comes
to how it handles high-order sequences.
"""

import numpy as np
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nupic.bindings.algorithms import TemporalMemory as TM

def accuracy(curr, pred):
  acc = 0
  if np.count_nonzero(pred) > 0:
    acc = float(np.dot(curr, pred))/float(np.count_nonzero(pred))
  return acc

def corruptVector(v1, noiseLevel, numActiveCols):
  size = len(v1)
  v2 = np.zeros(size, dtype="uint32")
  bitsToSwap = int(noiseLevel * numActiveCols)
  # Copy the contents of v1 into v2
  for i in range(size):
    v2[i] = v1[i]
  for _ in range(bitsToSwap):
    i = random.randrange(size)
    if v2[i] == 1:
      v2[i] = 0
    else:
      v2[i] = 1
  return v2

uintType = "uint32"
random.seed(1)

# After you have understood the concepts described in this script
# you should try changing some of the parameters of the TM and
# observe its behaviour.
# For instance, try changing the number of cells per column,
# activation threshold, etc. In particular try setting the
# permanenceDecrement to zero and tell whether the TM is able to
# forget previous input
tm = TM(columnDimensions = (2048,),
    cellsPerColumn=8,
    initialPermanence=0.21,
    connectedPermanence=0.3,
    minThreshold=15,
    maxNewSynapseCount=40,
    permanenceIncrement=0.1,
    permanenceDecrement=0.1,
    activationThreshold=15,
    predictedSegmentDecrement=0.01,
    )

sparsity = 0.02
sparseCols = int(tm.numberOfColumns() * sparsity)

# We will create a sparse representation of characters A, B, C, D, X, and Y.
# In this particular example we manually construct them, but usually you would
# use the spatial pooler to build these.
seq1 = np.zeros((4, tm.numberOfColumns()), dtype="uint32")
seq1[0, 0:sparseCols] = 1  # Input SDR representing "A"
seq1[1, sparseCols:2*sparseCols] = 1   # Input SDR representing "B"
seq1[2, 2*sparseCols:3*sparseCols] = 1   # Input SDR representing "C"
seq1[3, 3*sparseCols:4*sparseCols] = 1   # Input SDR representing "D"

seq2 = np.zeros((4, tm.numberOfColumns()), dtype="uint32")
seq2[0, 4*sparseCols:5*sparseCols] = 1   # Input SDR representing "X"
seq2[1, sparseCols:2*sparseCols] = 1   # Input SDR representing "B"
seq2[2, 2*sparseCols:3*sparseCols] = 1   # Input SDR representing "C"
seq2[3, 5*sparseCols:6*sparseCols] = 1   # Input SDR representing "Y"

seqT = np.zeros((6, tm.numberOfColumns()), dtype="uint32")
seqT[0, 0:sparseCols] = 1  # Input SDR representing "A"
seqT[1, sparseCols:2*sparseCols] = 1   # Input SDR representing "B"
seqT[2, 2*sparseCols:3*sparseCols] = 1   # Input SDR representing "C"
seqT[3, 3*sparseCols:4*sparseCols] = 1   # Input SDR representing "D"
seqT[4, 4*sparseCols:5*sparseCols] = 1   # Input SDR representing "X"
seqT[5, 5*sparseCols:6*sparseCols] = 1   # Input SDR representing "Y"

# PART 1. Feed the TM with sequence "ABCD". The TM will eventually learn
# the pattern and it's prediction accuracy will go to 1.0 (except in-between sequences
# where the TM doesn't output any prediction)
print ""
print "-"*50
print "Part 1. We present the sequence ABCD to the TM. The TM will eventually"
print "will learn the sequence and predict the upcoming characters. This can be"
print "measured by the prediction accuracy in Fig 1."
print "N.B. In-between sequences the accuracy is 0.0 as the TM does not output"
print "any prediction."
print "-"*50
print ""

currCols = np.zeros(tm.numberOfColumns(), dtype="uint32")
predCols = np.zeros(tm.numberOfColumns(), dtype="uint32")
ts = 0
x = []
y = []
for t in range(10):
  tm.reset()
  for k in range(4):
    tm.compute(set(seq1[k][:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

plt.ylim([-0.1,1.1])
plt.plot(x, y)
plt.xlabel("Timestep")
plt.ylabel("Prediction Accuracy")
plt.title("Fig. 1: TM learns sequence ABCD")
plt.savefig("figure_1")
plt.close()

print ""
print "-"*50
print "Once the TM has learned the sequence ABCD, we will present the individual"
print "characters to the TM to know its prediction. The TM outputs the columns"
print "that become active upon the presentation of a particular character as well"
print "as the columns predicted in the next time step. Here, you should see that"
print "A predicts B, B predicts C, C predicts D, and D does not output any"
print "prediction."
print "N.B. Here, we are presenting individual characters, that is, a character"
print "deprived of context in a sequence."
print "-"*50
print ""

for k in range(4):
  print "--- " + "ABCD"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

# PART 2. Now we will present the sequence XBCY to the TM. The prediction accuracy
# drops as the TM learns the new sequence. ABCD and XBCY are high-order sequences,
# if we presented the sequence BC to the TM, it would not be able to disambiguate
# between ABCD and XBCY. As such, we would expect to see simultaneous predictions
# when presenting the TM with particular individual characters.
print ""
print "-"*50
print "Part 2. We now present the sequence XBCY to the TM. As expected, the accuracy will"
print "drop until the TM learns the new sequence (Fig 2). What will be the prediction of"
print "the TM if presented with the sequence BC? This would depend on what character"
print "anteceding B. This is an important feature of high-order sequences."
print "-"*50
print ""

for t in range(10):
  tm.reset()
  for k in range(4):
    tm.compute(set(seq2[k][:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

# In this figure you can see how the TM starts making good predictions for particular
# characters (spikes in the plot). Then, it will get half of its predictions right, which
# correspond to the times in which is presented with character C. After some time, it
# will learn correctly the sequence XBCY, and predict its characters accordingly.
plt.ylim([-0.1,1.1])
plt.xlim([40,80])
plt.plot(x, y)
plt.xlabel("Timestep")
plt.ylabel("Prediction Accuracy")
plt.title("Fig. 2: TM learns new sequence XBCY")
plt.savefig("figure_2")
plt.close()

print ""
print "-"*50
print "We will present again each of the characters individually to the TM, that is,"
print "not within any of the two sequences. When presented with character A the TM"
print "predicts B, B predicts C, but this time C outputs a simultaneous prediction of"
print "both D and Y. In order to disambiguate, the TM would require to know if the"
print "preceding characters were AB or XB. When presented with character X the TM"
print "predicts B, whereas Y and D yield no prediction."
print "-"*50
print ""

for k in range(6):
  print "--- " + "ABCDXY"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

# PART 3. Now we will present noisy inputs to the TM. We will add noise to the sequence XBCY
# by corrupting 50% of its bits. We would like to see how the TM responds in the presence of
# noise and how it recovers from it.
print ""
print "-"*50
print "Part 3. We will add noise to the sequence XBCY by corrupting 50% of the bits in the vectors"
print "encoding each character. We would expect to see a decrease in prediction accuracy as the"
print "TM is unable to learn the random noise in the input (Fig 3)."
print "-"*50
print ""

for t in range(50):
  tm.reset()
  for k in range(4):
    v = corruptVector(seq2[k][:], 0.5, sparseCols)
    tm.compute(set(v[:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

print ""
print "-"*50
print "Let's have a look again at the output of the TM when presented with noisy"
print "input. The prediction of some characters (eg. X) now includes columns that"
print "are not related to any other character. This is because the TM tried to learn"
print "the noise in the input patterns."
print "-"*50
print ""

for k in range(6):
  print "--- " + "ABCDXY"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

plt.ylim([-0.1,1.1])
plt.xlim([200,280])
plt.plot(x, y)
plt.xlabel("Timestep")
plt.ylabel("Prediction Accuracy")
plt.title("Fig. 3: Accuracy in TM drops when presented with noisy input")
plt.savefig("figure_3")
plt.close()

# Will the TM be able to forget the 'noisy' columns learned in the previous step?
# We will present the TM with the original sequence XBCY in order to re-learn it.
for t in range(10):
  tm.reset()
  for k in range(4):
    tm.compute(set(seq2[k][:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

print ""
print "-"*50
print "After presenting the original sequence XBCY to the TM, we would expect to see"
print "the predicted noisy columns from the previous step disappear. We will verify that"
print "by presenting the individual characters to the TM."
print "-"*50
print ""

for k in range(6):
  print "--- " + "ABCDXY"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

# We can see how the prediction accuracy goes back to 1.0 (as before, not in-between sequences)
# when the TM re-learns the sequence XCBY and 'forgets' the noisy columns.
plt.ylim([-0.1,1.1])
plt.xlim([280,320])
plt.plot(x, y)
plt.xlabel("Timestep")
plt.ylabel("Prediction Accuracy")
plt.title("Fig. 4: TM re-learns sequence XBCY when noise is over")
plt.savefig("figure_4")
plt.close()

# Let's corrupt the sequence even more and add 90% of noise to each of its characters.
# Here, we would expect to see even more of a decrease in accuracy along with more 'noisy'
# columns being predicted.
print ""
print "-"*50
print "We will add more noise to the characters in the sequence XBCY. This time we will"
print "corrupt 90% of its contents. As expected, the accuracy will decrease (Fig 5) and"
print "'noisy' columns will be predicted by the TM."
print "-"*50
print ""

for t in range(50):
  tm.reset()
  for k in range(4):
    v = corruptVector(seq2[k][:], 0.9, sparseCols)
    tm.compute(set(v[:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

print ""
print "-"*50
print "Next, we will have a look at the output of the TM when presented with the"
print "individual characters of the sequence. As before, we see 'noisy' predicted"
print "columns emerging as a result of the TM trying to learn the noise."
print "-"*50
print ""

for k in range(6):
  print "--- " + "ABCDXY"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

# In this figure we can observe how the prediction accuracy is affected by the presence
# of noise in the input. However, the accuracy does not drops dramatically even with 90%
# of noise which implies that the TM exhibits some resilience to noise in its input
# which means that it does not forget easily a well-learned, real pattern.
plt.ylim([-0.1,1.1])
plt.xlim([320,520])
plt.plot(x, y)
plt.xlabel("Timestep")
plt.ylabel("Prediction Accuracy")
plt.title("Fig. 5: Accuracy drops even more when more noise is added to input")
plt.savefig("figure_5")
plt.close()

# Let's present the original sequence to the TM in order to re-learn it. After this, the
# TM will predict accurately the sequence again, and its predictions will not include 'noisy'
# columns anymore.
for t in range(25):
  tm.reset()
  for k in range(4):
    tm.compute(set(seq2[k][:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

# We will observe how the prediction accuracy gets back to 1.0 (not in-between sequences)
# as the TM re-learns the original sequence.
plt.ylim([-0.1,1.1])
plt.xlim([520,620])
plt.plot(x, y)
plt.xlabel("Timestep")
plt.ylabel("Prediction Accuracy")
plt.title("Fig. 6: When noise is suspended, accuracy is restored")
plt.savefig("figure_6")
plt.close()

# The TM restores its prediction accuracy and it can be seen when presented with the individual characters.
# There's no noisy columns being predicted.
print ""
print "-"*50
print "After presenting noisy input to the TM, we present the original sequence in"
print "order to make it re-learn XBCY. We verify that this was achieved by presenting"
print "the TM with the individual characters and observing its output. Again, we can"
print "see that the 'noisy' columns are not being predicted anymore, and that the"
print "prediction accuracy goes back to 1.0 when the sequence is presented (Fig 6)."
print "-"*50
print ""

for k in range(6):
  print "--- " + "ABCDXY"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]  
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

# PART 4. Now, we will present both sequences ABCD and XBCY randomly to the TM.
# What would be the output of the TM when presented with character D if it has
# been exposed to sequences ABCD and XBCY occurring randomly one after the other?
# If one quarter of the time the TM sees the sequence ABCDABCD, another quarter the
# TM sees ABCDXBCY, another quarter it sees XBCYXBCY, and the last quarter it saw
# XBCYABCD, then the TM would exhibit simultaneous predictions for characters D, Y
# and C.
print ""
print "-"*50
print "Part 4. We will present both sequences ABCD and XBCY randomly to the TM."
print "Here, we might observe simultaneous predictions occurring when the TM is"
print "presented with characters D, Y, and C."
print "-"*50
print ""

for t in range(75):
  rnd = random.randrange(2)
  for k in range(4):
    if rnd == 0:
      tm.compute(set(seq1[k][:].nonzero()[0].tolist()), learn=True)
    else:
      tm.compute(set(seq2[k][:].nonzero()[0].tolist()), learn=True)
    activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
    predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]
    actColState = ['1' if i in activeColumnsIndeces else '0' for i in range(tm.numberOfColumns())]
    actColStr = ("".join(actColState))
    currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
    acc = accuracy(currCols, predCols)
    x.append(ts)
    y.append(acc)
    ts += 1
    predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
    predColState = ['1' if i in predictedColumnIndeces else '0' for i in range(tm.numberOfColumns())]
    predColStr = ("".join(predColState))

print ""
print "-"*50
print "We now have a look at the output of the TM when presented with the individual"
print "characters A, B, C, D, X, and Y. We might observe simultaneous predictions when"
print "presented with character D (predicting A and X), character Y (predicting A and X),"
print "and when presented with character C (predicting D and Y)."
print "N.B. Due to the stochasticity of this script, we might not observe simultaneous"
print "predictions in *all* the aforementioned characters."
print "-"*50
print ""

for k in range(6):
  print "--- " + "ABCDXY"[k] + " ---"
  tm.compute(set(seqT[k][:].nonzero()[0].tolist()), learn=False)
  activeColumnsIndeces = [tm.columnForCell(i) for i in tm.getActiveCells()]
  predictedColumnIndeces = [tm.columnForCell(i) for i in tm.getPredictiveCells()]  
  currCols = [1 if i in activeColumnsIndeces else 0 for i in range(tm.numberOfColumns())]
  predCols = [1 if i in predictedColumnIndeces else 0 for i in range(tm.numberOfColumns())]
  print("Active cols: " + str(np.nonzero(currCols)[0]))
  print("Predicted cols: " + str(np.nonzero(predCols)[0]))
  print ""

print ""
print "-*"*25
print "Scroll up to see the development of this simple"
print "tutorial. Also open the source file to see more"
print "comments regarding each part of the script."
print "All images generated by this script will be saved"
print "in your current working directory."
print "-*"*25
print ""
