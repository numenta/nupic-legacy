# Copyright 2013-2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""SDR classifier diff tool.

This class can be used just like versions of the SDR classifier but internally
creates instances of each SDR classifier. Each record is fed to both
classifiers and the results are checked for differences.
"""

import numbers

from nupic.algorithms.sdr_classifier import SDRClassifier
from nupic.bindings.algorithms import SDRClassifier as SDRClassifierCpp


CALLS_PER_SERIALIZE = 100



class SDRClassifierDiff(object):
  """Classifier-like object that diffs the output from different classifiers.

  Instances of each version of the SDR classifier are created and each call to
  compute is passed to each version of the classifier. The results are diffed
  to make sure the there are no differences.

  Optionally, the classifiers can be serialized and deserialized after a
  specified number of calls to compute to ensure that serialization does not
  cause discrepencies between the results.

  TODO: Check internal state as well.
  TODO: Provide option to write output to a file.
  TODO: Provide record differences without throwing an exception.
  """


  __VERSION__ = 'SDRClassifierDiffV1'


  def __init__(self, steps=(1,), alpha=0.001, actValueAlpha=0.3, verbosity=0,
               callsPerSerialize=CALLS_PER_SERIALIZE):
    self._sdrClassifier = SDRClassifier(steps, alpha, actValueAlpha, verbosity)
    self._sdrClassifierCpp = SDRClassifierCpp(steps, alpha, actValueAlpha,
                                                verbosity)
    self._calls = 0
    self._callsPerSerialize = callsPerSerialize


  def compute(self, recordNum, patternNZ, classification, learn, infer):
    result1 = self._sdrClassifier.compute(recordNum, patternNZ, classification,
                                          learn, infer)
    result2 = self._sdrClassifierCpp.compute(recordNum, patternNZ,
                                              classification, learn, infer)
    self._calls += 1
    # Check if it is time to serialize and deserialize.
    if self._calls % self._callsPerSerialize == 0:
      schemaPy = self._sdrClassifier.getSchema()
      protoPy = schemaPy.new_message()
      self._sdrClassifier.write(protoPy)
      protoPy = schemaPy.from_bytes(protoPy.to_bytes())
      self._sdrClassifier = SDRClassifier.read(protoPy)

      schemaCpp = self._sdrClassifierCpp.getSchema()
      protoCpp = schemaCpp.new_message()
      self._sdrClassifierCpp.write(protoCpp)
      protoCpp = schemaCpp.from_bytes(protoCpp.to_bytes())
      self._sdrClassifierCpp = SDRClassifierCpp.read(protoCpp)

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
              'Python SDRClassifier has value %f and C++ SDRClassifierCpp has '
              'value %f.' % (l[i], result2[k][i]))
        else:
          assert l[i] == result2[k][i], (
              'Python SDRClassifier has value %s and C++ SDRClassifierCpp has '
              'value %s.' % (str(l[i]), str(result2[k][i])))
    return result1
