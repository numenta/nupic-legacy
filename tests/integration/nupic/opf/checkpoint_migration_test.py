# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

"""TODO"""

import shutil
import tempfile
import unittest

from nupic.frameworks.opf import checkpoint_migration, clamodel
from nupic.frameworks.opf.common_models import cluster_params



class CheckpointMigrationTest(unittest.TestCase):


  def testCheckpointMigration(self):
    startTime = datetime.datetime.utcnow()
    fiveMin = datetime.timedelta(minutes=5)

    model1Before = cluster_params.getScalarMetricWithTimeOfDayAnomalyParams(
        metricData=[], minVal=0.0, maxVal=100.0)
    model1Before.run({"c0": startTime, "c1": 10.0})
    model1Before.run({"c0": startTime + fiveMin, "c1": 30.0})

    model2Before = cluster_params.getScalarMetricWithTimeOfDayAnomalyParams(
        metricData=[], minVal=0.0, maxVal=100.0)
    model2Before.run({"c0": startTime, "c1": 10.0})
    model2Before.run({"c0": startTime + fiveMin, "c1": 60.0})

    tmp = tempfile.mkdtemp()
    checkpointDir1 = os.path.join(tmp, "checkpoint1")
    checkpointDir2 = os.path.join(tmp, "checkpoint2")
    try:
      model1Before.save(checkpointDir1)
      model2Before.save(checkpointDir2)

      checkpoint_migration.migrateMultipleModels([checkpointDir1, checkpointDir2])

      model1After = modelfactory.loadFromCheckpoint(checkpointDir1)
      model2After = modelfactory.loadFromCheckpoint(checkpointDir2)
    finally:
      shutil.rmtree(tmp)

    model1BeforeResult = model1Before.run({"c0": startTime + (2*fiveMin), 10.0})
    model1AfterResult = model1After.run({"c0": startTime + (2*fiveMin), 10.0})
    self.assertEqual(True, model1BeforeResult)
