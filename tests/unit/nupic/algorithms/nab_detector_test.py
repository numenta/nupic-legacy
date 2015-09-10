#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
Test the NuPIC imports run as expected in 
nab/detectors/numenta/numenta_detector.py. They are 
nupic/algorithms/anomaly_likelihood and
nupic/frameworks/opf/modelfactory.ModelFactory. The intent here is not to test
functionality but rather that the functions are able to run in NAB.

NAB repo: https://github.com/numenta/NAB
"""

import copy
import csv
import datetime
import os
import unittest

from nupic.algorithms import anomaly_likelihood as an
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.clamodel import CLAModel
from nupic.support.unittesthelpers.testcasebase import TestCaseBase


def _getDateList(numSamples, startDatetime):
  """
  Generate a sequence of sample dates starting at startDatetime and incrementing
  every 5 minutes.
  
  @param numSamples       (int)         number of datetimes to generate
  @param startDatetime    (datetime)    the start (first) datetime
  @return dateList        (list)        generated sequence of datetimes
  """
  dateList = []
  td = datetime.timedelta(minutes=5)
  currentDate = startDatetime + td
  for _ in xrange(numSamples):
    dateList.append(currentDate)
    currentDate = currentDate + td
  
  return dateList


def _addSampleData(numSamples=20, spikeValue=1.0, spikePeriod=10):
  """
  Add sample anomaly data to the existing/new data list. Data is constant 0.0,
  where anomalies are spikes to 1.0 at an interval set by spikePeriod. The test
  data is trivial, as explicit testing of functions is done in other unit tests.

  @param numSamples   (int)       number of data entries to produce
  @param spikeValue   (float)     value of the anomaly spikes
  @param spikePeriod  (int)       periodicity of anomaly spikes, where one will
                                  occur for every spikePeriod data entries
  @return data        (list)      list of generated data entries
  """
  # Generate datetimes
  lastDate = datetime.datetime(2015, 4, 1)
  dateList = _getDateList(numSamples, lastDate)

  # Generate data with anomaly spikes
  data = []
  for idx, date in enumerate(dateList):
    if (spikePeriod > 0) and ( (idx + 1) % spikePeriod == 0):
      data.append([date, idx, spikeValue])
    else:
      data.append([date, idx, 0.0])

  return data


def _writeToCSV(data, headers, fileName):
  """
  Write list of data to CSV.
  
  @param data       (list)      list of data entries, where each row is a list
  @param headers    (list)      column headers, where each entry in list is
                                a string
  """
  with open(fileName, "wb") as f:
    writer = csv.writer(f, delimiter=",", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(data)



class NABTest(TestCaseBase):
  
  
  def setUp(self):
    # Generate sample data, save to CSV (not used now, but put in place
    # for future NAB tests)
    self.data = _addSampleData()
    self.dataFileName = "temp_data.csv"
    _writeToCSV(self.data, ["datetime", "index", "value"], self.dataFileName)

  
  def tearDown(self):
    os.remove(self.dataFileName)

  
  def testModelCreator(self):
    """
    Tests the ModelFactory.create() method in 
    "nupic/frameworks/opf/modelfactory.py" by creating a new model object, as
    in "NAB/detectors/numenta/numenta_detector.py".
    Model paramaters are same as in NAB v0.8.
    """
    # Create model as in NAB/.../numenta_detector.py
    modelParams = {
                  "aggregationInfo": {
                      "days": 0,
                      "fields": [],
                      "hours": 0,
                      "microseconds": 0,
                      "milliseconds": 0,
                      "minutes": 0,
                      "months": 0,
                      "seconds": 0,
                      "weeks": 0,
                      "years": 0
                  },
                  "model": "CLA",
                  "modelParams": {
                      "anomalyParams": {
                          "anomalyCacheRecords": None,
                          "autoDetectThreshold": None,
                          "autoDetectWaitRecords": 5030
                      },
                      "clEnable": False,
                      "clParams": {
                          "alpha": 0.035828933612158,
                          "clVerbosity": 0,
                          "regionName": "CLAClassifierRegion",
                          "steps": "1"
                      },
                      "inferenceType": "TemporalAnomaly",
                      "sensorParams": {
                          "encoders": {
                              "timestamp_timeOfDay": {
                                  "fieldname": "timestamp",
                                  "name": "timestamp_timeOfDay",
                                  "timeOfDay": [
                                      21,
                                      9.49122334747737
                                  ],
                                  "type": "DateEncoder"
                              },
                              "timestamp_dayOfWeek": None,
                              "timestamp_weekend": None,
                              "value": {
                                  "name": "value",
                                  "fieldname": "value",
                                  "numBuckets": 94.0,
                                  "seed": 42,
                                  "type": "RandomDistributedScalarEncoder"
                              }
                          },
                          "sensorAutoReset": None,
                          "verbosity": 0
                      },
                      "spEnable": True,
                      "spParams": {
                          "potentialPct": 0.8,
                          "columnCount": 2048,
                          "globalInhibition": 1,
                          "inputWidth": 0,
                          "maxBoost": 1.0,
                          "numActiveColumnsPerInhArea": 40,
                          "seed": 1956,
                          "spVerbosity": 0,
                          "spatialImp": "cpp",
                          "synPermActiveInc": 0.0015,
                          "synPermConnected": 0.1,
                          "synPermInactiveDec": 0.0005
                      },
                      "tpEnable": True,
                      "tpParams": {
                          "activationThreshold": 13,
                          "cellsPerColumn": 32,
                          "columnCount": 2048,
                          "globalDecay": 0.0,
                          "initialPerm": 0.21,
                          "inputWidth": 2048,
                          "maxAge": 0,
                          "maxSegmentsPerCell": 128,
                          "maxSynapsesPerSegment": 32,
                          "minThreshold": 10,
                          "newSynapseCount": 20,
                          "outputType": "normal",
                          "pamLength": 3,
                          "permanenceDec": 0.1,
                          "permanenceInc": 0.1,
                          "seed": 1960,
                          "temporalImp": "cpp",
                          "verbosity": 0
                      },
                      "trainSPNetOnlyIfRequested": False
                  },
                  "predictAheadTime": None,
                  "version": 1
                  }
    sensorParams = (modelParams["modelParams"]["sensorParams"]
                               ["encoders"]["value"])
    sensorParams["resolution"] = max(0.001,
      (1.2 - 0.2) / sensorParams.pop("numBuckets"))
    model = ModelFactory.create(modelParams)
    
    self.assertIs(type(model), CLAModel, msg="The created model is not a"
                  "CLAModel, but rather is of type %s" % type(model))


  def testNABAnomalyLikelihood(self):
    """
    Tests the specific calls to nupic/algorithms/anomaly_likelihood as they"re
    made in "NAB/detectors/numenta/numenta_detector.py".
    Note "NAB/.../numenta_detector.py" has its own class AnomalyLikelihood,
    different from nupic/algorithms/anomaly_likelihood.AnomalyLikelihood, but
    which calls the functions estimateAnomalyLikelihoods() and 
    updateAnomalyLikelihoods() from "nupic/algorithms/anomaly_likelihood.py".
    """
    # AnomalyLikelihood object initial values
    iteration = 0
    probationaryPeriod = 4
    historicalScores = []
    
    likelihoodList = []
    for dataPoint in self.data:
      # Ignore the first probationaryPeriod data points
      if len(historicalScores) < probationaryPeriod:
        likelihood = 0.5
      else:
        if iteration % 4 == 0:
          _, _, distribution = an.estimateAnomalyLikelihoods(
                                 historicalScores,
                                 skipRecords = probationaryPeriod)
          likelihoods, _, distribution = an.updateAnomalyLikelihoods(
                                [dataPoint], distribution)
          likelihood = 1.0 - likelihoods[0]
      historicalScores.append(dataPoint)
      iteration += 1
      likelihoodList.append(likelihood)
    
    truthLikelihoodList = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                           0.044565462999999972, 0.044565462999999972,
                           0.044565462999999972, 0.044565462999999972,
                           0.90319951499999995, 0.90319951499999995,
                           0.90319951499999995, 0.90319951499999995,
                           0.78814460099999994, 0.78814460099999994,
                           0.78814460099999994, 0.78814460099999994]
    for i in xrange(len(likelihoodList)):
      self.assertAlmostEqual(likelihoodList[i], truthLikelihoodList[i],
        msg="unequal values are at index %i" % i)


if __name__ == "__main__":
  unittest.main()
