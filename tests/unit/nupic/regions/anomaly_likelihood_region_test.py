#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import tempfile
import unittest
import random

import numpy

from nupic.regions.AnomalyLikelihoodRegion import AnomalyLikelihoodRegion
from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood

from pkg_resources import resource_filename
import csv

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.regions.AnomalyLikelihoodRegion_capnp import AnomalyLikelihoodRegionProto

_INPUT_DATA_FILE = resource_filename(
  "nupic.datafiles", "extra/hotgym/hotgym-anomaly.csv"
)

class AnomalyLikelihoodRegionTest(unittest.TestCase):
  """Tests for anomaly likelihood region"""
  
  def testParamterError(self):
    try:
      anomalyLikelihoodRegion = AnomalyLikelihoodRegion(estimationSamples=100,
                                                        historicWindowSize=99)
      self.assertEqual(False, True, "Should have failed with ValueError")
    except ValueError:
      pass

  def testLikelihoodValues(self):
    anomalyLikelihoodRegion = AnomalyLikelihoodRegion()
    anomalyLikelihood = AnomalyLikelihood()
    
    inputs = AnomalyLikelihoodRegion.getSpec()['inputs']
    outputs = AnomalyLikelihoodRegion.getSpec()['outputs']
    with open (_INPUT_DATA_FILE) as f:
      reader = csv.reader(f)
      headers = reader.next()
      for record in reader:
        consumption = float(record[1])
        anomalyScore = float(record[2])
        likelihood1 = anomalyLikelihood.anomalyProbability(
          consumption, anomalyScore)

        inputs['rawAnomalyScore'] = numpy.array([anomalyScore])
        inputs['value'] = numpy.array([consumption])
        anomalyLikelihoodRegion.compute(inputs, outputs)
        likelihood2 = outputs['anomalyLikelihood'][0]

        self.assertEqual(likelihood1, likelihood2)

  @unittest.skipUnless(
      capnp, "pycapnp is not installed, skipping serialization test.")
  def testSerialization(self):
    anomalyLikelihoodRegion1 = AnomalyLikelihoodRegion()
    inputs = AnomalyLikelihoodRegion.getSpec()['inputs']
    outputs = AnomalyLikelihoodRegion.getSpec()['outputs']
    for i in xrange(0, 6):
      inputs['rawAnomalyScore'] = numpy.array([random.random()])
      inputs['value'] = numpy.array([random.random()])
      anomalyLikelihoodRegion1.compute(inputs, outputs)
      score1 = outputs['anomalyLikelihood'][0]
      # print score1
    proto1 = AnomalyLikelihoodRegionProto.new_message()
    anomalyLikelihoodRegion1.write(proto1)

    # Write the proto to a temp file and read it back into a new proto
    with tempfile.TemporaryFile() as f:
      proto1.write(f)
      f.seek(0)
      proto2 = AnomalyLikelihoodRegionProto.read(f)

    # # Load the deserialized proto

    anomalyLikelihoodRegion2 = AnomalyLikelihoodRegion.read(proto2)
    self.assertEqual(anomalyLikelihoodRegion1, anomalyLikelihoodRegion2)

    for i in xrange(6, 500):
      inputs['rawAnomalyScore'] = numpy.array([random.random()])
      inputs['value'] = numpy.array([random.random()])
      anomalyLikelihoodRegion1.compute(inputs, outputs)
      score1 = outputs['anomalyLikelihood'][0]
      anomalyLikelihoodRegion2.compute(inputs, outputs)
      score2 = outputs['anomalyLikelihood'][0]
      self.assertEqual(score1, score2)


if __name__ == "__main__":
  unittest.main()
