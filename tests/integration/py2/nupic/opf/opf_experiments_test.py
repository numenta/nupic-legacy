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

from optparse import OptionParser
import os
import sys
import traceback
import unittest2 as unittest

from nupic.frameworks.opf.experiment_runner import (
    runExperiment, initExperimentPrng)



# Globals
excludedExperiments = [] # none for now
predictionDir = os.path.join(os.environ['NTA'], 'share', 'opf')
runAllIterations = False



def getAllDirectoriesWithFile(path, filename, excludeDirs):
  """
  Returns a list of directories in the <path> with a given <filename>, excluding
  <excludeDirs>
  """
  directoryList = []
  for dirpath, dirnames, filenames in os.walk(path):
    for dir in dirnames[:]:
      if dir in excludeDirs:
        dirnames.remove(dir)
        print "EXCLUDING %s..." % (os.path.join(dirpath, dir))
        
      # If this directory is UNDER_DEVELOPMENT, exclude it
      elif 'UNDER_DEVELOPMENT' in os.listdir(os.path.join(dirpath, dir)):
        dirnames.remove(dir)
        print "EXCLUDING %s..." % (os.path.join(dirpath, dir))

    for file in filenames:
      if file==filename:
        directoryList.append(dirpath)
  
  return directoryList


def getAllExperimentDirectories(excludedExperiments=[]):
  """
  Experiment directories are the directories with a description.py file
  """

  excludedDirectories = ['exp', 'inference', 'networks', 'legacy']
  excludedDirectories.extend(excludedExperiments)
  return getAllDirectoriesWithFile(
                    path="experiments",
                    filename="description.py",
                    excludeDirs=excludedDirectories)


def runReducedExperiment(path, reduce=True):
  """
  Run the experiment in the <path> with a reduced iteration count
  """

  initExperimentPrng()
  
  # Load experiment
  if reduce:
    args = [path, '--testMode']
  else:
    args = [path]
    
  runExperiment(args)



class OPFExperimentsTest(unittest.TestCase):

  def testExperiments(self):
    os.chdir(predictionDir)
    expDirPathList =  getAllExperimentDirectories(excludedExperiments)

    if len(expDirPathList)==0:
      print "Unable to find any prediction experiments"
      sys.exit(1)

    failedExperiments = []
    successExperiments = []
    for expDirPath in expDirPathList:
      if os.path.exists(os.path.join(expDirPath, "UNDER_DEVELOPMENT")):
        print "Skipping experiment: %s -- under development" % expDirPath
        continue
      print "Running experiment: %s" % expDirPath
      try:
        if runAllIterations:
          runReducedExperiment(expDirPath, False)
        else:
          runReducedExperiment(expDirPath)
      except KeyboardInterrupt:
        print "Keyboard interrupt received. Exiting"
        sys.exit(1)
      except:
        failedExperiments.append(expDirPath)
        print
        print "Unable to run experiment: %s" % expDirPath
        print "See the trace below-"
        traceback.print_exc()
      else:
        print "Successfully ran experiment: %s" % expDirPath
        successExperiments.append(expDirPath)

    if len(failedExperiments)>0:
      print "The following experiments failed:", failedExperiments
      sys.exit(1)

    print "Successfully ran all experiments: %s" % (successExperiments)


if __name__ == "__main__":
  description = \
      "Test all experiments in opf/experiments with reduced iterations.\
       Currently excludes %s in the default mode" % str(excludedExperiments)
  parser = OptionParser(description=description)
  parser.add_option("-a", "--all", action="store_true", dest="runAllExperiments",
                    default=False, help="Don't exclude any experiments.")
  parser.add_option("-l", "--long", action="store_true", dest="runAllIterations",
                    default=False, help="Don't reduce iterations.")
  (options, args) = parser.parse_args()

  if len(args) > 0:
    predictionDir = args[0]

  if options.runAllExperiments:
    excludedExperiments=[]

  runAllIterations = options.runAllIterations

  unittest.main()
