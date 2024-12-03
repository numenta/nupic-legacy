# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Tests the following set of sequences:
z-a-b-c:    (1X)
a-b-c:      (6X)
a-d-e:      (2X)
a-f-g-a-h:  (1X)

We want to insure that when we see 'a', that we predict 'b' with highest
confidence, then 'd', then 'f' and 'h' with equally low confidence. 

We expect the following prediction scores:
inputPredScore_at1        :  0.7
inputPredScore_at2        :  1.0
inputPredScore_at3        :  1.0
inputPredScore_at4        :  1.0

"""

from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
              sensorVerbosity=0,
              spVerbosity=0,
              tpVerbosity=0,
              ppVerbosity=2,
              
              filenameTrain = 'confidence/confidence2.csv',
              filenameTest = 'confidence/confidence2.csv',

              iterationCountTrain=None,
              iterationCountTest=None,
              trainTPRepeats = 5,
              
              trainTP=True,
              )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)


