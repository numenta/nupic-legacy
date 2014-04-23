#! /usr/bin/python

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
This is the command-line interface for the Hot Gym Tutorial.
"""
import sys
import optparse

import swarm_helper
import nupic_runner
import cleaner

GYM_NAME = "Balgowlah Platinum"
INPUT_FILE = "Balgowlah_Platinum.csv"



def run_hot_gym(args):
  helpString = (
      "\n\n%prog <command> [options]\n\n"

      "Current commands are:\n"

      "\n\tswarm\n"
      "\t\tRuns a swarm on the input data (Balgowlah_Platinum.csv) and\n"
      "\t\tcreates a model parameters file in the `model_params` directory\n"
      "\t\tcontaining the best model found by the swarm. Dumps a bunch of\n"
      "\t\tcrud to stdout because that is just what swarming does at this\n"
      "\t\tpoint. You really don't need to pay any attention to it.\n"

      "\n\trun [--plot]\n"
      "\t\tStarts a NuPIC model from the model params returned by the swarm\n"
      "\t\tand pushes each line of input from the gym into the model. Results\n"
      "\t\tare written to an output file (default) or plotted dynamically if\n"
      "\t\tthe --plot option is specified.\n"
      "\t\tNOTE: You must run the `swarm` command before this one, because\n"
      "\t\tmodel parameters are required to run NuPIC.\n"

      "\n\tcleanup\n"
      "\t\tRemoves all generated files so you can start from scratch.\n"

      "\n\nExample:\n"
      "--------\n"

      "> ./run.py swarm\n"
      "> ./run.py run --plot\n"
      "> ./run.py cleanup\n"

      )

  parser = optparse.OptionParser(usage=helpString)

  parser.add_option(
    "--plot", dest="plot", action="store_true",
    help="If set, will plot results using matplotlib, otherwise writes to "
         "output file."
  )

  (options, positional_args) = parser.parse_args(args)

  # There must be a command.
  if len(positional_args) is not 1:
    parser.error("Please specify a command.")

  command = positional_args[0]

  # Handle swarm command.
  if command == "swarm":
    swarm_helper.swarm(INPUT_FILE)

  # Handle run command.
  elif command == "run":
    nupic_runner.run_model(GYM_NAME, options.plot)

  # Handle cleanup command.
  elif command == "cleanup":
    cleaner.cleanup(working_dirs=["swarm"])

  else:
    parser.error("Unrecognized command '%s'." % command)



if __name__ == "__main__":
  run_hot_gym(sys.argv[1:])
