#!/usr/bin/env python
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

import sys
import time
import json
import csv
from optparse import OptionParser

from nupic.support import initLogging
from nupic.dataase.ClientJobsDAO import ClientJobsDAO


helpString = \
"""%prog [options]
This script can be used to analyze the results of a hypersearch run. Given a
jobID, it will read the models table for that hypersearch, generate a csv with
useful information and print out other statistics.
"""



def main(argv):
  parser = OptionParser(helpString)

  parser.add_option("--jobID", action="store", type="int", default=None,
        help="jobID of the hypersearch job [default: %default].")

  # Evaluate command line arguments
  options, args = parser.parse_args(argv[1:])
  if len(args) != 0:
    raise RuntimeError("Expected no command line arguments but got: %s" % args)

  initLogging(verbose=True)

  # Open up the database client
  cjDAO = ClientJobsDAO.get()

  # Read in the models for this job
  modelIDCtrList = cjDAO.modelsGetUpdateCounters(options.jobID)
  if len(modelIDCtrList) == 0:
    raise RuntimeError ("No models found")
    return

  modelIDs = [x[0] for x in modelIDCtrList]
  modelInfos = cjDAO.modelsInfo(modelIDs)

  # See which variables are permuted over
  permuteVars = set()
  for modelInfo in modelInfos:
    data = modelInfo._asdict()
    params = json.loads(data['params'])
    varStates = params['particleState']['varStates']
    permuteVars = permuteVars.union(varStates.keys())

  # Prepare a csv file to hold the results
  modelsCSVFilename = 'job%d_models.tsv' % (options.jobID)
  modelsCSVFD = open(modelsCSVFilename, 'wb')
  modelsCSV = csv.writer(modelsCSVFD, delimiter='\t',
                quoting=csv.QUOTE_MINIMAL)

  # Include all the built-in fields of the models table
  fieldsToDump = list(modelInfos[0]._fields)

  # Re-order the columns slightly
  fieldsToDump.remove('engParamsHash')
  fieldsToDump.insert(2, 'engParamsHash')
  fieldsToDump.remove('optimizedMetric')
  fieldsToDump.insert(3, 'optimizedMetric')

  # Insert our generated fields
  generatedFields = ['_sprintIdx', '_swarmId', '_particleId', '_genIdx',
                     '_particleVars', '_modelVars']
  generatedFields.extend(sorted(permuteVars))
  idx=4
  for field in generatedFields:
    fieldsToDump.insert(idx, field)
    idx += 1

  # Write the header
  modelsCSV.writerow(fieldsToDump)

  # Write the data for each model
  scorePerSeconds = dict()
  for modelInfo in modelInfos:
    data = modelInfo._asdict()
    params = json.loads(data['params'])
    data['_swarmId'] = params['particleState']['swarmId']
    fields = data['_swarmId'].split('.')
    data['_sprintIdx'] = len(fields)-1
    data['_particleId'] = params['particleState']['id']
    data['_genIdx'] = params['particleState']['genIdx']
    data['_particleVars'] = json.dumps(params['particleState']['varStates'])
    data['_modelVars'] = json.dumps(params['structuredParams'])

    varStates = params['particleState']['varStates']
    for varName in permuteVars:
      if varName in varStates:
        data[varName] = varStates[varName]['position']
      else:
        data[varName] = ' '

    # Convert hashes to hex
    data['engParamsHash'] = data['engParamsHash'].encode('hex')
    data['engParticleHash'] = data['engParticleHash'].encode('hex')

    # Write out the data
    rowData = []
    for field in fieldsToDump:
      rowData.append(data[field])
    modelsCSV.writerow(rowData)

    # Keep track of the best score over time
    if data['completionReason'] in ['eof', 'stopped']:
      errScore = data['optimizedMetric']
      endSeconds = time.mktime(data['endTime'].timetuple())
      if endSeconds in scorePerSeconds:
        if errScore < scorePerSeconds[endSeconds]:
          scorePerSeconds[endSeconds] = errScore
      else:
        scorePerSeconds[endSeconds] = errScore

  # Close the models table
  modelsCSVFD.close()
  print "Generated output file %s" % (modelsCSVFilename)

  # Generate the score per seconds elapsed
  scoresFilename = 'job%d_scoreOverTime.csv' % (options.jobID)
  scoresFilenameFD = open(scoresFilename, 'wb')
  scoresFilenameCSV = csv.writer(scoresFilenameFD, delimiter=',',
                quoting=csv.QUOTE_MINIMAL)
  scoresFilenameCSV.writerow(['seconds', 'score', 'bestScore'])

  # Write out the best score over time
  scores = scorePerSeconds.items()
  scores.sort()   # Sort by time
  startTime = scores[0][0]
  bestScore = scores[0][1]
  for (secs, score) in scores:
    if score < bestScore:
      bestScore = score
    scoresFilenameCSV.writerow([secs-startTime, score, bestScore])
  scoresFilenameFD.close()
  print "Generated output file %s" % (scoresFilename)



if __name__ == "__main__":
  main(sys.argv)
