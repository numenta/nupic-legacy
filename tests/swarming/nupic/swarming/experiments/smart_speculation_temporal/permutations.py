# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
Template file used by ExpGenerator to generate the actual
permutations.py file by replacing $XXXXXXXX tokens with desired values.

This permutations.py file was generated by:
'/Users/ronmarianetti/nupic/eng/lib/python2.6/site-packages/nupic/frameworks/opf/expGenerator/experiment_generator.py'
"""

import os

from nupic.swarming.permutation_helpers import *

# The name of the field being predicted.  Any allowed permutation MUST contain
# the prediction field.
# (generated from PREDICTION_FIELD)
predictedField = 'attendance'

permutations = {

  'modelParams': {
    'sensorParams': {
      'encoders': {
        'A': PermuteEncoder(fieldName='daynight', encoderClass='SDRCategoryEncoder', w=7, n=100),
        'C': PermuteEncoder(fieldName='precip', encoderClass='SDRCategoryEncoder', w=7, n=100),
        'B': PermuteEncoder(fieldName='daynight', encoderClass='SDRCategoryEncoder', w=7, n=100),
        'E': PermuteEncoder(fieldName='home_winloss', encoderClass='AdaptiveScalarEncoder', maxval=0.7, n=PermuteInt(13, 500, 25), clipInput=True, w=7, minval=0),
        'D': PermuteEncoder(fieldName='visitor_winloss', encoderClass='AdaptiveScalarEncoder', maxval=0.786, n=PermuteInt(13, 500, 25), clipInput=True, w=7, minval=0),
        'G': PermuteEncoder(fieldName='timestamp', encoderClass='DateEncoder.timeOfDay', radius=PermuteChoices([1, 8]), w=7),
        'F': PermuteEncoder(fieldName='timestamp', encoderClass='DateEncoder.dayOfWeek', radius=PermuteChoices([1, 3]), w=7),
        'Pred': PermuteEncoder(fieldName='attendance', encoderClass='AdaptiveScalarEncoder', maxval=36067, n=PermuteInt(13, 500, 25), clipInput=True, w=7, minval=0),
      },
    },


    'tmParams': {
      'minThreshold': PermuteInt(9, 12),
      'activationThreshold': PermuteInt(12, 16),
    },


    }
}


# Fields selected for final hypersearch report;
# NOTE: These values are used as regular expressions by RunPermutations.py's
#       report generator
# (fieldname values generated from PERM_PREDICTED_FIELD_NAME)
report = [
          '.*attendance.*',
         ]

# Permutation optimization setting: either minimize or maximize metric
# used by RunPermutations.
# NOTE: The value is used as a regular expressions by RunPermutations.py's
#       report generator
# (generated from minimize = 'nonprediction:aae:window=1000:field=attendance')
minimize = 'prediction:aae:window=1000:field=attendance'



def dummyModelParams(perm):
  """ This function can be used for Hypersearch algorithm development. When
  present, we don't actually run the CLA model in the OPF, but instead run
  a dummy model. This function returns the dummy model params that will be
  used. See the OPFDummyModelRunner class source code (in
  nupic.swarming.ModelRunner) for a description of the schema for
  the dummy model params.
  """

  errScore = 500

  if not perm['modelParams']['sensorParams']['encoders']['A'] is None:
  	errScore -= 50
  if not perm['modelParams']['sensorParams']['encoders']['B'] is None:
  	errScore -= 40
  if not perm['modelParams']['sensorParams']['encoders']['C'] is None:
  	errScore -= 30
  if not perm['modelParams']['sensorParams']['encoders']['D'] is None:
  	errScore -= 20
  if not perm['modelParams']['sensorParams']['encoders']['E'] is None:
  	errScore -= 15
  if not perm['modelParams']['sensorParams']['encoders']['F'] is None:
  	errScore -= 10
  if not perm['modelParams']['sensorParams']['encoders']['G'] is None:
  	errScore -= 5
  delay = 0
  #If the model only has the A field have it run slowly to simulate speculation.

  encoderCount = 0
  for key in perm.keys():
 	if 'encoder' in key and not perm[key] is None:
 		encoderCount+=1
  delay=encoderCount*encoderCount*.1




  dummyModelParams = dict(
                metricValue = errScore,
                metricFunctions = None,
                delay=delay,
                )
  return dummyModelParams



def permutationFilter(perm):
  """ This function can be used to selectively filter out specific permutation
  combinations. It is called by RunPermutations for every possible permutation
  of the variables in the permutations dict. It should return True for valid a
  combination of permutation values and False for an invalid one.

  Parameters:
  ---------------------------------------------------------
  perm: dict of one possible combination of name:value
        pairs chosen from permutations.
  """

  # An example of how to use this
  #if perm['__consumption_encoder']['maxval'] > 300:
  #  return False;
  #
  return True
