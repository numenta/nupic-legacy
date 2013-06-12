#!/usr/bin/env python2
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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
import sys

# assumes build_system/pybuild is in sys.path
# assumes that logging has already been initialized with utils.initlog()
import manifest

def createRelease(releaseName, trunkDir, installDir, tmpDir="/tmp"):
  """Create the release for to this standalone app. 
  Copies files from installDir into a temporary dir, and returns
  the name of the temporary dir."""


  # Get a temp directory to hold the release. 
  baseName = os.path.join(tmpDir, "%s-release" % releaseName)
  for i in xrange(0, 10):
    releaseDir = baseName + str(i)
    if not os.path.exists(releaseDir):
      break
  if os.path.exists(releaseDir):
    raise Exception("unable to find release directory in tmpDir %s" % tmpDir)

  print "Creating release in %s" % releaseDir


  # install from the manifest
  manifestFile = os.path.join(trunkDir, "release", "%s_release" % releaseName, "manifests", "%s_release.manifest" % releaseName)
  manifest.installFromManifest(manifestFile, installDir, releaseDir, level=0, overwrite=False, destdirExists=False, allArchitectures=False)
  print "Finished creating release %s" % releaseName
  return releaseDir

