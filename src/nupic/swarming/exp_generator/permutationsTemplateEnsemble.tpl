# Copyright 2012-2015 Numenta Inc.
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
$EXP_GENERATOR_PROGRAM_PATH
"""

import os
from nupic.swarming.permutation_helpers import *

# The name of the field being predicted.  Any allowed permutation MUST contain
# the prediction field.
# (generated from PREDICTION_FIELD)
predictedField = '$PREDICTION_FIELD'

permutations = {
  'aggregationInfo': $PERM_AGGREGATION_CHOICES,

  'modelParams': {
    $PERM_INFERENCE_TYPE_CHOICES

    'sensorParams': {
      'encoders': {
        $PERM_ENCODER_CHOICES
      },
    },

    'spParams': {
      $PERM_SP_CHOICES
    },

    'tmParams': {
      $PERM_TP_CHOICES
    },

    'clParams': {
      $PERM_CL_CHOICES
    },
  }
}


# Fields selected for final hypersearch report;
# NOTE: These values are used as regular expressions by RunPermutations.py's
#       report generator
# (fieldname values generated from PERM_PREDICTED_FIELD_NAME)
report = [
          '.*$PREDICTION_FIELD.*',
         ]

# Permutation optimization setting: either minimize or maximize metric
# used by RunPermutations.
# NOTE: The value is used as a regular expressions by RunPermutations.py's
#       report generator
# (generated from $PERM_OPTIMIZE_SETTING)
$PERM_OPTIMIZE_SETTING

minParticlesPerSwarm = $HS_MIN_PARTICLES



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
