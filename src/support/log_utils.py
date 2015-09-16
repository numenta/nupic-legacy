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

# This file contains utility functions that are used
# internally by the prediction framework. It should not be
# imported by description files. (see helpers.py)


import logging
import inspect

def createLogger(obj):
  """Helper function to create a logger object for the current object with
  the standard Numenta prefix """
  if inspect.isclass(obj):
    myClass = obj
  else:
    myClass = obj.__class__
  logger = logging.getLogger(".".join(
    ['com.numenta', myClass.__module__, myClass.__name__]))
  return logger
