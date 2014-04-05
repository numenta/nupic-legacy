#!/usr/bin/python

import datetime
from random import randint

from nupic_output import NuPICPlotOutput

names = ['one', 'two', 'three', 'four', 'five']

out = NuPICPlotOutput(names)
start_date = datetime.datetime(2000, 1, 1)

TIMES = 1000

for i in range(TIMES):
  timestamps = [start_date + datetime.timedelta(i)] * len(names)
  a = []
  b = []
  for j in range(len(names)):
    a.append(randint(0,10))
    b.append(randint(5,15))
  out.write(timestamps, a, b)

out.close()