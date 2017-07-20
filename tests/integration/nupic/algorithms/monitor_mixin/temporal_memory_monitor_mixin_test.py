# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

import unittest

from nupic.algorithms.monitor_mixin.temporal_memory_monitor_mixin import (
  TemporalMemoryMonitorMixin)
from nupic.algorithms.temporal_memory import TemporalMemory
from nupic.data.generators.pattern_machine import ConsecutivePatternMachine
from nupic.data.generators.sequence_machine import SequenceMachine
class MonitoredTemporalMemory(TemporalMemoryMonitorMixin, TemporalMemory): pass



class TemporalMemoryMonitorMixinTest(unittest.TestCase):


  def setUp(self):
    self.patternMachine = ConsecutivePatternMachine(100, 5)
    self.sequenceMachine = SequenceMachine(self.patternMachine)

    self.tm = MonitoredTemporalMemory(columnDimensions=[100],
                                      cellsPerColumn=4,
                                      initialPermanence=0.6,
                                      connectedPermanence=0.5,
                                      minThreshold=1,
                                      maxNewSynapseCount=6,
                                      permanenceIncrement=0.1,
                                      permanenceDecrement=0.05,
                                      activationThreshold=1)


  def testFeedSequence(self):
    sequence = self._generateSequence()
    sequenceLength = len(sequence) - 3  # without resets

    # Replace last pattern (before the None) with an unpredicted one
    sequence[-2] = self.patternMachine.get(4)

    self._feedSequence(sequence, sequenceLabel="Test")

    activeColumnsTrace = self.tm.mmGetTraceActiveColumns()
    predictiveCellsTrace = self.tm.mmGetTracePredictiveCells()
    sequenceLabelsTrace = self.tm.mmGetTraceSequenceLabels()
    resetsTrace = self.tm.mmGetTraceResets()
    predictedActiveCellsTrace = self.tm.mmGetTracePredictedActiveCells()
    predictedInactiveCellsTrace = self.tm.mmGetTracePredictedInactiveCells()
    predictedActiveColumnsTrace = self.tm.mmGetTracePredictedActiveColumns()
    predictedInactiveColumnsTrace = self.tm.mmGetTracePredictedInactiveColumns()
    unpredictedActiveColumnsTrace = self.tm.mmGetTraceUnpredictedActiveColumns()

    self.assertEqual(len(activeColumnsTrace.data), sequenceLength)
    self.assertEqual(len(predictiveCellsTrace.data), sequenceLength)
    self.assertEqual(len(sequenceLabelsTrace.data), sequenceLength)
    self.assertEqual(len(resetsTrace.data), sequenceLength)
    self.assertEqual(len(predictedActiveCellsTrace.data), sequenceLength)
    self.assertEqual(len(predictedInactiveCellsTrace.data), sequenceLength)
    self.assertEqual(len(predictedActiveColumnsTrace.data), sequenceLength)
    self.assertEqual(len(predictedInactiveColumnsTrace.data), sequenceLength)
    self.assertEqual(len(unpredictedActiveColumnsTrace.data), sequenceLength)

    self.assertEqual(activeColumnsTrace.data[-1], self.patternMachine.get(4))
    self.assertEqual(sequenceLabelsTrace.data[-1], "Test")
    self.assertEqual(resetsTrace.data[0], True)
    self.assertEqual(resetsTrace.data[1], False)
    self.assertEqual(resetsTrace.data[10], True)
    self.assertEqual(resetsTrace.data[-1], False)
    self.assertEqual(len(predictedActiveCellsTrace.data[-2]), 5)
    self.assertEqual(len(predictedActiveCellsTrace.data[-1]), 0)
    self.assertEqual(len(predictedInactiveCellsTrace.data[-2]), 0)
    self.assertEqual(len(predictedInactiveCellsTrace.data[-1]), 5)
    self.assertEqual(len(predictedActiveColumnsTrace.data[-2]), 5)
    self.assertEqual(len(predictedActiveColumnsTrace.data[-1]), 0)
    self.assertEqual(len(predictedInactiveColumnsTrace.data[-2]), 0)
    self.assertEqual(len(predictedInactiveColumnsTrace.data[-1]), 5)
    self.assertEqual(len(unpredictedActiveColumnsTrace.data[-2]), 0)
    self.assertEqual(len(unpredictedActiveColumnsTrace.data[-1]), 5)


  def testClearHistory(self):
    sequence = self._generateSequence()
    self._feedSequence(sequence, sequenceLabel="Test")
    self.tm.mmClearHistory()

    activeColumnsTrace = self.tm.mmGetTraceActiveColumns()
    predictiveCellsTrace = self.tm.mmGetTracePredictiveCells()
    sequenceLabelsTrace = self.tm.mmGetTraceSequenceLabels()
    resetsTrace = self.tm.mmGetTraceResets()
    predictedActiveCellsTrace = self.tm.mmGetTracePredictedActiveCells()
    predictedInactiveCellsTrace = self.tm.mmGetTracePredictedInactiveCells()
    predictedActiveColumnsTrace = self.tm.mmGetTracePredictedActiveColumns()
    predictedInactiveColumnsTrace = self.tm.mmGetTracePredictedInactiveColumns()
    unpredictedActiveColumnsTrace = self.tm.mmGetTraceUnpredictedActiveColumns()

    self.assertEqual(len(activeColumnsTrace.data), 0)
    self.assertEqual(len(predictiveCellsTrace.data), 0)
    self.assertEqual(len(sequenceLabelsTrace.data), 0)
    self.assertEqual(len(resetsTrace.data), 0)
    self.assertEqual(len(predictedActiveCellsTrace.data), 0)
    self.assertEqual(len(predictedInactiveCellsTrace.data), 0)
    self.assertEqual(len(predictedActiveColumnsTrace.data), 0)
    self.assertEqual(len(predictedInactiveColumnsTrace.data), 0)
    self.assertEqual(len(unpredictedActiveColumnsTrace.data), 0)


  def testSequencesMetrics(self):
    sequence = self._generateSequence()
    self._feedSequence(sequence, "Test1")

    sequence.reverse()
    sequence.append(sequence.pop(0))  # Move None (reset) to the end
    self._feedSequence(sequence, "Test2")

    sequencesPredictedActiveCellsPerColumnMetric = \
      self.tm.mmGetMetricSequencesPredictedActiveCellsPerColumn()
    sequencesPredictedActiveCellsSharedMetric = \
      self.tm.mmGetMetricSequencesPredictedActiveCellsShared()

    self.assertEqual(sequencesPredictedActiveCellsPerColumnMetric.mean, 1)
    self.assertEqual(sequencesPredictedActiveCellsSharedMetric.mean, 1)

    self._feedSequence(sequence, "Test3")

    sequencesPredictedActiveCellsPerColumnMetric = \
      self.tm.mmGetMetricSequencesPredictedActiveCellsPerColumn()
    sequencesPredictedActiveCellsSharedMetric = \
      self.tm.mmGetMetricSequencesPredictedActiveCellsShared()

    self.assertEqual(sequencesPredictedActiveCellsPerColumnMetric.mean, 1)
    self.assertTrue(sequencesPredictedActiveCellsSharedMetric.mean > 1)


  # ==============================
  # Helper functions
  # ==============================

  def _generateSequence(self):
    numbers = range(0, 10)
    sequence = self.sequenceMachine.generateFromNumbers(numbers)
    sequence.append(None)
    sequence *= 3

    return sequence


  def _feedSequence(self, sequence, sequenceLabel=None):
    for pattern in sequence:
      if pattern is None:
        self.tm.reset()
      else:
        self.tm.compute(pattern, sequenceLabel=sequenceLabel)



if __name__ == "__main__":
  unittest.main()
