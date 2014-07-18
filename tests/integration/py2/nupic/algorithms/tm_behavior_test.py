#!/usr/bin/env python
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
# along with this program.  If not, see httm://www.gnu.org/licenses.
#
# httm://numenta.org/licenses/
# ----------------------------------------------------------------------

import argparse
import pprint
import sys
import unittest

import numpy

from nupic.research.TM import TM



SHOW_ENABLED = False



# ==============================
# Tests
# ==============================

class TemporalMemoryBehaviorTest(unittest.TestCase):

  def testA(self):
    showTest("Basic first order sequences")
    tm = newTM()
    p = generatePatterns(tm.connections.numberOfColumns())

    showSegments(tm)
    sequence = [p[0], p[1], p[2], p[3]]
    feedTM(tm, sequence)

    sequence = [p[0], p[1], p[2]]
    feedTM(tm, sequence, reset=False, learn=False)
    self.assertEqual(len(getPredictions(tm)), 0)
    resetTM(tm)

    sequence = [p[0], p[1], p[2], p[3]]
    feedTM(tm, sequence, num=2)

    sequence = [p[0]]
    feedTM(tm, sequence, reset=False)
    self.assertEqual(len(getPredictions(tm)), 1)
    sequence = [p[1]]
    feedTM(tm, sequence, reset=False)
    sequence = [p[2]]
    feedTM(tm, sequence, reset=False)
    sequence = [p[3]]
    feedTM(tm, sequence, reset=False)
    resetTM(tm)

    sequence = [p[0], p[1], p[2], p[3]]
    feedTM(tm, sequence, num=3)

    sequence = [p[0]]
    feedTM(tm, sequence, reset=False, learn=False)
    sequence = [p[1]]
    feedTM(tm, sequence, reset=False, learn=False)
    sequence = [p[2]]
    feedTM(tm, sequence, reset=False, learn=False)
    resetTM(tm)

    sequence = [p[0], p[1], p[2], p[3]]
    feedTM(tm, sequence, num=5)

    sequence = [p[0], p[1], p[2]]
    feedTM(tm, sequence, reset=False, learn=False)
    self.assertEqual(len(getPredictions(tm)), 1)
    resetTM(tm)


  def testB(self):
    showTest("High order sequences")
    tm = newTM()
    p = generatePatterns(tm.connections.numberOfColumns())

    sequence = [p[0], p[1], p[2], p[3]]
    feedTM(tm, sequence, num=5)

    sequence = [p[1], p[2]]
    feedTM(tm, sequence, reset=False, learn=False)
    self.assertEqual(len(getPredictions(tm)), 1)
    resetTM(tm)

    sequence = [p[4], p[1], p[2], p[5]]
    feedTM(tm, sequence, num=5)

    sequence = [p[1], p[2]]
    feedTM(tm, sequence, reset=False, learn=False)
    self.assertEqual(len(getPredictions(tm)), 2)
    resetTM(tm)

    sequence = [p[0], p[1], p[2]]
    feedTM(tm, sequence, reset=False, learn=False)
    self.assertEqual(len(getPredictions(tm)), 1)
    resetTM(tm)


# ==============================
# TM
# ==============================

def newTM(overrides=None):
  params = {
    "columnDimensions": [6],
    "cellsPerColumn": 4,
    "initialPermanence": 0.3,
    "connectedPermanence": 0.5,
    "minThreshold": 1,
    "maxNewSynapseCount": 6,
    "permanenceIncrement": 0.1,
    "permanenceDecrement": 0.05,
    "activationThreshold": 1
  }
  params.update(overrides or {})
  tm = TM(**params)
  show("Initialized new TM with parameters:")
  show(pprint.pformat(params), newline=True)
  return tm


def feedTM(tm, sequence, learn=True, reset=True, num=1):
  showInput(sequence, learn=learn, reset=reset, num=num)

  for _ in range(num):
    for element in sequence:
      tm.compute(element, learn=learn)
    if reset:
      tm.reset()

  if learn:
    showSegments(tm)

  if not reset:
    showActivations(tm)
    showPredictions(tm)

    noteText = "(connectedPermanence: {0})".format(tm.connectedPermanence)
    show(noteText, newline=True)


def resetTM(tm):
  tm.reset()
  showReset()


def groupCellsByColumns(tm, cells):
  groups = dict()

  for cell in sorted(cells):
    col = tm.connections.columnForCell(cell)
    if not col in groups:
      groups[col] = []
    groups[col].append(cell)

  return groups


def getPredictions(tm):
  return groupCellsByColumns(tm, tm.predictiveCells)


def getActivations(tm):
  return groupCellsByColumns(tm, tm.activeCells)


# ==============================
# Patterns
# ==============================

def generatePatterns(length):
  patterns = []

  for i in range(length):
    patterns.append({i})

  return patterns


def getCodeForIndex(index):
  return chr(int(index) + 65)


def getCodeForPattern(pattern):
  return getCodeForIndex(list(pattern)[0])


# ==============================
# Show
# ==============================

def show(text, newline=False):
  if SHOW_ENABLED:
    print text
    if newline:
      print


def showTest(text):
  show(("\n"
        "====================================\n"
        "Test: {0}\n"
        "===================================="
       ).format(text))


def showPatterns(patterns):
  show("Patterns: ")
  for pattern in patterns:
    show("{0}: {1}".format(getCodeForPattern(pattern), pattern))
  show("")


def showInput(sequence, reset=True, learn=True, num=1):
  sequenceText = ", ".join([getCodeForPattern(element) for element in sequence])
  resetText = ", reset" if reset else ""
  learnText = "(learning {0})".format("enabled" if learn else "disabled")
  numText = "[{0} times]".format(num) if num > 1 else ""
  show("Feeding sequence: {0}{1} {2} {3}".format(
       sequenceText, resetText, learnText, numText),
       newline=True)


def showSegments(tm):
  show("Segments: (format => "
       "{segment: [(source column, source cell, permanence), ...]) ")
  show("------------------------------------")

  columns = range(tm.connections.numberOfColumns())

  for column in columns:
    cells = tm.connections.cellsForColumn(column)

    for cell in cells:
      segmentDict = dict()

      for seg in tm.connections.segmentsForCell(cell):
        synapseList = []

        for synapse in tm.connections.synapsesForSegment(seg):
          (_, sourceCell, permanence) = tm.connections.dataForSynapse(synapse)
          synapseList.append((column, sourceCell, permanence))

        segmentDict[seg] = synapseList

      show("Column {0} ({1}) / Cell {2}:\t{3}".format(
        column, getCodeForIndex(column), cell, segmentDict))

    if column < len(columns) - 1:  # not last
      show("")

  show("------------------------------------", newline=True)


def showTMState(state, label):
  text = ", ".join(
    ["{0} (cells: {1})".format(
     getCodeForIndex(i),
     ", ".join([str(c) for c in cells]))
       for (i, cells) in state.iteritems()])
  text = text or "None"

  show("{0} ({1}): {2}".format(
    label, len(state), text))


def showPredictions(tm):
  showTMState(getPredictions(tm), "Predictions")


def showActivations(tm):
  showTMState(getActivations(tm), "Activations")


def showReset():
  show("TM reset.", newline=True)


# ==============================
# Main
# ==============================

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--show', default=False, action='store_true')
  parser.add_argument('unittest_args', nargs='*')

  args = parser.parse_args()
  SHOW_ENABLED = args.show

  unitArgv = [sys.argv[0]] + args.unittest_args
  unittest.main(argv=unitArgv)
