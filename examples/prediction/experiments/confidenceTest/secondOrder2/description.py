# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This test trains and tests on data generated from a second order markov source model.  

If things are working correctly then, you should do as well as a 2-grams model


"""

from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
              sensorVerbosity=0,
              spVerbosity=0,
              tpVerbosity=0,
              ppVerbosity=0,
              
              dataSetPackage = 'secondOrder2',

              iterationCountTrain=3000,
              iterationCountTest=250,
              trainTPRepeats = 1,
              
              spNumActivePerInhArea = 5,
              
              trainTP=True,
              tpNCellsPerCol = 10, 

              tpInitialPerm = 0.11,
              tpPermanenceInc = 0.05,
              tpPermanenceDec = 0.10,
              tpGlobalDecay = 0.05,
              tpMaxAge = 100,
              tpPAMLength = 1,
              #tpMaxSeqLength = 3,
              
              tpTimingEvery = 250
              )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)



