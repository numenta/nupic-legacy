# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2010-2015, Numenta, Inc.  Unless you have an agreement
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

"""Unify the various Gym CSV files to a single coherent CSV file

The Gym dataset has two file types:

1. Hourly attendance data per gym
2. KW consumption in 15 minutes intervals

The createDataset() function merges the two file types and creates
a single CSV file with hourly data. Each record contains the following fields:

Gym name, Date, Hour, # Atendees, KW consumption
"""

import os
import sys
import fileinput
import glob
import operator
import datetime
from nupic.data.file import File

months = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()

class Record(object):
  def __init__(self):
    self.club = ''
    self.date = None
    self.time = 0
    self.KW = 0
    self.attendeeCount = 0
    self.consumption = 0
        
class Club(object):
  def __init__(self, name):
    self.name = name
    self.records = {}
    
  def processAttendance(self, f):
    # Skip first two
    line = f.next()
    assert line == ',,,,,,,,,,,,,,,,,,,\n'

    line = f.next()
    assert line == 'Date Of Swipe, < 6 am,6-7 am,7-8 am,8-9 am,9-10 am,10-11 am,11-12 am,12-1 pm,1-2 pm,2-3 pm,3-4 pm,4-5 pm,5-6 pm,6-7 pm,7-8 pm,8-9 pm,9-10 pm,> 10 pm,Totals\n'
    
    for i, line in enumerate(f):
      # Check weather we're done with this club
      if line == ',,,,,,,,,,,,,,,,,,,\n':
        # skip next two lines
        line = f.next()
        assert line.startswith('Club Totals:')
        line = f.next()
        assert line == ',,,,,,,,,,,,,,,,,,,\n'
        return
      else:
        self.addRecord(line)
        
  def addRecord(self, line):
    fields = line.split(',')
    assert len(fields) == 20
    date = fields[0].split('-')
    
    # Convert day to 'dd'
    dd = int(date[0])
    mm = months.index(date[1]) + 1
    assert mm in (9, 10)
    # Convert year from 'yy' to 'yyyy'
    yyyy = 2000 + int(date[2])
    date = (yyyy, mm, dd)
    
    # Add 0 for hours without attendants (<12AM-4AM and 11PM)
    attendance =  [0] * 5 + fields[1:19] + [0]
    assert len(attendance) == 24
    # Create a record for each hour of the day.
    for i, a in enumerate(attendance):
      r = Record()
      r.club = self.name
      r.timestamp = datetime.datetime(yyyy, mm, dd, i)
      #r.time = i
      r.attendeeCount = a
      self.records[(date, i)] = r
      
  def updateRecord(self, date, t, consumption):
    # Get rid of time and AM/PM if needed
    date = date.split()[0]
    
    # Convert to (yyyy, mmm, dd)
    date = date.split('/')
    
    # Convert day to 'dd'
    dd = int(date[0])
    # Convert month index to month name
    mm = int(date[1])
    yyyy = int(date[2])
    # Locate record
    key = ((yyyy, mm, dd), t)
    if not key in self.records:
      print self.name, 'is missing attendance data for', key
    else:
      r = self.records[key]
      r.consumption = consumption
          
def processClubAttendance(f, clubs):
  """Process the attendance data of one club
  
  If the club already exists in the list update its data.
  If the club is new create a new Club object and add it to the dict
  
  The next step is to iterate over all the lines and add a record for each line.
  When reaching an empty line it means there are no more records for this club.
  
  Along the way some redundant lines are skipped. When the file ends the f.next()
  call raises a StopIteration exception and that's the sign to return False,
  which indicates to the caller that there are no more clubs to process.
  """
  try:
    # Skip as many empty lines as necessary (file format inconsistent)
    line = f.next()
    while line == ',,,,,,,,,,,,,,,,,,,\n':
      line = f.next()
    
    # The first non-empty line should have the name as the first field
    name = line.split(',')[0]
    
    # Create a new club object if needed
    if name not in clubs:
      clubs[name] = Club(name)
    
    # Get the named club
    c = clubs[name]
    
    c.processAttendance(f)      
    return True
  except StopIteration:
    return False
  
def processClubConsumption(f, clubs):
  """Process the consumption a club
  
  - Skip the header line
  - Iterate over lines
    - Read 4 records at a time
      - Parse each line: club, date, time, consumption
      - Get club object from dictionary if needed
      - Aggregate consumption
    - Call club.processConsumption() with data
  """
  try:
    # Skip header line
    line = f.next()
    assert line.endswith('"   ","SITE_LOCATION_NAME","TIMESTAMP","TOTAL_KWH"\n')

    valid_times = range(24)
    t = 0 # used to track time
    club = None
    clubName = None
    lastDate = None
    while True:
      assert t in valid_times
      consumption = 0
      for x in range(4):
        # Read the line and get rid of the newline character
        line = f.next()[:-1]
        fields = line.split(',')
        assert len(fields) == 4
        for i, field in enumerate(fields):
          # Strip the redundant double quotes
          assert field[0] == '"' and field[-1] == '"'
          fields[i] = field[1:-1]
        
        # Ignoring field 0, which is just a running count
        
        # Get the club name  
        name = fields[1]
        
        # Hack to fix inconsistent club names like: "Melbourne CBD - Melbourne Central" vs. "Melbourne Central"
        partialNames = ('Melbourne Central', 'North Sydney', 'Park St', 'Pitt St')
        for pn in partialNames:
          if pn in name:
            name = pn
        
        # Locate the club if needed (maybe )
        if name != clubName:
          clubName = name
          club = clubs[name]
        
        # Split the date (time is counted using the t variable)
        tokens = fields[2].split()
        
        # Verify that t == 0 and consumption == 0 when there is no time in the file
        if len(tokens) == 1:
          assert consumption == 0 and t == 0
        
        # The first (and sometimes only) token is the date
        date = tokens[0]
                
        # Aggregate the consumption
        consumption += float(fields[3])
      
      # Update the Club object after aggregating the consumption of 4 lines 
      club.updateRecord(date, t, consumption)
      
      # Increment time
      t += 1
      t %= 24
  except StopIteration:
    return
  
def processAttendanceFiles():
  files = glob.glob('Attendance*.csv')

  f = fileinput.input(files=files)

  # Process the input files and create a dictionary of Club objects
  clubs = {}
  while processClubAttendance(f, clubs):
    pass
  
  return clubs
        
def processConsumptionFiles(clubs):
  """
  """
  files = glob.glob('all_group*detail.csv')

  f = fileinput.input(files=files)

  # Process the input files and create a dictionary of Club objects
  while processClubConsumption(f, clubs):
    pass
  
  return clubs

def makeDataset():
  """
  """
  clubs = processAttendanceFiles()
  clubs = processConsumptionFiles(clubs)
  
  
  fields = [('gym', 'string', 'S'),
            ('timestamp', 'datetime', 'T'),
            ('attendeeCount', 'int', ''),
            ('consumption', 'float', ''),
             ]
  with File('gym.csv', fields) as f:
    ## write header
    #f.write('Gym Name,Date,Time,Attendee Count,Consumption (KWH)\n')
    for c in clubs.values():
      for k, r in sorted(c.records.iteritems(), key=operator.itemgetter(0)):          
        #dd = r.date[2]
        #mm = r.date[1]
        #yyyy = r.date[0]
        #line = ','.join(str(x) for x in
        #          (c.name, '%d-%s-%d' % (dd, mmm, yyyy), r.time, r.attendeeCount, r.consumption))
        #f.write(line + '\n')
        f.write([r.club, r.timestamp, r.attendeeCount, r.consumption])
      
if __name__=='__main__':
  makeDataset()
  print 'Done.'
  
