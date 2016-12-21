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

import os
import tempfile
import unittest

from datetime import datetime
from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import MultiEncoder, ScalarEncoder
from nupic.engine import Network


def _getTempFileName():
  """Creates unique test csv file name."""
  handle = tempfile.NamedTemporaryFile(prefix="test", suffix=".csv", dir=".")
  filename = handle.name
  handle.close()

  return filename



class MulticlassKNNTest(unittest.TestCase):
  """
  A simple end to end to end test of a RecordSensor->KNNClassifier network,
  where the data records each contain multiple categories.
  """
  
  def testSimpleMulticlassNetwork(self):
  
    # Setup data record stream of fake data (with three categories)
    filename = _getTempFileName()
    fields = [("timestamp", "datetime", "T"),
              ("value", "float", ""),
              ("reset", "int", "R"),
              ("sid", "int", "S"),
              ("categories", "list", "C")]
    records = (
      [datetime(day=1, month=3, year=2010), 0.0, 1, 0, ""],
      [datetime(day=2, month=3, year=2010), 1.0, 0, 0, "1 2"],
      [datetime(day=3, month=3, year=2010), 1.0, 0, 0, "1 2"],
      [datetime(day=4, month=3, year=2010), 2.0, 0, 0, "0"],
      [datetime(day=5, month=3, year=2010), 3.0, 0, 0, "1 2"],
      [datetime(day=6, month=3, year=2010), 5.0, 0, 0, "1 2"],
      [datetime(day=7, month=3, year=2010), 8.0, 0, 0, "0"],
      [datetime(day=8, month=3, year=2010), 13.0, 0, 0, "1 2"])
    dataSource = FileRecordStream(streamID=filename, write=True, fields=fields)
    for r in records:
      dataSource.appendRecord(list(r))

    # Create the network and get region instances.
    net = Network()
    net.addRegion("sensor", "py.RecordSensor", "{'numCategories': 3}")
    net.addRegion("classifier","py.KNNClassifierRegion",
                  "{'k': 2,'distThreshold': 0,'maxCategoryCount': 3}")
    net.link("sensor", "classifier", "UniformLink", "",
             srcOutput = "dataOut", destInput = "bottomUpIn")
    net.link("sensor", "classifier", "UniformLink", "",
             srcOutput = "categoryOut", destInput = "categoryIn")
    sensor = net.regions["sensor"]
    classifier = net.regions["classifier"]
    
    # Setup sensor region encoder and data stream.
    dataSource.close()
    dataSource = FileRecordStream(filename)
    sensorRegion = sensor.getSelf()
    sensorRegion.encoder = MultiEncoder()
    sensorRegion.encoder.addEncoder(
        "value", ScalarEncoder(21, 0.0, 13.0, n=256, name="value"))
    sensorRegion.dataSource = dataSource
    
    # Get ready to run.
    net.initialize()

    # Train the network (by default learning is ON in the classifier, but assert
    # anyway) and then turn off learning and turn on inference mode.
    self.assertEqual(classifier.getParameter("learningMode"), 1)
    net.run(8)
    classifier.setParameter("inferenceMode", 1)
    classifier.setParameter("learningMode", 0)

    # Assert learning is OFF and that the classifier learned the dataset.
    self.assertEqual(classifier.getParameter("learningMode"), 0,
        "Learning mode is not turned off.")
    self.assertEqual(classifier.getParameter("inferenceMode"), 1,
        "Inference mode is not turned on.")
    self.assertEqual(classifier.getParameter("categoryCount"), 3,
        "The classifier should count three total categories.")
    # classififer learns 12 patterns b/c there are 12 categories amongst the
    # records:
    self.assertEqual(classifier.getParameter("patternCount"), 12,
        "The classifier should've learned 12 samples in total.")

    # Test the network on the same data as it trained on; should classify with
    # 100% accuracy.
    expectedCats = ([0.0, 0.5, 0.5],
                    [0.0, 0.5, 0.5],
                    [0.0, 0.5, 0.5],
                    [0.5, 0.5, 0.0],
                    [0.0, 0.5, 0.5],
                    [0.0, 0.5, 0.5],
                    [0.5, 0.5, 0.0],
                    [0.0, 0.5, 0.5])
    dataSource.rewind()
    for i in xrange(8):
      net.run(1)
      inferredCats = classifier.getOutputData("categoriesOut")
      self.assertSequenceEqual(expectedCats[i], inferredCats.tolist(),
          "Classififer did not infer expected category probabilites for record "
          "number {}.".format(i))
    
    # Close data stream, delete file.
    dataSource.close()
    os.remove(filename)


if __name__ == "__main__":
  unittest.main()
