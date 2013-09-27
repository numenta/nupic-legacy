#!/usr/bin/env python
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

"""Unit tests for SDR Category encoder"""

import numpy
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
import unittest2 as unittest

from nupic.encoders.sdrcategory import SDRCategoryEncoder


#########################################################################
class SDRCategoryEncoderTest(unittest.TestCase):
  '''Unit tests for SDRCategory encoder class'''


  def testSDRCategoryEncoder(self):
      print "Testing CategoryEncoder...",
      # make sure we have > 16 categories so that we have to grow our sdrs
      categories = ["ES", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8",
                    "S9","S10", "S11", "S12", "S13", "S14", "S15", "S16",
                    "S17", "S18", "S19", "GB", "US"]

      fieldWidth = 100
      bitsOn = 10

      s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = categories,
                             name="foo", verbosity=0)

      # internal check
      assert s.sdrs.shape == (32, fieldWidth)

      # ES
      es = s.encode("ES")
      assert es.sum() == bitsOn
      assert es.shape == (fieldWidth,)
      assert es.sum() == bitsOn

      x = s.decode(es)
      assert isinstance(x[0], dict)
      assert "foo" in x[0]
      assert x[0]["foo"][1] == "ES"

      topDown = s.topDownCompute(es)
      assert topDown.value == 'ES'
      assert topDown.scalar == 1
      assert topDown.encoding.sum() == bitsOn

      # ----------------------------------------------------------------------
      # Test topdown compute
      for v in categories:
        output = s.encode(v)
        topDown = s.topDownCompute(output)
        assert topDown.value == v
        assert topDown.scalar == s.getScalars(v)[0]

        bucketIndices = s.getBucketIndices(v)
        print "bucket index =>", bucketIndices[0]
        topDown = s.getBucketInfo(bucketIndices)[0]
        assert topDown.value == v
        assert topDown.scalar == s.getScalars(v)[0]
        assert (topDown.encoding == output).all()
        assert topDown.value == s.getBucketValues()[bucketIndices[0]]


      # Unknown
      unknown = s.encode("ASDFLKJLK")
      assert unknown.sum() == bitsOn
      assert unknown.shape == (fieldWidth,)
      assert unknown.sum() == bitsOn
      x = s.decode(unknown)
      assert x[0]["foo"][1] == "<UNKNOWN>"

      topDown = s.topDownCompute(unknown)
      assert topDown.value == "<UNKNOWN>"
      assert topDown.scalar == 0

      # US
      us = s.encode("US")
      assert us.sum() == bitsOn
      assert us.shape == (fieldWidth,)
      assert us.sum() == bitsOn
      x = s.decode(us)
      assert x[0]["foo"][1] == "US"

      topDown = s.topDownCompute(us)
      assert topDown.value == "US"
      assert topDown.scalar == len(categories)
      assert topDown.encoding.sum() == bitsOn

      # empty field
      empty = s.encode(SENTINEL_VALUE_FOR_MISSING_DATA)
      assert empty.sum() == 0
      assert empty.shape == (fieldWidth,)
      assert empty.sum() == 0

      # make sure it can still be decoded after a change
      bit =  s.random.randint(0, s.getWidth()-1)
      us[bit] = 1 - us[bit]
      x = s.decode(us)
      assert x[0]["foo"][1] == "US"


      # add two reps together
      newrep = ((us + unknown) > 0).astype('uint8')
      x = s.decode(newrep)
      name =x[0]["foo"][1]
      if name != "US <UNKNOWN>" and name != "<UNKNOWN> US":
        othercategory = name.replace("US", "")
        othercategory = othercategory.replace("<UNKNOWN>", "")
        othercategory = othercategory.replace(" ", "")
        otherencoded = s.encode(othercategory)
        print "Got: %s instead of US/unknown" % name
        print "US: %s" % us
        print "unknown: %s" % unknown
        print "Sum: %s" % newrep
        print "%s: %s" % (othercategory, s.encode(othercategory))

        print "Matches with US: %d" % (us * newrep).sum()
        print "Matches with unknown: %d" % (unknown * newrep).sum()
        print "Matches with %s: %d" % (othercategory,
                         (otherencoded * newrep).sum())

        raise RuntimeError("Decoding failure")

      # serialization
      import cPickle as pickle
      t = pickle.loads(pickle.dumps(s))
      assert (t.encode("ES") == es).all()
      assert (t.encode("GB") == s.encode("GB")).all()


      # Test autogrow
      s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = None, name="bar")

      es = s.encode("ES")
      assert es.shape == (fieldWidth,)
      assert es.sum() == bitsOn
      x = s.decode(es)
      assert isinstance(x[0], dict)
      assert "bar" in x[0]
      assert x[0]["bar"][1] == "ES"


      us = s.encode("US")
      assert us.shape == (fieldWidth,)
      assert us.sum() == bitsOn
      x = s.decode(us)
      assert x[0]["bar"][1] == "US"

      es2 = s.encode("ES")
      assert (es2 == es).all()

      us2 = s.encode("US")
      assert (us2 == us).all()

      # make sure it can still be decoded after a change
      bit =  s.random.randint(0, s.getWidth()-1)
      us[bit] = 1 - us[bit]
      x = s.decode(us)
      assert x[0]["bar"][1] == "US"

      # add two reps together
      newrep = ((us + es) > 0).astype('uint8')
      x = s.decode(newrep)
      name =x[0]["bar"][1]
      assert name == "US ES" or name == "ES US"

      # Catch duplicate categories
      caughtException = False
      newcategories = categories[:]
      assert "ES" in newcategories
      newcategories.append("ES")
      try:
        s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, categoryList = newcategories, name="foo")
      except RuntimeError, e:
        caughtException = True
      if not caughtException:
        raise RuntimeError("Did not catch duplicate category in constructor")
        raise

      # serialization for autogrow encoder
      gs = s.encode("GS")
      t = pickle.loads(pickle.dumps(s))
      assert (t.encode("ES") == es).all()
      assert (t.encode("GS") == gs).all()

    # -----------------------------------------------------------------------

  def testAutogrow(self):
      """testing auto-grow"""
      fieldWidth = 100
      bitsOn = 10

      s = SDRCategoryEncoder(n=fieldWidth, w=bitsOn, name="foo", verbosity=2)

      encoded = numpy.zeros(fieldWidth)
      assert s.topDownCompute(encoded).value == "<UNKNOWN>"

      s.encodeIntoArray("catA", encoded)
      assert encoded.sum() == bitsOn
      assert s.getScalars('catA') == 1
      catA = encoded.copy()

      s.encodeIntoArray("catB", encoded)
      assert encoded.sum() == bitsOn
      assert s.getScalars('catB') == 2
      catB = encoded.copy()

      assert s.topDownCompute(catA).value == 'catA'
      assert s.topDownCompute(catB).value == 'catB'

      s.encodeIntoArray(SENTINEL_VALUE_FOR_MISSING_DATA, encoded)
      assert sum(encoded) == 0
      assert s.topDownCompute(encoded).value == "<UNKNOWN>"

      #Test Disabling Learning and autogrow
      s.setLearning(False)
      s.encodeIntoArray("catC", encoded)
      assert encoded.sum() == bitsOn
      assert s.getScalars('catC') == 0
      assert s.topDownCompute(encoded).value == "<UNKNOWN>"

      s.setLearning(True)
      s.encodeIntoArray("catC", encoded)
      assert encoded.sum() == bitsOn
      assert s.getScalars('catC') == 3
      assert s.topDownCompute(encoded).value == "catC"


###########################################
if __name__ == '__main__':
  unittest.main()
