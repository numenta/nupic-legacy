# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
"""
Simple module used for cleaning up the file system after running the One Hot Gym
Prediction Tutorial.
"""
import os
import shutil
import re

DESCRIPTION = "Removes all generated files so you can start from scratch.\n"


def cleanDirectoryCruft(directory):
  if os.path.exists(directory):
    for f in os.listdir(directory):
      if re.search(r"_out\.csv$", f)\
      or re.search(r"\.pyc$", f):
        print "Removing %s" % f
        os.remove(os.path.join(directory, f))



def cleanUp(directory=None, workingDirs=None):
  if directory is None:
    directory = os.getcwd()
  # Cleanup this dir.
  cleanDirectoryCruft(directory)
  # Cleanup model_params dir (for pyc files).
  cleanDirectoryCruft("model_params")
  # Cleanup working dirs.
  if workingDirs is not None:
    for doomed in workingDirs:
      doomedPath = os.path.join(directory, doomed)
      if os.path.exists(doomedPath):
        print "Removing %s" % doomedPath
        shutil.rmtree(doomedPath)



if __name__ == "__main__":
  print DESCRIPTION
  cleanUp(workingDirs=["swarm"])
