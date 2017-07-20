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

"""This script is a command-line client of Online Prediction Framework (OPF).
It executes a single experiment and diffs the results for the SDRClassifier.
"""

import sys

from nupic.algorithms.sdr_classifier_diff import SDRClassifierDiff
from nupic.algorithms.sdr_classifier_factory import SDRClassifierFactory
from nupic.frameworks.opf.experiment_runner import (runExperiment,
                                                    initExperimentPrng)
from nupic.support import initLogging



def main():
  """Run according to options in sys.argv and diff classifiers."""
  initLogging(verbose=True)

  # Initialize PRNGs
  initExperimentPrng()

  # Mock out the creation of the SDRClassifier.
  @staticmethod
  def _mockCreate(*args, **kwargs):
    kwargs.pop('implementation', None)
    return SDRClassifierDiff(*args, **kwargs)
  SDRClassifierFactory.create = _mockCreate

  # Run it!
  runExperiment(sys.argv[1:])



if __name__ == "__main__":
  main()
