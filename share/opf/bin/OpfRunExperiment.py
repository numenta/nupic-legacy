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

"""This script is a command-line client of Online Prediction Framework (OPF).
It executes a single experiment.
"""


import sys

from nupic.frameworks.opf.experiment_runner import (runExperiment,
                                                    initExperimentPrng)
import nupic.support



def main():
  """Run according to options in sys.argv"""
  nupic.support.initLogging(verbose=True)

  # Initialize pseudo-random number generators (PRNGs)
  #
  # This will fix the seed that is used by numpy when generating 'random'
  # numbers. This allows for repeatability across experiments.
  initExperimentPrng()

  # Run it!
  runExperiment(sys.argv[1:])



if __name__ == "__main__":
  main()
