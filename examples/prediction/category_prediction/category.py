# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2018, Numenta, Inc.  Unless you have an agreement
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
This example shows how to use the `CategoryEncoder` with `HTMPredictionModel`.

This model uses the [MSNBC.com Anonymous Web Data Data Set][1] provided by
[UCI Machine Learning Repository][2] to predict the next page the user is more
likely to click. Each page is assigned a category and the user behavior is
recorded as navigating from one page category to another. The dataset contains
one user session per line. See [dataset][1] description for more information.

For the purpose of this demonstration, the model will be trained on the
first 100 user sessions and try to predict a random session from the learned
sessions.

References:
  1: https://archive.ics.uci.edu/ml/datasets/MSNBC.com+Anonymous+Web+Data
  2: Lichman, M. (2013). UCI Machine Learning Repository [http://archive.ics.uci.edu/ml].
     Irvine, CA: University of California, School of Information and Computer Science
"""
import os
import random
import sys
import zipfile
from operator import itemgetter

from nupic.frameworks.opf.model_factory import ModelFactory

# List of categories in the dataset
CATEGORIES = {
  "1": "frontpage", "2": "news", "3": "tech", "4": "local", "5": "opinion",
  "6": "on-air", "7": "misc", "8": "weather", "9": "msn-news", "10": "health",
  "11": "living", "12": "business", "13": "msn-sports", "14": "sports",
  "15": "summary", "16": "bbs", "17": "travel"
}

# HTM Prediction Model Parameters
MODEL_PARAMS = {
  "model": "HTMPrediction",
  "version": 1,
  "predictAheadTime": None,

  "modelParams": {
    "inferenceType": "TemporalMultiStep",
    "sensorParams": {
      "verbosity": 0,
      "encoders": {

        # Category encoder used for web page categories
        "category": {
          "fieldname": u"category",
          "name": u"category",
          "type": "CategoryEncoder",
          "categoryList": CATEGORIES.keys(),
          "w": 21
        },
      },
      "sensorAutoReset": None,
    },

    # No need to use SP for this dataset
    "spEnable": False,
    "spParams": {
    },
    "tmEnable": True,
    "tmParams": {
      'seed': 1960,
      'temporalImp': 'cpp',
      'globalDecay': 0.0,
      'initialPerm': 0.21,
      'inputWidth': 2048,
      'maxAge': 0,
      'outputType': 'normal',
      'pamLength': 2,
      'permanenceDec': 0.1,
      'permanenceInc': 0.1,
      'verbosity': 0,
      'activationThreshold': 13,
      'cellsPerColumn': 32,
      'columnCount': 2048,
      'maxSegmentsPerCell': 128,
      'maxSynapsesPerSegment': 32,
      'minThreshold': 10,
      'newSynapseCount': 20,

    },
    "clParams": {
      'implementation': 'cpp',
      "regionName": "SDRClassifierRegion",
      "verbosity": 0,
      "alpha": 0.01,
      "steps": "1",
    },
  },
}



def main():
  # Create HTM Prediction model and enable inference on the "category" field
  model = ModelFactory.create(MODEL_PARAMS)
  model.enableInference({"predictedField": "category"})

  # Assumes data file is in same directory as the script
  datafile = os.path.join(os.path.dirname(__file__), "msnbc990928.zip")
  with zipfile.ZipFile(datafile) as archive:

    sessions = set()
    # Extract data file from archive
    with archive.open("msnbc990928.seq") as data:

      # Skip header lines (7 lines)
      for _ in xrange(7):
        next(data)

      print "Start Learning"
      model.enableLearning()
      count = 0
      for line in data:
        # Learn distinct user sessions
        if line in sessions:
          continue

        # Select user sessions with 2 or more pages
        pages = line.split()
        if len(pages) < 2:
          continue

        # Train model using the first 100 users sessions
        count += 1
        if count == 100:
          break

        # Simple progress status
        sys.stdout.write("\r{} Sessions".format(count))
        sys.stdout.flush()

        # Keep track of learned user session
        sessions.add(line)

        # Present each user session 10 times
        for _ in xrange(10):
          # Learn each user session as a single sequence
          model.resetSequenceStates()
          for category in pages:
            model.run({"category": category})

      model.disableLearning()
      print
      print "Finished Learning"

  # Infer random user session
  pages = random.choice(list(sessions)).split()
  model.resetSequenceStates()
  for category in pages:
    result = model.run({"category": category})
    inferences = result.inferences["multiStepPredictions"][1]

    # Print inferences
    predictions = map(lambda i: (CATEGORIES[i[0]], i[1]),
                      sorted(inferences.items(), key=itemgetter(1),
                             reverse=True))
    print "{} => ".format(CATEGORIES[category]), predictions



if __name__ == "__main__":
  random.seed(1)
  main()
