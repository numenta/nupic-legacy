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


# SPTMModel-specific experiment task callbacks that may be used
# in setup, postIter, and finish callback lists

import os

from nupic.support.fshelpers import makeDirectoryFromAbsolutePath
from sptmmodel import SPTMModel



def smtpModelControlEnableSPLearningCb(smtpModel):
  """ Enables learning in the CLA model's Spatial Pooler

  See also smtpModelControlDisableSPLearningCb.

  smtpModel:  pointer to a SPTMModel instance

  Returns: nothing
  """

  assert isinstance(smtpModel, SPTMModel)

  smtpModel._getSPRegion().setParameter('learningMode', True)
  return



def smtpModelControlDisableSPLearningCb(smtpModel):
  """ Disables learning in the CLA model's Spatial Pooler, while retaining
  the ability to re-enable SP learning in the future.

  See also: smtpModelControlEnableSPLearningCb.
  See also: modelcallbacks.modelControlFinishLearningCb.

  smtpModel:  pointer to a SPTMModel instance

  Returns: nothing
  """

  assert isinstance(smtpModel, SPTMModel)

  smtpModel._getSPRegion().setParameter('learningMode', False)
  return



def smtpModelControlEnableTPLearningCb(smtpModel):
  """ Enables learning in the CLA model's Temporal Pooler

  See also smtpModelControlDisableTPLearningCb.

  smtpModel:  pointer to a SPTMModel instance

  Returns: nothing
  """

  assert isinstance(smtpModel, SPTMModel)

  smtpModel._getTPRegion().setParameter('learningMode', True)
  return



def smtpModelControlDisableTPLearningCb(smtpModel):
  """ Disables learning in the CLA model's Temporal Pooler, while retaining
  the ability to re-enable TP learning in the future.

  See also: smtpModelControlEnableTPLearningCb.
  See also: modelcallbacks.modelControlFinishLearningCb.

  smtpModel:  pointer to a SPTMModel instance

  Returns: nothing
  """

  assert isinstance(smtpModel, SPTMModel)

  smtpModel._getTPRegion().setParameter('learningMode', False)
  return



class CLAModelPickleSPInitArgs(object):
  """ Saves SP initialization args
  """
  def __init__(self, filePath):
    """
    filePath: path of file where SP __init__ args are to be saved
    """

    self.__filePath = filePath

    return


  def __call__(self, smtpModel):

    import pickle

    # Get the SP args dictionary
    assert isinstance(smtpModel, SPTMModel)

    spRegion = smtpModel._getSPRegion().getSelf()

    sfdr = spRegion._sfdr

    initArgsDict = sfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return



class CLAModelPickleTPInitArgs(object):
  """ Saves TP10X2 initialization args
  """
  def __init__(self, filePath):
    """
    filePath: path of file where TP __init__ args are to be saved
    """

    self.__filePath = filePath

    return


  def __call__(self, smtpModel):

    import pickle

    # Get the TP args dictionary
    assert isinstance(smtpModel, SPTMModel)

    tpRegion = smtpModel._getTPRegion().getSelf()

    tfdr = tpRegion._tfdr

    initArgsDict = tfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return
