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
import imp

# This file contains utility functions that are used
# internally by the prediction framework and may be imported
# by description files. Functions that are used only by
# the prediction framework should be in utils.py



#########################################################
# Utility methods for description files  are organized as a base description
#  and an experiment based on that base description.
# The base description calls getConfig to get the configuration from the
# specific experiment, and the specific experiment calls importBaseDescription

# empty initial config allows base experiment to run by itself
_config = dict()

# Save the path to the current sub-experiment here during importBaseDescription()
subExpDir = None


# We will load the description file as a module, which allows us to
# use the debugger and see source code. But description files are frequently
# modified and we want to be able to easily reload them. To facilitate this,
# we reload with a unique module name ("pf_description%d") each time.
baseDescriptionImportCount = 0


#########################################################
def importBaseDescription(path, config):
  global baseDescriptionImportCount, _config, subExpDir
  if not os.path.isabs(path):
    # grab the path to the file doing the import
    import inspect
    callingFrame = inspect.stack()[1][0]
    callingFile = callingFrame.f_globals['__file__']
    subExpDir = os.path.dirname(callingFile)
    path = os.path.join(subExpDir, path)

  #print "Importing from: %s" % path

  # stash the config in a place where the loading module can find it.
  _config = config
  mod = imp.load_source("pf_base_description%d" % baseDescriptionImportCount,
                        path)
  # don't want to override __file__ in our caller
  mod.__base_file__ = mod.__file__
  del mod.__file__
  baseDescriptionImportCount += 1
  return mod


#########################################################
# Newer method just updates from sub-experiment
def updateConfigFromSubConfig(config):
  # _config is the configuration provided by the sub-experiment
  global _config
  badOptions = set(_config.keys()).difference(config.keys())
  '''
  assert len(badOptions) == 0, "The following config options provided by the "\
      "sub-experiment are not supported " \
      "by this base experiment: %s" % (str(list(badOptions)))
  '''
  config.update(_config)
  _config = dict()


#########################################################
def getSubExpDir():
  global subExpDir
  return subExpDir
