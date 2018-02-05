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
This example shows how to use the `SDRCategoryEncoder` with `HTMPredictionModel`
to analyze web site traffic data by extracting temporal patterns from user
sessions described as a sequences of web page categories.

We will use the [MSNBC.com Anonymous Web Data][1] data set provided by
[UCI Machine Learning Repository][2] to predict the next page the user is more
likely to click. In this data set each page is assigned a category and the user
behavior is recorded as navigating from one page to another.

Dataset characteristics:

  - Number of users: 989,818
  - Average number of visits per user: 5.7
  - Number of categories: 17
  - Number of URLs per category: 10 to 5,000

See [dataset][1] description for more information.

References:

  1. https://archive.ics.uci.edu/ml/datasets/MSNBC.com+Anonymous+Web+Data
  2. Lichman, M. (2013). UCI Machine Learning Repository [http://archive.ics.uci.edu/ml].
     Irvine, CA: University of California, School of Information and Computer Science
"""
import os
import random
import sys
import zipfile
from operator import itemgetter

import numpy as np
import prettytable
from prettytable import PrettyTable

from nupic.frameworks.opf.model_factory import ModelFactory

# List of page categories used in the dataset
PAGE_CATEGORIES = [
  "frontpage", "news", "tech", "local", "opinion", "on-air", "misc", "weather",
  "msn-news", "health", "living", "business", "msn-sports", "sports", "summary",
  "bbs", "travel"
]

# Configure the sensor/input region using the "SDRCategoryEncoder" to encode
# the page category into SDRs suitable for processing directly by the TM
SENSOR_PARAMS = {
  "verbosity": 0,
  "encoders": {
    "page": {
      "fieldname": "page",
      "name": "page",
      "type": "SDRCategoryEncoder",
      # The output of this encoder will be passed directly to the TM region,
      # therefore the number of bits should match TM's "inputWidth" parameter
      "n": 1024,
      # Use ~2% sparsity
      "w": 21
    },
  },
}

# Configure the temporal memory to learn a sequence of page SDRs and make
# predictions on the next page of the sequence.
TM_PARAMS = {
  "seed": 1960,
  # Use "nupic.bindings.algorithms.TemporalMemoryCPP" algorithm
  "temporalImp": "tm_cpp",
  # Should match the encoder output
  "inputWidth": 1024,
  "columnCount": 1024,
  # Use 1 cell per column for first order prediction.
  # Use more cells per column for variable order predictions.
  "cellsPerColumn": 1,
}

# Configure the output region with a classifier used to decode TM SDRs back
# into pages
CL_PARAMS = {
  "implementation": "cpp",
  "regionName": "SDRClassifierRegion",
  # alpha parameter controls how fast the classifier learns/forgets. Higher
  # values make it adapt faster and forget older patterns faster.
  "alpha": 0.001,
  "steps": 1,
}

# Create a simple HTM network that will receive the current page as input, pass
# the encoded page SDR to the temporal memory to learn the sequences and
# interpret the output SDRs from the temporary memory using the SDRClassifier
# whose output will be a list of predicted next pages and their probabilities.
#
#   page => [encoder] => [TM] => [classifier] => prediction
#
MODEL_PARAMS = {
  "version": 1,
  "model": "HTMPrediction",
  "modelParams": {
    "inferenceType": "TemporalMultiStep",

    "sensorParams": SENSOR_PARAMS,

    # The purpose of the spatial pooler is to create a stable representation of
    # the input SDRs. In our case the category encoder output is already a
    # stable representation of the category therefore adding the spatial pooler
    # to this network would not help and could potentially slow down the
    # learning process
    "spEnable": False,
    "spParams": {},

    "tmEnable": True,
    "tmParams": TM_PARAMS,

    "clParams": CL_PARAMS,
  },
}

TRAINING_RECORDS = 100000



def computeAccuracy(model, size, top):
  """
  Compute prediction accuracy by checking if the next page in the sequence is
  within the top N predictions calculated by the model
  Args:
    model: Trained model
    size: Sample size
    top: top N predictions to use

  Returns: Probability the next page in the sequence is within the top N
           predicted pages
  """
  accuracy = []

  # Load MSNBC web data file
  filename = os.path.join(os.path.dirname(__file__), "msnbc990928.zip")
  with zipfile.ZipFile(filename) as archive:
    with archive.open("msnbc990928.seq") as datafile:
      # Skip header lines (first 7 lines)
      for _ in xrange(7):
        next(datafile)

      # Skip training data and compute accuracy using only new sessions
      for _ in xrange(TRAINING_RECORDS):
        next(datafile)

      # Compute prediction accuracy by checking if the next page in the sequence
      # is within the top N predictions calculated by the model
      for _ in xrange(size):
        pages = readUserSession(datafile)
        model.resetSequenceStates()
        for i in xrange(len(pages) - 1):
          result = model.run({"page": pages[i]})
          inferences = result.inferences["multiStepPredictions"][1]

          # Get top N predictions for the next page
          predicted = sorted(inferences.items(), key=itemgetter(1), reverse=True)[:top]

          # Check if the next page is within the predicted pages
          accuracy.append(1 if pages[i + 1] in zip(*predicted)[0] else 0)

  return np.mean(accuracy)



def readUserSession(datafile):
  """
  Reads the user session record from the file's cursor position
  Args:
    datafile: Data file whose cursor points at the beginning of the record

  Returns:
    list of pages in the order clicked by the user
  """
  for line in datafile:
    pages = line.split()
    total = len(pages)
    # Select user sessions with 2 or more pages
    if total < 2:
      continue

    # Exclude outliers by removing extreme long sessions
    if total > 500:
      continue

    return [PAGE_CATEGORIES[int(i) - 1] for i in pages]
  return []



def main():
  # Create HTM prediction model and enable inference on the page field
  model = ModelFactory.create(MODEL_PARAMS)
  model.enableInference({"predictedField": "page"})

  # Use the model encoder to display the encoded SDRs the model will learn
  sdr_table = PrettyTable(field_names=["Page Category", "Encoded SDR"],
                          sortby="Page Category")
  sdr_table.align = "l"

  encoder = model._getEncoder()
  sdrout = np.zeros(encoder.getWidth(), dtype=np.bool)

  for page in PAGE_CATEGORIES:
    encoder.encodeIntoArray({"page": page}, sdrout)
    sdr_table.add_row([page, sdrout.nonzero()[0]])

  print "The following table shows the encoded SDRs for every page " \
        "category in the dataset"
  print sdr_table

  # At this point our model is configured and ready to learn the user sessions
  # Extract the training data from MSNBC archive and stream it to the model
  filename = os.path.join(os.path.dirname(__file__), "msnbc990928.zip")
  with zipfile.ZipFile(filename) as archive:
    with archive.open("msnbc990928.seq") as datafile:
      # Skip header lines (first 7 lines)
      for _ in xrange(7):
        next(datafile)

      print
      print "Start Learning page sequences using the first {} user " \
            "sessions".format(TRAINING_RECORDS)
      model.enableLearning()
      for count in xrange(TRAINING_RECORDS):
        # Learn each user session as a single sequence
        session = readUserSession(datafile)
        model.resetSequenceStates()
        for page in session:
          model.run({"page": page})

        # Simple progress status
        sys.stdout.write("\rLearned {} Sessions".format(count + 1))
        sys.stdout.flush()

      print "\nFinished Learning"
      model.disableLearning()

      # Use the newly trained model to predict next user session
      # The test data starts right after the training data
      print
      print "Start Inference using a new user session from the dataset"
      prediction_table = PrettyTable(field_names=["Page", "Prediction"],
                                     hrules=prettytable.ALL)
      prediction_table.align["Prediction"] = "l"

      # Infer one page of the sequence at the time
      model.resetSequenceStates()
      session = readUserSession(datafile)
      for page in session:
        result = model.run({"page": page})
        inferences = result.inferences["multiStepPredictions"][1]

        # Print predictions ordered by probabilities
        predicted = sorted(inferences.items(),
                           key=itemgetter(1),
                           reverse=True)
        prediction_table.add_row([page, zip(*predicted)[0]])

      print "User Session to Predict: ", session
      print prediction_table

  print
  print "Compute prediction accuracy by checking if the next page in the " \
        "sequence is within the predicted pages calculated by the model:"
  accuracy = computeAccuracy(model, 100, 1)
  print " - Prediction Accuracy:", accuracy
  accuracy = computeAccuracy(model, 100, 3)
  print " - Accuracy Predicting Top 3 Pages:", accuracy



if __name__ == "__main__":
  random.seed(1)
  np.random.seed(1)
  main()
