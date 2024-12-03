# Copyright 2016 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Module providing a factory for instantiating a SDR classifier."""

from nupic.algorithms.sdr_classifier import SDRClassifier
from nupic.algorithms.sdr_classifier_diff import SDRClassifierDiff
from nupic.bindings.algorithms import SDRClassifier as FastSDRClassifier
from nupic.support.configuration import Configuration



class SDRClassifierFactory(object):
  """Factory for instantiating SDR classifiers."""


  @staticmethod
  def create(*args, **kwargs):
    """
    Create a SDR classifier factory.
    The implementation of the SDR Classifier can be specified with
    the "implementation" keyword argument.

    The SDRClassifierFactory uses the implementation as specified in
     `Default NuPIC Configuration <default-config.html>`_.
    """
    impl = kwargs.pop('implementation', None)
    if impl is None:
      impl = Configuration.get('nupic.opf.sdrClassifier.implementation')
    if impl == 'py':
      return SDRClassifier(*args, **kwargs)
    elif impl == 'cpp':
      return FastSDRClassifier(*args, **kwargs)
    elif impl == 'diff':
      return SDRClassifierDiff(*args, **kwargs)
    else:
      raise ValueError('Invalid classifier implementation (%r). Value must be '
                       '"py", "cpp" or "diff".' % impl)


  @staticmethod
  def read(proto):
    """
    :param proto: SDRClassifierRegionProto capnproto object
    """
    impl = proto.implementation
    if impl == 'py':
      return SDRClassifier.read(proto.sdrClassifier)
    elif impl == 'cpp':
      return FastSDRClassifier.read(proto.sdrClassifier)
    elif impl == 'diff':
      return SDRClassifierDiff.read(proto.sdrClassifier)
    else:
      raise ValueError('Invalid classifier implementation (%r). Value must be '
                       '"py", "cpp" or "diff".' % impl)
