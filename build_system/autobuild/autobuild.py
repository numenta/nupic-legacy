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


import os
import sys
import time
import traceback
import logging
import platform
import glob

# The autobuild script lives in trunk/build_system/autobuild
# We need to import the pybuild package in trunk/build_system
myDir = os.path.dirname(os.path.abspath(__file__))
buildSystemDir = os.path.normpath(os.path.join(myDir, os.pardir))
if buildSystemDir not in sys.path:
  sys.path.insert(0, buildSystemDir)

import pybuild.make_release as release
import pybuild.utils as utils
import pybuild.test_release as test
import pybuild.svn as svn
import pybuild.mail as mail
import pybuild.qa as qa
from pybuild.arch import getArch

# Flags used in debugging the autobuild script
testAutobuild = False
haveNetwork = True
createQAReleases = True

if not testAutobuild and not haveNetwork:
  raise Exception("Autobuild: running without a network allowed only in test mode")

if createQAReleases:
  import pybuild.qa


# Module-level variables. Easier for these to be global
# than to pass around as function arguments. 
log = logging.getLogger("auto")
config = dict()
overallStatus = test.statusFail
currentOperation = "Unknown"


def mailResults(recipients, comment, failureSetDiff, svnlog, date, revision, shortlog) :
  """
  Mail results to a set of recipients, including the contents of the shortlog
  in the message. 
  """

  global overallStatus, currentOperation, config

  subject =  "%s on %s/r%s  %s on %s" % (config["autobuildName"], getArch(), revision,
                                                  overallStatus, date)
  messageText = "\nResults from autobuild of revision %s for %s on %s:\n\n" % \
      (revision, getArch(), date)

  if comment:
    messageText = messageText + "\n%s\n" % comment

  if failureSetDiff:
    messageText = messageText + "\n%s\n" % failureSetDiff

  if svnlog:
    messageText = messageText + "\n%s\n" % svnlog

  if shortlog is not None:
    messageText = messageText + \
        "\n\n------------------------------- Log -------------------\n"
    try:
      f = open(shortlog)
      for line in f.readlines():
        messageText = messageText + line
    except:
      messageText = messageText + "Unable to read log file '%s'\n" % shortlog

    messageText = messageText+ \
          "\n\n------------------------------- End of Log -------------------\n"
  mail.mail(config["sender"], recipients, subject, messageText, debug=(not haveNetwork))
  # spm("%s %s on %s" % (revision, overallStatus, getArch()))

def syslog(filename, message) :
  """
  Append a single date-stamped message to the given file.
  Used for build system startup/shutdown messages.
  Heavyweight, because it opens and closes the file each time.
  All other message go into a build logs with the
  logger methods (INFO, DEBUG, WARN, ERROR).
  """
  file = open(filename, "a")
  out = "%s %s\n" % (time.strftime("%m/%d-%H:%M:%S "), message)
  file.write(out)
  print out,
  file.close()

def loadConfig(configFile):
  """
  Load configuration options from a file.
  Initial implementation we just exec the file.
  """
  global config
  if not os.path.exists(configFile):
    log.error("loadConfig: file '%s' does not exist" % configFile)
    raise Exception()

  exec open(configFile) in config
  checkVar("masterBuildHost")
  checkVar("qaReleaseHost")
  checkVar("webServerHost")
  checkVar("webServerStatusDir")
  checkVar("baseURL")
  checkVar("statusFilename")
  checkVar("buildAccount")
  checkVar("adminList")
  checkVar("changeNotifyList")
  checkVar("alwaysNotifyList")
  checkVar("maxBuildTime")
  checkVar("sender")
  checkVar("nprocs")
  checkVar("autobuildName")
  checkVar("directories")
  checkVar("cleanDirectories",  False)

def checkVar(varName, default=None):
  """Make sure that a config option is defined"""
  global config
  if not config.has_key(varName):
    if default is not None:
      log.warning("Variable '%s' not specified in autobuild configuration file. Default: %s", varName, default)
      config[varName] = default
    else:
      log.error("Configuration file did not set variable '%s'" % varName)
      raise Exception()


def usage() :
  print "Usage: %s [--config=<filename>]"
  sys.exit(1)


class BuildStatusInfo:
  """
  Contains status information about a completed build.
  Contains the revision number, overall status, timestamp,
  and if not passed, the list of failed tests.
  Can save itself to a file and read itself
  back from a file. Does not use pickle, so that the file
  is human-readable. 
  @todo: this data structure has become more complicated, and 
  needs flexibility 
  """

  def __init__(self, revision=0, status=test.statusUnknown, failedTests=None):
    # default to revision 0 means we rebuild if
    # there is no status file.
    self.revision = revision
    self.status = status
    # t is the time (approximate) that the build was started.
    self.t = time.time()
    if failedTests == None:
      self.failedTests = list()
    else:
      if type(failedTests) == type(str()):
        failedTests = [failedTests]
      self.failedTests = failedTests

  def loadFromFile(self, filename):
    lines = open(filename).readlines()
    self.loadFromArray(lines)

  def loadFromArray(self, array):
    if len(array) < 3:
      log.error("BuildStatusInfo::loadFromArray -- incorrect number of elements: %d",
                len(array))
      raise Exception()
    self.failedTests = list()
    self.revision = int(array[0])
    self.status = array[1].strip()
    self.t = float(array[2].strip())
    # everything after the first four lines is the name of a failed test
    for i in xrange(3, len(array)):
      self.failedTests.append(array[i].strip())
    if self.status == test.statusPass and len(self.failedTests) > 0:
      log.error("BuildStatusInfo: test status is pass but there are failed tests.")
      log.error("Setting status to fail")
      self.status = test.statusFail
      self.failedTests.append("BuildStatusInfo inconsistent")
    if self.status == test.statusFail and len(self.failedTests) == 0:
      log.error("BuildStatusInfo: test status is fail but there are no failed tests listed")
      self.failedTests.append("BuildStatusInfo inconsistent")

  def saveToFile(self, filename):
    f = open(filename, "w")
    # if self.revision is not an integer, this will throw an exception.
    print >> f, self.revision
    print >> f, self.status
    print >> f, self.t
    for failure in self.failedTests:
      print >> f, failure


def spm(msg):

  if sys.platform == "win32":
    return
  import socket
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect(("172.16.190.20", 9100))
  s.send('@PJL RDYMSG DISPLAY="%s"\n' % msg)
  s.close()



############
# Main Program
############

logHelpMessage = """
============================ How to find errors in the log ================================

- To see what failed, go to the end of the log

- To find the test failure in the build log:
  . search for FAILMESSAGE to find failed external command that caused a test failure
  . if no FAILMESSAGE, go to the end of the log and search backward for the test name
    until you get to it

- To find a build error on Unix: search for "] Error 1" (bracket-space-"Error"-space-"1")
  from the beginning ot the log and then scroll up to find the actual error.

- To find a build error on Windows: search for ": error C" (colon-space-"error"-space-"c")
  If that does not work, search for "error(s)" from the top of the file until you find a
  non-zero error count
==========================================================================================
"""


import getopt
if __name__ == '__main__':

  # Enable full logging to the terminal right away, so that we see error messages
  # even if the log isn't set up.
  initialhandler = logging.StreamHandler(sys.stdout)
  formatter = logging.Formatter("%(asctime)s %(name)-7s %(levelname)-7s %(message)s", "%y-%m-%d %H:%M:%S")
  initialhandler.setFormatter(formatter)
  initialhandler.setLevel(logging.NOTSET)

  rootlogger = logging.getLogger('')
  rootlogger.setLevel(logging.NOTSET)
  rootlogger.addHandler(initialhandler)

  # Turn down manifest file logging level
  logging.getLogger('install').setLevel(logging.INFO)

  #
  # Get configuration information
  #

  # config file lives in same directory as this script
  if testAutobuild:
    autobuildConfigFile="autobuild_test.cfg"
  else:
    autobuildConfigFile = "autobuild.cfg"

  optionsFile = os.path.join(myDir, autobuildConfigFile)
  options = "config="
  try:
    opts, arags = getopt.getopt(sys.argv[1:], "", options)
  except getopt.GetoptError:
    usage()
  for o, a in opts:
    if o == "--config":
      optionsFile = a
  loadConfig(optionsFile)


  #
  # Set up some things we'll need throughout the build.
  #
  date = "Unknown date"
  buildRevision = 0
  stamp = "unknownRevision"

  # TODO: replace by socket.gethostname()?
  hostname = platform.node()
  hostname = hostname.replace(".numenta.com", "")
  hostname = hostname.replace(".local", "")
  hostname = hostname.lower()

  if hostname in config["nprocs"]:
    nprocs = config["nprocs"][hostname]
  else:
    nprocs = 1

  arch = getArch()
  rootdir = os.path.expanduser(os.path.join("~", "autobuild"))
  srcdir = os.path.join(rootdir, "src")
  statusdir = os.path.join(rootdir, "status")
  utils.createDir(statusdir, quiet=True)
  syslogFile = os.path.join(statusdir, "syslog")

  autobuildFailures = list()
  #
  # Grab the lock. Exit if we can't get it
  #
  lockfile = os.path.join(statusdir, "lock")
  try:
    lock  = utils.getLock(lockfile, config["maxBuildTime"])
    if lock == True:
      syslog(syslogFile, "Autobuild starting on %s for arch %s" % (hostname, arch))
    else:
      syslog(syslogFile, "Autobuild -- another autobuild is already running")
      sys.exit(1)
  except SystemExit, s:
    sys.exit(s);
  except Exception, e:
    log.error("Expired lock exception: %s", e)
    syslog(syslogFile, "Autobuild -- lock from another autobuild is expired")
    # Notify admin of hung build, but don't do it every time
    # the cron job is run. Do this by grabbing a process-free lock
    notifylockfile = os.path.join(statusdir, "notifylock")
    try:
      notifylock = utils.getLock(notifylockfile, 3600, processFree=True)
    except:
      # An exception means something bad happened. Pretend we got it
      log.exception("Got an exception when trying to get notifylock")
      notifylock = True
    if notifylock:
      mail.mail(config["sender"], config["adminList"], "Autobuild: hung build process on %s" % hostname, messageText="")
      log.info("Sent notification mail")
    else:
      log.info("Not sending notification because there was a recent notification")

    # always exit if we failed to get the main autobuild lock
    sys.exit(1)


  #
  # Get revision to build. Exit if there is nothing new to build.
  #
  currentOperation = "Autobuild setup"
  latestLocalBuildInfo = BuildStatusInfo(revision=0)


  localBuildStatusFilename = os.path.join(rootdir, config["statusFilename"].replace("@arch@", arch))
  localPassedBuildStatusFilename = os.path.join(rootdir, config["statusFilename"].replace("@arch@", "%s-passed" % arch))
  if os.path.exists(localBuildStatusFilename):
    try:
      latestLocalBuildInfo.loadFromFile(localBuildStatusFilename)
    except:
      syslog(syslogFile, "Unable to read local build file. Assuming revision 0")

  try:
    if hostname != config["masterBuildHost"]:
      # non-masters only build from the latest successful master build
      latestMasterBuildInfo = BuildStatusInfo()
      filename = config["masterStatusFilename"]
      masterStatusFilename = utils.createTemporaryFile("status")
      foundMasterStatusFile = True
      try:
        utils.copyFileFromRemoteHost(config["webServerHost"], config["masterStatusFilename"], masterStatusFilename, config["buildAccount"])
        latestMasterBuildInfo.loadFromFile(masterStatusFilename)
      except:
        utils.remove(masterStatusFilename)
        log.exception("Unable to read a master status file %s on host %s. Exiting" % (filename, config["webServerHost"]))
        syslog(syslogFile, "Unable to read a master status file %s on host %s. Exiting" % (filename, config["webServerHost"]))
        sys.exit(1)
      utils.remove(masterStatusFilename)

      if latestMasterBuildInfo.revision <= latestLocalBuildInfo.revision:
        syslog(syslogFile,
                     "Latest local build is %d; Latest master build is %d; not running" %
                     (latestLocalBuildInfo.revision, latestMasterBuildInfo.revision))
        sys.exit(0)
      buildRevision = latestMasterBuildInfo.revision
    else:
      # we're running on the master -- build from the latest svn checkin to the trunk
      latestMasterBuildInfo = latestLocalBuildInfo
      if haveNetwork:
        headRevision = svn.getHeadRevision(srcdir)
      else:
        headRevision = svn.getRevision(srcdir)

      if latestMasterBuildInfo.revision >= headRevision:
        syslog(syslogFile,
                     "No new updates. Latest master build: %d; revision: %d" %
                     (latestMasterBuildInfo.revision, headRevision))
        sys.exit(0)
      buildRevision = headRevision

    #
    # Set up logging
    #
    stamp = "r" + str(buildRevision)
    longlog = os.path.join(statusdir, "log." + stamp + "." + arch + ".txt")
    shortlog = os.path.join(statusdir, "slog." + stamp + "." + arch + ".txt")
    # Don't overwrite an existing log (but normally there will never be an existing log)
    # try logname.1, logname.2, etc
    if os.path.exists(shortlog):
        for i in xrange(0, 10):
            newname = "%s.%s" % (shortlog, str(i))
            if not os.path.exists(newname):
                shortlog = newname
                longlog = "%s.%s" % (longlog, str(i))
                break

    # long log contains all messages
    longlogger = logging.FileHandler(longlog, "w")
    formatter = logging.Formatter("%(asctime)s %(name)-7s %(levelname)-7s %(message)s", "%y-%m-%d %H:%M:%S")
    longlogger.setFormatter(formatter)
    longlogger.setLevel(logging.NOTSET)

    # short log contains only autobuild messages of INFO or higher
    shortlogger = logging.FileHandler(shortlog, "w")
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
    shortlogger.setFormatter(formatter)
    shortlogger.addFilter(logging.Filter("auto"))
    shortlogger.setLevel(logging.INFO)

    rootlogger = logging.getLogger('')
    rootlogger.setLevel(logging.NOTSET)
    if not testAutobuild:
      rootlogger.removeHandler(initialhandler)
    rootlogger.addHandler(shortlogger)
    rootlogger.addHandler(longlogger)

  except SystemExit, s:
    # intentional early exit
    # No need to update status file
    sys.exit(s)
  except Exception, e:
    # Unexpected build system failure in setup.
    # We probably don't even have a standard log file at this point
    message = "Unexpected exception in autobuild setup:\n"
    items = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    for item in items:
      message = message + item
    newStatus = BuildStatusInfo(buildRevision, test.statusFail, "Failure in autobuild setup")
    newStatus.saveToFile(localBuildStatusFilename)

    mail.mail(config["sender"], config["adminList"], "Autobuild: unexpected exception on %s" % hostname, message)
    syslog(syslogFile, "Unexpected exception in autobuild setup")
    raise
  #
  # Everything after this point is recorded in a standard log file, which
  # we always copy to the web server. We have also identified a specific
  # svn revision number that we are building.
  #
  try:
    syslog(syslogFile, "Building at revision %s" % buildRevision)
    # write out a status file saying we have started, so if we are
    # killed before we can write out a final status, the next autobuild
    # will not try to rebuild
    buildInfo = BuildStatusInfo(buildRevision, test.statusStarted, "Autobuild terminated abnormally")
    buildInfo.saveToFile(localBuildStatusFilename)

    log.debug("Logging initialized")
    log.debug(logHelpMessage)
    dateinfo = time.localtime(time.time())
    date = "%d/%02d/%02d at %02d%02d" % (dateinfo[0], dateinfo[1], dateinfo[2],
                                         dateinfo[3], dateinfo[4])
    log.info("Continuous build/test on %s" %(date))

    #
    # Use ramDisk if specified
    # We will create a temporpary directory inside the
    #
    if hostname in config["directories"]:
      directories = config["directories"][hostname]
      if config["cleanDirectories"]:
        # Remove all contents of directories if requested
        for dir in set(directories.values()):
          log.debug("Cleaning directory %s", dir)
          items = glob.glob("%s/*" % dir)
          for item in items:
            utils.remove(item)
    else:
      directories = dict()

    installParentDir=directories.get("install", None)
    buildParentDir=directories.get("build", None)
    installcopyParentDir=directories.get("installcopy", None)
    testoutputParentDir=directories.get("testoutput", None)
    releaseTmpDir=directories.get("release", None)


    #
    # Update the tree and build the software
    #
    currentOperation = "Build"
    log.info("Building at revision %s" % (str(buildRevision)))
    if installParentDir == None:
      installParentDir=os.path.join(rootdir, "installs")
    installdir = os.path.join(installParentDir, "install." + stamp + "." + arch)
    if os.path.exists(installdir) :
      raise Exception("Install directory %s already exists." % (installdir))
    if buildParentDir == None:
      buildParentDir=os.path.join(rootdir, "builds")
    builddir = os.path.join(buildParentDir, "build." + stamp + "." + arch)
    if os.path.exists(builddir) :
      raise Exception("Build directory %s already exists. Can't build twice into the same location" % (builddir))
    utils.createDir(builddir)

    utils.changeDir(srcdir)
    if testAutobuild:
      svnpath = "tmp/autobuild_test"
    else:
      svnpath = "trunk"

    # Assertions turned on for darwin, off everywhere else
    if hostname != config["masterBuildHost"]:
      assertions = False
    else:
      assertions = True
    if haveNetwork:
      update = True
    else:
      update = False
    try:
      release.buildit(rootdir, srcdir, builddir, installdir, svnpath, stamp, \
                      buildRevision, date, assertions, update, nprocs=nprocs)
    except Exception, e:
      log.error("Build failed: %s", e)
      autobuildFailures.append("Build failed")
      raise

    # If build dir location is specified, assume it is on a ram disk and
    # needs to be cleaned up. We are currently in the build dir so get out of there. 
    utils.changeDir(rootdir)
    if buildParentDir is not None:
      utils.remove(builddir)

    #
    # Test the build
    #
    os.environ['NTA_AUTOBUILD_NO_DISPLAY']=str(1)
    currentOpration = "Primary tests"
    log.debug("Testing the build")
    testlist = "standard"
    if sys.platform == "win32":
      (passed, failed, disabled) = ([], [], [])
    else:
      (passed, failed, disabled) = \
          test.runTestsInSeparateDirectory(installdir, srcdir,
                                           testlist=testlist, nprocs=nprocs,
                                           installcopyParentDir=installcopyParentDir,
                                           testoutputParentDir=testoutputParentDir)

    test.logTestResults((passed, failed, disabled),
                        (False, True, True),
                        "Primary Tests", log)
    if len(failed) > 0:
      for failure in failed:
        autobuildFailures.append("Primary Test: " + failure)
      overallStatus = test.statusFail
      raise Exception("One or more primary tests failed")

    #
    # Regression tests.
    #
    #if True:
      #currentOperation = "Regression tests"
      #log.debug("Running regression tests")
      #regressionSrcdir = os.path.join(srcdir, "qa", "regression", "1.7.1")
      #(passed, failed, disabled) = \
          #test.runTestsInSeparateDirectory(installdir, regressionSrcdir,
                                           #testlist="standard", nprocs=nprocs,
                                           #installcopyParentDir=installcopyParentDir,
                                           #testoutputParentDir=testoutputParentDir)
      #test.logTestResults((passed, failed, disabled),
                          #(False, True, True),
                          #"1.7.1 Regression Tests", log)
      #if len(failed) > 0:
        #for failure in failed:
          #autobuildFailures.append("Regression Tests: " + failure)
        #overallStatus = test.statusFail
        #raise Exception("One or more regression tests failed")

    #
    # Create customer releases and test them
    #
    currentOperation = "Creating customer releases"
    allReleases = []
    try:
      custReleaseDir = os.path.join(rootdir, "releases", stamp)

      # Create engineering tarball. No additional tests
      # It is rare for this to fail, since there are no manifests/builds/tests involved
      log.info("Creating all releases")
      releaseName = release.getReleaseName(stamp, "npp", debug=testAutobuild)
      engRelease = release.createEngineeringRelease(custReleaseDir, installdir, releaseName, tmpDir=releaseTmpDir)
      allReleases.append(engRelease)

    ###############
    # DISABLE BINARY RELEASE, INSTALLERS, AND STANDALONE APPS FOR NUPIC2
    ###############
    #   # Create binary release
    #   try:
    #     log.debug("Creating binary release")
    #     releaseName = release.getReleaseName(stamp, "binary", debug=testAutobuild)
    #     binaryRelease = release.createCustomerRelease("binary", os.path.join(srcdir, "release"),
    #                                           custReleaseDir, installdir, releaseName, parentTmpDir=releaseTmpDir)
    #   except:
    #     autobuildFailures.append("Binary release creation failed")
    #     raise

    #   # Test binary release
    #   log.debug("Testing binary release")
    #   (passed, failed, disabled) = release.testCustomerRelease("binary", binaryRelease, srcdir, parentTmpDir=releaseTmpDir, nprocs=nprocs)
    #   test.logTestResults((passed, failed, disabled), (False, True, True), "Binary Release Tests", log)
    #   if len(failed) > 0:
    #     for failure in failed:
    #       autobuildFailures.append("Binary release: " + failure)
    #     raise Exception("Binary release tests failed")

    #   allReleases.append(binaryRelease)


    #   # Create windows installers
    #   if sys.platform == "win32":
    #     try:
    #       log.debug("Creating win32 installer")
    #       win32_installer_path = os.path.join(srcdir, "build_system", "win32", "gui_installer", "create_win32_installer.py")
    #       # @todo createInstaller should use releaseName() method from utils
    #       # Currently that logic is recreated to find the binary release
    #       archiveDir = os.path.dirname(binaryRelease)
    #       installerPath = os.path.join(archiveDir, "nupic-%s-win32_installer.exe" % stamp)
    #       log.debug("Creating installer '%s' from archive '%s' with stamp '%s'", installerPath, binaryRelease, stamp)
    #       command = [sys.executable, win32_installer_path, installdir, binaryRelease, srcdir]
    #       # create_win32_installer.createInstaller(installdir, binaryRelease, installerPath, stamp, srcdir, debug=False, force=False)
    #       try:
    #         utils.runCommand(command)
    #         allReleases.append(installerPath)
    #       except:
    #         log.error("Win32 installer creation failed")
    #         raise

    #       nppInstallerPath = os.path.join(archiveDir, "nupic-npp-%s-win32_installer.exe" % stamp)
    #       log.debug("Creating NPP installer '%s' from archive '%s' with stamp '%s'", nppInstallerPath, engRelease, stamp)
    #       command = [sys.executable, win32_installer_path, installdir, engRelease, srcdir]
    #       # create_win32_installer.createInstaller(installdir, engRelease, nppInstallerPath, "npp-" + stamp, srcdir, debug=False, force=False)
    #       try:
    #         utils.runCommand(command)
    #         allReleases.append(nppInstallerPath)
    #       except:
    #         log.error("Win32 installer creation failed")
    #         raise

    #     except Exception, e:
    #       autobuildFailures.append("Win32 installer creation failed")
    #       raise

    #   # Build standalone apps
    #   if arch == "darwin86":
    #     buildScript = os.path.join(srcdir, "examples", "vision", "utilities", "build_standalone_demo.py")
    #     image = os.path.join(custReleaseDir, "NumentaVision4Demo-%s.dmg" % stamp)
    #     command = [sys.executable, buildScript, "--installDir", installdir, "--image", image,
    #                "--version", stamp]
    #     if releaseTmpDir is not None:
    #       command.extend(["--tmpDir", releaseTmpDir])
    #     try:
    #       utils.runCommand(command)
    #       allReleases.append(image)
    #     except:
    #       log.error("Standalone demo creation failed")
    #       raise
    #     # and the vision toolkit
    #     buildScript = os.path.join(srcdir, "build_system", "unix", "vision_toolkit", "build_vision_toolkit_app.py")
    #     image = os.path.join(custReleaseDir, "NumentaVisionToolkit-%s.dmg" % stamp)
    #     command = [sys.executable, buildScript, "--installDir", installdir, "--image", image,
    #                "--version", stamp]
    #     if releaseTmpDir is not None:
    #       command.extend(["--tmpDir", releaseTmpDir])
    #     try:
    #       utils.runCommand(command)
    #       allReleases.append(image)
    #     except:
    #       log.error("Vision toolkit demo creation failed")
    #       raise
    #   elif arch == "win32":
    #     buildScript = os.path.join(srcdir, "build_system", "win32", "demo", "create_demo.py")
    #     target = os.path.join(custReleaseDir, "NumentaVision4Demo-%s.exe" % stamp)
    #     command = [sys.executable, buildScript, "--install_dir", installdir, "--target", target,
    #                "--version", stamp]
    #     if releaseTmpDir is not None:
    #       command.extend(["--tmpDir", releaseTmpDir])
    #     try:
    #       utils.runCommand(command)
    #       allReleases.append(target)
    #     except:
    #       log.error("Standalone demo creation failed")
    #       raise

    #     buildScript = os.path.join(srcdir, "build_system", "win32", "vision_toolkit", "create_vision_toolkit.py")
    #     target = os.path.join(custReleaseDir, "NumentaVisionToolkit-%s.exe" % stamp)
    #     command = [sys.executable, buildScript, "--install_dir", installdir, "--target", target,
    #                "--version", stamp]
    #     if releaseTmpDir is not None:
    #       command.extend(["--tmpDir", releaseTmpDir])
    #     try:
    #       utils.runCommand(command)
    #       allReleases.append(target)
    #     except:
    #       log.error("vision toolkit creation failed")
    #       raise

    #   # Build source releases

    #   # Disable all source releases but basic plugin source for now
    #   # Re-enable after 1.7.1 per BIC-251
    #   # for releaseType in release.sourceReleaseTypes:
    #   for releaseType in ["basicplugin-source"]:
    #     # don't build the source release on win32 while it is still based on python 2.5
    #     if arch == "win32" and sys.version_info[1] == 5:
    #       continue
    #     releaseName = release.getReleaseName(stamp, releaseType, debug=testAutobuild)
    #     if hostname == config["masterBuildHost"]:
    #       try:
    #         log.debug("Creating source release '%s'" % releaseType)
    #         (sourceRelease, sourceReleaseZip) = release.createCustomerRelease(releaseType, os.path.join(srcdir, "release"),
    #                                                       custReleaseDir, srcdir, releaseName, allArchiveTypes=True,
    #                                                       parentTmpDir=releaseTmpDir)
    #         allReleases.append(sourceRelease)
    #         allReleases.append(sourceReleaseZip)
    #       except Exception, e:
    #         autobuildFailures.append("Source release creation failed")
    #         raise
    #     else:
    #       # Assume web server is a unix system
    #       # Source release should always be .tgz
    #       log.debug("Copying source release from %s" % config["webServerHost"])
    #       if sys.platform == "win32":
    #         remoteFilename = "%s/%s/%s.zip" % (config["webServerReleaseDir"], stamp, releaseName)
    #         sourceRelease = os.path.join(custReleaseDir, releaseName + ".zip")
    #       else:
    #         remoteFilename = "%s/%s/%s.tgz" % (config["webServerReleaseDir"], stamp, releaseName)
    #         sourceRelease = os.path.join(custReleaseDir, releaseName + ".tgz")
    #       utils.copyFileFromRemoteHost(config["webServerHost"], remoteFilename, sourceRelease, config["buildAccount"])

    #     # Test source release
    #     log.debug("Testing source release '%s'" % releaseType)
    #     (passed, failed, disabled) = release.testCustomerRelease(releaseType, sourceRelease, srcdir, binaryTarball=binaryRelease, parentTmpDir=releaseTmpDir, nprocs=nprocs)
    #     test.logTestResults((passed, failed, disabled), (False, True, True),
    #                         "%s Release Tests" % releaseType, log)

    #     if len(failed) > 0:
    #       for failure in failed:
    #         autobuildFailures.append("Source release: " + failure)
    #       raise Exception("Source release tests failed")
    # END OF NUPIC2 DISABLED SECTION

      # Create qa release on the master system
      if createQAReleases and hostname == config["qaReleaseHost"]:
        log.debug("Creating qa release")
        try:
          (qaReleaseTgz, qaReleaseZip) = qa.createQAReleases(stamp, srcdir, custReleaseDir)
        except Exception, e:
          autobuildFailures.append("QA release creation failed")
          raise
        allReleases.append(qaReleaseTgz)
        allReleases.append(qaReleaseZip)


      # Copy releases to master build host if we are on a build machine
      # If creation of any releases failed, createReleases throws an exception
      # so the releases will not be copied
      # Don't use os.path.join to create the directory name, as this will
      # produce the wrong name on a windows system. Instead, assume unix
      # pathnames.
      if hostname.startswith("build-") or testAutobuild:
        utils.copyFilesToDirOnRemoteHost(allReleases,
          config["webServerHost"], config["webServerReleaseDir"] + "/" + stamp,
          config["buildAccount"])

        for file in allReleases:
          checksum = utils.computeFileMD5(file)
          log.debug("Checksum for %s: %s", os.path.basename(file), checksum)

      # If we made it to this point, we have successfully created/tested all releases.
      overallStatus = test.statusPass

    except:
      if len(autobuildFailures) == 0:
        autobuildFailures.append("Creating customer releases")
      overallStatus = test.statusFail
      log.error("Creating customer releases failed.")
      raise

  except Exception, e:
    overallStatus = test.statusFail
    if len(autobuildFailures) == 0:
      autobuildFailures.append("Autobuild internal error")
      log.exception("Autobuild terminated by exception: %s", e)
    else:
      log.error("Autobuild failed: %s", e)

  # Cleanup builddir and installdir -- no need to keep these around
  # Make sure we get out of the directory before we delete it!
  utils.changeDir("/")
  try:
    # exception may have occured before created
    # For now, delete only if build passes
    if not testAutobuild and overallStatus == test.statusPass:
      try:
        utils.remove(builddir)
        utils.remove(installdir)
      except Exception, e:
        log.warn("Unable to remove builddir and/or installdir: %s" % e)
  except:
    pass

  # sanity check -- there should be no errors if we passed
  if overallStatus == test.statusPass and len(autobuildFailures) > 0:
    overallStatus = test.statusFail
    log.error("Autobuild appears to have passed but there are failed tests: %s", str(autobuildFailures))

  log.info("Overall status: %s" % overallStatus)
  newStatus = BuildStatusInfo(buildRevision, overallStatus, autobuildFailures)
  newStatus.saveToFile(localBuildStatusFilename)

  # one status file reports only the latest passing build
  if overallStatus == test.statusPass:
    newStatus.saveToFile(localPassedBuildStatusFilename)


  # If set of failures is different from last time, print them
  # out.
  previousFailures = latestLocalBuildInfo.failedTests
  failureSetChanged = False
  if len(autobuildFailures) != len(previousFailures):
    failureSetChanged = True
  else:
    for i in xrange(0, len(autobuildFailures)):
      if autobuildFailures[i] != previousFailures[i]:
        failureSetChanged = True
        break

  failureSetDiff = ""
  if failureSetChanged:
    failureSetDiff += "Set of failures changed between previous build and this build\n"
    if len(previousFailures) > 0:
      failureSetDiff += "Failures in previous build:\n"
      for failure in previousFailures:
        failureSetDiff += "    %s\n" % failure
    else:
      failureSetDiff += "No failures in previous build\n"
    if len(autobuildFailures) > 0:
      failureSetDiff += "Failures in this build:\n"
      for failure in autobuildFailures:
        failureSetDiff += "    %s\n" % failure
    else:
      failureSetDiff += "No failures in this build\n"
    log.debug("---------------")
    log.debug(failureSetDiff)
    log.debug("---------------")

  # Put SVN delta in the log. 
  svnlog = ""
  previousRevision = latestLocalBuildInfo.revision
  if buildRevision - previousRevision < 100 and haveNetwork:
    try:
      svnlog = svn.getLog(srcdir, previousRevision+1, buildRevision)
      svnlog = "SVN log since previous autobuild (%d):\n%s" % (previousRevision, svnlog)
      log.debug(svnlog)
    except Exception, e:
      log.warn("Error trying to get subversion log: %s", e)
  else:
    # svn log was supressed if previous revision was too long ago
    svnlog = "SVN log suppressed. Previous: '%s'  Current: '%s'" % (previousRevision, buildRevision)
    log.debug(svnlog)

  #
  # Give slave builds the go-ahead if build passed on master
  #
  if overallStatus == test.statusPass and hostname == config["masterBuildHost"] :
    utils.copyFileToRemoteHost(localBuildStatusFilename, config["webServerHost"], config["masterStatusFilename"], config["buildAccount"])

  # All architectures copy status of latest build so that it is available on the master.
  if hostname.startswith("build-"):
    utils.copyFilesToDirOnRemoteHost(localBuildStatusFilename, config["webServerHost"], config["webServerStatusDir"], config["buildAccount"])
    # Give autotest the go-ahead if build passed on this architecture
    if overallStatus == test.statusPass:
      utils.copyFilesToDirOnRemoteHost(localPassedBuildStatusFilename, config["webServerHost"], config["webServerStatusDir"], config["buildAccount"])

  #
  # Copy log files to web server
  # Anything written to the logs after this point won't be visible on the web server
  # Put URL to logs in the logs themselves so that email containing the short log
  # will have a pointer to the full log and long log will have pointer back to short log
  #
  # @todo dont hardcode "autobuild" in pathname
  #
  if locals().has_key("longlog") and locals().has_key("shortlog"):
    log.info("Long  log: %s/%s/%s",
             config["baseURL"], stamp, os.path.basename(longlog))
    log.info("Short log: %s/%s/%s",
             config["baseURL"], stamp, os.path.basename(shortlog))

    # Make sure output has reached the disk so that we copy the whole thing
    longlogger.flush()
    shortlogger.flush()
    # On win32, an external program can't access an open file, but
    # we can, so copy log contents to a temp file
    if sys.platform == "win32":
      tmpdir = utils.createTemporaryDirectory("logs")
      longToCopy = os.path.join(tmpdir, os.path.basename(longlog))
      shortToCopy = os.path.join(tmpdir, os.path.basename(shortlog))

      open(longToCopy,  "w").write(open(longlog).read())
      open(shortToCopy, "w").write(open(shortlog).read())
    else:
      longToCopy = longlog
      shortToCopy = shortlog
    # Don't use os.path.join to create the directory name, as this will
    # produce the wrong name on a windows system. Instead, assume unix
    # pathnames.
    try:
      utils.copyFilesToDirOnRemoteHost([longToCopy, shortToCopy, localBuildStatusFilename],
                                  config["webServerHost"],
                                  config["webServerReleaseDir"] + "/" + stamp,
                                  config["buildAccount"])
    except:
      recipients = config["adminList"]
      buildComment = "Autobuild internal failure -- unable to upload files to data server"
      log.exception("Unable to upload files to data server")

    if sys.platform == "win32":
      utils.remove(tmpdir)

  #
  # Mail results
  # Sent to larger list if 1) status changed or 2) failing and status not changed
  #
  notifylockfile = os.path.join(statusdir, "statuschangelock")
  renotifyHours = 4
  buildComment = ""
  if failureSetChanged:
    recipients = config["changeNotifyList"]
    buildComment = "Build result has changed since last autobuild"
    if overallStatus != test.statusPass:
      # Make sure we dont get another notification for the same failure in the next build
      notifylock = utils.getLock(notifylockfile, renotifyHours*3600, processFree=True, force=True)
  elif overallStatus != test.statusPass:
    # Failure set hasn't changed, but it's been a while since last notification
    try:
      notifylock = utils.getLock(notifylockfile, renotifyHours*3600, processFree=True)
      if notifylock:
        recipients = config["changeNotifyList"]
        buildComment = "Build has been failing for more than %d hours with no change in failed tests." % renotifyHours
      else:
        recipients = config["alwaysNotifyList"]
        buildComment  = "Build has been failing for less than %d hours. Not renotifying" % renotifyHours
    except:
      recipients = config["adminList"]
      buildComment = "Autobuild internal failure -- unable to grab renotify lock"
      log.exception("Unable to grab renotify lock")
  else:
    recipients = config["alwaysNotifyList"]
    buildComment = "Build status unchanged since last autobuild"

  log.debug("Sending mail to: %s" % recipients)

  try:
    # If we got a very early exception, there may be no shortlog
    logfile = locals().get("shortlog", None)
    mailResults(recipients, buildComment, failureSetDiff, svnlog, date, buildRevision, logfile)
    log.info("Mail sent")
  except:
    log.exception("Mail failed")

  if overallStatus == test.statusPass:
    syslog(syslogFile, "Build at revision %s succeeded" % buildRevision)
    sys.exit(0)
  else:
    syslog(syslogFile, "Build at revision %s failed" % buildRevision)
    sys.exit(1)
