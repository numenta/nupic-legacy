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

""" @file model_factory.py

 Model factory.
"""

import logging

import nupic.frameworks.opf.opf_utils as opf_utils

# Import models
from htm_prediction_model import HTMPredictionModel
from model import Model
from two_gram_model import TwoGramModel
from previous_value_model import PreviousValueModel

class ModelFactory(object):
  """
  Static factory class that produces a :class:`nupic.frameworks.opf.model.Model`
  based on a description dict.
  """
  __logger = None


  @classmethod
  def __getLogger(cls):
    """ Get the logger for this object.

    :returns: (Logger) A Logger object.
    """
    if cls.__logger is None:
      cls.__logger = opf_utils.initLogger(cls)
    return cls.__logger


  @staticmethod
  def create(modelConfig, logLevel=logging.ERROR):
    """ Create a new model instance, given a description dictionary.

    :param modelConfig: (dict)
           A dictionary describing the current model,
           `described here <../../quick-start/example-model-params.html>`_.

    :param logLevel: (int) The level of logging output that should be generated

    :raises Exception: Unsupported model type

    :returns: :class:`nupic.frameworks.opf.model.Model`
    """
    logger = ModelFactory.__getLogger()
    logger.setLevel(logLevel)
    logger.debug("ModelFactory returning Model from dict: %s", modelConfig)

    modelClass = None
    if modelConfig['model'] == "HTMPrediction":
      modelClass = HTMPredictionModel
    elif modelConfig['model'] == "TwoGram":
      modelClass = TwoGramModel
    elif modelConfig['model'] == "PreviousValue":
      modelClass = PreviousValueModel
    else:
      raise Exception("ModelFactory received unsupported Model type: %s" % \
                      modelConfig['model'])

    return modelClass(**modelConfig['modelParams'])

  @staticmethod
  def loadFromCheckpoint(savedModelDir, newSerialization=False):
    """ Load saved model.

    :param savedModelDir: (string)
           Directory of where the experiment is to be or was saved
    :returns: (:class:`nupic.frameworks.opf.model.Model`) The loaded model
              instance.
    """
    if newSerialization:
      return HTMPredictionModel.readFromCheckpoint(savedModelDir)
    else:
      return Model.load(savedModelDir)
