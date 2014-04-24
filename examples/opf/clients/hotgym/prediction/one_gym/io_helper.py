# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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
Helper dealing with passing data into NuPIC models and extracting their
predictions. Uses the nupic_output module for output either to file or plot.
(This is a component of the One Hot Gym Prediction Tutorial.)
"""
import datetime
import csv

from nupic.data.inference_shifter import InferenceShifter
from nupic_output import NuPICFileOutput, NuPICPlotOutput

DATE_FORMAT = "%m/%d/%y %H:%M"
# '7/2/10 0:00'



def runIoThroughNupic(inputData, models, names, plot):
  readers = []
  inputFiles = []
  if plot:
    output = NuPICPlotOutput(names)
    shifter = InferenceShifter()
  else:
    output = NuPICFileOutput(names)
  # Populate input files and csv readers for each model.
  for index, model in enumerate(models):
    inputFile = open(inputData[index], 'rb')
    inputFiles.append(inputFile)
    csvReader = csv.reader(inputFile)
    # Skip header rows.
    csvReader.next()
    csvReader.next()
    csvReader.next()
    # Reader is now at the top of the real data.
    readers.append(csvReader)

  readCount = 0

  while True:
    nextLines = [next(reader, None) for reader in readers]
    # If all lines are None, we're done.
    if all(value is None for value in nextLines):
      print "Done after reading %i lines" % readCount
      break

    readCount += 1

    if (readCount % 100 == 0):
      print "Read %i lines..." % readCount

    times = []
    consumptions = []
    predictions = []

    # Gather one more input from each input file and send into each model.
    for index, line in enumerate(nextLines):
      model = models[index]
      # Ignore models that are out of input data.
      if line is None:
        timestamp = None
        consumption = None
        prediction = None
      else:
        timestamp = datetime.datetime.strptime(line[0], DATE_FORMAT)
        consumption = float(line[1])
        result = model.run({
          "timestamp": timestamp,
          "kw_energy_consumption": consumption
        })

        if plot:
          # The shifter will align prediction and actual values for plotting.
          result = shifter.shift(result)

        prediction = result.inferences \
          ['multiStepBestPredictions'][1]

      times.append(timestamp)
      consumptions.append(consumption)
      predictions.append(prediction)

    output.write(times, consumptions, predictions)

  # close all I/O
  for f in inputFiles:
    f.close()
  output.close()