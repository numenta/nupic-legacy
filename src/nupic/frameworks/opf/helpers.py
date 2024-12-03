# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
