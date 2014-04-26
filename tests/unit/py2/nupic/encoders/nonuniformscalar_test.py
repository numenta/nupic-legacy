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

"""Unit tests for non-uniform scalar encoder"""


from nupic.encoders.base import defaultDtype
import unittest2 as unittest

from nupic.encoders.nonuniformscalar import NonUniformScalarEncoder


#########################################################################
class NonUniformScalarEncoderTest(unittest.TestCase):
  '''Unit tests for DateEncoder class'''


    ############################################################################
  def testNonUniformScalarEncoder(self):
      import numpy.random
      print "Testing NonUniformScalarEncoder..."

      def testEncoding(value, expected, encoder):
        observed = None
        expected = numpy.array(expected, dtype=defaultDtype)
        try:
          observed = encoder.encode(value)
          self.assertTrue((observed == expected).all())
        except :
          print "Encoder Bins:\n%s"% encoder.bins
          raise Exception("Encoding Error: encoding value %f \
                                    expected %s\n got %s "%
                                    (value, str(expected), str(observed)))

      # TODO: test parent class methods
      #
      # -----------------------------------------
      # Start with simple uniform case:
      print "\t*Testing uniform distribution*"

      data = numpy.linspace( 1, 10, 10, endpoint = True)
      # forced=True is not recommended, but used here for readibility, see scalar.py
      enc = NonUniformScalarEncoder(w=7,n=16, data=data, verbosity=3, forced=True)
      expectedEncoding = numpy.zeros(16)
      expectedEncoding[:7] = 1
      for i in range(1,10):
        testEncoding(i, expectedEncoding, enc)
        expectedEncoding = numpy.roll(expectedEncoding, 1)

      testEncoding(10, [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,0], enc)
      del enc

      ## -----------------------------------------
      # Make sure the encoder works with a larger set of
      # bins and skewed distributions
      print "\t*Testing skewed distribution*"
      data = numpy.linspace(0, 10, 100)
      data = numpy.append(data, numpy.linspace(10,20,200))
      # Shuffle the data so that the order doesn't matter
      numpy.random.shuffle(data)
      enc = NonUniformScalarEncoder(w = 7, n=9, data=data, forced=True)

      testEncoding(5, [1,1,1,1,1,1,1,0,0], enc)
      testEncoding(9, [1,1,1,1,1,1,1,0,0], enc)
      testEncoding(10, [0,1,1,1,1,1,1,1,0], enc)
      testEncoding(14.9, [0,1,1,1,1,1,1,1,0], enc)
      testEncoding(15, [0,0,1,1,1,1,1,1,1], enc)
      testEncoding(19, [0,0,1,1,1,1,1,1,1], enc)

      del enc

      ## -----------------------------------------
      ## Make sure the encoder works with non-uniform weights
      ## bins and very skewed distributions
      print "\t*Testing weighted distribution*"
      data = numpy.linspace(0, 10, 100)
      weights= 4 * numpy.ones_like(data)
      data = numpy.append(data, numpy.linspace(10,20,200))
      weights = numpy.append(weights, numpy.ones(200))
      enc = NonUniformScalarEncoder(w = 7, n=9, data=data, weights=weights, forced=True)

      testEncoding(3, [1,1,1,1,1,1,1,0,0], enc)
      testEncoding(5, [0,1,1,1,1,1,1,1,0], enc)
      testEncoding(9, [0,1,1,1,1,1,1,1,0], enc)
      testEncoding(10, [0,0,1,1,1,1,1,1,1], enc)
      testEncoding(15, [0,0,1,1,1,1,1,1,1], enc)

      del enc
      #
      ## -----------------------------------------
      ## Stress test: make sure that ranges still
      ## make sense if there are a lot of bins
      print "\t*Stress Test*"
      data = numpy.concatenate([numpy.repeat(10, 30),
                                                  numpy.repeat(5, 20),
                                                  numpy.repeat(20, 35)])
      enc = NonUniformScalarEncoder(w=7, n=100, data=data, verbosity=2, forced=True)
      result = numpy.zeros(100, dtype=defaultDtype)
      result[0:7] = 1
      testEncoding(5, result, enc)



      ##  Now test a very discontinuous distribution
      #TODO: Not really sure what should happen here
      #data = 10 * numpy.ones(500)
      #data[250:] *= 2
      #enc = NonUniformScalarEncoder(w =3, n=4, data=data, verbosity = 2)
      #
      #assert enc.resolution == 1.0
      #assert enc._numBins == 2
      ##assert(enc.bins == numpy.array([[0,10.0], [10.0, 20.0]])).all()
      #
      #testEncoding(-1, [1,1,1,0], enc)
      #testEncoding(5, [1,1,1,0], enc)
      #testEncoding(10, [0,1,1,1], enc)
      #testEncoding(15, [0,1,1,1], enc)
      #testEncoding(25, [0,1,1,1], enc)
      #del enc
      #
      ## -----------------------------------------
      ## Now a case similar to the first, but with the proportions slightly uneven
      ## TODO: What should actually happen here ?
      #print "\t*Testing uneven distribution*"
      #data = 10 * numpy.ones(500)
      #data[248:] *= 2
      #enc = NonUniformScalarEncoder(w =3, n=4, data=data, verbosity = 0)
      #testEncoding(9, [1,1,1,0], enc)
      #testEncoding(10, [1,1,1,0], enc)
      #testEncoding(20, [0,1,1,1], enc)
      #del enc


      ## -----------------------------------------
      ## Test top-down decoding
      print "\t*Testing top-down decoding*"
      data = numpy.random.random_sample(400)
      enc = NonUniformScalarEncoder(w=7, n=9, data=data, verbosity=3, forced=True)
      print enc.dump()
      output = numpy.array([1,1,1,1,1,1,1,0,0], dtype=defaultDtype)
      for i in xrange(enc.n - enc.w + 1):
        topdown = enc.topDownCompute(output)
        bin = enc.bins[i,:]
        self.assertTrue(topdown[0].value >= bin[0] and topdown[0].value < bin[1])
        output = numpy.roll(output, 1)

      print "\t*Test TD decoding with explicit bins*"
      bins = [[   0. ,    199.7  ],
        [ 199.7,   203.1  ],
        [ 203.1,    207.655],
        [ 207.655,  212.18 ],
        [ 212.18,   214.118],
        [ 214.118,  216.956],
        [ 216.956,  219.133]]

      enc = NonUniformScalarEncoder(w=7, n=13, bins=bins, forced=True)

      # -----------------------------------------
      # Test TD compute on
      tdOutput = numpy.array([ 0.0, 0.0, 0.0, 0.0, 0.40000001, 1.0,
                            1.0, 1.0, 1.0, 1.0, 1.0, 0.60000002,
                            0.60000002])
      enc.topDownCompute(tdOutput)
      topdown = enc.topDownCompute(tdOutput)
      testEncoding(topdown[0].value, [0,0,0,0,0,1,1,1,1,1,1,1,0], enc)
      # -----------------------------------------
      print "\t*Test TD decoding with non-contiguous ranges*"

      tdOutput = numpy.array([ 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
                            1.0, 1.0, 1.0, 1.0, 1.0, 0.60000002,
                            0.60000002])

      topdown = enc.topDownCompute(tdOutput)
      testEncoding(topdown[0].value, [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,1], enc)

###########################################
if __name__ == '__main__':
  unittest.main()
