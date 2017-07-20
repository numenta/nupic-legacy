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

"""
This test trains and tests on the following set of sequence probabilities:

1-11-16 (1X)
1-12-17 (1X)
1-13-18 (1X)
1-14-19 (1X)
1-15-20 (1X)

2-11-21 (1X)
2-12-22 (1X)
2-13-23 (1X)
2-14-24 (1X)
2-15-25 (1X)


We would expect it to learn 10 sub-sequences. This set of sequences exposes
a problem in the way permanenceDec is used to determine what are sub-sequences. 
Basically, it only looks at fan-out - if an element has high fan-out, it will
NOT maintain connections to the following elements and thus we will lose any
high order context when we go through a high fan-out element. 

In the example above, the transitions out of 0 have a high fan-out. With any
non-zero permanenceDec and sufficient fan-out, you will always end up remaining
unconnected from 1 to 11,12,13,.... This means you will then burst on the
element following the 1 (for example on the 11), and you will not be able to
predict that you should go to 16 instead of to 21. 

If we successfully learn the above set of sequences, we would expect to
be able to predict with the following accuracy:
1 - 11:       0.2 out of 1
11 - 16:      1 out of 1
16 - 1:       0.5 out of 1
16 - 2:       0.5 out of 1
(same for 1-12-17..., 2-11-21...)
Total:        2.2 out of 4 = 0.55 probability


If things are working correctly then, you should get approximately the following 
result from post-processing:

  inputPredScore_burnIn1    :  0.55

"""

from nupic.frameworks.prediction.helpers import importBaseDescription

config = dict(
              sensorVerbosity=0,
              spVerbosity=0,
              tpVerbosity=0,
              ppVerbosity=0,
              
              dataSetPackage = 'secondOrder1',

              iterationCountTrain=2500,
              iterationCountTest=250,
              trainTPRepeats = 1,
              
              spNumActivePerInhArea = 5,
              
              trainTP=True,
              tpNCellsPerCol = 10, 

              tpInitialPerm = 0.11,
              tpPermanenceInc = 0.05,
              tpPermanenceDec = 0.10,
              tpGlobalDecay = 0.05,
              tpMaxAge = 50,
              tpPAMLength = 1,
              #tpMaxSeqLength = 4,
              
              tpTimingEvery = 250
              )
              
mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)



