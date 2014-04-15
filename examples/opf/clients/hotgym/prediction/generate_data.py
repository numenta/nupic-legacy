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
import csv
import datetime

# Hot Gym data is stored with other data at
# examples/prediction/data/extra/hotgym
INPUT = '../../../../prediction/data/extra/hotgym/raw/gym_input.csv'
LOCAL_DATA = 'local_data'
data_out = {}
low = 100.0
high = 0.0


def _create_output_header():
  return [
    ['timestamp', 'kw_energy_consumption'],
    ['datetime', 'float'],
    ['T','']
  ]


def _convert_date(date_string):
  tokens = date_string.split()
  day, month, year = [int(x) for x in tokens[0].split('/')]
  if len(tokens) == 1:
    hour = 0
    minute = 0
  else:
    hour, minute, seconds = [int(x) for x in tokens[1].split(':')]
    hour %= 12
    if tokens[2] == 'PM':
      hour += 12

  return datetime.datetime(year, month, day, hour, minute)


def _to_file_name(name):
  return name.replace(' ', '_') + '.csv'


def _line_to_data(line):
  global low, high
  # "   ","SITE_LOCATION_NAME","TIMESTAMP","TOTAL_KWH"
  kw_energy_consumption = float(line[3])
  # update low and high values
  if kw_energy_consumption > high:
    high = kw_energy_consumption
  if kw_energy_consumption < low:
    low = kw_energy_consumption
  return [_convert_date(line[2]), kw_energy_consumption]


def _process_line(line):
  gym_name = line[1]
  if gym_name not in data_out.keys():
    data_out[gym_name] = _create_output_header()
  data_out[gym_name].append(_line_to_data(line))


def _write_data_files():
  written_files = {}
  if not os.path.exists(LOCAL_DATA):
    os.makedirs(LOCAL_DATA)
  for name, data in data_out.iteritems():
    file_path = os.path.join(LOCAL_DATA, _to_file_name(name))
    written_files[name] = file_path
    with open(file_path, 'wb') as file_out:
      writer = csv.writer(file_out)
      for line in data:
        writer.writerow(line)
    print "Wrote output file: %s" % file_path
  return written_files



def run(input_file=INPUT):
  with open(input_file, 'rb') as file_handle:
    reader = csv.reader(file_handle)
    # Skip header line.
    reader.next()
    for line in reader:
      _process_line(line)
    # Now that all the data has been input and processed, write out the files.
    written_files = _write_data_files()
    print "Low: %f\t\tHigh: %f" % (low, high)
    return written_files
