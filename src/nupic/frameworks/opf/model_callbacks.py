# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


# Generic model experiment task callbacks that may be used
# in setup, postIter, and finish callback lists



def modelControlFinishLearningCb(model):
  """ Passes the "finish learning" command to the model.  NOTE: Upon completion
  of this command, learning may not be resumed on the given instance of
  the model (e.g., the implementation may prune data structures that are
  necessary for learning)

  model:  pointer to the Model instance

  Returns: nothing
  """

  model.finishLearning()
  return
