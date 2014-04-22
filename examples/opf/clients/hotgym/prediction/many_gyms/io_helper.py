import datetime
import csv

from nupic.data.inference_shifter import InferenceShifter
from nupic_output import NuPICFileOutput, NuPICPlotOutput



def run_io_through_nupic(input_data, models, names, plot):
  readers = []
  input_files = []
  if plot:
    output = NuPICPlotOutput(names)
    shifter = InferenceShifter()
  else:
    output = NuPICFileOutput(names)
  # Populate input files and csv readers for each model.
  for index, model in enumerate(models):
    input_file = open(input_data[index], 'rb')
    input_files.append(input_file)
    csv_reader = csv.reader(input_file)
    # Skip header rows.
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()
    # Reader is now at the top of the real data.
    readers.append(csv_reader)

  read_count = 0

  while True:
    next_lines = [next(reader, None) for reader in readers]
    # If all lines are None, we're done.
    if all(value is None for value in next_lines):
      print "Done after reading %i lines" % read_count
      break

    read_count += 1

    if (read_count % 100 == 0):
      print "Read %i lines..." % read_count

    times = []
    consumptions = []
    predictions = []

    # Gather one more input from each input file and send into each model.
    for index, line in enumerate(next_lines):
      model = models[index]
      # Ignore models that are out of input data.
      if line is None:
        timestamp = None
        consumption = None
        prediction = None
      else:
        timestamp = datetime.datetime.strptime(line[0], "%Y-%m-%d %H:%M:%S")
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
  for file in input_files:
    file.close()
  output.close()