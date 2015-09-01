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

import os
import pickle

from pkg_resources import resource_filename

from nupic.regions.RecordSensor import RecordSensor
from nupic.data.file_record_stream import FileRecordStream


"""
Generate column statistics for a StandardSource.
Each entry in statsInfo corresponds to one column, and contains a list
of statistics that should be computed for that column.  Known statistics
are:

for floating point or integer values:
number -- min, max, mean

for string or integer values:
category -- list of all unique values and count

The model for a stats object is that you call the constructor with
the first value, and then add values with add().
(The alternative would be no args for the constructor, and
all values would be added with add()).

There are two reasons for this:
- no initialization check required every time we add a value
- getStats() can always return a valid result

"""


class NumberStatsCollector(object):
  validTypes = [int, float]
  def __init__(self):
    self.min = 0
    self.max = 0
    self.sum = 0
    self.n = 0
    self.initialized = False

  def _addFirst(self, value):
    if type(value) not in self.validTypes:
      raise RuntimeError("NumberStatsCollector -- value '%s' is not a valid type" % value)

    value = float(value)
    self.min = value
    self.max = value
    self.sum = value
    self.n = 1
    self.initialized = True

  def add(self, value):
    if not self.initialized:
      self._addFirst(value)
      return

    value = float(value)
    if value < self.min:
      self.min = value
    if value > self.max:
      self.max = value
    self.sum += value
    self.n += 1

  def getStats(self):
    return dict(min = self.min,
                max = self.max,
                sum = self.sum,
                n = self.n,
                average = self.sum / self.n)

class CategoryStatsCollector(object):
  def __init__(self):
    self.categories = dict()

  def add(self, value):
    self.categories[value] = self.categories.get(value, 0) + 1

  def getStats(self):
    return dict(categories = self.categories)

def getStatsFilename(filename, statsInfo, filters=[]):
  if not os.path.isabs(filename):
    raise RuntimeError("Filename %s is not an absolute path" % filename)
  if not filename.endswith(".csv"):
    raise RuntimeError("generateStats only supports csv files: %s" % filename)
  d = os.path.dirname(filename)
  basename = os.path.basename(filename).replace("csv", "stats")
  sstring = "stats"
  for key in statsInfo:
    sstring += "_" + key
  if len(filters) > 0:
    sstring += "_filters"
  for filter in filters:
    sstring += "_" + filter.getShortName()

  statsFilename = os.path.join(d, sstring + "_" + basename)
  return statsFilename

def generateStats(filename, statsInfo, maxSamples = None, filters=[], cache=True):
  """Generate requested statistics for a dataset and cache to a file.
  If filename is None, then don't cache to a file"""

  # Sanity checking
  if not isinstance(statsInfo, dict):
    raise RuntimeError("statsInfo must be a dict -- "
                       "found '%s' instead" % type(statsInfo))

  filename = resource_filename("nupic.datafiles", filename)

  if cache:
    statsFilename = getStatsFilename(filename, statsInfo, filters)
    # Use cached stats if found AND if it has the right data
    if os.path.exists(statsFilename):
      try:
        r = pickle.load(open(statsFilename, "rb"))
      except:
        # Ok to ignore errors -- we will just re-generate the file
        print "Warning: unable to load stats for %s -- " \
              "will regenerate" % filename
        r = dict()
      requestedKeys = set([s for s in statsInfo])
      availableKeys = set(r.keys())
      unavailableKeys = requestedKeys.difference(availableKeys)
      if len(unavailableKeys ) == 0:
        return r
      else:
        print "generateStats: re-generating stats file %s because " \
              "keys %s are not available" %  \
              (filename, str(unavailableKeys))
        os.remove(filename)

  print "Generating statistics for file '%s' with filters '%s'" % (filename, filters)
  sensor = RecordSensor()
  sensor.dataSource = FileRecordStream(filename)
  sensor.preEncodingFilters = filters

  # Convert collector description to collector object
  stats = []
  for field in statsInfo:
    # field = key from statsInfo
    if statsInfo[field] == "number":
      # This wants a field name e.g. consumption and the field type as the value
      statsInfo[field] = NumberStatsCollector()
    elif statsInfo[field] == "category":
      statsInfo[field] = CategoryStatsCollector()
    else:
      raise RuntimeError("Unknown stats type '%s' for field '%s'" % (statsInfo[field], field))

  # Now collect the stats
  if maxSamples is None:
    maxSamples = 500000
  for i in xrange(maxSamples):
    try:
      record = sensor.getNextRecord()
    except StopIteration:
      break
    for (name, collector) in statsInfo.items():
      collector.add(record[name])

  del sensor

  # Assemble the results and return
  r = dict()
  for (field, collector) in statsInfo.items():
    stats = collector.getStats()
    if field not in r:
      r[field] = stats
    else:
      r[field].update(stats)

  if cache:
    f = open(statsFilename, "wb")
    pickle.dump(r, f)
    f.close()
    # caller may need to know name of cached file
    r["_filename"] = statsFilename

  return r
