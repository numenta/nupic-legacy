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

"""
This file defines the 'starBlock' explorer.

"""

import numpy



class ModifyFields:
  """
  This RecordSensor filter adds noise to the input

  """


  def __init__(self, fields=[], operation='setToZero', seed=-1):
    """ Construct the filter

    Parameters:
    -------------------------------------------------
    fields:     List of field names to modify
    operation:  Operation to perform on the fields, options include:
                 - setToZero: set fields to all 0's.

    """

    assert operation in ['setToZero']

    self.operation = operation

    # If fields is a simple string, make it a list
    if not hasattr(fields, '__iter__'):
      fields = [fields]
    self.fields = fields

    if seed != -1:
      numpy.random.seed(seed)


  def process(self, encoder, data):
    """ Modify the data in place, adding noise
    """

    if len(self.fields) == 0:
      return

    # Impelement self.operation on each named field
    for field in self.fields:
      (offset, width) = encoder.getFieldDescription(field)

      if self.operation == 'setToZero':
        data[offset: offset+width] = 0

      else:
        assert (False)
