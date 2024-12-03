# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

## This file defines parameters for a prediction experiment.

import os
from nupic.frameworks.opf.exp_description_helpers import importBaseDescription

# the sub-experiment configuration
config = \
{ 'modelParams': { 'clParams': { 'verbosity': 0},
                   'inferenceType': 'NontemporalMultiStep',
                   'sensorParams': { 'encoders': { 'consumption': { 'clipInput': True,
                                                                    'fieldname': u'consumption',
                                                                    'n': 28,
                                                                    'name': u'consumption',
                                                                    'type': 'AdaptiveScalarEncoder',
                                                                    'w': 21},
                                                   'timestamp_dayOfWeek': { 'dayOfWeek': ( 21,
                                                                                           1),
                                                                            'fieldname': u'timestamp',
                                                                            'name': u'timestamp_dayOfWeek',
                                                                            'type': 'DateEncoder'},
                                                   'timestamp_timeOfDay': { 'fieldname': u'timestamp',
                                                                            'name': u'timestamp_timeOfDay',
                                                                            'timeOfDay': ( 21,
                                                                                           1),
                                                                            'type': 'DateEncoder'},
                                                   'timestamp_weekend': { 'fieldname': u'timestamp',
                                                                          'name': u'timestamp_weekend',
                                                                          'type': 'DateEncoder',
                                                                          'weekend': 21}},
                                     'verbosity': 0},
                   'spEnable': False,
                   'spParams': { },
                   'tmEnable': False,
                   'tmParams': { 'activationThreshold': 14,
                                 'minThreshold': 12,
                                 'verbosity': 0}}}

mod = importBaseDescription('../hotgym/description.py', config)
locals().update(mod.__dict__)
