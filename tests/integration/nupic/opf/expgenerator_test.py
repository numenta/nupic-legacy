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

import copy
import imp
import json
import logging
from optparse import OptionParser
import os
import pprint
import shutil
import string
import subprocess
import sys

from pkg_resources import resource_filename
import unittest2 as unittest

from nupic.database.ClientJobsDAO import ClientJobsDAO
from nupic.support import aggregationDivide
from nupic.support.unittesthelpers.testcasebase import (
  TestCaseBase as HelperTestCaseBase)
from nupic.swarming import HypersearchWorker
from nupic.swarming.permutationhelpers import PermuteChoices
from nupic.swarming.utils import generatePersistentJobGUID, rCopy
from nupic.frameworks.opf.expdescriptionapi import OpfEnvironment
from nupic.swarming.exp_generator import ExpGenerator
from nupic.frameworks.opf.opfutils import (InferenceType,
                                           InferenceElement)

LOGGER = logging.getLogger(__name__)
HOTGYM_INPUT = "extra/hotgym/hotgym.csv"


g_debug = False

# Our __main__ entry block sets this to an instance of MyTestEnvironment()
g_myEnv = None



class MyTestEnvironment(object):

  def __init__(self, options):

    # Save all command line options
    self.options = options

    # Build installation root (e.g., ~/nupic/current)
    installRootDir = os.path.abspath(options.installDir)
    if not os.path.exists(installRootDir):
      raise RuntimeError("install directory %s doesn't exist" % \
                         (options.installDir))
    _debugOut("installRootDir=<%s>" % (installRootDir,))


    # Where this script is running from (autotest expgenerator_test.py may have
    # copied it from its original location)
    self.testRunDir = os.path.dirname(os.path.abspath(__file__))
    _debugOut("self.testRunDir=<%s>" % (self.testRunDir,))

    # Where to place generated files
    self.testOutDir = os.path.join(self.testRunDir, 'expGeneratorOut')
    shutil.rmtree(self.testOutDir, ignore_errors=True)
    os.makedirs(self.testOutDir)

    LOGGER.info("Generating experiment description files in: %s", \
                  os.path.abspath(self.testOutDir))


  def cleanUp(self):
    shutil.rmtree(self.testOutDir, ignore_errors=True)
    return



class ExperimentTestBaseClass(HelperTestCaseBase):

  # We will load the description.py and permutations.py files as modules
  # multiple times in order to verify that they are valid python scripts. To
  # facilitate this, we reload with a unique module name
  # ("expGenerator_generated_script%d") each time.
  __pythonScriptImportCount = 0

  @classmethod
  def newScriptImportName(cls):
    cls.__pythonScriptImportCount += 1
    name = "expGenerator_generated_script%d" % cls.__pythonScriptImportCount
    return name


  def setUp(self):
    """ Method called to prepare the test fixture. This is called by the
    unittest framework immediately before calling the test method; any exception
    raised by this method will be considered an error rather than a test
    failure. The default implementation does nothing.
    """
    global g_myEnv
    if not g_myEnv:
      # Setup environment
      params = type('obj', (object,), {'installDir' : resource_filename("nupic", "")})
      g_myEnv = MyTestEnvironment(params)


  def tearDown(self):
    """ Method called immediately after the test method has been called and the
    result recorded. This is called even if the test method raised an exception,
    so the implementation in subclasses may need to be particularly careful
    about checking internal state. Any exception raised by this method will be
    considered an error rather than a test failure. This method will only be
    called if the setUp() succeeds, regardless of the outcome of the test
    method. The default implementation does nothing.
    """
    self.resetExtraLogItems()
    g_myEnv.cleanUp()


  def shortDescription(self):
    """ Override to force unittest framework to use test method names instead
    of docstrings in the report.
    """
    return None


  def checkPythonScript(self, scriptAbsPath):
    self.assertTrue(os.path.isabs(scriptAbsPath))

    self.assertTrue(os.path.isfile(scriptAbsPath),
                    ("Expected python script to be present here: <%s>") % \
                        (scriptAbsPath))

    # Test viability of the file as a python script by loading it
    # An exception will be raised if this fails
    mod = imp.load_source(self.newScriptImportName(), scriptAbsPath)
    return mod


  def getModules(self, expDesc, hsVersion='v2'):
    """ This does the following:

    1.) Calls ExpGenerator to generate a base description file and permutations
    file from expDescription.

    2.) Verifies that description.py and permutations.py are valid python
    modules that can be loaded

    3.) Returns the loaded base description module and permutations module

    Parameters:
    -------------------------------------------------------------------
    expDesc:       JSON format experiment description
    hsVersion:     which version of hypersearch to use ('v2'; 'v1' was dropped)
    retval:        (baseModule, permutationsModule)
    """

    #------------------------------------------------------------------
    # Call ExpGenerator to generate the base description and permutations
    #  files.
    shutil.rmtree(g_myEnv.testOutDir, ignore_errors=True)
    args = [
      "--description=%s" % (json.dumps(expDesc)),
      "--outDir=%s" % (g_myEnv.testOutDir),
      "--version=%s" % (hsVersion)
    ]
    self.addExtraLogItem({'args':args})
    ExpGenerator.expGenerator(args)


    #----------------------------------------
    # Check that generated scripts are present
    descriptionPyPath = os.path.join(g_myEnv.testOutDir, "description.py")
    permutationsPyPath = os.path.join(g_myEnv.testOutDir, "permutations.py")

    return (self.checkPythonScript(descriptionPyPath),
            self.checkPythonScript(permutationsPyPath))



  def runBaseDescriptionAndPermutations(self, expDesc, hsVersion, maxModels=2):
    """ This does the following:

    1.) Calls ExpGenerator to generate a base description file and permutations
    file from expDescription.

    2.) Verifies that description.py and permutations.py are valid python
    modules that can be loaded

    3.) Runs the base description.py as an experiment using OPF RunExperiment.

    4.) Runs a Hypersearch using the generated permutations.py by passing it
    to HypersearchWorker.

    Parameters:
    -------------------------------------------------------------------
    expDesc:       JSON format experiment description
    hsVersion:     which version of hypersearch to use ('v2'; 'v1' was dropped)
    retval:        list of model results
    """


    # --------------------------------------------------------------------
    # Generate the description.py and permutations.py. These get generated
    # in the g_myEnv.testOutDir directory.
    self.getModules(expDesc, hsVersion=hsVersion)
    permutationsPyPath = os.path.join(g_myEnv.testOutDir, "permutations.py")

    # ----------------------------------------------------------------
    # Try running the base experiment
    args = [g_myEnv.testOutDir]
    from nupic.frameworks.opf.experiment_runner import runExperiment
    LOGGER.info("")
    LOGGER.info("============================================================")
    LOGGER.info("RUNNING EXPERIMENT")
    LOGGER.info("============================================================")
    runExperiment(args)


    # ----------------------------------------------------------------
    # Try running the generated permutations
    jobParams = {'persistentJobGUID' : generatePersistentJobGUID(),
                 'permutationsPyFilename': permutationsPyPath,
                 'hsVersion': hsVersion,
                 }
    if maxModels is not None:
      jobParams['maxModels'] = maxModels
    args = ['ignoreThis', '--params=%s' % (json.dumps(jobParams))]
    self.resetExtraLogItems()
    self.addExtraLogItem({'params':jobParams})

    LOGGER.info("")
    LOGGER.info("============================================================")
    LOGGER.info("RUNNING PERMUTATIONS")
    LOGGER.info("============================================================")

    jobID = HypersearchWorker.main(args)

    # Make sure all models completed successfully
    cjDAO = ClientJobsDAO.get()
    models = cjDAO.modelsGetUpdateCounters(jobID)
    modelIDs = [model.modelId for model in models]
    results = cjDAO.modelsGetResultAndStatus(modelIDs)
    if maxModels is not None:
      self.assertEqual(len(results), maxModels, "Expected to get %d model "
                "results but only got %d" % (maxModels, len(results)))

    for result in results:
      self.assertEqual(result.completionReason, cjDAO.CMPL_REASON_EOF,
          "Model did not complete successfully:\n%s" % (result.completionMsg))

    return results


  def assertIsInt(self, x, msg=None):

    xInt = int(round(x))
    if msg is None:
      msg = "%s is not a valid integer" % (str(x))
    self.assertLess(abs(x - xInt), 0.0001 * x, msg)


  def assertValidSwarmingAggregations(self, expDesc, expectedAttempts):
    """ Test that the set of aggregations produced for a swarm are correct

    Parameters:
    -----------------------------------------------------------------------
    expDesc:   JSON experiment description
    expectedAttempts: list of (minAggregationMultiple, predictionSteps) pairs
                      that we expect to find in the aggregation choices.
    """


    # Extract out the minAggregation
    minAggregation = dict(expDesc['streamDef']['aggregation'])
    minAggregation.pop('fields')

    # --------------------------------------------------------------------
    (base, perms) = self.getModules(expDesc)

    predictionSteps = expDesc['inferenceArgs']['predictionSteps'][0]

    # Make sure we have the expected info in the base description file
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                     expDesc['inferenceArgs']['predictionSteps'])
    #self.assertEqual(base.config['modelParams']['clParams']['steps'],
    #                 '%s' % (predictionSteps))
    tmpAggregationInfo = rCopy(
        base.config['aggregationInfo'],
        lambda value, _: value)
    tmpAggregationInfo.pop('fields')
    self.assertDictEqual(tmpAggregationInfo, minAggregation)

    predictAheadTime = dict(minAggregation)
    for key in predictAheadTime.iterkeys():
      predictAheadTime[key] *=  predictionSteps
    self.assertEqual(base.config['predictAheadTime'],
                     predictAheadTime)


    # And in the permutations file
    self.assertEqual(
        perms.minimize,
        ("multiStepBestPredictions:multiStep:errorMetric='altMAPE':"
         "steps=\\[.*\\]:window=1000:field=consumption"))

    # Make sure the right metrics were put in
    metrics = base.control['metrics']
    metricTuples = [(metric.metric, metric.inferenceElement, metric.params) \
                   for metric in metrics]

    self.assertIn(('multiStep',
                   'multiStepBestPredictions',
                   {'window': 1000, 'steps': [predictionSteps],
                    'errorMetric': 'altMAPE'}),
                  metricTuples)

    # ------------------------------------------------------------------------
    # Get the aggregation periods to permute over, and make sure each is
    #  valid
    aggPeriods = perms.permutations['aggregationInfo']
    aggAttempts = []
    for agg in aggPeriods.choices:

      # Make sure it's an integer multiple of minAggregation
      multipleOfMinAgg = aggregationDivide(agg, minAggregation)
      self.assertIsInt(multipleOfMinAgg,
            "invalid aggregation period %s is not an integer multiple" \
            "of minAggregation (%s)" % (agg, minAggregation))
      self.assertGreaterEqual(int(round(multipleOfMinAgg)), 1,
            "invalid aggregation period %s is not >= minAggregation (%s)" % \
            (agg, minAggregation))

      # Make sure the predictAheadTime is an integer multiple of the aggregation
      requiredSteps = aggregationDivide(predictAheadTime, agg)
      self.assertIsInt(requiredSteps,
            "invalid aggregation period %s is not an integer factor" \
            "of predictAheadTime (%s)" % (agg, predictAheadTime))
      self.assertGreaterEqual(int(round(requiredSteps)), 1,
            "invalid aggregation period %s greater than " \
            " predictAheadTime (%s)" % (agg, predictAheadTime))


      # Make sure that computeInterval is an integer multiple of the aggregation
      quotient = aggregationDivide(expDesc['computeInterval'], agg)
      self.assertIsInt(quotient,
            "invalid aggregation period %s is not an integer factor" \
            "of computeInterval (%s)" % (agg, expDesc['computeInterval']))
      self.assertGreaterEqual(int(round(quotient)), 1,
          "Invalid aggregation period %s is greater than the computeInterval " \
          "%s" % (agg, expDesc['computeInterval']))


      aggAttempts.append((int(round(multipleOfMinAgg)), int(requiredSteps)))

    # Print summary of aggregation attempts
    LOGGER.info("This swarm will try the following \
      (minAggregationMultiple, predictionSteps) combinations: %s", aggAttempts)


    # ----------------------------------------------------------------------
    # Were these the expected attempts?
    aggAttempts.sort()
    expectedAttempts.sort()
    self.assertEqual(aggAttempts, expectedAttempts, "Expected this swarm to " \
                     "try the following (minAggMultiple, predictionSteps) " \
                     "attempts: %s, but instead it is going to try: %s" % \
                     (expectedAttempts, aggAttempts))



class PositiveExperimentTests(ExperimentTestBaseClass):


  def test_ShowSchema(self):
    """ Test showing the schema
    """

    args = [
      "--showSchema"
    ]
    self.addExtraLogItem({'args':args})

    #----------------------------------------
    # Run it
    ExpGenerator.expGenerator(args)
    return


  def test_PredictionElement(self):
    """ Test correct behavior in response to different settings in the
    prediction element
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"MultiStep",
      "inferenceArgs":{
        "predictedField":"consumption",
        "predictionSteps": [1]
      },
      'environment':OpfEnvironment.Experiment,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
        },
      ],
      "resetPeriod": {"days" : 1, "hours" : 12},
      "iterationCount": 10,
    }

    # --------------------------------------------------------------------
    # Test it out with no prediction element
    (_base, perms) = self.getModules(expDesc)

    # Make sure we have the right optimization designation
    self.assertEqual(perms.minimize,
        ("multiStepBestPredictions:multiStep:errorMetric='altMAPE':"
         "steps=\\[1\\]:window=%d:field=consumption")
          % ExpGenerator.METRIC_WINDOW,
          msg="got: %s" % perms.minimize)

    # Should not have any classifier info to permute over
    self.assertNotIn('clAlpha', perms.permutations)


    return


  def assertMetric(self, base, perm, predictedField,
                   optimizeMetric, nupicScore,
                   movingBaseline,
                   oneGram,
                   trivialMetric,
                   legacyMetric=None):
    print "base.control"
    pprint.pprint(base.control)
    #taskMetrics = base.control['tasks'][0]['taskControl']['metrics']
    taskMetrics = base.control['metrics']

    for metricSpec in taskMetrics:
      print metricSpec.metric
      self.assertTrue(metricSpec.metric in ["multiStep", optimizeMetric,
                                            movingBaseline, oneGram,
                                            nupicScore, trivialMetric,
                                            legacyMetric],
                      "Unrecognized Metric type: %s"% metricSpec.metric)
      if metricSpec.metric == trivialMetric:
        self.assertEqual(metricSpec.metric, trivialMetric)
        self.assertEqual(metricSpec.inferenceElement,
                         InferenceElement.prediction)
      elif metricSpec.metric == movingBaseline:
        self.assertTrue("errorMetric" in metricSpec.params)
      elif metricSpec.metric == oneGram:
        self.assertTrue("errorMetric" in metricSpec.params)
      elif metricSpec.metric == "multiStep":
        pass
      else:
        self.assertEqual(metricSpec.metric, optimizeMetric)

    #optimizeString = "prediction:%s:window=%d:field=%s" % \
    #                            (optimizeMetric, ExpGenerator.METRIC_WINDOW,
    #                             predictedField)
    optimizeString = ("multiStepBestPredictions:multiStep:"
                     "errorMetric='%s':steps=\[1\]"
                     ":window=%d:field=%s" % \
                                (optimizeMetric, ExpGenerator.METRIC_WINDOW,
                                 predictedField))
    print "perm.minimize=",perm.minimize
    print "optimizeString=",optimizeString
    self.assertEqual(perm.minimize, optimizeString,
                     msg="got: %s" % perm.minimize)


  def test_Metrics(self):
    """ Test to make sure that the correct metrics are generated """

    # =========================================================================
    # Test category predicted field
    # =========================================================================
    streamDef = dict(
      version = 1,
      info = "test_category_predicted_field",
      streams = [
        # It doesn't matter if this stream source points to a real place or not.
        dict(source="file://dummy",
             info="dummy.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"MultiStep",
      "inferenceArgs":{
        "predictedField":"playType",
        "predictionSteps": [1]
      },
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "address",
          "fieldType": "string"
        },
        { "fieldName": "ydsToGo",
          "fieldType": "float",
        },
        { "fieldName": "playType",
          "fieldType": "string",
        },
      ],
    }
    
    # Make sure we have the right metric type
    #   (avg_err for categories, aae for scalars)
    (base, perms) = self.getModules(expDesc)
    self.assertMetric(base, perms, expDesc['inferenceArgs']['predictedField'],
                      'avg_err',
                      'moving_mode',
                      'one_gram',
                      InferenceElement.prediction,
                      "trivial")
    self.assertEqual(base.control['loggedMetrics'][0], ".*")

    # =========================================================================
    # Test scalar predicted field
    # =========================================================================

    expDesc['inferenceArgs']['predictedField'] = 'ydsToGo'
    (base, perms)  = self.getModules(expDesc)
    self.assertMetric(base, perms, expDesc['inferenceArgs']['predictedField'],
                      'altMAPE',"moving_mean","one_gram",
                      InferenceElement.encodings, "trivial")
    self.assertEqual(base.control['loggedMetrics'][0], ".*")


  def test_IncludedFields(self):
    """ Test correct behavior in response to different settings in the
    includedFields element
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"TemporalNextStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Experiment,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "gym",
          "fieldType": "string"
        },
        { "fieldName": "address",
          "fieldType": "string"
        },
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ],
      "resetPeriod": {"days" : 1, "hours" : 12},
      "iterationCount": 10,
    }

    # --------------------------------------------------------------------
    # Test it out with all fields
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected encoders
    actEncoderFields = set()
    actEncoderNames = set()
    for _, encoder in (
        base.config['modelParams']['sensorParams']['encoders'].iteritems()):
      actEncoderFields.add(encoder['fieldname'])
      actEncoderNames.add(encoder['name'])

    # Make sure we have the right optimization designation
    self.assertEqual(actEncoderFields, set(['gym', 'address', 'timestamp',
                                            'consumption']))
    self.assertEqual(actEncoderNames, set(['gym', 'address',
              'timestamp_timeOfDay', 'timestamp_dayOfWeek', 'timestamp_weekend',
              'consumption']))


    # --------------------------------------------------------------------
    # Test with a subset of fields
    expDesc['includedFields'] = [
        { "fieldName": "gym",
          "fieldType": "string"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ]
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected encoders
    actEncoderFields = set()
    actEncoderNames = set()
    for _, encoder in (
        base.config['modelParams']['sensorParams']['encoders'].iteritems()):
      actEncoderFields.add(encoder['fieldname'])
      actEncoderNames.add(encoder['name'])

    # Make sure we have the right optimization designation
    self.assertEqual(actEncoderFields, set(['gym', 'consumption']))
    self.assertEqual(actEncoderNames, set(['gym', 'consumption']))


    # --------------------------------------------------------------------
    # Test that min and max are honored
    expDesc['includedFields'] = [
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue" : 42,
          "maxValue" : 42.42,
        },
      ]
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected encoders
    actEncoderFields = set()
    actEncoderNames = set()
    actEncoderTypes = set()
    minValues = set()
    maxValues = set()
    for _, encoder in (
        base.config['modelParams']['sensorParams']['encoders'].iteritems()):
      actEncoderFields.add(encoder['fieldname'])
      actEncoderNames.add(encoder['name'])
      actEncoderTypes.add(encoder['type'])
      minValues.add(encoder['minval'])
      maxValues.add(encoder['maxval'])

    # Make sure we have the right optimization designation
    self.assertEqual(actEncoderFields, set(['consumption']))
    self.assertEqual(actEncoderNames, set(['consumption']))
    # Because both min and max were specifed,
    #   the encoder should be  non-adaptive
    self.assertEqual(actEncoderTypes, set(['ScalarEncoder']))
    self.assertEqual(minValues, set([42]))
    self.assertEqual(maxValues, set([42.42]))

    # --------------------------------------------------------------------
    # Test that overriding the encoderType is supported
    expDesc['includedFields'] = [
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue" : 42,
          "maxValue" : 42.42,
          "encoderType": 'AdaptiveScalarEncoder',
        },
      ]
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected encoders
    actEncoderFields = set()
    actEncoderNames = set()
    actEncoderTypes = set()
    minValues = set()
    maxValues = set()
    for _, encoder in (
        base.config['modelParams']['sensorParams']['encoders'].iteritems()):
      actEncoderFields.add(encoder['fieldname'])
      actEncoderNames.add(encoder['name'])
      actEncoderTypes.add(encoder['type'])
      minValues.add(encoder['minval'])
      maxValues.add(encoder['maxval'])

    # Make sure we have the right optimization designation
    self.assertEqual(actEncoderFields, set(['consumption']))
    self.assertEqual(actEncoderNames, set(['consumption']))
    self.assertEqual(actEncoderTypes, set(['AdaptiveScalarEncoder']))
    self.assertEqual(minValues, set([42]))
    self.assertEqual(maxValues, set([42.42]))

    # --------------------------------------------------------------------
    # Test that fieldnames with funny characters (-?<>!@##'"\=...) are
    # generated properly. Should throw exception for \ character
    characters = string.punctuation
    expDesc['includedFields'] = [{'fieldName':char+'helloField'+char,
                                  "fieldType":"float"}
                                  for char in characters]\
                                +[{'fieldName':'consumption',
                                  'fieldType':'float'}]

    try:
      (base, _perms) = self.getModules(expDesc)
    except:
      LOGGER.info("Passed: Threw exception for bad fieldname.")

    # --------------------------------------------------------------------
    ## Now test without backslash
    characters = characters.replace('\\','')
    #expDesc['includedFields'] = [{'fieldName':char+'helloField'+char,
    #                              "fieldType":"float"}
    #                              for char in characters]\
    #                            +[{'fieldName':'consumption',
    #                              'fieldType':'float'}]
    #(base, perms) = self.getModules(expDesc)


    return


  def test_Aggregation(self):
    """ Test that aggregation gets pulled out of the streamDef as it should
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "TestAggregation",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
      ],
      aggregation = {
        'years': 1,
        'months': 2,
        'weeks': 3,
        'days': 4,
        'hours': 5,
        'minutes': 6,
        'seconds': 7,
        'milliseconds': 8,
        'microseconds': 9,
        'fields': [('consumption', 'sum'),
                   ('gym', 'first')]
      },
      sequenceIdField = 'gym',
      providers = {
        "order": ["weather"],
        "weather":{
          "locationField": "address",
          "providerType": "NamedProvider",
          "timestampField": "timestamp",
          "weatherTypes":[
            "TEMP"
          ]
        }
      }
    )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"TemporalNextStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Experiment,
      "streamDef":streamDef,
      "includedFields": [
        { "fieldName": "gym",
          "fieldType": "string"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
        { "fieldName": "TEMP",
          "fieldType": "float",
          "minValue": -30.0,
          "maxValue": 120.0,
        },
      ],
      "iterationCount": 10,
      "resetPeriod": {"days" : 1, "hours" : 12},
    }

    # --------------------------------------------------------------------
    # Test with aggregation
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected aggregation
    aggInfo = base.config['aggregationInfo']
    aggInfo['fields'].sort()
    streamDef['aggregation']['fields'].sort()
    self.assertEqual(aggInfo, streamDef['aggregation'])

    # --------------------------------------------------------------------
    # Test with no aggregation
    expDesc['streamDef'].pop('aggregation')
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected aggregation
    aggInfo = base.config['aggregationInfo']
    expAggInfo = {
      'years': 0,
      'months': 0,
      'weeks': 0,
      'days': 0,
      'hours': 0,
      'minutes': 0,
      'seconds': 0,
      'milliseconds': 0,
      'microseconds': 0,
      'fields': []
    }
    aggInfo['fields'].sort()
    expAggInfo['fields'].sort()
    self.assertEqual(aggInfo, expAggInfo)

    return


  def test_ResetPeriod(self):
    """ Test that reset period gets handled correctly
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
   )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"TemporalNextStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Experiment,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "gym",
          "fieldType": "string"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ],
      "iterationCount": 10,
      "resetPeriod": {
        'weeks': 3,
        'days': 4,
        'hours': 5,
        'minutes': 6,
        'seconds': 7,
        'milliseconds': 8,
        'microseconds': 9,
      },
    }

    # --------------------------------------------------------------------
    # Test with reset period
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected reset info
    resetInfo = base.config['modelParams']['sensorParams']['sensorAutoReset']
    self.assertEqual(resetInfo, expDesc['resetPeriod'])

    # --------------------------------------------------------------------
    # Test no reset period
    expDesc.pop('resetPeriod')
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected reset info
    resetInfo = base.config['modelParams']['sensorParams']['sensorAutoReset']
    self.assertEqual(resetInfo, None)
    return


  def test_RunningExperimentHSv2(self):
    """ Try running a basic Hypersearch V2 experiment and permutations
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"TemporalMultiStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Nupic,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
        },
      ],
      "resetPeriod": {"days" : 1, "hours" : 12},
      "iterationCount": 10,
    }

    # Test it out
    self.runBaseDescriptionAndPermutations(expDesc, hsVersion='v2')

    return


  def test_MultiStep(self):
    """ Test the we correctly generate a multi-step prediction experiment
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"],
             last_record=20),
        ],
      aggregation = {
        'years': 0,
        'months': 0,
        'weeks': 0,
        'days': 0,
        'hours': 1,
        'minutes': 0,
        'seconds': 0,
        'milliseconds': 0,
        'microseconds': 0,
        'fields': [('consumption', 'sum'),
                   ('gym', 'first'),
                   ('timestamp', 'first')]
      }
   )

    # Generate the experiment description
    expDesc = {
      'environment':    OpfEnvironment.Nupic,
      "inferenceArgs":{
        "predictedField":"consumption",
        "predictionSteps": [1, 5],
      },
      "inferenceType":  "MultiStep",
      "streamDef":      streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ],
      "iterationCount": -1,
      "runBaselines": True,
    }

    # --------------------------------------------------------------------
    (base, perms) = self.getModules(expDesc)
    
    print "base.config['modelParams']:"
    pprint.pprint(base.config['modelParams'])
    print "perms.permutations"
    pprint.pprint(perms.permutations)
    print "perms.minimize"
    pprint.pprint(perms.minimize)
    print "expDesc"
    pprint.pprint(expDesc)

    # Make sure we have the expected info in the base description file
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                     expDesc['inferenceArgs']['predictionSteps'])
    self.assertEqual(base.control['inferenceArgs']['predictedField'],
                     expDesc['inferenceArgs']['predictedField'])
    self.assertEqual(base.config['modelParams']['inferenceType'],
                     "TemporalMultiStep")
    
    # Make sure there is a '_classifier_input' encoder with classifierOnly
    #  set to True
    self.assertEqual(base.config['modelParams']['sensorParams']['encoders']
                     ['_classifierInput']['classifierOnly'], True)
    self.assertEqual(base.config['modelParams']['sensorParams']['encoders']
                     ['_classifierInput']['fieldname'],
                     expDesc['inferenceArgs']['predictedField'])
    

    # And in the permutations file
    self.assertIn('inferenceType', perms.permutations['modelParams'])
    self.assertEqual(perms.minimize,
            "multiStepBestPredictions:multiStep:errorMetric='altMAPE':" \
            + "steps=\\[1, 5\\]:window=1000:field=consumption")
    self.assertIn('alpha', perms.permutations['modelParams']['clParams'])

    # Should permute over the _classifier_input encoder params
    self.assertIn('_classifierInput',
                  perms.permutations['modelParams']['sensorParams']['encoders'])

    # Should set inputPredictedField to "auto" (the default)
    self.assertEqual(perms.inputPredictedField, "auto")
    

    # Should have TP parameters being permuted
    self.assertIn('activationThreshold',
                  perms.permutations['modelParams']['tpParams'])
    self.assertIn('minThreshold', perms.permutations['modelParams']['tpParams'])


    # Make sure the right metrics were put in
    metrics = base.control['metrics']
    metricTuples = [(metric.metric, metric.inferenceElement, metric.params) \
                   for metric in metrics]

    self.assertIn(('multiStep',
                   'multiStepBestPredictions',
                   {'window': 1000, 'steps': [1, 5], 'errorMetric': 'aae'}),
                  metricTuples)

    # Test running it
    self.runBaseDescriptionAndPermutations(expDesc, hsVersion='v2')


    # --------------------------------------
    # If we put the 5 step first, we should still get a list of steps to
    #  optimize over
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2['inferenceArgs']['predictionSteps'] = [5, 1]
    (base, perms) = self.getModules(expDesc2)
    self.assertEqual(perms.minimize,
            "multiStepBestPredictions:multiStep:errorMetric='altMAPE':" \
            + "steps=\\[5, 1\\]:window=1000:field=consumption")


    # --------------------------------------
    # If we specify NonTemporal, we shouldn't permute over TP parameters
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2['inferenceType'] = 'NontemporalMultiStep'
    (base, perms) = self.getModules(expDesc2)
    self.assertEqual(base.config['modelParams']['inferenceType'],
                     expDesc2['inferenceType'])
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                     expDesc2['inferenceArgs']['predictionSteps'])
    self.assertEqual(base.control['inferenceArgs']['predictedField'],
                     expDesc2['inferenceArgs']['predictedField'])

    self.assertIn('alpha', perms.permutations['modelParams']['clParams'])
    self.assertNotIn('inferenceType', perms.permutations['modelParams'])
    self.assertNotIn('activationThreshold',
                     perms.permutations['modelParams']['tpParams'])
    self.assertNotIn('minThreshold',
                     perms.permutations['modelParams']['tpParams'])

    # Make sure the right metrics were put in
    metrics = base.control['metrics']
    metricTuples = [(metric.metric, metric.inferenceElement, metric.params) \
                   for metric in metrics]

    self.assertIn(('multiStep',
                   'multiStepBestPredictions',
                   {'window': 1000, 'steps': [1, 5], 'errorMetric': 'aae'}),
                  metricTuples)

    # Test running it
    self.runBaseDescriptionAndPermutations(expDesc, hsVersion='v2')


    # --------------------------------------
    # If we specify just generic MultiStep, we should permute over the inference
    #  type
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2['inferenceType'] = 'MultiStep'
    (base, perms) = self.getModules(expDesc2)

    self.assertEqual(base.config['modelParams']['inferenceType'],
                     'TemporalMultiStep')
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                      expDesc2['inferenceArgs']['predictionSteps'])
    self.assertEqual(base.control['inferenceArgs']['predictedField'],
                     expDesc2['inferenceArgs']['predictedField'])

    self.assertIn('alpha', perms.permutations['modelParams']['clParams'])
    self.assertIn('inferenceType', perms.permutations['modelParams'])
    self.assertIn('activationThreshold',
                  perms.permutations['modelParams']['tpParams'])
    self.assertIn('minThreshold', perms.permutations['modelParams']['tpParams'])

    # Make sure the right metrics were put in
    metrics = base.control['metrics']
    metricTuples = [(metric.metric, metric.inferenceElement, metric.params) \
                   for metric in metrics]

    self.assertIn(('multiStep',
                   'multiStepBestPredictions',
                   {'window': 1000, 'steps': [1,5], 'errorMetric': 'aae'}),
                  metricTuples)

    # Test running it
    self.runBaseDescriptionAndPermutations(expDesc, hsVersion='v2')
    
    
    # ---------------------------------------------------------------------
    # If the caller sets inferenceArgs.inputPredictedField, make
    # sure the permutations file has the same setting
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2["inferenceArgs"]["inputPredictedField"] = "yes"
    (base, perms) = self.getModules(expDesc2)
    self.assertEqual(perms.inputPredictedField, "yes")

    expDesc2 = copy.deepcopy(expDesc)
    expDesc2["inferenceArgs"]["inputPredictedField"] = "no"
    (base, perms) = self.getModules(expDesc2)
    self.assertEqual(perms.inputPredictedField, "no")

    expDesc2 = copy.deepcopy(expDesc)
    expDesc2["inferenceArgs"]["inputPredictedField"] = "auto"
    (base, perms) = self.getModules(expDesc2)
    self.assertEqual(perms.inputPredictedField, "auto")


    # ---------------------------------------------------------------------
    # If the caller sets inferenceArgs.inputPredictedField to 'no', make
    # sure there is no encoder for the predicted field
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2["inferenceArgs"]["inputPredictedField"] = "no"
    (base, perms) = self.getModules(expDesc2)

    self.assertNotIn(
      'consumption',
      base.config['modelParams']['sensorParams']['encoders'].keys())


  def test_DeltaEncoders(self):

    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "inferenceType":"TemporalMultiStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Nupic,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
          "runDelta": True
        },
      ],
    }

    (base, perms) = self.getModules(expDesc)

    encoder = base.config["modelParams"]["sensorParams"]["encoders"]\
                          ["consumption"]
    encoderPerm = perms.permutations["modelParams"]["sensorParams"]\
                          ["encoders"]["consumption"]

    self.assertEqual(encoder["type"], "ScalarSpaceEncoder")
    self.assertIsInstance(encoderPerm.kwArgs['space'], PermuteChoices)

    expDesc = {
      "inferenceType":"TemporalMultiStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Nupic,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
          "runDelta": True,
          "space": "delta"
        },
      ],
    }

    (base, perms) = self.getModules(expDesc)
    encoder = base.config["modelParams"]["sensorParams"] \
      ["encoders"]["consumption"]
    encoderPerm = perms.permutations["modelParams"]["sensorParams"] \
      ["encoders"]["consumption"]

    self.assertEqual(encoder["type"], "ScalarSpaceEncoder")
    self.assertEqual(encoder["space"], "delta")
    self.assertEqual(encoderPerm.kwArgs['space'], "delta")


  def test_AggregationSwarming(self):
    """ Test the we correctly generate a multi-step prediction experiment that
    uses aggregation swarming
    """


    # The min aggregation
    minAggregation = {
        'years': 0,
        'months': 0,
        'weeks': 0,
        'days': 0,
        'hours': 0,
        'minutes': 15,
        'seconds': 0,
        'milliseconds': 0,
        'microseconds': 0,
        }

    streamAggregation = dict(minAggregation)
    streamAggregation.update({
     'fields': [('consumption', 'sum'),
                ('gym', 'first'),
                ('timestamp', 'first')]
      })

    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"],
             last_record=10),
        ],
      aggregation = streamAggregation,
   )

    # Generate the experiment description
    expDesc = {
      'environment':    OpfEnvironment.Nupic,
      "inferenceArgs":{
        "predictedField":"consumption",
        "predictionSteps": [24],
      },
      "inferenceType":  "TemporalMultiStep",
      "streamDef":      streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ],
      "iterationCount": -1,
      "runBaselines": False,
      "computeInterval": {
        'hours': 2
      }
    }

    # ------------------------------------------------------------------------
    # Test running it
    #self.runBaseDescriptionAndPermutations(expDesc, hsVersion='v2')


    # --------------------------------------------------------------------
    # Check for consistency. (example 1)
    # The expectedAttempts parameter is a list of
    #  (minAggregationMultiple, predictionSteps) pairs that will be attempted
    self.assertValidSwarmingAggregations(expDesc = expDesc,
          expectedAttempts = [(1, 24), (2, 12), (4, 6), (8, 3)])


    # --------------------------------------------------------------------
    # Try where there are lots of possible aggregations that we only try
    #  the last 5
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['streamDef']['aggregation']['minutes'] = 1
    expDescTmp['inferenceArgs']['predictionSteps'] = \
      [4*60/1] # 4 hours / 1 minute
    self.assertValidSwarmingAggregations(expDesc = expDescTmp,
          expectedAttempts = [(24, 10), (30, 8), (40, 6), (60, 4), (120, 2)])


    # --------------------------------------------------------------------
    # Make sure computeInterval is honored (example 2)
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['computeInterval']['hours'] = 3
    expDescTmp['inferenceArgs']['predictionSteps'] = [16] # 4 hours
    self.assertValidSwarmingAggregations(expDesc = expDescTmp,
          expectedAttempts = [(1,16), (2, 8), (4, 4)])

    # --------------------------------------------------------------------
    # Make sure computeInterval in combination with predictAheadTime is honored
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['computeInterval']['hours'] = 2
    expDescTmp['inferenceArgs']['predictionSteps'] = [16] # 4 hours
    self.assertValidSwarmingAggregations(expDesc = expDescTmp,
          expectedAttempts = [(1,16), (2, 8), (4, 4), (8, 2)])



    # --------------------------------------------------------------------
    # Make sure we catch bad cases:

    # computeInterval must be >= minAggregation
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['computeInterval']['hours'] = 0
    expDescTmp['computeInterval']['minutes'] = 1
    with self.assertRaises(Exception) as cm:
      self.assertValidSwarmingAggregations(expDesc = expDescTmp,
                      expectedAttempts = [(1, 16), (2, 8), (4, 4), (8, 2)])
    LOGGER.info("Got expected exception: %s", cm.exception)

    # computeInterval must be an integer multiple of minAggregation
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['computeInterval']['hours'] = 0
    expDescTmp['computeInterval']['minutes'] = 25
    with self.assertRaises(Exception) as cm:
      self.assertValidSwarmingAggregations(expDesc = expDescTmp,
                      expectedAttempts = [(1, 16), (2, 8), (4, 4), (8, 2)])
    LOGGER.info("Got expected exception: %s", cm.exception)

    # More than 1 predictionSteps passed in
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['inferenceArgs']['predictionSteps'] = [1, 16]
    with self.assertRaises(Exception) as cm:
      self.assertValidSwarmingAggregations(expDesc = expDescTmp,
                      expectedAttempts = [(1, 16), (2, 8), (4, 4), (8, 2)])
    LOGGER.info("Got expected exception: %s", cm.exception)

    # No stream aggregation
    expDescTmp = copy.deepcopy(expDesc)
    expDescTmp['streamDef']['aggregation']['minutes'] = 0
    with self.assertRaises(Exception) as cm:
      self.assertValidSwarmingAggregations(expDesc = expDescTmp,
                      expectedAttempts = [(1, 16), (2, 8), (4, 4), (8, 2)])
    LOGGER.info("Got expected exception: %s", cm.exception)


  def test_SwarmSize(self):
    """ Test correct behavior in response to different settings in the
    swarmSize element
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "swarmSize": "large",
      "inferenceType":"TemporalNextStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Nupic,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
        },
      ],
      "resetPeriod": {"days" : 1, "hours" : 12},
    }


    # --------------------------------------------------------------------
    # Test out "large" swarm generation
    (base, perms) = self.getModules(expDesc)

    self.assertEqual(base.control['iterationCount'], -1,
                     msg="got: %s" % base.control['iterationCount'])
    self.assertEqual(perms.minParticlesPerSwarm, 15,
                     msg="got: %s" % perms.minParticlesPerSwarm)

    # Temporarily disable new large swarm features
    #self.assertEqual(perms.killUselessSwarms, False,
    #                 msg="got: %s" % perms.killUselessSwarms)
    #self.assertEqual(perms.minFieldContribution, -1000,
    #                 msg="got: %s" % perms.minFieldContribution)
    #self.assertEqual(perms.maxFieldBranching, 10,
    #                 msg="got: %s" % perms.maxFieldBranching)
    #self.assertEqual(perms.tryAll3FieldCombinations, True,
    #                 msg="got: %s" % perms.tryAll3FieldCombinations)
    self.assertEqual(perms.tryAll3FieldCombinationsWTimestamps, True,
                     msg="got: %s" % perms.tryAll3FieldCombinationsWTimestamps)
    self.assertFalse(hasattr(perms, 'maxModels'))

    # Should set inputPredictedField to "auto"
    self.assertEqual(perms.inputPredictedField, "auto")
    


    # --------------------------------------------------------------------
    # Test it out with medium swarm
    expDesc["swarmSize"] = "medium"
    (base, perms) = self.getModules(expDesc)

    self.assertEqual(base.control['iterationCount'], 4000,
                     msg="got: %s" % base.control['iterationCount'])
    self.assertEqual(perms.minParticlesPerSwarm, 5,
                     msg="got: %s" % perms.minParticlesPerSwarm)
    self.assertEqual(perms.maxModels, 200,
                     msg="got: %s" % perms.maxModels)
    self.assertFalse(hasattr(perms, 'killUselessSwarms'))
    self.assertFalse(hasattr(perms, 'minFieldContribution'))
    self.assertFalse(hasattr(perms, 'maxFieldBranching'))
    self.assertFalse(hasattr(perms, 'tryAll3FieldCombinations'))

    # Should set inputPredictedField to "auto"
    self.assertEqual(perms.inputPredictedField, "auto")


    # --------------------------------------------------------------------
    # Test it out with small swarm
    expDesc["swarmSize"] = "small"
    (base, perms) = self.getModules(expDesc)

    self.assertEqual(base.control['iterationCount'], 100,
                     msg="got: %s" % base.control['iterationCount'])
    self.assertEqual(perms.minParticlesPerSwarm, 3,
                     msg="got: %s" % perms.minParticlesPerSwarm)
    self.assertEqual(perms.maxModels, 1,
                     msg="got: %s" % perms.maxModels)
    self.assertFalse(hasattr(perms, 'killUselessSwarms'))
    self.assertFalse(hasattr(perms, 'minFieldContribution'))
    self.assertFalse(hasattr(perms, 'maxFieldBranching'))
    self.assertFalse(hasattr(perms, 'tryAll3FieldCombinations'))

    # Should set inputPredictedField to "yes"
    self.assertEqual(perms.inputPredictedField, "yes")


    # --------------------------------------------------------------------
    # Test it out with all of swarmSize, minParticlesPerSwarm, iteration
    #   count, and inputPredictedField specified
    expDesc["swarmSize"] = "small"
    expDesc["minParticlesPerSwarm"] = 2
    expDesc["iterationCount"] = 42
    expDesc["inferenceArgs"]["inputPredictedField"] = "auto"
    (base, perms) = self.getModules(expDesc)

    self.assertEqual(base.control['iterationCount'], 42,
                     msg="got: %s" % base.control['iterationCount'])
    self.assertEqual(perms.minParticlesPerSwarm, 2,
                     msg="got: %s" % perms.minParticlesPerSwarm)
    self.assertEqual(perms.maxModels, 1,
                     msg="got: %s" % perms.maxModels)
    self.assertFalse(hasattr(perms, 'killUselessSwarms'))
    self.assertFalse(hasattr(perms, 'minFieldContribution'))
    self.assertFalse(hasattr(perms, 'maxFieldBranching'))
    self.assertFalse(hasattr(perms, 'tryAll3FieldCombinations'))
    self.assertEqual(perms.inputPredictedField, "auto")


    # Test running it
    modelResults = self.runBaseDescriptionAndPermutations(
      expDesc, hsVersion='v2', maxModels=None)
    self.assertEqual(len(modelResults), 1, "Expected to get %d model "
          "results but only got %d" % (1, len(modelResults)))


  def test_FixedFields(self):
    """ Test correct behavior in response to setting the fixedFields swarming
    option.
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    # Generate the experiment description
    expDesc = {
      "swarmSize": "large",
      "inferenceType":"TemporalNextStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Nupic,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
        },
      ],
      "resetPeriod": {"days" : 1, "hours" : 12},
      "fixedFields": ['consumption', 'timestamp'],
    }


    # --------------------------------------------------------------------
    # Test out using fieldFields
    (_base, perms) = self.getModules(expDesc)
    self.assertEqual(perms.fixedFields, ['consumption', 'timestamp'],
                     msg="got: %s" % perms.fixedFields)


    # Should be excluded from permutations script if not part of the JSON
    #  description
    expDesc.pop('fixedFields')
    (_base, perms) = self.getModules(expDesc)
    self.assertFalse(hasattr(perms, 'fixedFields'))


  def test_FastSwarmModelParams(self):
    """ Test correct behavior in response to setting the fastSwarmModelParams
    swarming option.
    """


    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
    )

    fastSwarmModelParams = {'this is': 'a test'}

    # Generate the experiment description
    expDesc = {
      "swarmSize": "large",
      "inferenceType":"TemporalNextStep",
      "inferenceArgs":{
        "predictedField":"consumption"
      },
      'environment':OpfEnvironment.Nupic,
      "streamDef": streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
          "minValue":  0,
          "maxValue":  200,
        },
      ],
      "resetPeriod": {"days" : 1, "hours" : 12},
      "fastSwarmModelParams": fastSwarmModelParams,
    }


    # --------------------------------------------------------------------
    # Test out using fieldFields
    (_base, perms) = self.getModules(expDesc)
    self.assertEqual(perms.fastSwarmModelParams, fastSwarmModelParams,
                     msg="got: %s" % perms.fastSwarmModelParams)


    # Should be excluded from permutations script if not part of the JSON
    #  description
    expDesc.pop('fastSwarmModelParams')
    (base, perms) = self.getModules(expDesc)
    self.assertFalse(hasattr(perms, 'fastSwarmModelParams'))


  def test_AnomalyParams(self):
    """ Test correct behavior in response to setting the anomalyParams
    experiment description options
    """

    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"]),
        ],
   )

    # Generate the experiment description
    expDesc = {
      'environment':    OpfEnvironment.Nupic,
      "inferenceArgs":{
        "predictedField":"consumption",
        "predictionSteps": [1],
      },
      "inferenceType":  "TemporalAnomaly",
      "streamDef":      streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ],
      "iterationCount": -1,
      "anomalyParams": {
        "autoDetectThreshold": 1.1,
        "autoDetectWaitRecords": 0,
        "anomalyCacheRecords": 10
      }
    }

    # --------------------------------------------------------------------
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected info in the base description file
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                     expDesc['inferenceArgs']['predictionSteps'])
    self.assertEqual(base.control['inferenceArgs']['predictedField'],
                     expDesc['inferenceArgs']['predictedField'])
    self.assertEqual(base.config['modelParams']['inferenceType'],
                     expDesc['inferenceType'])
    self.assertEqual(base.config['modelParams']['anomalyParams'],
                     expDesc['anomalyParams'])

    # Only TemporalAnomaly models will have and use anomalyParams
    expDesc['inferenceType'] = 'TemporalNextStep'
    (base, _perms) = self.getModules(expDesc)

    # Make sure we have the expected info in the base description file
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                     expDesc['inferenceArgs']['predictionSteps'])
    self.assertEqual(base.control['inferenceArgs']['predictedField'],
                     expDesc['inferenceArgs']['predictedField'])
    self.assertEqual(base.config['modelParams']['inferenceType'],
                     expDesc['inferenceType'])
    self.assertEqual(base.config['modelParams']['anomalyParams'],
        expDesc['anomalyParams'])


  def test_NontemporalClassification(self):
    """ Test the we correctly generate a Nontemporal classification experiment
    """

    # Form the stream definition
    streamDef = dict(
      version = 1,
      info = "test_NoProviders",
      streams = [
        dict(source="file://%s" % HOTGYM_INPUT,
             info="hotGym.csv",
             columns=["*"],
             last_record=10),
        ],
      aggregation = {
        'years': 0,
        'months': 0,
        'weeks': 0,
        'days': 0,
        'hours': 1,
        'minutes': 0,
        'seconds': 0,
        'milliseconds': 0,
        'microseconds': 0,
        'fields': [('consumption', 'sum'),
                   ('gym', 'first'),
                   ('timestamp', 'first')]
      }
   )

    # Generate the experiment description
    expDesc = {
      'environment':    OpfEnvironment.Nupic,
      "inferenceArgs":{
        "predictedField":"consumption",
        "predictionSteps": [0],
      },
      "inferenceType":  "TemporalMultiStep",
      "streamDef":      streamDef,
      "includedFields": [
        { "fieldName": "timestamp",
          "fieldType": "datetime"
        },
        { "fieldName": "consumption",
          "fieldType": "float",
        },
      ],
      "iterationCount": -1,
      "runBaselines": True,
    }

    # --------------------------------------------------------------------
    (base, perms) = self.getModules(expDesc)

    # Make sure we have the expected info in the base description file
    self.assertEqual(base.control['inferenceArgs']['predictionSteps'],
                     expDesc['inferenceArgs']['predictionSteps'])
    self.assertEqual(base.control['inferenceArgs']['predictedField'],
                     expDesc['inferenceArgs']['predictedField'])
    self.assertEqual(base.config['modelParams']['inferenceType'],
                     InferenceType.NontemporalClassification)

    self.assertEqual(base.config['modelParams']['sensorParams']['encoders']
                     ['_classifierInput']['classifierOnly'], True)
    self.assertEqual(base.config['modelParams']['sensorParams']['encoders']
                     ['_classifierInput']['fieldname'],
                     expDesc['inferenceArgs']['predictedField'])
    
    self.assertNotIn('consumption',
             base.config['modelParams']['sensorParams']['encoders'].keys())

    
    # The SP and TP should both be disabled
    self.assertFalse(base.config['modelParams']['spEnable'])
    self.assertFalse(base.config['modelParams']['tpEnable'])

    # Check permutations file
    self.assertNotIn('inferenceType', perms.permutations['modelParams'])
    self.assertEqual(perms.minimize,
            "multiStepBestPredictions:multiStep:errorMetric='altMAPE':" \
            + "steps=\\[0\\]:window=1000:field=consumption")
    self.assertIn('alpha', perms.permutations['modelParams']['clParams'])

    # Should have no SP or TP params to permute over
    self.assertEqual(perms.permutations['modelParams']['tpParams'], {})
    self.assertEqual(perms.permutations['modelParams']['spParams'], {})


    # Make sure the right metrics were put in
    metrics = base.control['metrics']
    metricTuples = [(metric.metric, metric.inferenceElement, metric.params) \
                   for metric in metrics]

    self.assertIn(('multiStep',
                   'multiStepBestPredictions',
                   {'window': 1000, 'steps': [0], 'errorMetric': 'aae'}),
                  metricTuples)


    # Test running it
    self.runBaseDescriptionAndPermutations(expDesc, hsVersion='v2')


    # --------------------------------------
    # If we specify NonTemporalClassification, we should get the same
    #   description and permutations files
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2['inferenceType'] = 'NontemporalClassification'
    (newBase, _newPerms) = self.getModules(expDesc2)
    self.assertEqual(base.config, newBase.config)


    # --------------------------------------
    # If we specify NonTemporalClassification, prediction steps MUST be [0]
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2['inferenceType'] = 'NontemporalClassification'
    expDesc2['inferenceArgs']['predictionSteps'] = [1]
    gotException = False
    try:
      (newBase, _newPerms) = self.getModules(expDesc2)
    except:
      gotException = True
    self.assertTrue(gotException)
    
    
    # --------------------------------------
    # If we specify NonTemporalClassification, inferenceArgs.inputPredictedField
    #  can not be 'yes'
    expDesc2 = copy.deepcopy(expDesc)
    expDesc2["inferenceArgs"]["inputPredictedField"] = "yes"
    gotException = False
    try:
      (newBase, _newPerms) = self.getModules(expDesc2)
    except:
      gotException = True
    self.assertTrue(gotException)
    

    return



def _executeExternalCmdAndReapStdout(args):
  """
  args:     Args list as defined for the args parameter in subprocess.Popen()

  Returns:  result dicionary:
              {
                'exitStatus':<exit-status-of-external-command>,
                'stdoutData':"string",
                'stderrData':"string"
              }
  """

  _debugOut(("_executeExternalCmdAndReapStdout: Starting...\n<%s>") % \
                (args,))

  p = subprocess.Popen(args,
                       env=os.environ,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
  _debugOut(("Process started for <%s>") % (args,))

  (stdoutData, stderrData) = p.communicate()
  _debugOut(("Process completed for <%s>: exit status=%s, " +
             "stdoutDataType=%s, stdoutData=<%s>, stderrData=<%s>") % \
                (args, p.returncode, type(stdoutData), stdoutData, stderrData))

  result = dict(
    exitStatus = p.returncode,
    stdoutData = stdoutData,
    stderrData = stderrData,
  )

  _debugOut(("_executeExternalCmdAndReapStdout for <%s>: result=\n%s") % \
                (args, pprint.pformat(result, indent=4)))

  return result


def _debugOut(text):
  if g_debug:
    LOGGER.info(text)

  return


def _getTestList():
  """ Get the list of tests that can be run from this module"""

  suiteNames = ['PositiveExperimentTests']
  testNames = []
  for suite in suiteNames:
    for f in dir(eval(suite)):
      if f.startswith('test'):
        testNames.append('%s.%s' % (suite, f))

  return testNames



if __name__ == '__main__':
  LOGGER.info("\nCURRENT DIRECTORY: %s", os.getcwd())

  helpString = \
  """%prog [options] [suitename.testname | suitename]...
  Run the Hypersearch unit tests. Available suitename.testnames: """

  # Update help string
  allTests = _getTestList()
  for test in allTests:
    helpString += "\n    %s" % (test)


  # ============================================================================
  # Process command line arguments
  parser = OptionParser(helpString)


  # Our custom options (that don't get passed to unittest):
  customOptions = ['--installDir', '--verbosity', '--logLevel']

  parser.add_option("--installDir", dest="installDir",
        default=resource_filename("nupic", ""),
        help="Path to the NTA install directory [default: %default].")

  parser.add_option("--verbosity", default=0, type="int",
        help="Verbosity level, either 0, 1, 2, or 3 [default: %default].")

  parser.add_option("--logLevel", action="store", type="int",
        default=logging.INFO,
        help="override default log level. Pass in an integer value that "
        "represents the desired logging level (10=logging.DEBUG, "
        "20=logging.INFO, etc.) [default: %default].")

  # The following are put here to document what is accepted by the unittest
  #  module - we don't actually use them in this code bas.
  parser.add_option("--verbose", dest="verbose", default=os.environ['NUPIC'],
        help="Verbose output")
  parser.add_option("--quiet", dest="quiet", default=None,
        help="Minimal output")
  parser.add_option("--failfast", dest="failfast", default=None,
        help="Stop on first failure")
  parser.add_option("--catch", dest="catch", default=None,
        help="Catch control-C and display results")
  parser.add_option("--buffer", dest="buffer", default=None,
        help="Buffer stdout and stderr during test runs")


  (options, args) = parser.parse_args()


  # Setup our environment
  g_myEnv = MyTestEnvironment(options)

  # Remove our private options
  args = sys.argv[:]
  for arg in sys.argv:
    for option in customOptions:
      if arg.startswith(option):
        args.remove(arg)
        break

  # Run the tests
  unittest.main(argv=args)
