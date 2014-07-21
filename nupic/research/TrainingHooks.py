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

from __future__ import with_statement

import os

from nupic.frameworks.vision2 import VisionUtils as VU


"""This file contains training hooks, testing hooks, and other
functions that are useful in experimental params files."""


###############################################################################
# Training hook used for FDR networks. This prints out pertinent information
#  about each trained level
def trainingHookFDR(net, path, report):
  """
  This training hook is used extensively by the FDR experiments. It prints
  out the learned information about each level in the network
  """
  # Print header
  print "\n## Executing trainingHook...."

  # Print info for each level
  tierCount = VU.getTierCount(net)

  # This loop is temporary until NuPIC 2 allows retrieval of Region names and
  # node types
  regions = net.regions
  for name, r in regions.items():
    if 'FDR' in r.type or 'CLARegion' in r.type:
      if not r.getParameter('disableTemporal'):
        msg = "\n# Temporal node info for %s (nodetype %s):" % (name, r.type)
        print msg
        report.write(msg + os.linesep)

        for paramName in ['tpNumCells', 'tpNumSegments', 'tpNumSynapses',
                          'tpNumSynapsesPerSegmentMax',
                          'tpNumSynapsesPerSegmentAvg']:
          msg = "#   %s: %s" % (paramName, str(r.getParameter(paramName)))
          print msg
          report.write(msg + os.linesep)

      if not r.getParameter('disableSpatial'):
        msg = "\n# Spatial node info for %s (nodetype %s):" % (name, r.type)
        print msg
        report.write(msg + os.linesep)

        if 'spLearningStatsStr' in r.spec.parameters:
          stats = eval(r.getParameter('spLearningStatsStr'))
          keys = stats.keys()
          keys.sort()
          for key in keys:
            msg = "#   %-25s: %s" % (key, str(stats[key]))
            print msg
            report.write(msg + os.linesep)





###############################################################################
# Helper function to add test datasets
def addFDRInvarianceTest(testing, datasetName, radialLength, configPath,
                         numCategories, noiseLevel = 0.0):
  """Add the center and block mode testing stanzas useful for FDR invariance
  experiments. They are inserted into the given testing list which is then
  returned.

  testing        - testing stanza
  datasetName    - name of dataset, such as 'simple'
  configPath     - .cfg file corresponding to this dataset
  numCategories  - number of categories in the .cfg file
  radialLength   - parameter to PictureSensor used in block mode
  noiseLevel     - parameter to PictureSensor used in block mode

  numIterations is calculated as (radialLength*2+1)**2 * numCategories

  """
  testing += [
    dict(
      name=datasetName + '_center',
      sequenceLength=1,
      numRepetitions=1,
      mode='center',
      configPath=configPath,
      numIterations=numCategories,
    ),
    dict(
      name=datasetName + '_block',
      sequenceLength=1,
      numRepetitions=1,
      mode='block',
      numIterations=(radialLength*2+1)**2 * numCategories,
      configPath=configPath,
      radialLength=radialLength,
      noiseLevel=noiseLevel,
    ),
  ]
  return testing
