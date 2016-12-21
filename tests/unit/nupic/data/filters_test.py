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

"""Unit tests for filters module.

NOTE: This test was migrated from the old repo and could use some refactoring.
"""

from datetime import datetime

import numpy
import unittest2 as unittest
from pkg_resources import resource_filename

from nupic.regions.RecordSensor import RecordSensor
from nupic.data.file_record_stream import FileRecordStream
from nupic.encoders import MultiEncoder
from nupic.data.filters import DeltaFilter



class FiltersTest(unittest.TestCase):


  @unittest.skip("Disabled until we figure out why it is failing in internal"
                 " tests")
  def testDeltaFilter(self):
    """
    data looks like:        should generate deltas
      "t"   "s"               "dt"     "ds"

      t     10                 X
      t+1s  20                 1s      10
      t+1d  50                 86399   30

    r t+1d+1s  60              X
      r+1d+3s  65              2s       5

    """
    r = RecordSensor()
    filename = resource_filename("nupic.datafiles", "extra/qa/delta.csv")
    datasource = FileRecordStream(filename)
    r.dataSource = datasource
    n = 50
    encoder = MultiEncoder({'blah': dict(fieldname="s", type='ScalarEncoder',
                                         n=n, w=11, minval=0, maxval=100)})

    r.encoder = encoder

    # Test #1 -- no deltas
    # Make sure we get a reset when the gym changes
    resetOut = numpy.zeros((1,), dtype='float')
    sequenceIdOut = numpy.zeros((1,), dtype='float')
    dataOut = numpy.zeros((n,), dtype='float')
    sourceOut = numpy.zeros((1,), dtype='float')
    categoryOut = numpy.zeros((1,), dtype='float')

    outputs = dict(resetOut=resetOut,
                   sourceOut = sourceOut,
                   sequenceIdOut = sequenceIdOut,
                   dataOut = dataOut,
                   categoryOut = categoryOut)
    inputs = dict()
    r.verbosity=0

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=24, hour=16,
                                       minute=8, second=0))
    self.assertEqual(lr['s'], 10)
    self.assertEqual(lr['_reset'], 1)
    self.assertTrue('dt' not in lr)
    self.assertTrue('ds' not in lr)

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=24, hour=16,
                                       minute=8, second=1))
    self.assertEqual(lr['s'], 20)
    self.assertEqual(lr['_reset'], 0)

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=25, hour=16,
                                       minute=8, second=0))
    self.assertEqual(lr['s'], 50)
    self.assertEqual(lr['_reset'], 0)

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=25, hour=16,
                                       minute=8, second=1))
    self.assertEqual(lr['s'], 60)
    self.assertEqual(lr['_reset'], 1)

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=25, hour=16,
                                       minute=8, second=3))
    self.assertEqual(lr['s'], 65)
    self.assertEqual(lr['_reset'], 0)

    # Add filters

    r.preEncodingFilters = [DeltaFilter("s", "ds"), DeltaFilter("t", "dt")]
    r.rewind()

    # skip first record, which has a reset

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=24, hour=16,
                                       minute=8, second=1))
    self.assertEqual(lr['s'], 20)
    self.assertEqual(lr['_reset'], 1)  # this record should have a reset since
                                       # it is first of a sequence
    self.assertEqual(lr['dt'], 1)
    self.assertEqual(lr['ds'], 10)

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=25, hour=16,
                                       minute=8, second=0))
    self.assertEqual(lr['s'], 50)
    self.assertEqual(lr['_reset'], 0)
    self.assertEqual(lr['dt'], 3600 * 24 - 1)
    self.assertEqual(lr['ds'], 30)

    # next reset record is skipped

    r.compute(inputs, outputs)
    lr = r.lastRecord
    self.assertEqual(lr['t'], datetime(year=2011, month=2, day=25, hour=16,
                                       minute=8, second=3))
    self.assertEqual(lr['s'], 65)
    self.assertEqual(lr['_reset'], 1)
    self.assertEqual(lr['dt'], 2)
    self.assertEqual(lr['ds'], 5)



if __name__ == "__main__":
  unittest.main()
