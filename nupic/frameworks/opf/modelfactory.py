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

""" @file modelfactory.py

 Model factory.
"""

import logging
import random

import nupic.frameworks.opf.opfutils as opfutils

# Import models
from clamodel import CLAModel
from model import Model
from two_gram_model import TwoGramModel
from previousvaluemodel import PreviousValueModel

class ModelFactory(object):
  """ Static factory class that produces a Model based on a description dict.
  Eventually this will be the source for all Model creation, CLA and otherwise.
  We may also implement building the description dict from a database or a
  description.py file. For now, this is a very skeletal implementation.
  """
  __logger = None


  @classmethod
  def __getLogger(cls):
    """ Get the logger for this object.
    @returns (Logger) A Logger object.
    """
    if cls.__logger is None:
      cls.__logger = opfutils.initLogger(cls)
    return cls.__logger


  @staticmethod
  def create(modelConfig, logLevel=logging.ERROR):
    """ Create a new model instance, given a description dictionary.
    @param modelConfig (dict)
           A dictionary describing the current model (TODO: schema)
    @param logLevel (int) The level of logging output that should be generated
    @exception (Exception) Unsupported model type
    @returns (nupic.frameworks.opf.model.Model) A model.
    """
    logger = ModelFactory.__getLogger()
    logger.setLevel(logLevel)
    logger.debug("ModelFactory returning Model from dict: %s", modelConfig)

    modelClass = None
    if modelConfig['model'] == "CLA":
      modelClass = CLAModel
    elif modelConfig['model'] == "TwoGram":
      modelClass = TwoGramModel
    elif modelConfig['model'] == "PreviousValue":
      modelClass = PreviousValueModel
    else:
      raise Exception("ModelFactory received unsupported Model type: %s" % \
                      modelConfig['model'])

    model = modelClass(**modelConfig['modelParams'])
    
    name = modelConfig.get("name", None)
    if name is not None:
      model._name = name
    else:
      model._name = random.randint(0,10000)
    ModelFactory._addGlobalModel(model)
    return model


  @staticmethod
  def loadFromCheckpoint(savedModelDir):
    """ Load saved model.
    @param savedModelDir (string)
           Directory of where the experiment is to be or was saved
    @returns (nupic.frameworks.opf.model.Model) The loaded model instance.
    """
    model = Model.load(savedModelDir)
    ModelFactory._addGlobalModel(model)
    return model


  @staticmethod
  def _addGlobalModel(newModel, logLevel=logging.ERROR):
    """ add a model to the global storage, used ie in Metrics
        Models are stored in a global variable 'globalModelsStorage' 
        and can be later accessed by name.
        @param newModel - instance of Model to add
    """
    global globalModelsStorage
    for model in globalModelsStorage:
      if model._name == newModel._name:
        raise ValueError("addGlobalModel: failed as model '%s' already exists." % model._name)
    globalModelsStorage.append(newModel)
  
    print "Globally stored model '%s' " % (newModel._name)

  
  @staticmethod
  def getGlobalModel(name):
    """
    access models in global storage 'globalModelsStorage' by name
    @return found model instance, or None when there is no such model with given name
    """
    global globalModelsStorage
    for m in globalModelsStorage:
      if m._name == name:
        return m
    return None

###################
# global variable
globalModelsStorage=[]

