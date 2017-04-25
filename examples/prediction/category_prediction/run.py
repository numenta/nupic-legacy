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
from operator import itemgetter
import sys
from collections import defaultdict
import re

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.model_factory import ModelFactory


# Prepare textfile and tokenize:

outfile = file("tokens.txt", "w")
alnum = re.compile(r"\W+")
words = defaultdict(int)
stopwords = []
with open("stopwords.txt") as skip:
  for line in skip:
    line = line[:-1]
    stopwords.append(line)
skip.close()
#print stopwords
with open("20748.txt") as inp:
  inp.seek(129017)
  count = 0
  prev_line = ""
  while True:
    line = inp.readline()
    # print line
    for line in line.split(" "):
      if line == "[Illustration]":
        pass
      token = alnum.sub("", line).lower()
      if token not in stopwords:
        outfile.write(token + "\n")
    if inp.tell() >= 138889:
      break
inp.close()
outfile.close()


# Create and run the model:

MODEL_PARAMS = {
  "model": "HTMPrediction",
  "version": 1,
  "predictAheadTime": None,
  "modelParams": {
    "inferenceType": "TemporalMultiStep",
    "sensorParams": {
      "verbosity" : 0,
      "encoders": {
        "token": {
          "fieldname": u"token",
          "name": u"token",
          "type": "CategoryEncoder",
          "categoryList": list(set(map(str.strip, open("tokens.txt").readlines()))),
          "w": 21
        }
      },
      "sensorAutoReset" : None,
    },
      "spEnable": True,
      "spParams": {
        "spVerbosity" : 0,
        "globalInhibition": 1,
        "columnCount": 2048,
        "inputWidth": 0,
        "numActiveColumnsPerInhArea": 40,
        "seed": 1956,
        "columnDimensions": 0.5,
        "synPermConnected": 0.1,
        "synPermActiveInc": 0.1,
        "synPermInactiveDec": 0.01,
    },

    "tmEnable" : True,
    "tmParams": {
      "verbosity": 0,
        "columnCount": 2048,
        "cellsPerColumn": 32,
        "inputWidth": 2048,
        "seed": 1960,
        "temporalImp": "cpp",
        "newSynapseCount": 20,
        "maxSynapsesPerSegment": 32,
        "maxSegmentsPerCell": 128,
        "initialPerm": 0.21,
        "permanenceInc": 0.1,
        "permanenceDec" : 0.1,
        "globalDecay": 0.0,
        "maxAge": 0,
        "minThreshold": 12,
        "activationThreshold": 16,
        "outputType": "normal",
        "pamLength": 1,
      },
      "clParams": {
        "implementation": "py",
        "regionName" : "SDRClassifierRegion",
        "verbosity" : 0,
        "alpha": 0.0001,
        "steps": "1",
      },
      "trainSPNetOnlyIfRequested": False,
    },
}



model = ModelFactory.create(MODEL_PARAMS)
model.enableInference({"predictedField": "token"})
shifter = InferenceShifter()
out = csv.writer(open("results.csv", "wb"))

with open("tokens.txt") as inp:
  for line in inp:
    token = line.strip()
    modelInput = {"token": token}
    result = shifter.shift(model.run(modelInput))
    if result.inferences["multiStepPredictions"][1]:
      out.writerow([token] + [y for x in sorted(result.inferences["multiStepPredictions"][1].items(), key=itemgetter(1)) for y in x])
