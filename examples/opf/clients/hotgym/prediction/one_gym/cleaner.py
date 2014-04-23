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

import os
import shutil
import re



def _clean_dir_cruft(dir):
  if os.path.exists(dir):
    for f in os.listdir(dir):
      if re.search("\.pkl$", f)\
      or re.search("_out\.csv$", f)\
      or re.search("_Report(.\d+)?\.csv$", f):
        print "Removing %s" % f
        os.remove(os.path.join(dir, f))



def cleanup(dir=None):
  if dir is None:
    dir = os.getcwd()
  # Starting in this directory.
  _clean_dir_cruft(dir)
  # In the swarm directory.
  _clean_dir_cruft("swarm")
  # Blow away swarm/model_0
  model_working_dir = os.path.join("swarm", "model_0")
  if os.path.exists(model_working_dir):
    print "Removing %s" % model_working_dir
    shutil.rmtree(model_working_dir)
  # Delete model params.
  model_params = os.path.join(
    "model_params", "Balgowlah_Platinum_model_params.py"
  )
  if os.path.exists(model_params):
    print "Removing %s" % model_params
    os.remove(model_params)

