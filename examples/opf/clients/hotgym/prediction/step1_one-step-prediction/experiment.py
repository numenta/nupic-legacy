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

import os
import datetime
import csv
import shutil

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic_output import NuPICFileOutput, NuPICPlotOutput


def run_experiment(name):
  shutil.copyfile("model_%s/model_params.py" % name, "model_params.py")
  import model_params
  output = NuPICFileOutput(name, show_anomaly_score=False)
  model = ModelFactory.create(model_params.MODEL_PARAMS)
  model.enableInference({"predictedField": "kw_energy_consumption"})
  input_file = os.path.join("../local_data", "%s.csv" % name)
  with open(input_file, "rb") as gym_input:
    csv_reader = csv.reader(gym_input)

    # skip header rows
    csv_reader.next()
    csv_reader.next()
    csv_reader.next()

    # the real data
    for row in csv_reader:
      timestamp = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
      consumption = float(row[1])
      result = model.run({
        "timestamp": timestamp,
        "kw_energy_consumption": consumption
      })
      output.write(timestamp, consumption, result, prediction_step=1)

  output.close()



if __name__ == "__main__":
  run_experiment('Lane_Cove')
