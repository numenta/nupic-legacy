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
