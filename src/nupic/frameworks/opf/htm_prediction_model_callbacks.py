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


# HTMPredictionModel-specific experiment task callbacks that may be used
# in setup, postIter, and finish callback lists

import os

from nupic.support.fs_helpers import makeDirectoryFromAbsolutePath
from htm_prediction_model import HTMPredictionModel



def htmPredictionModelControlEnableSPLearningCb(htmPredictionModel):
  """ Enables learning in the HTMPredictionModel's Spatial Pooler

  See also htmPredictionModelControlDisableSPLearningCb.

  htmPredictionModel:  pointer to a HTMPredictionModel instance

  Returns: nothing
  """

  assert isinstance(htmPredictionModel, HTMPredictionModel)

  htmPredictionModel._getSPRegion().setParameter('learningMode', True)
  return



def htmPredictionModelControlDisableSPLearningCb(htmPredictionModel):
  """ Disables learning in the HTMPredictionModel's Spatial Pooler, while
  retaining the ability to re-enable SP learning in the future.

  See also: htmPredictionModelControlEnableSPLearningCb.
  See also: model_callbacks.modelControlFinishLearningCb.

  htmPredictionModel:  pointer to a HTMPredictionModel instance

  Returns: nothing
  """

  assert isinstance(htmPredictionModel, HTMPredictionModel)

  htmPredictionModel._getSPRegion().setParameter('learningMode', False)
  return



def htmPredictionModelControlEnableTPLearningCb(htmPredictionModel):
  """ Enables learning in the HTMPredictionModel's Temporal Pooler

  See also htmPredictionModelControlDisableTPLearningCb.

  htmPredictionModel:  pointer to a HTMPredictionModel instance

  Returns: nothing
  """

  assert isinstance(htmPredictionModel, HTMPredictionModel)

  htmPredictionModel._getTPRegion().setParameter('learningMode', True)
  return



def htmPredictionModelControlDisableTPLearningCb(htmPredictionModel):
  """ Disables learning in the HTMPredictionModel's Temporal Pooler, while
  retaining the ability to re-enable TM learning in the future.

  See also: htmPredictionModelControlEnableTPLearningCb.
  See also: model_callbacks.modelControlFinishLearningCb.

  htmPredictionModel:  pointer to a HTMPredictionModel instance

  Returns: nothing
  """

  assert isinstance(htmPredictionModel, HTMPredictionModel)

  htmPredictionModel._getTPRegion().setParameter('learningMode', False)
  return



class HTMPredictionModelPickleSPInitArgs(object):
  """ Saves SP initialization args
  """
  def __init__(self, filePath):
    """
    filePath: path of file where SP __init__ args are to be saved
    """

    self.__filePath = filePath

    return


  def __call__(self, htmPredictionModel):

    import pickle

    # Get the SP args dictionary
    assert isinstance(htmPredictionModel, HTMPredictionModel)

    spRegion = htmPredictionModel._getSPRegion().getSelf()

    sfdr = spRegion._sfdr

    initArgsDict = sfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return



class HTMPredictionModelPickleTPInitArgs(object):
  """ Saves BacktrackingTMCPP initialization args
  """
  def __init__(self, filePath):
    """
    filePath: path of file where TM __init__ args are to be saved
    """

    self.__filePath = filePath

    return


  def __call__(self, htmPredictionModel):

    import pickle

    # Get the TM args dictionary
    assert isinstance(htmPredictionModel, HTMPredictionModel)

    tpRegion = htmPredictionModel._getTPRegion().getSelf()

    tfdr = tpRegion._tfdr

    initArgsDict = tfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return
