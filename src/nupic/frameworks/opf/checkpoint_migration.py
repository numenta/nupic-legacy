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

"""Provides utility for migrating saved models to the latest version."""

import argparse
import os
import shutil
import tempfile

from nupic.frameworks.opf.modelfactory import ModelFactory



def migrateModel(checkpointDir):
  """Migrates a single model.

  :param checkpointDir: String containing the path to the checkpoint directory.
  """
  model = ModelFactory.loadFromCheckpoint(checkpointDir)

  tempDir = tempfile.mkdtemp()
  try:
    # Write new checkpoint to temporary location.
    tempCheckpointDir = os.path.join(tempDir, "tmp")
    model.writeToCheckpoint(tempCheckpointDir)
    # Delete old checkpoint and move new one to replace it.
    shutil.rmtree(checkpointDir)
    shutil.move(tempCheckpointDir, checkpointDir)
  finally:
    shutil.rmtree(tempDir)



def migrateMultipleModels(checkpointDirs):
  """Migrate multiple model checkpoints.

  :param checkpointDirs: A sequence of strings that contain the checkpoint
      directories.
  """
  for checkpointDir in checkpointDirs:
    migrateModel(checkpointDir)



def migrateCheckpointsMain():
  """Command-line entry point for migrating models.

  Positional arguments are treated as input checkpoints to models be migrated.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("checkpointDirs", metavar="modelCheckpointDir", nargs="+",
                      help="Checkpoint directories to migrate.")
  args = parser.parse_args()
  migrateMultipleModels(args.checkpointDirs)
