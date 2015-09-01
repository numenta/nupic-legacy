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



