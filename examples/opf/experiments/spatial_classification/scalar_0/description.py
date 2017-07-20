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
{
  'dataSource': 'file://' + os.path.join(os.path.dirname(__file__),
                                         '../datasets/scalar_0.csv'),
  'errorMetric': 'aae',

  'modelParams': {
    'sensorParams': {
      'verbosity': 0,
      'encoders': {
        'field1': {
          'clipInput': True,
          'fieldname': u'field1',
          'maxval': 0.1,
          'minval': 0.0,
          'n': 211,
          'name': u'field1',
          'type': 'ScalarEncoder',
          'w': 21
        },
        'classification': {
          'classifierOnly': True,
          'clipInput': True,
          'fieldname': u'classification',
          'maxval': 1.0,
          'minval': 0.0,
          'n': 211,
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
