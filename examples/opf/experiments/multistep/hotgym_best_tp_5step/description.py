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

## This file defines parameters for a prediction experiment.

import os
from nupic.frameworks.opf.exp_description_helpers import importBaseDescription

# the sub-experiment configuration
config = \
{ 'modelParams': { 'clParams': { 'verbosity': 0},
                   'sensorParams': { 'encoders': { 'consumption': { 'clipInput': True,
                                                                    'fieldname': u'consumption',
                                                                    'n': 28,
                                                                    'name': u'consumption',
                                                                    'type': 'AdaptiveScalarEncoder',
                                                                    'w': 21},
                                                   'timestamp_dayOfWeek': { 'dayOfWeek': ( 21,
                                                                                           3),
                                                                            'fieldname': u'timestamp',
                                                                            'name': u'timestamp_dayOfWeek',
                                                                            'type': 'DateEncoder'},
                                                   'timestamp_timeOfDay': { 'fieldname': u'timestamp',
                                                                            'name': u'timestamp_timeOfDay',
                                                                            'timeOfDay': ( 21,
                                                                                           1),
                                                                            'type': 'DateEncoder'},
                                                   'timestamp_weekend': None},
                                     'verbosity': 0},
                   'spParams': { },
                   'tmParams': { 'activationThreshold': 13,
                                 'minThreshold': 9,
                                 'verbosity': 0}}}

mod = importBaseDescription('../hotgym/description.py', config)
locals().update(mod.__dict__)
