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
This file contains utility functions that may be imported
by clients of the framework. Functions that are used only by
the prediction framework should be in opf_utils.py

TODO: Rename as helpers.py once we're ready to replace the legacy
      helpers.py
"""

import imp
import os

import exp_description_api


def loadExperiment(path):
  """Loads the experiment description file from the path.

  :param path: (string) The path to a directory containing a description.py file
         or the file itself.
  :returns: (config, control)
  """
  if not os.path.isdir(path):
    path = os.path.dirname(path)
  descriptionPyModule = loadExperimentDescriptionScriptFromDir(path)
  expIface = getExperimentDescriptionInterfaceFromModule(descriptionPyModule)
  return expIface.getModelDescription(), expIface.getModelControl()


def loadExperimentDescriptionScriptFromDir(experimentDir):
  """ Loads the experiment description python script from the given experiment
  directory.

  :param experimentDir: (string) experiment directory path

  :returns:        module of the loaded experiment description scripts
  """
  descriptionScriptPath = os.path.join(experimentDir, "description.py")
  module = _loadDescriptionFile(descriptionScriptPath)
  return module


def getExperimentDescriptionInterfaceFromModule(module):
  """
  :param module: imported description.py module

  :returns: (:class:`nupic.frameworks.opf.exp_description_api.DescriptionIface`)
            represents the experiment description
  """
  result = module.descriptionInterface
  assert isinstance(result, exp_description_api.DescriptionIface), \
         "expected DescriptionIface-based instance, but got %s" % type(result)

  return result


g_descriptionImportCount = 0

def _loadDescriptionFile(descriptionPyPath):
  """Loads a description file and returns it as a module.

  descriptionPyPath: path of description.py file to load
  """
  global g_descriptionImportCount

  if not os.path.isfile(descriptionPyPath):
    raise RuntimeError(("Experiment description file %s does not exist or " + \
                        "is not a file") % (descriptionPyPath,))

  mod = imp.load_source("pf_description%d" % g_descriptionImportCount,
                        descriptionPyPath)
  g_descriptionImportCount += 1

  if not hasattr(mod, "descriptionInterface"):
    raise RuntimeError("Experiment description file %s does not define %s" % \
                       (descriptionPyPath, "descriptionInterface"))

  if not isinstance(mod.descriptionInterface, exp_description_api.DescriptionIface):
    raise RuntimeError(("Experiment description file %s defines %s but it " + \
                        "is not DescriptionIface-based") % \
                            (descriptionPyPath, name))

  return mod
