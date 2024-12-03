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
                                         '../datasets/scalar_1.csv'),
  'errorMetric': 'aae',

  'modelParams': {
    'sensorParams': {
      'verbosity': 0,
      'encoders': {
        'field1': {
          'clipInput': True,
          'fieldname': u'field1',
          'maxval': 5.0,
          'minval': 0.0,
          'n': 600,
          'name': u'field1',
          'type': 'ScalarEncoder',
          'w': 21
        },
        'classification': {
          'classifierOnly': True,
          'clipInput': True,
          'fieldname': u'classification',
          'maxval': 50.0,
          'minval': 0.0,
          'n': 600,
          'name': u'classification',
          'type': 'ScalarEncoder',
          'w': 21
         },
       },
    },
    'clParams': {
      'verbosity': 0,
    },
  }
}

mod = importBaseDescription('../base/description.py', config)
locals().update(mod.__dict__)
