#! /usr/bin/env python
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

""" @file run_swarm.py
This script is the command-line interface for running swarms in nupic."""

import sys
import os
import optparse

from nupic.swarming import permutations_runner
from nupic.swarming.permutations_runner import DEFAULT_OPTIONS


def runPermutations(args):
  """
  The main function of the RunPermutations utility.
  This utility will automatically generate and run multiple prediction framework
  experiments that are permutations of a base experiment via the Grok engine.
  For example, if you have an experiment that you want to test with 3 possible
  values of variable A and 2 possible values of variable B, this utility will
  automatically generate the experiment directories and description files for
  each of the 6 different experiments.

  Here is an example permutations file which is read by this script below. The
  permutations file must be in the same directory as the description.py for the
  base experiment that you want to permute. It contains a permutations dict, an
  optional list of the result items to report on for each experiment, and an
  optional result item to optimize for.

  When an 'optimize' entry is provided, this tool will attempt to prioritize the
  order in which the various permutations are run in order to improve the odds
  of running the best permutations sooner. It does this by watching the results
  for various parameter values and putting parameter values that give generally
  better results at the head of the queue.

  In addition, when the optimize key is provided, we periodically update the UI
  with the best results obtained so far on that metric.

  ---------------------------------------------------------------------------
  permutations = dict(
                  iterationCount = [1000, 5000],
                  coincCount = [50, 100],
                  trainTP = [False],
                  )

  report = ['.*reconstructErrAvg',
            '.*inputPredScore.*',
            ]

  optimize = 'postProc_gym1_baseline:inputPredScore'

  Parameters:
  ----------------------------------------------------------------------
  args:           Command-line args; the equivalent of sys.argv[1:]
  retval:         for the actions 'run', 'pickup', and 'dryRun', returns the
                  Hypersearch job ID (in ClinetJobs table); otherwise returns
                  None
  """

  helpString = (
      "\n\n%prog [options] permutationsScript\n"
      "%prog [options] expDescription.json\n\n"
      "This script runs permutations of an experiment via Grok engine, as "
      "defined in a\npermutations.py script or an expGenerator experiment "
      "description json file.\nIn the expDescription.json form, the json file "
      "MUST have the file extension\n'.json' and MUST conform to "
      "expGenerator/experimentDescriptionSchema.json.")

  parser = optparse.OptionParser(usage=helpString)

  parser.add_option(
    "--replaceReport", dest="replaceReport", action="store_true",
    default=DEFAULT_OPTIONS["replaceReport"],
    help="Replace existing csv report file if it exists. Default is to "
         "append to the existing file. [default: %default].")

  parser.add_option(
    "--action", dest="action", default=DEFAULT_OPTIONS["action"],
    choices=["run", "pickup", "report", "dryRun"],
    help="Which action to perform. Possible actions are run, pickup, choices, "
         "report, list. "
         "run: run a new HyperSearch via Grok. "
         "pickup: pick up the latest run of a HyperSearch job. "
         "dryRun: run a single HypersearchWorker inline within the application "
         "process without the Grok infrastructure to flush out bugs in "
         "description and permutations scripts; defaults to "
         "maxPermutations=1: use --maxPermutations to change this; "
         "report: just print results from the last or current run. "
         "[default: %default].")

  parser.add_option(
    "--maxPermutations", dest="maxPermutations",
    default=DEFAULT_OPTIONS["maxPermutations"], type="int",
    help="Maximum number of models to search. Applies only to the 'run' and "
    "'dryRun' actions. [default: %default].")

  parser.add_option(
    "--exports", dest="exports", default=DEFAULT_OPTIONS["exports"],
    type="string",
    help="json dump of environment variable settings that should be applied"
    "for the job before running. [default: %default].")

  parser.add_option(
    "--useTerminators", dest="useTerminators", action="store_true",
    default=DEFAULT_OPTIONS["useTerminators"], help="Use early model terminators in HyperSearch"
         "[default: %default].")

  parser.add_option(
      "--maxWorkers", dest="maxWorkers", default=DEFAULT_OPTIONS["maxWorkers"],
      type="int",
      help="Maximum number of concurrent workers to launch. Applies only to "
      "the 'run' action. [default: %default].")

  parser.add_option(
    "-v", dest="verbosityCount", action="count", default=0,
    help="Increase verbosity of the output.  Specify multiple times for "
         "increased verbosity. e.g., -vv is more verbose than -v.")

  parser.add_option(
    "--timeout", dest="timeout", default=DEFAULT_OPTIONS["timeout"], type="int",
     help="Time out for this search in minutes"
         "[default: %default].")

  parser.add_option(
    "--overwrite", default=DEFAULT_OPTIONS["overwrite"], action="store_true",
    help="If 'yes', overwrite existing description.py and permutations.py"
         " (in the same directory as the <expDescription.json> file) if they"
         " already exist. [default: %default].")

  parser.add_option(
    "--genTopNDescriptions", dest="genTopNDescriptions",
    default=DEFAULT_OPTIONS["genTopNDescriptions"], type="int",
    help="Generate description files for the top N models. Each one will be"
         " placed into it's own subdirectory under the base description file."
         "[default: %default].")

  (options, positionalArgs) = parser.parse_args(args)

  # Get the permutations script's filepath
  if len(positionalArgs) != 1:
    parser.error("You must supply the name of exactly one permutations script "
                 "or JSON description file.")

  fileArgPath = os.path.expanduser(positionalArgs[0])
  fileArgPath = os.path.expandvars(fileArgPath)
  fileArgPath = os.path.abspath(fileArgPath)

  permWorkDir = os.path.dirname(fileArgPath)

  outputLabel = os.path.splitext(os.path.basename(fileArgPath))[0]

  basename = os.path.basename(fileArgPath)
  fileExtension = os.path.splitext(basename)[1]
  optionsDict = vars(options)

  if fileExtension == ".json":
    returnValue = permutations_runner.runWithJsonFile(
      fileArgPath, optionsDict, outputLabel, permWorkDir)
  else:
    returnValue = permutations_runner.runWithPermutationsScript(
      fileArgPath, optionsDict, outputLabel, permWorkDir)

  return returnValue


if __name__ == "__main__":
  runPermutations(sys.argv[1:])
