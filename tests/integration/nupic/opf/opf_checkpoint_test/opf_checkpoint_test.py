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

import csv
import os
import shutil

from nupic.data.file_record_stream import FileRecordStream
from nupic.frameworks.opf.experiment_runner import runExperiment, getCheckpointParentDir
from nupic.support import initLogging
from nupic.support.unittesthelpers.testcasebase import (
    unittest, TestCaseBase as HelperTestCaseBase)

try:
  import capnp
except ImportError:
  capnp = None

_EXPERIMENT_BASE = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "experiments")



class MyTestCaseBase(HelperTestCaseBase):


  def shortDescription(self):
    """ Override to force unittest framework to use test method names instead
    of docstrings in the report.
    """
    return None


  def compareOPFPredictionFiles(self, path1, path2, temporal,
                                maxMismatches=None):
    """ Compare temporal or non-temporal predictions for the given experiment
    that just finished executing

    experimentName:     e.g., "gym"; this string will be used to form
                        a directory path to the experiments.

    maxMismatches:      Maximum number of row mismatches to report before
                        terminating the comparison; None means: report all
                        mismatches

    Returns:            True if equal; False if different
    """

    experimentLabel = "%s prediction comparison" % \
                        ("Temporal" if temporal else "Non-Temporal")

    print "%s: Performing comparison of OPF prediction CSV files %r and %r" % (
            experimentLabel, path1, path2)

    # Open CSV readers
    #
    self.assertTrue(
      os.path.isfile(path1),
      msg="OPF prediction file path1 %s doesn't exist or is not a file" % (
            path1))

    (opf1CsvReader, opf1FieldNames) = self._openOpfPredictionCsvFile(path1)


    self.assertTrue(
      os.path.isfile(path2),
      msg="OPF prediction file path2 %s doesn't exist or is not a file" % (
            path2))

    (opf2CsvReader, opf2FieldNames) = self._openOpfPredictionCsvFile(path2)

    self.assertEqual(len(opf1FieldNames), len(opf2FieldNames),
                    ("%s: Mismatch in number of prediction columns: "
                     "opf1: %s, opf2: %s") % (
                      experimentLabel, len(opf1FieldNames),
                         len(opf2FieldNames)))

    self.assertEqual(opf1FieldNames, opf2FieldNames)


    # Each data row is assumed to be arranged as follows:
    #
    #   reset, actual-field1, prediction-field1, actual-field2,
    #   prediction-field2, etc.
    #
    # Presently, we only compare the predicted values that need to match.

    opf1EOF = False
    opf2EOF = False

    opf1CurrentDataRowIndex = -1
    opf2CurrentDataRowIndex = -1

    if temporal:
      # Skip the first data rows for temporal tests, since they don't contain
      # prediction values.
      _skipOpf1Row = opf1CsvReader.next()
      opf1CurrentDataRowIndex += 1
      _skipOpf2Row = opf2CsvReader.next()
      opf2CurrentDataRowIndex += 1


    fieldsIndexesToCompare = tuple(xrange(2, len(opf1FieldNames), 2))

    self.assertGreater(len(fieldsIndexesToCompare), 0)

    print ("%s: Comparing fields at indexes: %s; "
           "opf1Labels: %s; opf2Labels: %s") % (
            experimentLabel,
            fieldsIndexesToCompare,
            [opf1FieldNames[i] for i in fieldsIndexesToCompare],
            [opf2FieldNames[i] for i in fieldsIndexesToCompare])


    for i in fieldsIndexesToCompare:
      self.assertTrue(opf1FieldNames[i].endswith("predicted"),
                      msg="%r doesn't end with 'predicted'" % opf1FieldNames[i])
      self.assertTrue(opf2FieldNames[i].endswith("predicted"),
                      msg="%r doesn't end with 'predicted'" % opf2FieldNames[i])

    mismatchCount = 0

    while True:

      try:
        opf1Row = opf1CsvReader.next()
      except StopIteration:
        opf1EOF = True
      else:
        opf1CurrentDataRowIndex += 1

      try:
        opf2Row = opf2CsvReader.next()
      except StopIteration:
        opf2EOF = True
      else:
        opf2CurrentDataRowIndex += 1

      if opf1EOF != opf2EOF:
        print ("%s: ERROR: Data row counts mismatch: "
               "opf1EOF: %s, opf1CurrentDataRowIndex: %s; "
               "opf2EOF: %s, opf2CurrentDataRowIndex: %s") % (
                  experimentLabel,
                  opf1EOF, opf1CurrentDataRowIndex,
                  opf2EOF, opf2CurrentDataRowIndex)
        return False

      if opf1EOF and opf2EOF:
        # Done with both prediction datasets
        break

      # Compare the rows
      self.assertEqual(len(opf1Row), len(opf2Row))

      for i in fieldsIndexesToCompare:
        opf1FloatValue = float(opf1Row[i])
        opf2FloatValue = float(opf2Row[i])

        if opf1FloatValue != opf2FloatValue:

          mismatchCount += 1

          print ("%s: ERROR: mismatch in "
           "prediction values: dataRowIndex: %s, fieldIndex: %s (%r); "
           "opf1FieldValue: <%s>, opf2FieldValue: <%s>; "
           "opf1FieldValueAsFloat: %s, opf2FieldValueAsFloat: %s; "
           "opf1Row: %s, opf2Row: %s") % (
            experimentLabel,
            opf1CurrentDataRowIndex,
            i,
            opf1FieldNames[i],
            opf1Row[i],
            opf2Row[i],
            opf1FloatValue,
            opf2FloatValue,
            opf1Row,
            opf2Row)

          # Stop comparison if we exceeded the allowed number of mismatches
          if maxMismatches is not None and mismatchCount >= maxMismatches:
            break


    if mismatchCount != 0:
      print "%s: ERROR: there were %s mismatches between %r and %r" % (
              experimentLabel, mismatchCount, path1, path2)
      return False


    # A difference here would indicate a logic error in this method
    self.assertEqual(opf1CurrentDataRowIndex, opf2CurrentDataRowIndex)


    print ("%s: Comparison of predictions "
           "completed: OK; number of prediction rows examined: %s; "
           "path1: %r; path2: %r") % \
              (experimentLabel,
               opf1CurrentDataRowIndex + 1,
               path1,
               path2)

    return True


  def _openOpfPredictionCsvFile(self, filepath):
    """ Open an OPF prediction CSV file and advance it to the first data row

    Returns:      the tuple (csvReader, fieldNames), where 'csvReader' is the
                  csv reader object, and 'fieldNames' is a sequence of field
                  names.
    """
    # Open the OPF prediction file
    csvReader = self._openCsvFile(filepath)

    # Advance it past the three NUPIC header lines
    names = csvReader.next()
    _types = csvReader.next()
    _specials = csvReader.next()

    return (csvReader, names)


  @staticmethod
  def _openCsvFile(filepath):
    # We'll be operating on csvs with arbitrarily long fields
    size = 2**27
    csv.field_size_limit(size)

    rawFileObj = open(filepath, 'r')

    csvReader = csv.reader(rawFileObj, dialect='excel')

    return csvReader


  def _createExperimentArgs(self, experimentDir,
                            newSerialization=False,
                            additionalArgs=()):
    args = []
    args.append(experimentDir)
    if newSerialization:
      args.append("--newSerialization")
    args += additionalArgs
    return args


  def _testSamePredictions(self, experiment, predSteps, checkpointAt,
                           predictionsFilename, additionalFields=None,
                           newSerialization=False):
    """ Test that we get the same predictions out from the following two
    scenarios:

    a_plus_b: Run the network for 'a' iterations followed by 'b' iterations
    a, followed by b: Run the network for 'a' iterations, save it, load it
                      back in, then run for 'b' iterations.

    Parameters:
    -----------------------------------------------------------------------
    experiment:   base directory of the experiment. This directory should
                    contain the following:
                        base.py
                        a_plus_b/description.py
                        a/description.py
                        b/description.py
                    The sub-directory description files should import the
                    base.py and only change the first and last record used
                    from the data file.
    predSteps:   Number of steps ahead predictions are for
    checkpointAt: Number of iterations that 'a' runs for.
                 IMPORTANT: This must match the number of records that
                 a/description.py runs for - it is NOT dynamically stuffed into
                 the a/description.py.
    predictionsFilename: The name of the predictions file that the OPF
                  generates for this experiment (for example
                  'DefaulTask.NontemporalMultiStep.predictionLog.csv')
    newSerialization: Whether to use new capnproto serialization.
    """

    # Get the 3 sub-experiment directories
    aPlusBExpDir = os.path.join(_EXPERIMENT_BASE, experiment, "a_plus_b")
    aExpDir = os.path.join(_EXPERIMENT_BASE, experiment, "a")
    bExpDir = os.path.join(_EXPERIMENT_BASE, experiment, "b")

    # Run a+b
    args = self._createExperimentArgs(aPlusBExpDir,
                                      newSerialization=newSerialization)
    _aPlusBExp = runExperiment(args)

    # Run a, the copy the saved checkpoint into the b directory
    args = self._createExperimentArgs(aExpDir,
                                      newSerialization=newSerialization)
    _aExp = runExperiment(args)
    if os.path.exists(os.path.join(bExpDir, 'savedmodels')):
      shutil.rmtree(os.path.join(bExpDir, 'savedmodels'))
    shutil.copytree(src=os.path.join(aExpDir, 'savedmodels'),
                    dst=os.path.join(bExpDir, 'savedmodels'))

    args = self._createExperimentArgs(bExpDir,
                                      newSerialization=newSerialization,
                                      additionalArgs=['--load=DefaultTask'])
    _bExp = runExperiment(args)

    # Now, compare the predictions at the end of a+b to those in b.
    aPlusBPred = FileRecordStream(os.path.join(aPlusBExpDir, 'inference',
                                   predictionsFilename))
    bPred = FileRecordStream(os.path.join(bExpDir, 'inference',
                                   predictionsFilename))

    colNames = [x[0] for x in aPlusBPred.getFields()]
    actValueColIdx = colNames.index('multiStepPredictions.actual')
    predValueColIdx = colNames.index('multiStepPredictions.%d' % (predSteps))

    # Skip past the 'a' records in aPlusB
    for i in range(checkpointAt):
      aPlusBPred.next()

    # Now, read through the records that don't have predictions yet
    for i in range(predSteps):
      aPlusBPred.next()
      bPred.next()

    # Now, compare predictions in the two files
    rowIdx = checkpointAt + predSteps + 4 - 1
    epsilon = 0.0001
    while True:
      rowIdx += 1
      try:
        rowAPB = aPlusBPred.next()
        rowB = bPred.next()

        # Compare actuals
        self.assertEqual(rowAPB[actValueColIdx], rowB[actValueColIdx],
              "Mismatch in actual values: row %d of a+b has %s and row %d of "
              "b has %s" % (rowIdx, rowAPB[actValueColIdx], rowIdx-checkpointAt,
                            rowB[actValueColIdx]))

        # Compare predictions, within nearest epsilon
        predAPB = eval(rowAPB[predValueColIdx])
        predB = eval(rowB[predValueColIdx])

        # Sort with highest probabilities first
        predAPB = [(a, b) for b, a in predAPB.items()]
        predB = [(a, b) for b, a in predB.items()]
        predAPB.sort(reverse=True)
        predB.sort(reverse=True)

        if additionalFields is not None:
          for additionalField in additionalFields:
            fieldIdx = colNames.index(additionalField)
            self.assertEqual(rowAPB[fieldIdx], rowB[fieldIdx],
              "Mismatch in field \'%s\' values: row %d of a+b has value: (%s)\n"
              " and row %d of b has value: %s" % \
              (additionalField, rowIdx, rowAPB[fieldIdx],
                rowIdx-checkpointAt, rowB[fieldIdx]))

        self.assertEqual(len(predAPB), len(predB),
              "Mismatch in predicted values: row %d of a+b has %d predictions: "
              "\n  (%s) and row %d of b has %d predictions:\n  (%s)" % \
              (rowIdx, len(predAPB), predAPB, rowIdx-checkpointAt, len(predB),
               predB))

        for i in range(len(predAPB)):
          (aProb, aValue) = predAPB[i]
          (bProb, bValue) = predB[i]
          self.assertLess(abs(aValue-bValue), epsilon,
              "Mismatch in predicted values: row %d of a+b predicts value %s "
              "and row %d of b predicts %s" % (rowIdx, aValue,
                                               rowIdx-checkpointAt, bValue))
          self.assertLess(abs(aProb-bProb), epsilon,
              "Mismatch in probabilities: row %d of a+b predicts %s with "
              "probability %s and row %d of b predicts %s with probability %s" \
               % (rowIdx, aValue, aProb, rowIdx-checkpointAt, bValue, bProb))

      except StopIteration:
        break

    # clean up model checkpoint directories
    shutil.rmtree(getCheckpointParentDir(aExpDir))
    shutil.rmtree(getCheckpointParentDir(bExpDir))
    shutil.rmtree(getCheckpointParentDir(aPlusBExpDir))

    print "Predictions match!"


  @staticmethod
  def _testBackwardsCompatibility(experiment, checkpointName):
    """ Test that we can load in a checkpoint saved by an earlier version of
    the OPF.

    Parameters:
    -----------------------------------------------------------------------
    experiment:       Directory of the experiment.
    checkpointName:   which checkpoint to verify
    """

    # Get the experiment directories
    expDir = os.path.join(_EXPERIMENT_BASE, experiment)

    # Copy the pertinent checkpoint
    if os.path.exists(os.path.join(expDir, 'savedmodels')):
      shutil.rmtree(os.path.join(expDir, 'savedmodels'))
    shutil.copytree(src=os.path.join(expDir, checkpointName),
                    dst=os.path.join(expDir, 'savedmodels'))

    # Run it from the checkpoint
    _aPlusBExp = runExperiment(args=[expDir, '--load=DefaultTask',
                                     '--noCheckpoint'])


class PositiveTests(MyTestCaseBase):


  def test_NonTemporalMultiStep(self):
    """ Test that we get the same predictions out of a model that was
    saved and reloaded from a checkpoint as we do from one that runs
    continuously.
    """

    self._testSamePredictions(
        experiment="non_temporal_multi_step", predSteps=24, checkpointAt=250,
        predictionsFilename=
        "DefaultTask.NontemporalMultiStep.predictionLog.csv")


  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def test_NonTemporalMultiStepNew(self):
    """ Test that we get the same predictions out of a model that was
    saved and reloaded from a checkpoint as we do from one that runs
    continuously.

    Uses new capnproto serialization.
    """

    self._testSamePredictions(
        experiment="non_temporal_multi_step", predSteps=24, checkpointAt=250,
        predictionsFilename=
        "DefaultTask.NontemporalMultiStep.predictionLog.csv",
        newSerialization=True)


  @unittest.skip("Currently Fails: NUP-1864")
  def test_TemporalMultiStep(self):
    """ Test that we get the same predictions out of a model that was
    saved and reloaded from a checkpoint as we do from one that runs
    continuously.
    """

    self._testSamePredictions(experiment="temporal_multi_step", predSteps=24,
      checkpointAt=250,
      predictionsFilename='DefaultTask.TemporalMultiStep.predictionLog.csv')


  @unittest.skip("Currently Fails: NUP-1864")
  def test_TemporalAnomaly(self):
    """ Test that we get the same predictions out of a model that was
    saved and reloaded from a checkpoint as we do from one that runs
    continuously.
    """

    self._testSamePredictions(experiment="temporal_anomaly", predSteps=1,
      checkpointAt=250,
      predictionsFilename='DefaultTask.TemporalAnomaly.predictionLog.csv',
      additionalFields=['anomalyScore'])


  @unittest.skip("We aren't currently supporting serialization backward "
                 "compatibility")
  def test_BackwardsCompatibility(self):
    """ Test that we can load in a checkpoint saved by an earlier version of
    the OPF.
    """

    self._testBackwardsCompatibility(
          os.path.join('backwards_compatibility', 'a'),
          'savedmodels_2012-10-05')



if __name__ == "__main__":
  initLogging(verbose=True)

  unittest.main()
