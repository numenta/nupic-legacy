#!/usr/bin/env python

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

from datetime import datetime, timedelta


class AutoResetFilter(object):
  """Initial implementation of auto-reset is fairly simple. You just give it a
  time interval.  Like aggregation, we the first time period start with the
  time of the first record (t0) and signal a reset at the first record on or after
  t0 + interval, t0 + 2 * interval, etc.

  We could get much fancier than this, but it is not clear what will be
  needed. For example, if you want a reset every day, you  might expect the
  period to start at midnight. We also don't handle variable-time periods --
  month and year.
  """
  def __init__(self, interval=None, datetimeField=None):
    self.setInterval(interval, datetimeField)

  def setInterval(self, interval=None, datetimeField=None):
    if interval is not None:
      assert isinstance(interval, timedelta)
    self.interval = interval
    self.datetimeField = datetimeField
    self.lastAutoReset = None


  def process(self, data):
    if self.interval is None:
      return True # no more data needed

    if self.datetimeField is None:
      self._getDatetimeField(data)

    date = data[self.datetimeField]
    if data['_reset'] != 0:
      self.lastAutoReset = date
      return True # no more data needed

    if self.lastAutoReset is None:
      self.lastAutoReset = date
      return True

    if  date >= self.lastAutoReset + self.interval:
      # might have skipped several intervals
      while  date >= self.lastAutoReset + self.interval:
        self.lastAutoReset += self.interval
      data['_reset'] = 1
      return True  # no more data needed

    elif date < self.lastAutoReset:
      # sequence went back in time!
      self.lastAutoReset = date

    return True


  def _getDatetimeField(self, data):
    datetimeField = None
    assert isinstance(data, dict)
    for (name, value) in data.items():
      if isinstance(value, datetime):
        datetimeField = name
        break
    if datetimeField is None:
      raise RuntimeError("Autoreset requested for the data but there is no date field")
    self.datetimeField = datetimeField

  def getShortName(self):
    if interval is not None:
      s = "autoreset_%d_%d" % (interval.days, interval.seconds)
    else:
      s = "autoreset_none"
    return s


class DeltaFilter(object):
  def __init__(self, origField, deltaField):
    """Add a delta field to the data.
    """
    self.origField = origField
    self.deltaField = deltaField
    self.previousValue = None
    self.rememberReset = False

  def process(self, data):
    val = data[self.origField]
    if self.previousValue is None or data['_reset']:
      self.previousValue = val
      self.rememberReset = data['_reset']
      return False

    # We have a delta
    delta = val - self.previousValue
    self.previousValue = val

    if isinstance(delta, timedelta):
      data[self.deltaField] = float(delta.days * 24 * 3600) + \
          float(delta.seconds) + float(delta.microseconds) * 1.0e-6
    else:
      data[self.deltaField] = float(delta)

    if self.rememberReset:
      data['_reset'] = 1
      self.rememberReset = False

    return True

  def getShortName(self):
    return "delta_%s" % self.origField
