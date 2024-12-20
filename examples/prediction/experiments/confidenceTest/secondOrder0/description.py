# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This test trains and tests on the following set of sequence probabilities:

1-2-3   (4X)
1-2-4   (1X)
5-2-3   (1X)
5-2-4   (4X)

We would expect it to learn 4 sub-sequences.  We are setting the
permanence decrement decay high enough that an element won't remain
connected to the previous unless it follows at least 2 out of 3 times.
This constraint makes the 3-1, 3-5, 4-1, 4-5 transitions remain
un-connected since they occur only 1 out of every 2 times. It also makes
the 2-4 (in the 1-2-4 sequence) and the 2-3 (in the 5-2-3) sequence remain 
unconnected. 

If we successfully learn the above set of sequences, we would expect to
be able to predict with the following accuracy:
1 - 2:      5 out of 5
1,2 - 3:    4 out of 4
1,2 - 4:    0 out of 1
1,2,3 - 1:  1 out of 2
1,2,3 - 5:  1 out of 2
1,2,4 - 1:  0.25 out of 0.5
1,2,4 - 5:  0.25 out of 0.5

5 - 2:      5 out of 5
5,2 - 4:    4 out of 4
5,2 - 3:    0 out of 1
5,2,4 - 5:  1 out of 2
5,2,4 - 1:  1 out of 2
5,2,3 - 1:  0.25 out of 0.5
5,2,3 - 5:  0.25 out of 0.5

Total:      23 out of 30 = 0.76666 probability


If things are working correctly then, you should get approximately the following 
result from post-processing:

  inputPredScore_burnIn1    :  0.7666666666

"""

from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
              sensorVerbosity=0,
              spVerbosity=0,
              tpVerbosity=0,
              ppVerbosity=0,
              
              dataSetPackage = 'secondOrder0',

              iterationCountTrain=250,
              iterationCountTest=500,
              #evalTrainingSetNumIterations = 0,
              trainTPRepeats = 1,
              
              spNumActivePerInhArea = 5,
              
              tpNCellsPerCol = 5, 

              tpInitialPerm = 0.11,
              tpPermanenceInc = 0.10,
              tpPermanenceDec = 0.10,
              tpGlobalDecay = 0.10,
              tpMaxAge = 50,   
              tpPAMLength = 1,
              #tpMaxSeqLength = 4,
              
              tpTimingEvery = 100,
              )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)



