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

import os
import logging

import nupic.frameworks.opf.opfutils as opfutils

# Import models
from clamodel import CLAModel
from model import Model
from two_gram_model import TwoGramModel
from previousvaluemodel import PreviousValueModel

class ModelFactory(object):
  """
    Static factory class that produces a Model based on a description dict.
    Eventually this will be the source for all Model creation, CLA and otherwise.
    We may also implement building the description dict from a database or a
    description.py file. For now, this is a very skeletal implementation.

  """
  __logger = None


  @classmethod
  def __getLogger(cls):
    if cls.__logger is None:
      cls.__logger = opfutils.initLogger(cls)
    return cls.__logger


  @staticmethod
  def create(modelConfig, logLevel=logging.ERROR):
    """
    Create a new model instance, given a description dictionary

    Parameters:
    -----------------------------------------------------------------------
    modelParams:      A dictionary describing the current model (TODO: schema)
    logLevel:         The level of logging output that should be generated
    """
    logger = ModelFactory.__getLogger()
    logger.setLevel(logLevel)
    logger.info("ModelFactory returning Model from dict: %s", modelConfig)

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
    """ Load saved model

    Parameters:
    -----------------------------------------------------------------------
    savedModelDir:
                  directory of where the experiment is to be or was saved

    Returns: the loaded model instance
    """
    return Model.load(savedModelDir)
