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

""" @file modelfactory.py

 Model factory.
"""

import logging

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

    return modelClass(**modelConfig['modelParams'])

  @staticmethod
  def loadFromCheckpoint(savedModelDir):
    """ Load saved model.
    @param savedModelDir (string)
           Directory of where the experiment is to be or was saved
    @returns (nupic.frameworks.opf.model.Model) The loaded model instance.
    """
    return Model.load(savedModelDir)
