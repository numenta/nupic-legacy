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

"""Module providing a factory for instantiating a CLA classifier."""

from nupic.algorithms.CLAClassifier import CLAClassifier
from nupic.algorithms.cla_classifier_diff import CLAClassifierDiff
from nupic.bindings.algorithms import FastCLAClassifier
from nupic.support.configuration import Configuration



class CLAClassifierFactory(object):
  """Factory for instantiating CLA classifiers."""


  @staticmethod
  def create(*args, **kwargs):
    impl = kwargs.pop('implementation', None)
    if impl is None:
      impl = Configuration.get('nupic.opf.claClassifier.implementation')
    if impl == 'py':
      return CLAClassifier(*args, **kwargs)
    elif impl == 'cpp':
      return FastCLAClassifier(*args, **kwargs)
    elif impl == 'diff':
      return CLAClassifierDiff(*args, **kwargs)
    else:
      raise ValueError('Invalid classifier implementation (%r). Value must be '
                       '"py" or "cpp".' % impl)
