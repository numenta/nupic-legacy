# Copyright 2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import importlib
import inspect
import os
import pkgutil
import tempfile
import unittest
import numpy

try:
  import capnp
  import serializable_test_capnp
except ImportError:
  # Ignore for platforms in which capnp is not available, e.g. windows
  capnp = None

import nupic
from nupic.frameworks.opf.common_models.cluster_params import (
  getScalarMetricWithTimeOfDayAnomalyParams)

from nupic.serializable import Serializable

MODEL_PARAMS = getScalarMetricWithTimeOfDayAnomalyParams([0],
                                                         minVal=23.42,
                                                         maxVal=23.420001)

SERIALIZABLE_SUBCLASSES = {
  "MovingAverage": {
    "params": {"windowSize": 1}
  },
  "AnomalyLikelihood": {},
  "BacktrackingTM": {},
  "Connections": {"params": {"numCells": 1}},
  "TemporalMemory": {},
  "KNNClassifier": {},
  "SDRClassifier": {},
  "SpatialPooler": {
    "params": {"inputDimensions": (2, 2), "columnDimensions": (4, 4)}
  },
  "Encoder": {},
  "Model": {},
  "AnomalyLikelihoodRegion": {},
  "AnomalyRegion": {},
  "TestRegion": {
    "skip": True
  },
  "BacktrackingTMCPP": {},
  "TemporalMemoryShim": {},
  "MonitoredTemporalMemory": {
    "volatile": ["mmName", "_mmTransitionTracesStale", "_mmTraces", "_mmData",
                 "_mmResetActive"]
  },
  "TMShim": {},
  "MonitoredTMShim": {
    "volatile": ["mmName", "_mmTraces", "_mmData", "_mmResetActive"]
  },
  "ScalarEncoder": {
    "params": {"w": 21, "n": 1024, "minval": 0, "maxval": 100}
  },
  "RandomDistributedScalarEncoder": {
    "params": {"resolution": 1}
  },
  "DateEncoder": {},
  "LogEncoder": {
    "params": {"w": 21, "n": 100}
  },
  "CategoryEncoder": {
    "params": {"w": 21, "categoryList": ["a", "b", "c"]}
  },
  "SDRCategoryEncoder": {
    "params": {"n": 100, "w": 21}
  },
  "ScalarSpaceEncoder": {},
  "CoordinateEncoder": {},
  "PassThroughEncoder": {
    "params": {"n": 100, "w": 21}
  },
  "MultiEncoder": {},
  "AdaptiveScalarEncoder": {
    "params": {"w": 21, "n": 1024, "minval": 0, "maxval": 100}
  },
  "DeltaEncoder": {
    "params": {"w": 21, "n": 1024, "minval": 0, "maxval": 100}
  },
  "GeospatialCoordinateEncoder": {
    "params": {"scale": 1, "timestep": 1}
  },
  "SparsePassThroughEncoder": {
    "params": {"n": 100, "w": 21}
  },
  "HTMPredictionModel": {
    "params": MODEL_PARAMS['modelConfig']['modelParams']
  },
  "TwoGramModel": {
    "params": {"encoderParams": {"blah": {"fieldname": "blah", "maxval": 9,
                                          "minval": 0, "n": 10, "w": 1,
                                          "clipInput": True, "forced": True,
                                          "type": "ScalarEncoder"}}}
  },
  "PreviousValueModel": {}
}



def _allSubclasses(cls):
  """
  Get all subclasses
  :param cls: The class to get subclasses from
  :return: list with all subclasses
  """
  return cls.__subclasses__() + [
    g for s in cls.__subclasses__() for g in _allSubclasses(s)
  ]



def _getAttributes(obj):
  """
  Get all attributes of the given object
  """
  if isinstance(obj, dict):
    attrs = obj
  elif hasattr(obj, "__slots__"):
    attrs = {attr: getattr(obj, attr) for attr in obj.__slots__}
  elif hasattr(obj, "__dict__"):
    attrs = obj.__dict__

  # Ignore volatile fields when comparing field values
  testParams = SERIALIZABLE_SUBCLASSES[obj.__class__.__name__]
  if "volatile" in testParams:
    for f in testParams["volatile"]:
      if f in attrs:
        del attrs[f]

  return attrs



def _remove(fname):
  """
  Clean up function used to delete files created by the test
  :param fname: File to be deleted
  :return:
  """
  if os.path.isfile(fname):
    os.remove(fname)



@unittest.skipUnless(capnp, "Capnp not available.")
class SerializableTest(unittest.TestCase):
  # pylint: disable=R0201,W0223
  def customAssertArrayEquals(self, a1, a2, msg=None):
    """
      Function used by `addTypeEqualityFunc` comparing numpy arrays
    """
    numpy.testing.assert_equal(a1, a2, msg)

  def customAssertSequenceEquals(self, l1, l2, msg=None):
    """
      Function used by `addTypeEqualityFunc` comparing sequences
    """
    self.assertEquals(len(l1), len(l2), msg)
    for i in xrange(len(l1)):
      first = l1[i]
      second = l2[i]
      if type(first).__name__ in SERIALIZABLE_SUBCLASSES:
        first = _getAttributes(first)
        second = _getAttributes(second)
      self.assertEquals(first, second, msg)

  def customAssertDictEquals(self, d1, d2, msg=None):
    """
        Function used by `addTypeEqualityFunc` comparing dicts
    """
    self.assertIsInstance(d1, dict, 'First argument is not a dictionary')
    self.assertIsInstance(d2, dict, 'Second argument is not a dictionary')
    self.assertEquals(len(d1), len(d2), msg + str(d1) + ' != ' + str(d2))

    for k, _ in d1.items():
      if k not in d2:
        raise AssertionError(repr(k))
      first = d1[k]
      second = d2[k]
      if type(first).__name__ in SERIALIZABLE_SUBCLASSES:
        first = _getAttributes(first)
        second = _getAttributes(second)

      self.assertEquals(first, second, 'key=%r\n%s' % (k, msg))

  def testABCProtocolEnforced(self):

    # pylint: disable=E0110
    class Foo(Serializable):
      pass  # read(), write(), getCapnpSchema() not implemented here

    with self.assertRaises(TypeError):
      Foo()

  def testReadFromAndWriteToFile(self):
    """ Test generic usage of serializable mixin class """

    class Bar(object):
      pass

    class Foo(Bar, Serializable):

      def __init__(self, bar):
        self.bar = bar

      @classmethod
      def getSchema(cls):
        return serializable_test_capnp.Foo

      @classmethod
      def read(cls, proto):
        foo = object.__new__(cls)
        foo.bar = proto.bar
        return foo

      def write(self, proto):
        proto.bar = self.bar

    filename = tempfile.mktemp()
    self.addCleanup(_remove, filename)

    with open(filename, "wb") as outp:
      Foo("bar").writeToFile(outp)

    with open(filename, "rb") as inp:
      self.assertEqual(Foo.readFromFile(inp).bar, "bar")

  def testAllSubClasses(self):
    """
    Test all Serializable subclasses making sure all the fields are initialized
    """
    self.addTypeEqualityFunc(numpy.ndarray, self.customAssertArrayEquals)
    self.addTypeEqualityFunc(tuple, self.customAssertSequenceEquals)
    self.addTypeEqualityFunc(list, self.customAssertSequenceEquals)
    self.addTypeEqualityFunc(dict, self.customAssertDictEquals)

    # Import all nupic modules to find Serializable subclasses
    packages = pkgutil.walk_packages(path=nupic.__path__,
                                     prefix=nupic.__name__ + ".")
    for _, modname, ispkg in packages:
      if not ispkg:
        try:
          importlib.import_module(modname)
        except: # pylint: disable=W0702
          pass  # Ignore deprecated modules

    # Check every Serializable subclass
    for klass in _allSubclasses(Serializable):
      if inspect.isabstract(klass):
        continue

      # Make sure all serializable classes are accounted for
      self.assertIn(klass.__name__, SERIALIZABLE_SUBCLASSES)
      print klass.__name__
      testParams = SERIALIZABLE_SUBCLASSES[klass.__name__]

      # Skip test class
      if "skip" in testParams:
        continue

      # Instantiate class with test parameters
      if "params" in testParams:
        original = klass(**(testParams["params"]))
      else:
        original = klass()

      # Test read/write
      filename = tempfile.mktemp()
      self.addCleanup(_remove, filename)
      with open(filename, "wb") as outp:
        original.writeToFile(outp)

      with open(filename, "rb") as inp:
        serialized = klass.readFromFile(inp)

      expected = _getAttributes(original)
      actual = _getAttributes(serialized)

      # Make sure all fields were initialized
      self.assertEquals(actual, expected, klass.__name__)
