#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

import logging
import sys
import os
import time
import pprint
from optparse import OptionParser
import random
import json
import hashlib
import binascii
import itertools
import traceback
import StringIO

import numpy

from nupic.support import initLogging
from nupic.support.ExtendedLogger import ExtendedLogger
from grokengine.support.configuration import Configuration

from nupic.database.ClientJobsDAO import ClientJobsDAO
from nupic.swarming.modelchooser import ModelChooser



class DummyWorker(object):
  """ DummyWorker is a dummy worker to test the scheduler algorithms. It burns
  through cpu or hogs I/O based on the params.
  """

  ########################################################################
  def __init__(self, options, cmdLineArgs):
    """ Instantiate the Dummy worker

    Parameters:
    ---------------------------------------------------------------------
    options:      The command line options. See the main() method for a
                    description of these options
    cmdLineArgs:  Copy of the command line arguments, so we can place them
                    in the log
    """

    # Save options
    self._options = options

    # Instantiate our logger
    self.logger = logging.getLogger(".".join( ['com.numenta',
                        self.__class__.__module__, self.__class__.__name__]))

    # Override log level?
    if options.logLevel is not None:
      self.logger.setLevel(options.logLevel)


    self.logger.info("Launched with command line arguments: %s" %
                      str(cmdLineArgs))

    # Init random seed
    random.seed(42)

    # This will be filled in by run()
    self._workerID = None

  ########################################################################
  def run(self):
    """ Run this worker.

    Parameters:
    ----------------------------------------------------------------------
    retval:     jobID of the job we ran. This is used by unit test code
                  when calling this working using the --params command
                  line option (which tells this worker to insert the job
                  itself).
    """
    # Easier access to options
    options = self._options

    # ---------------------------------------------------------------------
    # Connect to the jobs database
    self.logger.info("Connecting to the jobs database")
    cjDAO = ClientJobsDAO.get()

    # Get our worker ID
    self._workerID = cjDAO.getConnectionID()


    # -------------------------------------------------------------------------
    # if params were specified on the command line, insert a new job using
    #  them.
    if options.params is not None:
      options.jobID = cjDAO.jobInsert(client='dummy',
                  cmdLine="python -m nupic.swarming.DummyWorker --jobID={JOBID}",
                  params=options.params)



    # ---------------------------------------------------------------------
    # Get the search parameters
    jobInfo = cjDAO.jobInfo(options.jobID)
    self.logger.info("Job info retrieved: %s" % (str(jobInfo)))
    if options.workerID is not None:
      wID = options.workerID
    else:
      wID = self._workerID
    
    buildID = Configuration.get('nupic.software.buildNumber', 'N/A')
    logPrefix = '<BUILDID=%s, WORKER=DW, WRKID=%s, JOBID=%s> ' % \
                (buildID, wID, options.jobID)
    ExtendedLogger.setLogPrefix(logPrefix)


    # ---------------------------------------------------------------------
    # Instantiate the Dummy object, which will handle the logic of
    #  which models to create when we need more to evaluate.
    jobParams = json.loads(jobInfo.params)
    self.logger.info("Job Params: %s" % jobInfo.params)

    # prints the current status
    print >>sys.stderr, "reporter:status:Running dummy worker on job:%d" % \
                                                    (options.jobID)


    self.logger.info("Start of the dummy worker")
    startTime = time.time()
    runTime = jobParams['runTime']
    jobLoad = jobParams['load']
    crashJob = jobParams['crash']

    try:
      while True:
        if runTime != -1 and time.time() > startTime + runTime:
          break
        self.logger.info("In dummy worker")
        if jobLoad == 'heavy':
          # Computationally intensive process
          # Takes 0.8 sec approximately
          numIterations = 30000
          for i in range(numIterations):
            d = numpy.random.rand(1000).sum()
        else:
          time.sleep(0.8)
    except:
      self.logger.exception("DummyWorker exception;")

    if crashJob:
      self.logger.info("Crash of the dummy worker")
      print >>sys.stderr, "reporter:status:Crashed dummy worker..."
      raise RuntimeError("Simulating job crash.")
    else:
      self.logger.info("End of the dummy worker")
      print >>sys.stderr, "reporter:status:Finished dummy worker..."

    #import auxilary
    #auxilary.do_something()

    return options.jobID



#####################################################################################
helpString = \
"""%prog [options]
This script runs as a Dummy worker process.
"""


#####################################################################################
def main(argv):
  """
  The main function of the DummyWorker script. This parses the command
  line arguments, instantiates a DummyWorker instance, and then
  runs it.

  Parameters:
  ----------------------------------------------------------------------
  retval:     jobID of the job we ran. This is used by unit test code
                when calling this working using the --params command
                line option (which tells this worker to insert the job
                itself).
  """

  parser = OptionParser(helpString)

  parser.add_option("--jobID", action="store", type="int", default=None,
        help="jobID of the job within the dbTable [default: %default].")

  parser.add_option("--workerID", action="store", type="str", default=None,
        help=("workerID of the scheduler's SlotAgent (GenericWorker) that "
          "hosts this SpecializedWorker [default: %default]."))

  parser.add_option("--params", action="store", default=None,
        help="Create and execute a new hypersearch request using this JSON " \
        "format params string. This is helpful for unit tests and debugging. " \
        "When specified jobID must NOT be specified. [default: %default].")

  parser.add_option("--clearModels", action="store_true", default=False,
        help="clear out the models table before starting [default: %default].")

  parser.add_option("--logLevel", action="store", type="int", default=None,
        help="override default log level. Pass in an integer value that "
        "represents the desired logging level (10=logging.DEBUG, "
        "20=logging.INFO, etc.) [default: %default].")


  # Evaluate command line arguments
  (options, args) = parser.parse_args(argv[1:])
  if len(args) != 0:
    raise RuntimeError("Expected no command line arguments, but got: %s" % \
                        (args))

  if (options.jobID and options.params):
    raise RuntimeError("--jobID and --params can not be used at the same time")

  # Instantiate the DummyWorker and run it
  dum = DummyWorker(options, argv[1:])
  return dum.run()


#############################################################################
if __name__ == "__main__":
  # Init the NuPic logging configuration from the nupic-logging.conf configuration
  # file. This is found either in the NTA_CONF_DIR directory (if defined) or
  # in the 'conf' subdirectory of the NuPic install location.
  initLogging(verbose=True)
  # Replace default logger with our extention
  logging.setLoggerClass(ExtendedLogger)
  logger = logging.getLogger('com.numenta.nupic.cluster.dummyworker.main')
  
  buildID = Configuration.get('nupic.software.buildNumber', 'N/A')
  logPrefix = '<BUILDID=%s, WORKER=DW, WRKID=%s, JOBID=N/A> ' % \
              (buildID, wID)
  ExtendedLogger.setLogPrefix(logPrefix)

  try:
    main(sys.argv)
  except:
    msg = StringIO.StringIO()
    print >>msg, "Exception occurred running DummyWorker: "
    traceback.print_exc(None, msg)
    logger.error(msg.getvalue())
    msg.close()
    del msg
    raise
