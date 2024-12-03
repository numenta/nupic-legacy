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
{
  'dataSource': 'file://' + os.path.join(os.path.dirname(__file__),
                                         '../datasets/scalar_SP_0.csv'),
  'modelParams': { 'clParams': { 'verbosity': 0},
                   'inferenceType': 'NontemporalClassification',
                   'sensorParams': { 'encoders': { 'field1': { 'clipInput': True,
                                                               'fieldname': u'field1',
                                                               'maxval': 0.10000000000000001,
                                                               'minval': 0.0,
                                                               'n': 11,
                                                               'name': u'field1',
                                                               'type': 'AdaptiveScalarEncoder',
                                                               'w': 7}},
                                     'verbosity': 0},
                   'spEnable': False,
                   'spParams': { 'spVerbosity': 0},
                   'tmEnable': False,
                   'tmParams': { }}}

mod = importBaseDescription('../base_scalar/description.py', config)
locals().update(mod.__dict__)
