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

"""CLA classifier diff tool.

This class can be used just like versions of the CLA classifier but internally
creates instances of each CLA classifier. Each record is fed to both
classifiers and the results are checked for differences.
"""

import cPickle as pickle
import numbers

from nupic.algorithms.CLAClassifier import CLAClassifier
from nupic.bindings.algorithms import FastCLAClassifier


CALLS_PER_SERIALIZE = 100



class CLAClassifierDiff(object):
  """Classifier-like object that diffs the output from different classifiers.

  Instances of each version of the CLA classifier are created and each call to
  compute is passed to each version of the classifier. The results are diffed
  to make sure the there are no differences.

  Optionally, the classifiers can be serialized and deserialized after a
  specified number of calls to compute to ensure that serialization does not
  cause discrepencies between the results.

  TODO: Check internal state as well.
  TODO: Provide option to write output to a file.
  TODO: Provide record differences without throwing an exception.
  """


  __VERSION__ = 'CLAClassifierDiffV1'


  def __init__(self, steps=(1,), alpha=0.001, actValueAlpha=0.3, verbosity=0,
               callsPerSerialize=CALLS_PER_SERIALIZE):
    self._claClassifier = CLAClassifier(steps, alpha, actValueAlpha, verbosity)
    self._fastCLAClassifier = FastCLAClassifier(steps, alpha, actValueAlpha,
                                                verbosity)
    self._calls = 0
    self._callsPerSerialize = callsPerSerialize


  def compute(self, recordNum, patternNZ, classification, learn, infer):
    result1 = self._claClassifier.compute(recordNum, patternNZ, classification,
                                          learn, infer)
    result2 = self._fastCLAClassifier.compute(recordNum, patternNZ,
                                              classification, learn, infer)
    self._calls += 1
    # Check if it is time to serialize and deserialize.
    if self._calls % self._callsPerSerialize == 0:
      self._claClassifier = pickle.loads(pickle.dumps(self._claClassifier))
      self._fastCLAClassifier = pickle.loads(pickle.dumps(
          self._fastCLAClassifier))
    # Assert both results are the same type.
    assert type(result1) == type(result2)
    # Assert that the keys match.
    assert set(result1.keys()) == set(result2.keys()), "diff detected: " \
      "py result=%s, C++ result=%s" % (result1, result2)
    # Assert that the values match.
    for k, l in result1.iteritems():
      assert type(l) == type(result2[k])
      for i in xrange(len(l)):
        if isinstance(classification['actValue'], numbers.Real):
          assert abs(float(l[i]) - float(result2[k][i])) < 0.0000001, (
              'Python CLAClassifier has value %f and C++ FastCLAClassifier has '
              'value %f.' % (l[i], result2[k][i]))
        else:
          assert l[i] == result2[k][i], (
              'Python CLAClassifier has value %s and C++ FastCLAClassifier has '
              'value %s.' % (str(l[i]), str(result2[k][i])))
    return result1
