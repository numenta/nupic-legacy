# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
