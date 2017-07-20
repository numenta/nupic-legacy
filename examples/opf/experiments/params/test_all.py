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

"""Script for trying different model parameters for existing experiments."""

import os
from pprint import pprint
import time

from nupic.frameworks.opf import helpers
from nupic.frameworks.opf.client import Client

# Experiment directories relative to "trunk/examples/opf/experiments."
EXPERIMENTS_FILE = 'successful_experiments.txt'


def testAll(experiments):
  experimentsDir = os.path.join(os.path.split(
      os.path.dirname(__file__))[:-1])[0]
  for experiment in experiments:
    experimentBase = os.path.join(os.getcwd(), experimentsDir, experiment)

    config, control = helpers.loadExperiment(experimentBase)

    if control['environment'] == 'opfExperiment':
      experimentTasks = control['tasks']
      task = experimentTasks[0]
      datasetURI = task['dataset']['streams'][0]['source']

    elif control['environment'] == 'nupic':
      datasetURI = control['dataset']['streams'][0]['source']

    metricSpecs = control['metrics']

    datasetPath = datasetURI[len("file://"):]
    for i in xrange(1024, 2176, 128):
      #config['modelParams']['tmParams']['cellsPerColumn'] = 16
      config['modelParams']['tmParams']['columnCount'] = i
      config['modelParams']['spParams']['columnCount'] = i
      print 'Running with 32 cells per column and %i columns.' % i
      start = time.time()
      result = runOneExperiment(config, control['inferenceArgs'], metricSpecs,
                                datasetPath)
      print 'Total time: %d.' % (time.time() - start)
      pprint(result)


def runOneExperiment(modelConfig, inferenceArgs, metricSpecs, sourceSpec,
                     sinkSpec=None):
  client = Client(modelConfig, inferenceArgs, metricSpecs, sourceSpec, sinkSpec)
  return client.run().metrics


if __name__ == '__main__':
  # Because of the duration of some experiments, it is often better to do one
  # at a time.
  testAll(('anomaly/temporal/saw_big',))
