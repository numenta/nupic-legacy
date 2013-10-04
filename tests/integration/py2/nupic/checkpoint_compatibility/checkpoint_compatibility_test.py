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

import os
import sys
import tempfile
import json
import copy
import hashlib
import shutil
import pprint
import pkg_resources
import time
import random
import collections
import cPickle as pickle
from datetime import datetime, timedelta
from subprocess import CalledProcessError, PIPE, Popen, check_call

from nupic.frameworks.opf.exp_generator.ExpGenerator import expGenerator
from nupic.frameworks.opf import opfhelpers
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.opfutils import InferenceType
from nupic.support.unittesthelpers.testcasebase import (unittest,
                                                        TestOptionParser,
                                                        TestCaseBase)

_TRAVIS = "TRAVIS" in os.environ

extraDataFolder = "test_data"

experimentDesc = {
    "inferenceType": InferenceType.TemporalMultiStep,
    "environment": "grok",
    "inferenceArgs": {
        "predictionSteps": [1],
        "predictedField": "value1"
    },
    "streamDef": dict(
      version = 1,
      info = "checkpoint_test_dummy",
      streams = [
        dict(source="file://joined_mosman_2011.csv",
             info="checkpoint_test_dummy",
             columns=["*"],
             ),
        ],
      ),
    "includedFields": [
        {
            "fieldName": "TimeStamp",
            "fieldType": "datetime"
        },
        {
            "fieldName": "value1",
            "fieldType": "float"
        },
        {
            "fieldName": "value2",
            "fieldType": "string"
        }
    ]
}



class CompatibilityTest(TestCaseBase):
  """ Tests to make sure that serialized models in production can be
  deserialized properly"""


  @unittest.skipIf(_TRAVIS, "Test only works on Python 2.6.7, skipping on Travis.")
  def testCLAPredictionModelCompatibility(self):
    """
    Test whether a prediction model checkpoint can be deserialized
    successfully. Currently, this tests only checks to see if any exceptions
    are thrown, and that the results of a serialized model are the same as an
    unserialized models
    """

    description = copy.deepcopy(experimentDesc)

    newCheckpoint, newModel = self._saveModel(description, "prediction")
    self.assertPredictionResultsEqual(model=newModel, checkpoint=newCheckpoint)
    self.assertCheckpointsCompatible("prediction")
    self.assertNoUntrackedCheckpoints("prediction")


  @unittest.skipIf(_TRAVIS, "Test only works on Python 2.6.7, skipping on Travis.")
  def testCLAAnomalyModelCompatibility(self):
    """
    Tests that old anomaly models can be deserialized, as well as that
    the same results are returned by serialized and in-memory models
    """
    description = copy.deepcopy(experimentDesc)
    description["inferenceType"] = InferenceType.TemporalAnomaly
    description["anomalyParams"] = dict(
        autoDetectThreshold=1,
        autoDetectWaitRecords=10,
        anomalyCacheRecords=1000
    )
    newCheckpoint, newModel = self._saveModel(description, "anomaly")

    self.assertPredictionResultsEqual(model=newModel, checkpoint=newCheckpoint,
                                      inferenceElements=["multiStepPredictions",
                                                         "anomalyScore",
                                                         "anomalyLabel"])
    self.assertCheckpointsCompatible("anomaly")
    self.assertNoUntrackedCheckpoints("anomaly")


  def testCLAAnomalyModelConsistency(self):
    """
    Tests that the same model checkpointed twice has the same state in each
    version.
    """
    description = copy.deepcopy(experimentDesc)
    description["inferenceType"] = InferenceType.TemporalAnomaly
    description["anomalyParams"] = dict(
        autoDetectThreshold=1,
        autoDetectWaitRecords=10,
        anomalyCacheRecords=1000
    )

    model = _createModel(description)

    # Train the model with half the data
    for record in self._getRecordsBeforeCheckpoint():
      model.run(record)
    for record in self._getRecordsAfterCheckpoint():
      result = model.run(record)

    # Create a model checkpoint
    modelSaveDir = tempfile.mkdtemp()
    checkpointDir = os.path.join(modelSaveDir, "checkpoint")
    model.save(checkpointDir)

    # Create a model checkpoint
    modelSaveDir2 = tempfile.mkdtemp()
    checkpointDir2 = os.path.join(modelSaveDir2, "checkpoint")
    model.save(checkpointDir2)

    model2 = ModelFactory.loadFromCheckpoint(checkpointDir)
    model3 = ModelFactory.loadFromCheckpoint(checkpointDir2)

    knn1 = model._getAnomalyClassifier().getSelf()
    knn2 = model2._getAnomalyClassifier().getSelf()
    knn3 = model3._getAnomalyClassifier().getSelf()

    print "Comparing Anomaly Classifier Regions:"
    print "  Comparing Original to First Checkpoint..."
    self.assertEqual(knn1.diff(knn2), [])
    print "  Comparing Original to Second Checkpoint..."
    self.assertEqual(knn1.diff(knn3), [])
    print "done"

    # TODO: Rest fails - see NUP-1864
    # Model diverges after many records following an uncheckpointing
    # print "Running more records with uncheckpointed models..."
    # for record in self._getRecordsAfterCheckpoint():
    #   model.run(record)
    #   model2.run(record)
    #   model3.run(record)

    # for record in self._getRecordsAfterCheckpoint():
    #   model.run(record)
    #   model2.run(record)
    #   model3.run(record)

    # knn1 = model._getAnomalyClassifier().getSelf()
    # knn2 = model2._getAnomalyClassifier().getSelf()
    # knn3 = model3._getAnomalyClassifier().getSelf()

    # self.assertEqual(knn2.diff(knn3), [])
    # self.assertEqual(knn1.diff(knn2), [])
    # self.assertEqual(knn1.diff(knn3), [])
    # print "done"


  def assertCheckpointsCompatible(self, checkpointRoot):
    start = time.time()
    print "Testing backwards compatibility of", checkpointRoot, "models..."
    sys.stdout.flush()

    testCheckpoints = self._getTestCheckpoints(checkpointRoot)

    # For all models, run the remaining records through to check for errors.
    for checkpoint in testCheckpoints:
      self.confirmCheckpointValid(checkpoint)

    print "Done: ", time.time() - start, "s"


  def confirmCheckpointValid(self, checkpoint):
    print "   Checking: %s" % (checkpoint)
    model = ModelFactory.loadFromCheckpoint(checkpoint)

    modelDataFolder = os.path.join(checkpoint, extraDataFolder)
    if os.path.exists(modelDataFolder):
      # Load in saved test records
      records = open(os.path.join(modelDataFolder, 'records.json'), 'r').read()
      records = json.loads(records)
      for record in records:
        record['TimeStamp'] = datetime.strptime(record['TimeStamp'],
            "%Y-%m-%d %H:%M:%S")

      # Load in saved test results
      results = open(os.path.join(modelDataFolder, 'results.json'), 'r').read()
      results = json.loads(results)
    else:
      # If not saved records do a quick test with 10 records
      records = self._getRecordsAfterCheckpoint()[:10]
      results = None

    for record in records:
      result = model.run(record)
      if results is not None:
        savedResult = results.pop(0)
        for elem in savedResult:
          elemResult = result.inferences[elem]
          elemResultSaved = self.convert(savedResult[elem])

          if type(elemResult) is dict:
            self.assertDictEqual(elemResult, elemResultSaved)
          else:
            self.assertEqual(elemResult, elemResultSaved)


  def convert(self, data):
    if isinstance(data, unicode):
      try:
        return int(data)
      except Exception:
        try:
          return float(data)
        except Exception:
          return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(self.convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(self.convert, data))
    else:
        return data


  def assertPredictionResultsEqual(self, model, checkpoint,
                                   inferenceElements=['multiStepPredictions']):
    if checkpoint is None:
      return
    print ("Checking if in-memory and deserialized models "
           "produce same results..."),
    sys.stdout.flush()

    savedModel = ModelFactory.loadFromCheckpoint(checkpoint)
    savedResults = []
    savedRecords = []

    records = self._getRecordsAfterCheckpoint()[:10]
    for record in records:
      modelInferences = model.run(record)
      savedModelInferences = savedModel.run(record)
      savedValues = dict()
      for elem in inferenceElements:
        result = modelInferences.inferences[elem]
        savedModelResult = savedModelInferences.inferences[elem]

        if type(result) is dict:
          self.assertDictEqual(result, savedModelResult)
        else:
          self.assertEqual(result, savedModelResult)
        savedValues[elem] = result
      recordCopy = copy.deepcopy(record)
      recordCopy['TimeStamp'] = str(recordCopy['TimeStamp'])
      savedRecords.append(recordCopy)
      savedResults.append(savedValues)
    
    os.mkdir(os.path.join(checkpoint, extraDataFolder))

    # Save used records and results for use later to confirm uncheckpointing
    # gives same results.
    savedRecordsPath = os.path.join(checkpoint, extraDataFolder, "records.json")
    savedRecordsFile = open(savedRecordsPath, 'w')
    savedRecordsFile.write(json.dumps(savedRecords, indent=2))
    savedRecordsFile.close()

    savedResultsPath = os.path.join(checkpoint, extraDataFolder, "results.json")
    savedResultsFile = open(savedResultsPath, 'w')
    savedResultsFile.write(json.dumps(savedResults, indent=2))
    savedResultsFile.close()

    print "Done"

  def assertNoUntrackedCheckpoints(self, checkpointRoot):
    """
    Assert that there are no untracked checkpoints in the checkpoint directory.
    This might happen if the test is run multiple times without cleaning out
    the checkpoint directory.
    """
    start = time.time()
    print "Checking for untracked", checkpointRoot, "models...",
    sys.stdout.flush()

    untrackedCheckpoints = self._getUntrackedCheckpoints(checkpointRoot)
    checkpointRootPath = os.path.join("checkpoints", checkpointRoot)
    checkpointFullPath = pkg_resources.resource_filename(__name__,
                                                         checkpointRootPath)

    self.assertTrue(len(untrackedCheckpoints) == 0,
                         "\n\nFound the following untrackedCheckpoints: \n%s\n"
                         "Commit the appropriate checkpoints to the repository "
                         "and re-run test. Untracked checkpoints are created "
                         "by changes to the model that modify the serialized "
                         "state.\n\n"
                         "To clean out untracked checkpoints, run:\n\t"
                         "git clean -fd %s"
                         % (pprint.pformat(untrackedCheckpoints),
                            checkpointFullPath))

    print "Done: ", time.time() - start, "s"


  def _saveModel(self, expDesc, checkpointRoot):
    model = _createModel(expDesc)

    # Train the model with half the data
    for record in self._getRecordsBeforeCheckpoint():
      model.run(record)

    # Create a model checkpoint
    modelSaveDir = tempfile.mkdtemp()
    checkpointDir = os.path.join(modelSaveDir, "checkpoint")

    start = time.time()
    print "Saving", checkpointRoot, "model...",
    sys.stdout.flush()
    model.save(checkpointDir)
    print "Done :", time.time() - start, "s"

    # Check to see if the current model is a new version of the model
    curHash = _getCheckpointHash(checkpointDir)
    checkpoints = self._getTestCheckpoints(checkpointRoot)

    start = time.time()
    print "Getting ", checkpointRoot, "hashes...",
    sys.stdout.flush()
    testHashes = [_getCheckpointHash(c) for c in checkpoints]
    print "Done :", time.time() - start, "s"

    newVersion = curHash not in testHashes
    
    # If there is a new version, save it to the checkpoints directory
    if newVersion:
      print "Saving new checkpoint", curHash
      try:
        checkDstDir = os.path.join("checkpoints", checkpointRoot)
        checkDstDir = pkg_resources.resource_filename(__name__, checkDstDir)
        checkpointName = "model-%s" % curHash
        check_call("git rev-parse --is-inside-work-tree " + checkDstDir,
                   shell=True)
        dstDir = os.path.join(checkDstDir, checkpointName)
        os.rename(checkpointDir, dstDir)
        return dstDir, model
      except CalledProcessError:
        self.fail(
                  "Tried to add a new checkpoint %s with name %s, but the "
                  "current directory is not a git repository. The checkpoints "
                  "that  exist in the current repository are: \n%s\n This "
                  "indicates that a state change  was made to a model without "
                  "explicitly checking it in to  the repository. \n\nPlease "
                  "commit these changes and re-run. To generate the "
                  "checkpoints, run: python %s from within the repository. "
                  % (checkDstDir, checkpointName,
                     pprint.pformat(checkpoints), __file__))

    return None, model


  def _getTestCheckpoints(self, checkpointRoot):
    checkpointRelPath = os.path.join("checkpoints", checkpointRoot)
    self.assertTrue(pkg_resources.resource_exists(__name__, checkpointRelPath),
                    "Resource %s does not exist" % checkpointRelPath)

    checkpoints = []
    for elem in pkg_resources.resource_listdir(__name__, checkpointRelPath):
      resourceName = os.path.join(checkpointRelPath, elem)
      if pkg_resources.resource_isdir(__name__, resourceName):
        checkpoints.append(pkg_resources.resource_filename(__name__,
                                                          resourceName))

    return checkpoints


  def _getUntrackedCheckpoints(self, checkpointRoot):
    checkpointRootPath = os.path.join("checkpoints", checkpointRoot)
    checkpointFullPath = pkg_resources.resource_filename(__name__,
                                                         checkpointRootPath)

    cmd = 'git ls-files --other --directory --exclude-standard ' \
          + checkpointFullPath
    p = Popen(cmd, shell=True, stdout=PIPE, close_fds=True)
    output = p.stdout.read().strip()
    return output.splitlines()


  def _getRecordsBeforeCheckpoint(self):
    """
    Returns list of records used before the models are checkpointed.

    Change with caution. This will impact previously checkpointed models.
    """
    return [
        {"TimeStamp":datetime(year=2012, month=4, day=4, hour=1),
         "value1": 8.3,
         "value2": "BLUE"},

         {"TimeStamp":datetime(year=2012, month=4, day=4, hour=2),
         "value1": -8.3,
         "value2": "GREEN"},

         {"TimeStamp":datetime(year=2012, month=4, day=4, hour=3),
         "value1": 1.3,
         "value2": "RED"},
    ]


  def _getRecordsAfterCheckpoint(self):
    """
    Returns list of records used to test models after they are loaded in from
    checkpoint.
    """
    records = []
    recordTime = self._getRecordsBeforeCheckpoint()[-1]["TimeStamp"]
    recordTimeDelta = timedelta(hours=1)
    colors = ["RED", "GREEN", "BLUE"]
    for i in range(100):
      if i % 5 == 0:
        recordTime += recordTimeDelta
      records.append({
        "TimeStamp": recordTime,
        "value1": random.random() * 100,
        "value2": colors[i % len(colors)]
      })

    records.extend(records[:20])
    records.extend(records[:20])
    return records


def _createModel(expDesc):
  tempDir = tempfile.mkdtemp()

  expGenerator(["--description=%s" % json.dumps(expDesc),
               "--outDir=%s"%tempDir,
               "--version=v2"])

  modelDesc, _ = opfhelpers.loadExperiment(tempDir)
  model = ModelFactory.create(modelDesc)
  model.enableInference(expDesc["inferenceArgs"])
  return model


def _getCheckpointHash(checkpoint):
  """ Get the md5 hash of a checkpoint tarball"""
  checkSum = hashlib.md5()
  for root, _, files in os.walk(checkpoint):
    for filename in files:
      if filename in ["results.pkl", "records.json", "results.json"]:
        continue
      with open(os.path.join(root, filename)) as f:
        checkSum.update(f.read())
  return checkSum.hexdigest()



if __name__ == "__main__":
  unittest.main()
