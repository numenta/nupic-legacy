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
A list of all features that are in production or under development.

Required Metadata:
  name            The name of the feature
  description     A one or two line summary of the feature
  date            A date string in format YYYYMMDD
  author          Who came up with this crazy scheme?

'''



FEATURES_LIST = [
  {'name': 'base_feature',
    'description': 'This feature must exist for all environments for Nupic to run',
    'dateAdded': '20110916',
    'author': 'idanforth'},

  {'name': 'second_feature',
    'description': 'This is a secondary feature to use as an example',
    'dateAdded': '20110916',
    'author': 'idanforth'},

  {'name': 'third_feature',
    'description': 'This is another feature that would be cool to have',
    'dateAdded': '20110916',
    'author': 'idanforth'},

  {'name': 'increased_awesomeness',
    'description': 'Example feature added in default devconf-example.py',
    'dateAdded': '20110916',
    'author': 'idanforth'},

  {'name': 'bad_feature',
    'description': 'Example feature removed in default devconf-example.py',
    'dateAdded': '20110916',
    'author': 'idanforth'},

  {'name': 'project_delete_button',
    'description': 'A new button to delete a project from the "Projects" view',
    'dateAdded': '20110919',
    'author': 'idanforth'},
]



required_fields = ['name', 'description', 'dateAdded', 'author']
for feature in FEATURES_LIST:
  for field in required_fields:
    val = feature.get(field)
    if not val:
      raise Exception('Field "%s" is required. Feature: %s' % (field, str(feature)))
