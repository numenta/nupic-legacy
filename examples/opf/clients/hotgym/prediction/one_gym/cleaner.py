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
"""
Simple module used for cleaning up the file system after running the One Hot Gym
Prediction Tutorial.
"""
import os
import shutil
import re


def _clean_dir_cruft(dir):
  if os.path.exists(dir):
    for f in os.listdir(dir):
      if re.search("_out\.csv$", f)\
      or re.search("\.pyc$", f):
        print "Removing %s" % f
        os.remove(os.path.join(dir, f))



def cleanup(dir=None, working_dirs=None):
  if dir is None:
    dir = os.getcwd()
  # Cleanup this dir.
  _clean_dir_cruft(dir)
  # Cleanup model_params dir (for pyc files).
  _clean_dir_cruft("model_params")
  # Cleanup working dirs.
  if working_dirs is not None:
    for doomed in working_dirs:
      doomed_path = os.path.join(dir, doomed)
      if os.path.exists(doomed_path):
        print "Removing %s" % doomed_path
        shutil.rmtree(doomed_path)
