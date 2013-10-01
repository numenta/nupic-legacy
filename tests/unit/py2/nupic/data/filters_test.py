from nupic.regions.RecordSensor import RecordSensor
from nupic.data.file_record_stream import FileRecordStream
from nupic.data.datasethelpers import findDataset
from nupic.encoders import MultiEncoder
from nupic.data.filters import DeltaFilter
import numpy
from datetime import datetime, timedelta

r = RecordSensor()
filename = findDataset("extra/qa/delta.csv")
datasource = FileRecordStream(filename)
r.dataSource = datasource
n=50
encoder = MultiEncoder({'blah': dict(fieldname="s", type='ScalarEncoder', n=n,
                                     w=11, minval=0, maxval=100)})

r.encoder = encoder


"""
data looks like:        should generate deltas
  "t"   "s"               "dt"     "ds"

  t     10                 X
  t+1s  20                 1s      10
  t+1d  50                 86399   30

r t+1d+1s  60              X
  r+1d+3s  65              2s       5

"""

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
assert lr['t'] == datetime(year=2011, month=2, day=24, hour=16, minute=8, second=0)
assert lr['s'] == 10
assert lr['_reset'] == 1
assert 'dt' not in lr
assert 'ds' not in lr


r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=24, hour=16, minute=8, second=1)
assert lr['s'] == 20
assert lr['_reset'] == 0

r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=25, hour=16, minute=8, second=0)
assert lr['s'] == 50
assert lr['_reset'] == 0

r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=25, hour=16, minute=8, second=1)
assert lr['s'] == 60
assert lr['_reset'] == 1

r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=25, hour=16, minute=8, second=3)
assert lr['s'] == 65
assert lr['_reset'] == 0


# Add filters

r.preEncodingFilters = [DeltaFilter("s", "ds"), DeltaFilter("t", "dt")]
r.rewind()

# skip first record, which has a reset

r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=24, hour=16, minute=8, second=1)
assert lr['s'] == 20
assert lr['_reset'] == 1  # this record should have a reset since it is first of a sequence
assert lr['dt'] == 1
assert lr['ds'] == 10


r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=25, hour=16, minute=8, second=0)
assert lr['s'] == 50
assert lr['_reset'] == 0
assert lr['dt'] == (3600*24 - 1)
assert lr['ds'] == 30

# next reset record is skipped


r.compute(inputs, outputs)
lr = r.lastRecord
assert lr['t'] == datetime(year=2011, month=2, day=25, hour=16, minute=8, second=3)
assert lr['s'] == 65
assert lr['_reset'] == 1
assert lr['dt'] == 2
assert lr['ds'] == 5

print "All delta tests passed"
