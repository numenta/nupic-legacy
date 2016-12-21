# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-15, Numenta, Inc.  Unless you have an agreement
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


  def testFieldMetaInfoRaisesValueErrorOnInvalidFieldType(self):
    with self.assertRaises(ValueError):
      FieldMetaInfo("fieldName", "bogus-type", FieldMetaSpecial.none)


  def testFieldMetaInfoRaisesValueErrorOnInvalidFieldSpecial(self):
    with self.assertRaises(ValueError):
      FieldMetaInfo("fieldName", FieldMetaType.integer, "bogus-special")


  def testFieldMetaSpecialIsValid(self):
    self.assertEqual(FieldMetaSpecial.isValid(FieldMetaSpecial.none), True)
    self.assertEqual(FieldMetaSpecial.isValid(FieldMetaSpecial.reset), True)
    self.assertEqual(FieldMetaSpecial.isValid(FieldMetaSpecial.sequence), True)
    self.assertEqual(FieldMetaSpecial.isValid(FieldMetaSpecial.timestamp), True)
    self.assertEqual(FieldMetaSpecial.isValid(FieldMetaSpecial.category), True)
    self.assertEqual(FieldMetaSpecial.isValid(FieldMetaSpecial.learning), True)

    self.assertEqual(FieldMetaSpecial.isValid("bogus-special"), False)


  def testFieldMetaTypeIsValid(self):
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.string), True)
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.datetime), True)
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.integer), True)
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.float), True)
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.boolean), True)
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.list), True)
    self.assertEqual(FieldMetaType.isValid(FieldMetaType.sdr), True)

    self.assertEqual(FieldMetaType.isValid("bogus-type"), False)



if __name__ == "__main__":
  unittest.main()
