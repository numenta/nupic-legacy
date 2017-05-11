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

"""External API for hypersearch-related functions."""

import json
import os
import shutil
import tempfile

from nupic.frameworks.opf import helpers
from nupic.database.client_jobs_dao import ClientJobsDAO
from nupic.support.configuration import Configuration


def createAndStartSwarm(client, clientInfo="", clientKey="", params="",
                        minimumWorkers=None, maximumWorkers=None,
                        alreadyRunning=False):
  """Create and start a swarm job.

  Args:
    client - A string identifying the calling client. There is a small limit
        for the length of the value. See ClientJobsDAO.CLIENT_MAX_LEN.
    clientInfo - JSON encoded dict of client specific information.
    clientKey - Foreign key. Limited in length, see ClientJobsDAO._initTables.
    params - JSON encoded dict of the parameters for the job. This can be
        fetched out of the database by the worker processes based on the jobID.
    minimumWorkers - The minimum workers to allocate to the swarm. Set to None
        to use the default.
    maximumWorkers - The maximum workers to allocate to the swarm. Set to None
        to use the swarm default. Set to 0 to use the maximum scheduler value.
    alreadyRunning - Insert a job record for an already running process. Used
        for testing.
  """
  if minimumWorkers is None:
    minimumWorkers = Configuration.getInt(
        "nupic.hypersearch.minWorkersPerSwarm")
  if maximumWorkers is None:
    maximumWorkers = Configuration.getInt(
        "nupic.hypersearch.maxWorkersPerSwarm")

  return ClientJobsDAO.get().jobInsert(
      client=client,
      cmdLine="$HYPERSEARCH",
      clientInfo=clientInfo,
      clientKey=clientKey,
      alreadyRunning=alreadyRunning,
      params=params,
      minimumWorkers=minimumWorkers,
      maximumWorkers=maximumWorkers,
      jobType=ClientJobsDAO.JOB_TYPE_HS)



def getSwarmModelParams(modelID):
  """Retrieve the Engine-level model params from a Swarm model

  Args:
    modelID - Engine-level model ID of the Swarm model

  Returns:
    JSON-encoded string containing Model Params
  """

  # TODO: the use of nupic.frameworks.opf.helpers.loadExperimentDescriptionScriptFromDir when
  #  retrieving module params results in a leakage of pf_base_descriptionNN and
  #  pf_descriptionNN module imports for every call to getSwarmModelParams, so
  #  the leakage is unlimited when getSwarmModelParams is called by a
  #  long-running process.  An alternate solution is to execute the guts of
  #  this function's logic in a seprate process (via multiprocessing module).

  cjDAO = ClientJobsDAO.get()

  (jobID, description) = cjDAO.modelsGetFields(
    modelID,
    ["jobId", "genDescription"])

  (baseDescription,) = cjDAO.jobGetFields(jobID, ["genBaseDescription"])

  # Construct a directory with base.py and description.py for loading model
  # params, and use nupic.frameworks.opf.helpers to extract model params from
  # those files
  descriptionDirectory = tempfile.mkdtemp()
  try:
    baseDescriptionFilePath = os.path.join(descriptionDirectory, "base.py")
    with open(baseDescriptionFilePath, mode="wb") as f:
      f.write(baseDescription)

    descriptionFilePath = os.path.join(descriptionDirectory, "description.py")
    with open(descriptionFilePath, mode="wb") as f:
      f.write(description)

    expIface = helpers.getExperimentDescriptionInterfaceFromModule(
      helpers.loadExperimentDescriptionScriptFromDir(descriptionDirectory))

    return json.dumps(
      dict(
        modelConfig=expIface.getModelDescription(),
        inferenceArgs=expIface.getModelControl().get("inferenceArgs", None)))
  finally:
    shutil.rmtree(descriptionDirectory, ignore_errors=True)
