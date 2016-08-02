# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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

"""Module providing a factory for instantiating a SDR classifier."""

from nupic.algorithms.sdr_classifier import SDRClassifier
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
     src/nupic/support/nupic-default.xml
    """
    impl = kwargs.pop('implementation', None)
    if impl is None:
      impl = Configuration.get('nupic.opf.sdrClassifier.implementation')
    if impl == 'py':
      return SDRClassifier(*args, **kwargs)
    elif impl == 'cpp':
      return FastSDRClassifier(*args, **kwargs)
    else:
      raise ValueError('Invalid classifier implementation (%r). Value must be '
                       '"py" or "cpp".' % impl)


  @staticmethod
  def read(proto):
    """
    proto: SDRClassifierRegionProto capnproto object
    """
    impl = proto.implementation
    if impl == 'py':
      return SDRClassifier.read(proto.sdrClassifier)
    elif impl == 'cpp':
      return FastSDRClassifier.read(proto.sdrClassifier)
    else:
      raise ValueError('Invalid classifier implementation (%r). Value must be '
                       '"py" or "cpp".' % impl)
