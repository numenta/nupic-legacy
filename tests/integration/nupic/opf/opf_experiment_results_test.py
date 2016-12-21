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

"""
## @file
This file tests specific experiments to see if they are providing the
correct results. These are high level tests of the algorithms themselves.
"""

import os
import shutil
from subprocess import call
import time
import unittest2 as unittest
from pkg_resources import resource_filename


from nupic.data.file_record_stream import FileRecordStream



class OPFExperimentResultsTest(unittest.TestCase):


  def testExperimentResults(self):
    """Run specific experiments and verify that they are producing the correct
    results.

    opfDir is the examples/opf directory in the install path
    and is used to find run_opf_experiment.py

    The testdir is the directory that contains the experiments we will be
    running. When running in the auto-build setup, this will be a temporary
    directory that has had this script, as well as the specific experiments
    we will be running, copied into it by the qa/autotest/prediction_results.py
    script.
    When running stand-alone from the command line, this will point to the
    examples/prediction directory in the install tree (same as predictionDir)

    """

    nupic_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "..", "..", "..", "..")

    opfDir = os.path.join(nupic_dir, "examples", "opf")

    testDir = opfDir

    # The testdir is the directory that contains the experiments we will be
    #  running. When running in the auto-build setup, this will be a temporary
    #  directory that has had this script, as well as the specific experiments
    #  we will be running, copied into it by the
    #  qa/autotest/prediction_results.py script.
    # When running stand-alone from the command line, we can simply point to the
    #  examples/prediction directory in the install tree.
    if not os.path.exists(os.path.join(testDir, "experiments/classification")):
      testDir = opfDir

    # Generate any dynamically generated datasets now
    command = ['python', os.path.join(testDir, 'experiments', 'classification',
                                       'makeDatasets.py')]
    retval = call(command)
    self.assertEqual(retval, 0)


    # Generate any dynamically generated datasets now
    command = ['python', os.path.join(testDir, 'experiments', 'multistep',
                                       'make_datasets.py')]
    retval = call(command)
    self.assertEqual(retval, 0)


    # Generate any dynamically generated datasets now
    command = ['python', os.path.join(testDir, 'experiments',
                                'spatial_classification', 'make_datasets.py')]
    retval = call(command)
    self.assertEqual(retval, 0)


    # Run from the test directory so that we can find our experiments
    os.chdir(testDir)

    runExperiment = os.path.join(nupic_dir, "scripts", "run_opf_experiment.py")

    # A list of experiments to run.  Valid attributes:
    #   experimentDir - Required, path to the experiment directory containing
    #                       description.py
    #   args          - optional. List of arguments for run_opf_experiment
    #   results       - A dictionary of expected results. The keys are tuples
    #                    containing (predictionLogFileName, columnName). The
    #                    value is a (min, max) expected value from the last row
    #                    in the prediction log.
    multistepTests = [
      # For this one, in theory the error for 1 step should be < 0.20
      { 'experimentDir': 'experiments/multistep/simple_0',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=1:window=200:field=field1"):
                    (0.0, 0.20),
        }
      },

      # For this one, in theory the error for 1 step should be < 0.50, but we
      #  get slightly higher because our sample size is smaller than ideal
      { 'experimentDir': 'experiments/multistep/simple_0_f2',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='aae':steps=1:window=200:field=field2"):
                    (0.0, 0.66),
        }
      },

      # For this one, in theory the error for 1 step should be < 0.20
      { 'experimentDir': 'experiments/multistep/simple_1',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=1:window=200:field=field1"):
                    (0.0, 0.20),
        }
      },

      # For this test, we haven't figured out the theoretical error, this
      #  error is determined empirically from actual results
      { 'experimentDir': 'experiments/multistep/simple_1_f2',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='aae':steps=1:window=200:field=field2"):
                    (0.0, 3.76),
        }
      },

      # For this one, in theory the error for 1 step should be < 0.20, but we
      #  get slightly higher because our sample size is smaller than ideal
      { 'experimentDir': 'experiments/multistep/simple_2',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=1:window=200:field=field1"):
                    (0.0, 0.31),
        }
      },

      # For this one, in theory the error for 1 step should be < 0.10 and for
      #  3 step < 0.30, but our actual results are better.
      { 'experimentDir': 'experiments/multistep/simple_3',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=1:window=200:field=field1"):
                    (0.0, 0.06),
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=3:window=200:field=field1"):
                    (0.0, 0.20),
        }
      },

      # For this test, we haven't figured out the theoretical error, this
      #  error is determined empirically from actual results
      { 'experimentDir': 'experiments/multistep/simple_3_f2',
        'results': {
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='aae':steps=1:window=200:field=field2"):
                    (0.0, 0.6),
          ('DefaultTask.TemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='aae':steps=3:window=200:field=field2"):
                    (0.0, 1.8),
        }
      },

      # Test missing record support.
      # Should have 0 error by the end of the dataset
      { 'experimentDir': 'experiments/missing_record/simple_0',
        'results': {
          ('DefaultTask.NontemporalMultiStep.predictionLog.csv',
           "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=1:window=25:field=field1"):
                    (1.0, 1.0),
        }
      },

    ] # end of multistepTests

    classificationTests = [
      # ----------------------------------------------------------------------
      # Classification Experiments
      { 'experimentDir': 'experiments/classification/category_hub_TP_0',
        'results': {
            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classification:avg_err:window=200'): (0.0, 0.020),
            }
      },

      { 'experimentDir': 'experiments/classification/category_TP_0',
        'results': {
            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classification:avg_err:window=200'): (0.0, 0.045),

            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classConfidences:neg_auc:computeEvery=10:window=200'): (-1.0, -0.98),
            }
      },

      { 'experimentDir': 'experiments/classification/category_TP_1',
        'results': {
            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classification:avg_err:window=200'): (0.0, 0.005),
            }
      },

      { 'experimentDir': 'experiments/classification/scalar_TP_0',
        'results': {
            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classification:avg_err:window=200'): (0.0, 0.155),

            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classConfidences:neg_auc:computeEvery=10:window=200'): (-1.0, -0.900),
            }
      },

      { 'experimentDir': 'experiments/classification/scalar_TP_1',
        'results': {
            ('OnlineLearning.TemporalClassification.predictionLog.csv',
             'classification:avg_err:window=200'):  (0.0, 0.03),
            }
      },

    ] # End of classification tests
    
    spatialClassificationTests = [
      { 'experimentDir': 'experiments/spatial_classification/category_0',
        'results': {
            ('DefaultTask.NontemporalClassification.predictionLog.csv',
             "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=0:window=100:field=classification"): 
                    (0.0, 0.05),
            }

      },

      { 'experimentDir': 'experiments/spatial_classification/category_1',
        'results': {
            ('DefaultTask.NontemporalClassification.predictionLog.csv',
             "multiStepBestPredictions:multiStep:errorMetric='avg_err':steps=0:window=100:field=classification"): 
                    (0.0, 0.0),
            }
      },
      
      { 'experimentDir': 'experiments/spatial_classification/scalar_0',
        'results': {
            ('DefaultTask.NontemporalClassification.predictionLog.csv',
             "multiStepBestPredictions:multiStep:errorMetric='aae':steps=0:window=100:field=classification"): 
                    (0.0, 0.025),
            }
      },

      { 'experimentDir': 'experiments/spatial_classification/scalar_1',
        'results': {
            ('DefaultTask.NontemporalClassification.predictionLog.csv',
             "multiStepBestPredictions:multiStep:errorMetric='aae':steps=0:window=100:field=classification"): 
                    (-1e-10, 0.01),
            }
      },


    ]

    anomalyTests = [
      # ----------------------------------------------------------------------
      # Classification Experiments
      { 'experimentDir': 'experiments/anomaly/temporal/simple',
        'results': {
            ('DefaultTask.TemporalAnomaly.predictionLog.csv',
             'anomalyScore:passThruPrediction:window=1000:field=f'): (0.02,
                                                                      0.04),
          }
      },



    ] # End of anomaly tests

    tests = []
    tests += multistepTests
    tests += classificationTests
    tests += spatialClassificationTests
    tests += anomalyTests

    # Uncomment this to only run a specific experiment(s)
    #tests = tests[7:8]

    # This contains a list of tuples: (expDir, key, results)
    summaryOfResults = []
    startTime = time.time()

    testIdx = -1
    for test in tests:
      testIdx += 1
      expDirectory = test['experimentDir']

      # -------------------------------------------------------------------
      # Remove files/directories generated by previous tests:
      toDelete = []

      # Remove inference results
      path = os.path.join(expDirectory, "inference")
      toDelete.append(path)
      path = os.path.join(expDirectory, "savedmodels")
      toDelete.append(path)

      for path in toDelete:
        if not os.path.exists(path):
          continue
        print "Removing %s ..." % path
        if os.path.isfile(path):
          os.remove(path)
        else:
          shutil.rmtree(path)


      # ------------------------------------------------------------------------
      # Run the test.
      args = test.get('args', [])
      print "Running experiment %s ..." % (expDirectory)
      command = ['python', runExperiment, expDirectory] + args
      retVal = call(command)

      # If retVal is non-zero and this was not a negative test or if retVal is
      # zero and this is a negative test something went wrong.
      if retVal:
        print "Details of failed test: %s" % test
        print("TestIdx %d, OPF experiment '%s' failed with return code %i." %
              (testIdx, expDirectory, retVal))
      self.assertFalse(retVal)


      # -----------------------------------------------------------------------
      # Check the results
      for (key, expValues) in test['results'].items():
        (logFilename, colName) = key

        # Open the prediction log file
        logFile = FileRecordStream(os.path.join(expDirectory, 'inference',
                                                logFilename))
        colNames = [x[0] for x in logFile.getFields()]
        if not colName in colNames:
          print "TestIdx %d: %s not one of the columns in " \
            "prediction log file. Available column names are: %s" % (testIdx,
                    colName, colNames)
        self.assertTrue(colName in colNames)
        colIndex = colNames.index(colName)

        # Read till we get to the last line
        while True:
          try:
            row = logFile.next()
          except StopIteration:
            break
        result = row[colIndex]

        # Save summary of results
        summaryOfResults.append((expDirectory, colName, result))

        print "Actual result for %s, %s:" % (expDirectory, colName), result
        print "Expected range:", expValues
        failed = (expValues[0] is not None and result < expValues[0]) \
            or (expValues[1] is not None and result > expValues[1])
        if failed:
          print ("TestIdx %d: Experiment %s failed. \nThe actual result"
             " for %s (%s) was outside the allowed range of %s" % (testIdx,
              expDirectory, colName, result, expValues))
        else:
          print "  Within expected range."
        self.assertFalse(failed)


    # =======================================================================
    # Print summary of results:
    print
    print "Summary of results in all experiments run:"
    print "========================================="
    prevExpDir = None
    for (expDir, key, results) in summaryOfResults:
      if expDir != prevExpDir:
        print
        print expDir
        prevExpDir = expDir
      print "  %s: %s" % (key, results)

    print "\nElapsed time: %.1f seconds" % (time.time() - startTime)



if __name__ == "__main__":
  unittest.main()
