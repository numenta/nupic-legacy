#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
Groups together code used for creating a NuPIC model and dealing with IO.
(This is a component of the One Hot Gym Prediction Tutorial.)
"""
import importlib
import os
import sys

from nupic.frameworks.opf.modelfactory import ModelFactory

from io_helper import runIoThroughNupic


GYM_NAME = "rec-center-hourly"
DATA_DIR = "."
MODEL_PARAMS_DIR = "./model_params"
DESCRIPTION = (
  "Starts a NuPIC model from the model params returned by the swarm\n"
  "and pushes each line of input from the gym into the model. Results\n"
  "are written to an output file (default) or plotted dynamically if\n"
  "the --plot option is specified.\n"
  "NOTE: You must run ./swarm.py before this, because model parameters\n"
  "are required to run NuPIC.\n"
)


def createModel(modelParams):
  model = ModelFactory.create(modelParams)
  model.enableInference({"predictedField": "kw_energy_consumption"})
  return model



def getModelParamsFromName(gymName):
  importName = "model_params.%s_model_params" % (
    gymName.replace(" ", "_").replace("-", "_")
  )
  print "Importing model params from %s" % importName
  try:
    importedModelParams = importlib.import_module(importName).MODEL_PARAMS
  except ImportError:
    raise Exception("No model params exist for '%s'. Run swarm first!"
                    % gymName)
  return importedModelParams



def runModel(gymName, plot=False):
  print "Creating model from %s..." % gymName
  model = createModel(getModelParamsFromName(gymName))
  inputData = ["%s/%s.csv" % (DATA_DIR, gymName.replace(" ", "_"))]
  runIoThroughNupic(inputData, [model], [gymName], plot)



def runAllModels(plot=False):
  models = []
  names = []
  inputFiles = []
  for inputFile in sorted(os.listdir(DATA_DIR)):
    name = os.path.splitext(inputFile)[0]
    names.append(name)
    inputFiles.append(os.path.abspath(os.path.join(DATA_DIR, inputFile)))
    models.append(createModel(getModelParamsFromName(name)))
  runIoThroughNupic(inputFiles, models, names, plot)



if __name__ == "__main__":
  print DESCRIPTION
  plot = False
  args = sys.argv[1:]
  if "--plot" in args:
    plot = True
  runModel(GYM_NAME, plot=plot)