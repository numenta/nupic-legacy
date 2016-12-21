import csv
import shutil
import datetime

ORIGINAL = "rec-center-hourly.csv"
BACKUP = "rec-center-hourly-backup.csv"
DATE_FORMAT = "%m/%d/%y %H:%M"


def isTuesday(date):
  return date.weekday() is 1



def withinOctober(date):
  return datetime.datetime(2010, 10, 1) <= date < datetime.datetime(2010, 11, 1)



def run():
  # Backup original
  shutil.copyfile(ORIGINAL, BACKUP)
  with open(ORIGINAL, 'rb') as inputFile:
    reader = csv.reader(inputFile)
    outputCache = ""
    headers = reader.next()
    types = reader.next()
    flags = reader.next()

    for row in [headers, types, flags]:
      outputCache += ",".join(row) + "\n"

    for row in reader:
      dateString = row[0]
      date = datetime.datetime.strptime(dateString, DATE_FORMAT)
      consumption = float(row[1])
      if isTuesday(date) and withinOctober(date):
        consumption = 5.0
      outputCache += "%s,%f\n" % (dateString, consumption)

  with open(ORIGINAL, 'wb') as outputFile:
    outputFile.write(outputCache)


if __name__ == "__main__":
  run()
