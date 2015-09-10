#!/usr/bin/env python
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
