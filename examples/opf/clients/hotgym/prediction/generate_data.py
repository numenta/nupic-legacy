import os
import csv
import datetime

INPUT = '../data/raw/gym_input.csv'
LOCAL_DATA = 'local_data'
data_out = {}


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
  # "   ","SITE_LOCATION_NAME","TIMESTAMP","TOTAL_KWH"
  return [_convert_date(line[2]), float(line[3])]


def _process_line(line):
  gym_name = line[1]
  if gym_name not in data_out.keys():
    data_out[gym_name] = _create_output_header()
  data_out[gym_name].append(_line_to_data(line));


def _write_data_files():
  if not os.path.exists(LOCAL_DATA):
    os.makedirs(LOCAL_DATA)
  for name, data in data_out.iteritems():
    with open(os.path.join(LOCAL_DATA, _to_file_name(name)), 'wb') as file_out:
      writer = csv.writer(file_out)
      for line in data:
        writer.writerow(line);


def run():
  with open(INPUT, 'rb') as file_handle:
    reader = csv.reader(file_handle)
    # Skip header line.
    reader.next();
    for line in reader:
      _process_line(line)
    # Now that all the data has been input and processed, write out the files.
    _write_data_files()


if __name__ == '__main__':
  run();
