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


# CLAModel-specific experiment task callbacks that may be used
# in setup, postIter, and finish callback lists

import os

from nupic.support.fshelpers import makeDirectoryFromAbsolutePath
from clamodel import CLAModel



def claModelControlEnableSPLearningCb(claModel):
  """ Enables learning in the CLA model's Spatial Pooler

  See also claModelControlDisableSPLearningCb.

  claModel:  pointer to a CLAModel instance

  Returns: nothing
  """

  assert isinstance(claModel, CLAModel)

  claModel._getSPRegion().setParameter('learningMode', True)
  return



def claModelControlDisableSPLearningCb(claModel):
  """ Disables learning in the CLA model's Spatial Pooler, while retaining
  the ability to re-enable SP learning in the future.

  See also: claModelControlEnableSPLearningCb.
  See also: modelcallbacks.modelControlFinishLearningCb.

  claModel:  pointer to a CLAModel instance

  Returns: nothing
  """

  assert isinstance(claModel, CLAModel)

  claModel._getSPRegion().setParameter('learningMode', False)
  return



def claModelControlEnableTPLearningCb(claModel):
  """ Enables learning in the CLA model's Temporal Pooler

  See also claModelControlDisableTPLearningCb.

  claModel:  pointer to a CLAModel instance

  Returns: nothing
  """

  assert isinstance(claModel, CLAModel)

  claModel._getTPRegion().setParameter('learningMode', True)
  return



def claModelControlDisableTPLearningCb(claModel):
  """ Disables learning in the CLA model's Temporal Pooler, while retaining
  the ability to re-enable TP learning in the future.

  See also: claModelControlEnableTPLearningCb.
  See also: modelcallbacks.modelControlFinishLearningCb.

  claModel:  pointer to a CLAModel instance

  Returns: nothing
  """

  assert isinstance(claModel, CLAModel)

  claModel._getTPRegion().setParameter('learningMode', False)
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


  def __call__(self, claModel):

    import pickle

    # Get the SP args dictionary
    assert isinstance(claModel, CLAModel)

    spRegion = claModel._getSPRegion().getSelf()

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


  def __call__(self, claModel):

    import pickle

    # Get the TP args dictionary
    assert isinstance(claModel, CLAModel)

    tpRegion = claModel._getTPRegion().getSelf()

    tfdr = tpRegion._tfdr

    initArgsDict = tfdr._initArgsDict


    # Write it out to a file as json
    absFilePath = os.path.abspath(self.__filePath)

    absDir = os.path.dirname(absFilePath)
    makeDirectoryFromAbsolutePath(absDir)

    with open(absFilePath, 'wb') as pickleFile:
      pickle.dump(initArgsDict, pickleFile)

    return
