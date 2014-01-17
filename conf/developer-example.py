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


'''
DEVELOPER SPECIFIC CONFIGURATION FILE

Copy to devconf.py to enable.

This file should not be checked in, and should be added to your svn/git ignore lists
'''
from nupic.support.features_list import FEATURES_LIST

###############################################################################
# Features

FEATURES = {
  'ADD': [
    'increased_awesomeness',
    ],
  'REMOVE': [
    'bad_feature',
  ]
}


# All features in a given group must appear in the features.py file

validFeatureNames = [f['name'] for f in FEATURES_LIST]
for groupName, features in FEATURES.iteritems():
  for feature in features:
    if feature not in validFeatureNames:
      raise Exception('The feature "%s" is not a recognized feature name. Please '
                      'check your spelling and/or add it to '
                      'nupic/support/features_list.py' % feature)
      
###############################################################################
