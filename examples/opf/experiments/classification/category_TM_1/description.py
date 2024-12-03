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
                                         '../datasets/category_TM_1.csv'),
  'modelParams': { 'clParams': { 'verbosity': 0},
                   'sensorParams': { 'encoders': { }, 'verbosity': 0},
                   'spParams': { 'spVerbosity': 0},
                   'tmEnable': True,
                   'tmParams': { 'verbosity': 0}}}

mod = importBaseDescription('../base_category/description.py', config)
locals().update(mod.__dict__)
