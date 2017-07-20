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

"""
Run ExpGenerator to generate the description and permutations file for a
spatial classification experiment
"""

import os
import json
from optparse import OptionParser

from nupic.swarming.exp_generator.experiment_generator import expGenerator



if __name__ == '__main__':

  helpString = \
  """%prog [options] searchDef
  This script is used to create the description.py and permutations.py files
  for an experiment. The searchDef argument should be the name of a python
  script with a getSearch() method which returns the search definition as a
  dict. The schema for this dict can be found at
  py/nupic/swarming/exp_generator/experimentDescriptionSchema.json
  """


  # ============================================================================
  # Process command line arguments
  parser = OptionParser(helpString)

  parser.add_option("--verbosity", default=0, type="int",
        help="Verbosity level, either 0, 1, 2, or 3 [default: %default].")

  parser.add_option("--outDir", dest='outDir', default=None,
        help="Where to place generated files. Default is in the same directory"
        " as the searchDef script.")


  (options, args) = parser.parse_args()

  # Must provide the name of a script
  if len(args) != 1:
    parser.error("Missing required 'searchDef' argument")
  searchFileName = args[0]

  # ------------------------------------------------------------------------
  # Read in the search script and get the search definition
  searchFile = open(searchFileName)
  vars = {}
  exec(searchFile, vars)
  searchFile.close()

  getSearchFunc = vars.get('getSearch', None)
  if getSearchFunc is None:
    raise RuntimeError("Error: the %s python script does not provide the "
                       "required getSearch() method")

  searchDef = getSearchFunc(os.path.dirname(__file__))
  if not isinstance(searchDef, dict):
    raise RuntimeError("The searchDef function should return a dict, but it "
                       "returned %s" % (str(searchDef)))


  # ------------------------------------------------------------------------
  # Figure out the output directory if not provided
  if options.outDir is None:
    options.outDir = os.path.dirname(searchFileName)


  # ------------------------------------------------------------------------
  # Run through expGenerator
  expGenArgs = ['--description=%s' % (json.dumps(searchDef)),
                '--version=v2',
                '--outDir=%s' % (options.outDir)]
  print "Running ExpGenerator with the following arguments: ", expGenArgs
  expGenerator(expGenArgs)


  # Get the permutations file name
  permutationsFilename = os.path.join(options.outDir, 'permutations.py')

  print "Successfully generated permutations file: %s" % (permutationsFilename)














