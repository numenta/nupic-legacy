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


"""
Deploys autobuild engineering release to shona and neo.
- Log basic info to ~/autobuild/status/deploy.syslog
- Grab deployment lock (~/autobuild/status/deploy.lock) but only with 2 minute
  timeout. If can't grab it, then exit (this prevents us from doing 
  the disk-intensive searches for latest passed/deployed build)
- Find the latest passed build (unless --revision)
- Find the latest deployed build (~/autobuild/status/deploy.latest)
- If the latest deployed build is >= latest passed build, then exit (other
  deploy scripts are only locked out for two minutes)
- Re-grab deployment lock with timeout of for 6 hours, so deployment happens at most every 6 hours. 
- Write latest deployed build file (~/autobuild/status/deploy.latest)
- Deploy on neo and shona
  (note: if deployment on neo/shona fails, that build will not be recopied
  because deployed build file is already written)

Has options for:
- specifying a specific tarball to deploy (--tarball)
- specifying a specific revision number to deploy (--revision)
- deploying even if there is an unexpired lock (--force)
- using a link name other than "current"
"""


import sys
import os
import time
import getopt
import autobuild

mydir = sys.path[0]
buildSystemDir = os.path.abspath(os.path.normpath(os.path.join(mydir)))
sys.path.append(buildSystemDir)
import pybuild.utils as utils
import pybuild.test_release as test

testOnly = False
# Initially grab the lock only for two minutes
initialLockTime = 120
# If we decide to deploy, grab it for 6 hours to reduce frequency of copying
deployLockTime = 6 * 3600

def getLatestPassedRevision(releasesdir):
  dirs = [f for f in os.listdir(releasesdir) if f.startswith("r")]
  dirs = sorted(dirs, reverse=True)
  found = False
  for dir in dirs:
    # strip off "r"
    revision = int(dir[1:])
    build = getTarballFromRevision(revision)
    if os.path.exists(os.path.join(releasesdir, dir, build)):
      found = True
      break
  if found == False:
    raise Exception("No passed builds found")
  return revision


def getLatestDeployedRevision(filename):
  if not os.path.exists(filename):
    return 0
  lines = open(filename).readlines()
  if len(lines) == 0:
    try:
      os.remove(filename)
    except:
      pass
    raise Exception("getLatestDeployedRevision: filename %s is empty - deleting" % filename)
  revision = int(lines[0].strip())
  return revision

def setLatestDeployedRevision(filename, revision):
  print "Setting latest deployed revision to %s" % revision
  open(filename, "w").write(str(revision))

def getTarballFromRevision(revision):
    return os.path.join(releasesdir, 
                       "r%s" % revision,
                       "nupic-npp-r%s-linux64.tgz" % revision)

def deploy(tarball, host, label):
  print "Deploying tarball %s to host %s with label %s" % (tarball, host, label)
  if testOnly:
    return
  tarballFilename = os.path.basename(tarball)
  tarballBasename, ext = os.path.splitext(tarballFilename)
  print "Copying build %s to %s" % (tarballBasename, host)
  utils.copyFilesToDirOnRemoteHost(tarball, host, "/tmp", "buildaccount")
  command = 'ssh %s "cd /neo/nta; ' % host
  command = command + "rm -rf %s; " % tarballBasename
  command = command + "tar xzf /tmp/%s; " % tarballFilename
  command = command + "rm -f %s; " % label
  command = command + "ln -s %s %s; " % (tarballBasename, label)
  command = command + "rm -f /tmp/%s; " % tarballFilename
  command = command + '"'
  print "Extracting tarball on host %s" % host
  print "Running command: %s" % command
  utils.runCommand(command)
  


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
    
def usage():
  print "usage: %s [--force] [[--revision <revision>] | [--tarball <tarball>]] [--label <label>]" % sys.argv[0]
  sys.exit(1)

options = ["force", "revision=", "tarball=", "label="]

if __name__ == "__main__":

  try:
    opts, args = getopt.getopt(sys.argv[1:], "", options)
  except getopt.GetoptError:
    usage()

  if len(args) > 0:
    usage()

  force = False
  revision = None
  tarball = None
  label = "current"

  for o, a in opts:
    if o == "--force":
      force = True
    elif o == "--revision":
      revision = int(a)
    elif o == "--tarball":
      if revision is not None:
        print "Both --revision and --tarball specified. Only one allowed"
        usage()
      tarball = a
    elif o == "--label":
      label = a
        
  rootdir = os.path.expanduser("~/autobuild")
  statusdir = os.path.join(rootdir, "status")
  releasesdir = os.path.join(rootdir, "releases")
  latestDeployFile = os.path.join(statusdir, "deploy.latest")
  utils.createDir(statusdir, True)
  syslogFile = os.path.join(statusdir, "deploylog")
  syslog(syslogFile, "Deploying")

  deploylockfile = os.path.join(rootdir, "status", "deploy.lock")
  try:
    lock = utils.getLock(deploylockfile, initialLockTime, processFree=True, force=force)
    if not lock:
      raise Exception("Unable to get deployment lock %s. Use --force to override" % deploylockfile)

    if tarball is None:
      if revision is None:
        revision = getLatestPassedRevision(releasesdir)
        if revision is None:
          raise Exception("Unable to get latest passed revision")
        deployedRevision = getLatestDeployedRevision(latestDeployFile)
        if revision <= deployedRevision:
          raise Exception("Latest passed revision %d is not greater than latest deployed revision %d" % (revision, deployedRevision))
      tarball = getTarballFromRevision(revision)
    lock = utils.getLock(deploylockfile, deployLockTime, processFree=True, force=True)
  
    if revision is not None:
      setLatestDeployedRevision(latestDeployFile, revision)

#     deploy(tarball, "shona1", label)
#     syslog(syslogFile, "Deployed %s with label %s to shona1" % (tarball, label))
    deploy(tarball, "matrix.numenta.com", label)
    syslog(syslogFile, "Deployed %s with label %s to neo" % (tarball, label))
  except Exception, e:
    tb = sys.exc_info()[2]
    import traceback
    lineNumber = traceback.extract_tb(tb)[-1][1]
    syslog(syslogFile, "Exception (line %d): %s" % (lineNumber, e))


# sys.exc_info()[2] is traceback object
# traceback.extract_tb(traceback,limit=1)[0] -> [filename, line number, function name, text]

