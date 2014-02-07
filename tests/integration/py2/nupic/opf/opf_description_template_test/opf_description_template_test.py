#! /usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2011 Numenta Inc, All rights reserved,
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc, No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

# Tests OPF descriptionTemplate.py-based experiment/sub-experiment pair

import os
import pprint
import sys
import unittest2 as unittest

from nupic.frameworks.opf.opfhelpers import (
  loadExperimentDescriptionScriptFromDir,
  getExperimentDescriptionInterfaceFromModule
)
from nupic.support.unittesthelpers.testcasebase import (
  TestCaseBase as HelperTestCaseBase)



# Our __main__ entry block sets this to an instance of MyTestEnvironment()
g_myEnv = None
g_debug = False



class MyTestEnvironment(object):


  def __init__(self):

    from optparse import OptionParser

    # Parse the args
    #
    parser = OptionParser()
    parser.disable_interspersed_args()

    parser.add_option("--installDir",
                      help="[optional] Specifies the NUPIC <INSTALLDIR>. ",
                      dest="installDir",
                      action="store", type="string", default="",
                      metavar="<INSTALLDIR>")

    (options, remainingArgs) = parser.parse_args()
    _debugOut("remainingArgs: <%s>" % (remainingArgs,))
    _debugOut("parser.rargs: <%s>" % (parser.rargs,))

    # Remove script-specific args from command-line so unittest
    # doesn't get confused (other args may be for unittest)
    sys.argv = remainingArgs

    _debugOut("options.installDir: <%s>" % (options.installDir,))

    if options.installDir:
      examplesDir = os.path.abspath(os.path.join(options.installDir,
                                                         "share"))
    else:
      examplesDir = os.path.abspath(
        os.path.join(os.path.dirname(__file__),
                     os.path.pardir,
                     os.path.pardir,
                     os.path.pardir,
                     os.path.pardir,
                     os.path.pardir,
                     os.path.pardir,
                     "examples"))

    _debugOut("examplesDir=<%s>" % (examplesDir,))

    assert os.path.exists(examplesDir), \
           "%s is not present in filesystem" % examplesDir



    # This is where we find OPF binaries (e.g., OpfRunExperiment.py, etc.)
    # In the autobuild, it is a read-only directory
    self.__opfBinDir = os.path.join(examplesDir, "opf/bin")
    assert os.path.exists(self.__opfBinDir), \
           "%s is not present in filesystem" % self.__opfBinDir
    _debugOut("self.__opfBinDir=<%s>" % self.__opfBinDir)

    # Where this script is running from (our autotest counterpart may have
    # copied it from its original location)
    self.__testRunDir = os.path.abspath(os.path.dirname(__file__))
    _debugOut("self.__testRunDir=<%s>" % self.__testRunDir)

    # Parent directory of our private OPF experiments
    self.__opfExperimentsParentDir = os.path.join(self.__testRunDir,
                                                  "experiments")
    assert os.path.exists(self.__opfExperimentsParentDir), \
           "%s is not present in filesystem" % self.__opfExperimentsParentDir
    _debugOut("self.__opfExperimentsParentDir=<%s>"
        % self.__opfExperimentsParentDir)


  def getOpfRunExperimentPyPath(self):
    return os.path.join(self.__opfBinDir, "OpfRunExperiment.py")


  def getOpfExperimentPath(self, experimentName):
    """
    experimentName:     e.g., "gym"; this string will be used to form
                        a directory path to the experiment.

    Returns:            absolute path to the experiment directory
    """
    path = os.path.join(self.__opfExperimentsParentDir, experimentName)
    assert os.path.isdir(path), \
      "Experiment path %s doesn't exist or is not a directory" % (path,)
    return path



class MyTestCaseBase(HelperTestCaseBase):

  def setUp(self):
    """ Method called to prepare the test fixture. This is called immediately
    before calling the test method; any exception raised by this method will be
    considered an error rather than a test failure. The default implementation
    does nothing.
    """


  def tearDown(self):
    """ Method called immediately after the test method has been called and the
    result recorded. This is called even if the test method raised an exception,
    so the implementation in subclasses may need to be particularly careful
    about checking internal state. Any exception raised by this method will be
    considered an error rather than a test failure. This method will only be
    called if the setUp() succeeds, regardless of the outcome of the test
    method. The default implementation does nothing.
    """
    # Reset our log items
    self.resetExtraLogItems()


  def shortDescription(self):
    """ Override to force unittest framework to use test method names instead
    of docstrings in the report.
    """
    return None


  def executePositiveOpfExperiment(self, experimentName, short=False):
    """ Executes a positive OPF RunExperiment test as a subprocess and validates
    its exit status.

    experimentName:     e.g., "gym"; this string will be used to form
                        a directory path to the experiment.

    short:              if True, attempt to run the experiment with --testMode
                        flag turned on, which causes all inference and training
                        iteration counts to be overridden with small counts.

    Returns:            result from _executeExternalCmdAndReapOutputs
    """

    opfRunner = g_myEnv.getOpfRunExperimentPyPath()
    opfExpDir = g_myEnv.getOpfExperimentPath(experimentName)

    r = self.__executePositiveRunExperimentTest(runnerPath=opfRunner,
                                                experimentDirPath=opfExpDir,
                                                short=short)
    return r


  def __executePositiveRunExperimentTest(self,
                                        runnerPath,
                                        experimentDirPath,
                                        customOptions=[],
                                        short=False):
    """ Executes a positive RunExperiment.py test and performs
    basic validation

    runnerPath:         experiment running (LPF or OPF RunExperiment.py path)

    experimentDirPath:  directory containing the description.py file of interest

    short:              if True, attempt to run the experiment with --testMode
                        flag turned on, which causes all inference and training
                        iteration counts to be overridden with small counts.
                        NOTE: if the (possibly aggregated) dataset has fewer
                        rows than the count overrides, then an LPF experiment
                        will fail.

    Returns:            result from _executeExternalCmdAndReapOutputs
    """
    #----------------------------------------
    # Set up args
    command = [
      "python",
      runnerPath,
      experimentDirPath,
    ]

    command.extend(customOptions)

    if short:
      command.append("--testMode")

    self.addExtraLogItem({'command':command})

    #----------------------------------------
    # Execute RunExperiment.py as subprocess and collect results
    r = _executeExternalCmdAndReapOutputs(command)
    self.addExtraLogItem({'result':r})

    _debugOut(("_executeExternalCmdAndReapOutputs(%s)=%s") % (command, r))

    #----------------------------------------
    # Check subprocess exit status
    self.assertEqual(r['exitStatus'], 0,
                     ("Expected status = 0 from %s; got: %s") % \
                        (runnerPath, r['exitStatus'],))

    self.resetExtraLogItems()

    return r



class PositiveTests(MyTestCaseBase):

  #========================
  def test_sub_experiment_override(self):
    expDir = g_myEnv.getOpfExperimentPath("gym")
    module = loadExperimentDescriptionScriptFromDir(expDir)

    expIface = getExperimentDescriptionInterfaceFromModule(module)

    modelDesc = expIface.getModelDescription()

    tpActivationThreshold = modelDesc['modelParams'] \
        ['tpParams']['activationThreshold']

    expectedValue = 12
    self.assertEqual(tpActivationThreshold, expectedValue,
                     "Expected tp activationThreshold=%s, but got %s" % (
                      expectedValue, tpActivationThreshold))


  def test_run_sub_experiment(self):
    self.executePositiveOpfExperiment(experimentName="gym", short=True)



################################################################################
# Support functions
################################################################################

def _executeExternalCmdAndReapOutputs(args):
  """
  args:     Args list as defined for the args parameter in subprocess.Popen()

  Returns:  result dicionary:
              {
                'exitStatus':<exit-status-of-external-command>,
                'stdoutData':"string",
                'stderrData':"string"
              }
  """
  import subprocess

  _debugOut(("Starting...\n<%s>") % \
                (args,))

  p = subprocess.Popen(args,
                       env=os.environ,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
  _debugOut(("Process started for <%s>") % (args,))

  (stdoutData, stderrData) = p.communicate()
  _debugOut(("Process completed for <%s>: exit status=%s, " + \
             "stdoutDataType=%s, stdoutData=<%s>, stderrData=<%s>") % \
                (args, p.returncode, type(stdoutData), stdoutData, stderrData))

  result = dict(
    exitStatus = p.returncode,
    stdoutData = stdoutData,
    stderrData = stderrData,
  )

  _debugOut(("args: <%s>: result:\n%s") % \
                (args, pprint.pformat(result, indent=4)))

  return result


def _debugOut(msg):
  if g_debug:
    callerTraceback = whoisCallersCaller()
    print "OPF TestDescriptionTemplate (f=%s;line=%s): %s" % \
            (callerTraceback.function, callerTraceback.lineno, msg,)
    sys.stdout.flush()


def whoisCallersCaller():
  """
  Returns: Traceback namedtuple for our caller's caller
  """
  import inspect

  frameObj = inspect.stack()[2][0]

  return inspect.getframeinfo(frameObj)



g_myEnv = MyTestEnvironment()

if __name__ == "__main__":
  sys.argv.append("--verbose")
  unittest.longMessage = True
  unittest.main()