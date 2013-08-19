#! /usr/local/bin/python
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

from nupic.bindings.math import *
from nupic.bindings.algorithms import *

import sys
import numpy
import pylab
import cPickle

#--------------------------------------------------------------------------------
# Embed sequences - a utility to train a Grouper
#
# Embeds sequences passed into a random text of size text_size, containing
# digits in [0,alphabet). Alpha and beta control characteristics of the noise.
#--------------------------------------------------------------------------------
def generateData(text_size, alphabet, sequences):
  
  text = numpy.random.randint(0, alphabet, text_size).tolist()

  i = 0; j = 0
  while i < text_size:
    seq = sequences[j % len(sequences)]
    text[i:i+len(seq)] = seq
    j = j + 1
    i = i + len(seq) + numpy.random.randint(1,3)

  return text

#--------------------------------------------------------------------------------
# Parse groups
#
# A routine that parses the group string returned by the Grouper
# and returns a list of lists
#--------------------------------------------------------------------------------
def parse_groups(grouper):

  groups_str =  grouper.getGroups(False)
  groups_list = [int(i) for i in groups_str.split()]
  groups = []
  idx = 0
  n_groups = groups_list[idx] ; idx += 1
  for _ in xrange(n_groups):
    n_elts = groups_list[idx]; idx += 1
    group = []
    for _ in xrange(n_elts):
      group.append(groups_list[idx]); idx += 1
    groups.append(group)
  return groups

#--------------------------------------------------------------------------------
# TAM learning, HOT, AHC grouping and TAM inference
#--------------------------------------------------------------------------------
def temporal_pooler_use_case(graphics=False):
    
    # "Learn" some floaint point TAM
    data = numpy.random.random((4,4))
    tam = TAM32(data)
    tam /= 3.5
    print '\nFirst tam\n', tam

    # Update it with outer products
    tam.incrementOnOuterProductVal([1,3], [2,3], 2.3)
    print '\ntam after update\n', tam

    # Create a Grouper
    transitionMemory = 1; topNeighbors = 1; maxNGroups = 10; maxGroupSize = 10
    symmetricTam = 1; overlappingGroups = 1; ahc_lgp = 1; mode = 0
    windowLength = 10; windowCount = 10; minCnt2 = 1; maxPerStage = 10
    g = Grouper(transitionMemory, topNeighbors, maxNGroups, maxGroupSize,
                symmetricTam, overlappingGroups, ahc_lgp, mode, 
                windowCount, minCnt2, windowLength, maxPerStage)

    print tam.fullTAMToString()
    sys.exit(0)

    # Set the tam we have learnt in the Grouper
    g.setTAMStateFromCSR(tam.fullTAMToString())

    # Learn some more with the usual Grouper learning
    # argmax is the "winner takes all" operation
    for i in xrange(20):
        g.learn([numpy.argmax(numpy.random.random((4)))])

    # Reset the TAM and history
    g.resetTAM()
    g.resetHistory()

    # Generate a text that contains 3 sequences
    text = generateData(100, 4, [[0,1,2,3],[3,2,1,0],[1,2,1,2]])

    # Learn the TAM and do several passes of HOT
    for i in xrange(len(text)/2):
        g.learn([text[i]])
        if i % windowLength == 0:
            g.hot(4, 1, 10)

    for i in xrange(len(text)/2, len(text)):
        g.learn([text[i]])
        if i % windowLength == 0:
            g.hot(5, .9, 20)

    # Look at HOT data structures
    print '\nC2S (sparse matrix)\n', g.getPyHOTC2S()
    print '\nS2C (string)\n', g.getPyHOTS2C()

    # Analyze c2s and s2c
    c2s = g.getPyHOTC2S()
    allNZ = [(i[0], i[1], int(i[2]-1)) for i in c2s.getAllNonZeros()]
    c2s_h = dict((t[2],t[1]) for t in allNZ)
    s2c_tmp = [int(i) for i in g.getPyHOTS2C().split()]
    s2c = dict((s2c_tmp[2*i], s2c_tmp[2*i+1]) for i in range(len(s2c_tmp)/2))
    print '\nC2S non-zeros in dictionary:', c2s_h
    print '\nS2C as dictionary:', s2c

    # Do a final pass of learning, since HOT resets the TAM
    for i in xrange(len(text)):
        g.learn([text[i]])

    # Do one round of AHC grouping, with lgp = 1
    g.AHCGroup(4)
    print '\nMerges 1:', g.AHCMerges()
    
    # Again, with lgp = 5.5
    g.setAHCLargeGroupPenalty(5.5)
    print '\nMerges 5.5:', g.AHCMerges()

    # Get 3 groups
    g.AHCGroup(3)
    print '\n3 groups:', parse_groups(g)

    # Get 2 groups
    g.AHCGroup(2) 
    print '\n2 groups:', parse_groups(g)

    # Now do TBI inference and predict at the same time
    g.setMode(2)
    for i in range(0, 4):
        print 'prediction', g.predict(2, 0)
        print 'inference', g.infer(numpy.random.random((4)))
    print '\nCollapsed tam\n', g.collapsedTam()
    print '\nFull tam\n', g.tam()

    # TBI cell weights and outputs
    print '\nTBI weights for group 0\n', g.tbiWeights(0)
    print '\nTBI outputs for group 0\n', g.tbiOutputs(0)
    
    # Sample from groups
    print '\nSampling 5 steps from group 0:\n', g.sampleFromGroup(0,0,5)

    # Persist the Grouper
    cPickle.dump(g, open('test.txt', 'w'))
    g2 = cPickle.load(open('test.txt', 'r'))

#--------------------------------------------------------------------------------
# Matrix plots of TAMs
#
# Start ipython -whtread 
# Type: run temporal_pooler_use_case.py --graphics
#--------------------------------------------------------------------------------

    if graphics:
      pylab.ion()
      pylab.imshow(g.tam().toDense(), interpolation='nearest')
      pylab.colorbar()
      pylab.figure()
      pylab.imshow(g.collapsedTam().toDense(), interpolation='nearest')
      pylab.colorbar()

#--------------------------------------------------------------------------------
# Graph plot of TAM
#--------------------------------------------------------------------------------

    tam = g.tam()
    out = open("graph.dot", "w")
    print >>out, "digraph A {"
    print >>out, "  rankdir=LR;"
    nodes = set()
    for i in xrange(tam.nRows()):
      for j in xrange(tam.nCols()):
        if tam[i, j] > 0:
          nodes.add("n%d" % i)
          nodes.add("n%d" % j)
    for node in nodes:
      print >>out, "  %s;" % node
    for i in xrange(tam.nRows()):
      for j in xrange(tam.nCols()):
        if tam[i, j] > 0:
          print >>out, ("  n%d -> n%d [label=\"%d\"];" % (i, j, tam[i, j]))
    print >>out, "}" 


#--------------------------------------------------------------------------------
import getopt

graphics = False

try:
  opts, args = getopt.gnu_getopt(sys.argv[1:], "", ["graphics"])
  if ('--graphics','') in opts:
    graphics = True

except getopt.GetoptError:
  pass

temporal_pooler_use_case(graphics)

