#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
Template file used by ExpGenerator to generate the actual
permutations.py file by replacing $XXXXXXXX tokens with desired values.

This permutations.py file was generated by:
$EXP_GENERATOR_PROGRAM_PATH
"""

# The name of the field being predicted.  Any allowed permutation MUST contain
# the prediction field.
# (generated from PREDICTION_FIELD)
__predictionField = '$PREDICTION_FIELD'

# The maximum number of fields, including meta-fields (e.g., "timeOfDay",
# "dayOfWeek"), allowed in any given permutation (enforced by the filter() function.
# Set to 0 (zero) to suppress this check.
# (gernerated from FIELD_PERMUTATION_LIMIT)
__fieldPermutationLimit = $FIELD_PERMUTATION_LIMIT


permutations = {
  # Encoder permutation choices
  # Example:
  #
  #'__timestamp_dayOfWeek_encoder': [
  #             None,
  #             {'fieldname':'timestamp',
  #              'name': 'timestamp_timeOfDay',
  #              'type':'DateEncoder'
  #              'dayOfWeek': (7,1)
  #              },
  #             {'fieldname':'timestamp',
  #              'name': 'timestamp_timeOfDay',
  #              'type':'DateEncoder'
  #              'dayOfWeek': (7,3)
  #              },
  #          ],
  #
  #'__field_consumption_encoder': [
  #              None,
  #              {'fieldname':'consumption',
  #               'name': 'consumption',
  #               'type':'ScalarEncoder',
  #               'n': 13,
  #               'w': 7,
  #                }
  #           ]
  #
  # (generated from PERM_ENCODER_CHOICES)
  'modelParams': {
    'sensorParams': {
      'encoders': {
        $PERM_ENCODER_CHOICES
      },
    },

    'tpParams': {
      'activationThreshold': [12, 16],
      'minThreshold': [9, 12],
    },
  },
}


# Fields selected for final swarm report;
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


# A cache of field encoder property key names. It gets generated when needed
# by permutationFilter()
g_fieldEncoderKeyNames = ()


#############################################################################
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
  global g_fieldEncoderKeyNames

  # Generate a list of field encoder property key names
  if not g_fieldEncoderKeyNames:
    keyNames = []
    for key,value in perm.items():
      if key.endswith('_encoder'):
        keyNames.append(key)
    g_fieldEncoderKeyNames = tuple(keyNames)


  # Generate a list of active encoder keys in the given permutation.
  #
  # An encoder item looks like this:
  #               { 'fieldname':'consumption','type':'ScalarEncoder', ...}
  # or like this:
  #               None
  #
  activeEncoderKeys = filter(lambda x: x in perm and perm[x] != None,
                             g_fieldEncoderKeyNames)

  # Make sure this permitation is within the field permutation limit
  if __fieldPermutationLimit and len(activeEncoderKeys) > __fieldPermutationLimit:
    return False


  # Make sure the predictionField is represented in the encoders
  #
  # NOTE: there may be more than one in case the prediction field maps
  #  to meta-fields
  #
  # TODO: hmmm... but how would the meta-fields resolve against RunPermutations's
  #       optimization of the SINGLE prediction field from which they derive ?
  #	  Is it meaningful to use timestamp as a prediction field and does
  #       prediction field specification need to include a specific meta-field
  #       (e.g., 'timeOfDay', 'dayOfWeek')?
  #
  activePredictionFieldEncoderKeys = filter(
    lambda x: perm[x]['fieldname'] == __predictionField, activeEncoderKeys)

  if len(activePredictionFieldEncoderKeys) == 0:
    return False

  return True
