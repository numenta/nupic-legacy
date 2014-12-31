#!/usr/bin/env python
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

"""Unit tests for nupic.data.fieldmeta."""

import unittest2 as unittest

from nupic.data.fieldmeta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial



class FieldMetaTest(unittest.TestCase):
  """FieldMetaInfo unit tests."""


  def testFieldMetaInfo(self):
    # Create a single FieldMetaInfo instance from a File field"s meta-data tuple
    e = ("pounds", FieldMetaType.float, FieldMetaSpecial.none)
    m = FieldMetaInfo.createFromFileFieldElement(e)

    self.assertEqual(e, m)

    # Create a list of FieldMetaInfo instances from a list of File meta-data
    # tuples
    el = [("pounds", FieldMetaType.float, FieldMetaSpecial.none),
          ("price", FieldMetaType.float, FieldMetaSpecial.none),
          ("id", FieldMetaType.string, FieldMetaSpecial.sequence),
          ("date", FieldMetaType.datetime, FieldMetaSpecial.timestamp),
         ]
    ml = FieldMetaInfo.createListFromFileFieldList(el)

    self.assertEqual(el, ml)



if __name__ == "__main__":
  unittest.main()
