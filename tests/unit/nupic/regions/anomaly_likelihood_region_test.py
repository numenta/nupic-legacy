# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import tempfile
import unittest
import random
import csv
import numpy

try:
  import capnp
except ImportError:
  capnp = None
if capnp:
  from nupic.algorithms.anomaly_likelihood_capnp import\
    AnomalyLikelihoodProto as AnomalyLikelihoodRegionProto

from nupic.regions.anomaly_likelihood_region import AnomalyLikelihoodRegion
from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
from pkg_resources import resource_filename


_INPUT_DATA_FILE = resource_filename(
  "nupic.datafiles", "extra/hotgym/hotgym-anomaly.csv"
)

""" Unit tests for the anomaly likelihood region """


class AnomalyLikelihoodRegionTest(unittest.TestCase):
  """Tests for anomaly likelihood region"""

  def testParamterError(self):
    """ ensure historicWindowSize is greater than estimationSamples """
    try:
      anomalyLikelihoodRegion = AnomalyLikelihoodRegion(estimationSamples=100,
                                                        historicWindowSize=99)
      self.assertEqual(False, True, "Should have failed with ValueError")
    except ValueError:
      pass

  def testLikelihoodValues(self):
    """ test to see if the region keeps track of state correctly and produces
        the same likelihoods as the AnomalyLikelihood module """
    anomalyLikelihoodRegion = AnomalyLikelihoodRegion()
    anomalyLikelihood = AnomalyLikelihood()

    inputs = AnomalyLikelihoodRegion.getSpec()['inputs']
    outputs = AnomalyLikelihoodRegion.getSpec()['outputs']
    with open (_INPUT_DATA_FILE) as f:
      reader = csv.reader(f)
      reader.next()
      for record in reader:
        consumption = float(record[1])
        anomalyScore = float(record[2])
        likelihood1 = anomalyLikelihood.anomalyProbability(
          consumption, anomalyScore)

        inputs['rawAnomalyScore'] = numpy.array([anomalyScore])
        inputs['metricValue'] = numpy.array([consumption])
        anomalyLikelihoodRegion.compute(inputs, outputs)
        likelihood2 = outputs['anomalyLikelihood'][0]

        self.assertEqual(likelihood1, likelihood2)

  @unittest.skipUnless(
    capnp, "pycapnp is not installed, skipping serialization test.")
  def testSerialization(self):
    """ test to ensure serialization preserves the state of the region
        correctly. """
    anomalyLikelihoodRegion1 = AnomalyLikelihoodRegion()
    inputs = AnomalyLikelihoodRegion.getSpec()['inputs']
    outputs = AnomalyLikelihoodRegion.getSpec()['outputs']
    parameters = AnomalyLikelihoodRegion.getSpec()['parameters']

    # Make sure to calculate distribution by passing the probation period
    learningPeriod = parameters['learningPeriod']['defaultValue']
    reestimationPeriod = parameters['reestimationPeriod']['defaultValue']
    probation = learningPeriod + reestimationPeriod
    for _ in xrange(0, probation + 1):
      inputs['rawAnomalyScore'] = numpy.array([random.random()])
      inputs['metricValue'] = numpy.array([random.random()])
      anomalyLikelihoodRegion1.compute(inputs, outputs)
      score1 = outputs['anomalyLikelihood'][0]

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

    window = parameters['historicWindowSize']['defaultValue']
    for _ in xrange(0, window + 1):
      inputs['rawAnomalyScore'] = numpy.array([random.random()])
      inputs['metricValue'] = numpy.array([random.random()])
      anomalyLikelihoodRegion1.compute(inputs, outputs)
      score1 = outputs['anomalyLikelihood'][0]
      anomalyLikelihoodRegion2.compute(inputs, outputs)
      score2 = outputs['anomalyLikelihood'][0]
      self.assertEqual(score1, score2)


if __name__ == "__main__":
  unittest.main()
