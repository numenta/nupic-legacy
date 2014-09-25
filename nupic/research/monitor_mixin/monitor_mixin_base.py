# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
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

"""
MonitorMixinBase class used in monitor mixin framework.
"""

import abc


class MonitorMixinBase(object):
  """
  Base class for MonitorMixin. Each subclass will be a mixin for a particular
  algorithm.
  """
  __metaclass__ = abc.ABCMeta


  def __init__(self, *args, **kwargs):
    super(MonitorMixinBase, self).__init__(*args, **kwargs)

    # Mapping from key (string) => trace (Trace)
    self._traces = {}

