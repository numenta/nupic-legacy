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
import csv
import datetime
import time

class WeatherJoiner(object):
  '''
  Given a data file in standard numenta format and the types of weather you are
  interested in. WeatherJoiner allows you to create a new temporary file that
  includes relevant weather records for your data. It is subject to the following
  limitations.

  Each record in the original file must have an address field of type string. This
  can be either a street address or an IP address.

  Each record in the original file must have a timestamp field.

  There is no guarantee we will have any weather data to add to your data set.
  The records for your time range may be incomplete. Placeholder data will
  be provided for missing records.

  We will return statistics on how many records were missing from those requested.

  It is up to the user to set appropriate tolerances and reject data deemed
  insufficiently complete.
  '''

  def __init__(self, datasets, weatherTypes, WeatherProvider, GeoProvider):
    # Assumes that datasets exist and paths are valid
    self.datasets = datasets

    # Store the provider objects
    self.w = WeatherProvider
    self.g = GeoProvider

    # Check each of the input files and make sure they have address and timestamp
    for key in self.datasets:
      with open(self.datasets[key]) as f:
        header = f.readline()
        if 'address' not in header or 'timestamp' not in header:
          raise Exception('Data files must contain headers "address" and "timestamp"')

    # See WeatherProvider.py for full list of valid weatherTypes
    # An exception will be raised there if an invalid type is passed
    self.weatherTypes = weatherTypes

  def join(self, generateFlag = True):
    '''
    Writes out a new combined file containing weather data
    Returns statistics on the number of records missing
    '''
    # Create a dict to return paths to generated files
    joinedDatasets = {}

    # Set up other variables we'll return
    percentMissing = 0.00

    # For each data file we are given, create a new one with weather data
    for key in self.datasets:
      # Pull out the path to the csv, then isolate the filename
      inputPath = self.datasets[key]
      outputDir, inputFilename = os.path.split(inputPath)

      # Make up a name for the temp file
      outputFile = 'join_' + inputFilename

      # We'll put the joined datasets in the same folder as the originals
      outputPath = os.path.join(outputDir, outputFile)

      print 'Now writing to: ' + outputPath

      # Keep the dict keys the same as the input dict
      joinedDatasets[key] = outputPath

      # If we're not being asked to generate the file just spit out the paths
      if not generateFlag:
        continue

      # Open the input and output files for processing
      outputFile = csv.writer(open(outputPath, 'w'),dialect='excel')
      inputFile = csv.reader(open(inputPath, 'r'),dialect='excel')

      # Update the headers and find where the address and timestamp are
      addressIndex, timestampIndex = self._updateHeaders(self.weatherTypes,
                                                         inputFile,
                                                         outputFile)

      # Set up caches to eliminate duplicate API calls
      addressCache = {}

      # Set up counters for missing line stats
      goodRecords = 0
      missingRecords = 0

      # Iterate over all the lines in the input file
      for line in inputFile:
        # Get the address and the timestamp
        address = line[addressIndex]
        timestamp = line[timestampIndex]
        date = self._parseTimestamp(timestamp).date()

        # check to see if that address is in our cache
        if address not in addressCache:
          # Look up the lat/long for this address and store it
          # print "Getting lat/long for address:"
          # print address
          lat, long = self.g.getLatLong(address)
          addressCache[address] = (lat, long)
          # Also reset the range on the WeatherProvider for the new address
          self.w.setRange(0)
        else:
          lat, long = addressCache[address]

        # This is ugly, but we have to deal with the fact that the closest
        # station may not have complete records for the time period we're
        # interested in.
        range = 1
        while True:
          try:
            recordsDict = self.w.getRecords(lat, long, date)
            # We found a good station so kill the search loop
            break
          except LookupError:
            # We failed to find records for this location and time
            # try next closest station
            # print lat, long, date
            # print "DATA FILE MISSING, trying next closest station ..."
            # Will look farther away next time
            self.w.setRange(range)
            range += 1
            # Don't swamp Google API with requests
            time.sleep(1)
        '''
        Check to see if this was a blank row in the data files, put in
        placeholder values if it was
        '''
        if recordsDict == None:
          missingRecords += 1
          # Specifies the missing data placeholder
          line.extend([9999] * len(self.weatherTypes))
          outputFile.writerow(line)
        else:
          goodRecords += 1
          for type in self.weatherTypes:
            line.append(recordsDict[type])
          outputFile.writerow(line)

      try:
        percentMissing = float(missingRecords) / goodRecords # Oh python *shakeshead*
      except ZeroDivisionError:
        percentMissing = 100.00

    return joinedDatasets, percentMissing

  def _updateHeaders(self, newHeaders, inputFileHandle, outputFileHandle):
    # We need to deal with the first three header rows and update them with
    # the requested weather data
    for i in xrange(1,4): # Screw zero indexing!
      headerLine = inputFileHandle.next()
      for type in newHeaders:
        # Header row one
        if i == 1:
          headerLine.append(type)
          # Find out where our address and timestamp columns are
          addressIndex = headerLine.index('address')
          timestampIndex = headerLine.index('timestamp')
        # Header row two
        elif i == 2: headerLine.append('float')
        # Header row three
        elif i == 3: headerLine.append('')
      outputFileHandle.writerow(headerLine)

    return addressIndex, timestampIndex

  def _parseTimestamp(self,t):
    tokens = t.split()
    year, month, day = [int(x) for x in tokens[0].split('-')]
    # TODO Handle times smaller than a day

    result = datetime.datetime(year, month, day)
    return result
