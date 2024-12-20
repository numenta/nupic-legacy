# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
The test generates 1st order sequences using a dictionary of 5 different 
elements using a transition table with the following probabilities:

        1   2    3     4     5
    ---------------------------
1:     0%,  0%, 65%,   0%,  34%,
2:    14%, 11%, 36%,  31%,   5%,
3:     2%, 17%,  3%,  51%,  25%
4:    52%, 19%, 13%,   0%,  14%
5:    35%, 61%,  2%,   0%,   0%


What this says is that if you see a '1', the best thing to predict is a '3',
if you see a '3', the best thing to predict is a '4', etc. 

There is also a reset generated every 10 elements, although this should have
little to no effect on the prediction accuracy. 

When you run this dataset against 1st order n-grams, you get 52.6% accuracy,
so we would expect roughly the same accuracy using the TM:

inputPredScore_burnIn1    :  0.526

"""


from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
              sensorVerbosity=0,
              spVerbosity=0,
              tpVerbosity=0,
              ppVerbosity=0,
              
              dataSetPackage = 'firstOrder',
              iterationCountTest=1000,
              
              spNumActivePerInhArea = 1,
              
              #temporalImp = 'cpp',
              tpNCellsPerCol = 1,
              
              tpInitialPerm = 0.11,
              tpPermanenceInc = 0.10,
              tpPermanenceDec = 0.10,
              tpGlobalDecay = 0.10,
              tpMaxAge = 50,   

              tpTimingEvery = 500
              )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)


