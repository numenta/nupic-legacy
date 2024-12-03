# Copyright 2013-2015 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Unit tests for nupic.data.fieldmeta."""

import unittest2 as unittest

from nupic.data.field_meta import FieldMetaInfo, FieldMetaType, FieldMetaSpecial



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
