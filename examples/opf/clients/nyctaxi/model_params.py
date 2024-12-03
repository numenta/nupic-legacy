# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

MODEL_PARAMS = {
  "inferenceArgs": {
    "predictionSteps": [1],
    "predictedField": "value",
    "inputPredictedField": "auto"
  },
  "aggregationInfo": {
      "seconds": 0,
      "fields": [],
      "months": 0,
      "days": 0,
      "years": 0,
      "hours": 0,
      "microseconds": 0,
      "weeks": 0,
      "minutes": 0,
      "milliseconds": 0
    },
  "model": "HTMPrediction",
  "version": 1,
  "predictAheadTime": None,
  "modelParams": {
    "inferenceType": "TemporalAnomaly",
    "sensorParams": {
      "encoders": {
        "timestamp_timeOfDay": {
          "type": "DateEncoder",
          "timeOfDay": [
            21,
            9.49
          ],
          "fieldname": "timestamp",
          "name": "timestamp"
        },
        "timestamp_dayOfWeek": None,
        "timestamp_weekend": None,
        "value": {
          "name": "value",
          "fieldname": "value",
          "seed": 42,
          "numBuckets":130,
          "type": "RandomDistributedScalarEncoder"
        }
      },
      "sensorAutoReset": None,
      "verbosity": 0
    },
    "spEnable": True,
    "spParams": {
      "spatialImp": "cpp",
      "potentialPct": 0.8,
      "columnCount": 2048,
      "globalInhibition": 1,
      "inputWidth": 0,
      "boostStrength": 0.0,
      "numActiveColumnsPerInhArea": 40,
      "seed": 1956,
      "spVerbosity": 0,
      "spatialImp": "cpp",
      "synPermActiveInc": 0.003,
      "synPermConnected": 0.2,
      "synPermInactiveDec": 0.0005
    },
    "trainSPNetOnlyIfRequested": False,
    "tmEnable": True,
    "tmParams": {
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
    "clEnable": False,
    "clParams": {
      "alpha": 0.035828933612157998,
      "regionName": "SDRClassifierRegion",
      "steps": "1",
      "verbosity": 0
    },
    "anomalyParams": {
      "anomalyCacheRecords": None,
      "autoDetectThreshold": None,
      "autoDetectWaitRecords": 5030
    }
  }
}
