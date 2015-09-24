#! /usr/bin/env python
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

'''
This file contains all the features that are in production or under development.
Features must be listed and described separately in features.py

Generally new features should be added to the DEVELOPMENT group and then migrated
to the BASE_FEATURES group when we're ready to release

Note: This could be structured with classes and inheretence. A very simple
module will probably be good enough to start with.
'''

from nupic.support.features_list import FEATURES_LIST

GROUPS = {}
###############################################################################
# BASE FEATURES
'''
INHERITS FROM / ADDS
'''
BASE = [
    'base_feature',
    'second_feature',
    'third_feature'
]
'''
REMOVES
'''
# None

GROUPS['BASE'] = BASE

###############################################################################
# UNDER DEVELOPMENT
'''
INHERITS FROM / ADDS
'''
DEVELOPMENT = BASE + [
  'increased_awesomeness'
]

'''
REMOVES
'''
[DEVELOPMENT.remove(feature) for feature in [
  'second_feature',
  ]
]

GROUPS['DEVELOPMENT'] = DEVELOPMENT

###############################################################################
# RELEASED TO ALPHA USERS
'''
INHERITS FROM / ADDS
'''
ALPHA = BASE + [
  'super_secret_feature'
]

'''
REMOVES
'''
[ALPHA.remove(feature) for feature in [
  'second_feature',
  ]
]

GROUPS['ALPHA'] = ALPHA

###############################################################################
# A/B Test GROUP A
'''
INHERITS FROM / ADDS
'''
ALPHA_A = ALPHA #No additions

'''
REMOVES
'''
[ALPHA_A.remove(feature) for feature in [
  'super_secret_feature',
  ]
]

GROUPS['ALPHA_A'] = ALPHA_A

###############################################################################
# A/B Test GROUP B
'''
INHERITS FROM / ADDS
'''
ALPHA_B = ALPHA #No Additions

'''
REMOVES
'''
None

GROUPS['ALPHA_B'] = ALPHA_B

'''
All features in a given group must appear in the features.py file
'''
validFeatureNames = [f['name'] for f in FEATURES_LIST]
for groupName, features in GROUPS.iteritems():
  for feature in features:
    if feature not in validFeatureNames:
      raise Exception('The feature %s is not a recognized feature name. Please '
                      'check your spelling and/or add it to '
                      'nupic/support/features_list.py' % feature)
