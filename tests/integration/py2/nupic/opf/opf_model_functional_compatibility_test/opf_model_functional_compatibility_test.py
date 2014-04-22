#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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
This test will detect when an OPF model's serialized state is different
from the baseline serialized state. This can happen when the model's
output to a particular input changes due to a code change.

NOTE: If you want to change the baseline, run the test to see it fail
      and print the new hash, and update the appropriate hash below.
"""

MODEL_HASH_GLOBAL_SP = "00e3e2b7571e7cc3203e2478439995596a9a395a"
MODEL_HASH_LOCAL_SP  = "6f64ae762a9b356092640e49073e4a85231bbbf1"



import hashlib
import os
import shutil
import unittest2 as unittest

from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params_global_sp
import model_params_local_sp



CHECKPOINT_DIR = os.path.join(os.path.abspath(
                              os.path.dirname(__file__)), "test.out")



class OPFModelFunctionalCompatibilityTest(unittest.TestCase):


  def setUp(self):
    cleanUp()


  def tearDown(self):
    cleanUp()


  def _testModel(self, modelParams, expectedHash):
    model = ModelFactory.create(modelParams)
    model.enableInference({'predictedField': 'letter'})
    model.run({'letter': 'a'})
    model.run({'letter': 'b'})
    model.run({'letter': 'c'})
    model.run({'letter': 'a'})
    model.run({'letter': 'b'})
    model.save(CHECKPOINT_DIR)

    self.assertEquals(getCheckpointHash(CHECKPOINT_DIR), expectedHash)


  def testModelGlobal(self):
    self._testModel(model_params_global_sp.MODEL_PARAMS, MODEL_HASH_GLOBAL_SP)


  def testModelLocal(self):
    self._testModel(model_params_local_sp.MODEL_PARAMS, MODEL_HASH_LOCAL_SP)



def cleanUp():
  if os.path.exists(CHECKPOINT_DIR):
    shutil.rmtree(CHECKPOINT_DIR)


def getCheckpointHash(directory, verbose=False):
  checkpointHash = hashlib.sha1()

  for root, _dirs, files in os.walk(directory):
    for names in files:
      filepath = os.path.join(root, names)

      if verbose == True:
        print "Hashing: ", filepath

      f = open(filepath, 'rb')

      while True:
        buf = f.read(4096)

        if not buf:
          break

        checkpointHash.update(hashlib.sha1(buf).hexdigest())

      f.close()

  return checkpointHash.hexdigest()



if __name__ == '__main__':
  unittest.main()
