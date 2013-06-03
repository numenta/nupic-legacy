#! /usr/local/bin/python

# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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
## @file

This package contains modules for analyzing HTM networks
and their inputs and outputs.

Import packages, modules, functions and classes include:

"""
import nupic

__all__ = [
    "inferenceanalysis",
    "InferenceAnalysis",
    "ClassifyInference",
    "CompareClassifications",
    "ReadInference",
  ]

# The inspectors rely on wxPython and TraitsUI,
# which are not included on all platforms
try:
  import wx
  import enthought.traits
except ImportError:
  pass
else:
  from nupic.analysis._inspect import inspect, loadInspectors, saveInspectors