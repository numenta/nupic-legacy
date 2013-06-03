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
Copies vitamind release (windows and darwin86) to neo. 
- Log basic info to ~/deploy/deploy.syslog
- Grab deployment lock (~/deploy/deploy.lock) but only with 2 minute
  timeout. If can't grab it, then exit (this prevents us from doing 
  the disk-intensive searches for latest passed/deployed build)
- Find the latest passed build (unless --revision)
- Find the latest deployed build (~/deploy/deploy.latest)
- If the latest deployed build is >= latest passed build, then exit (other
  deploy scripts are only locked out for two minutes)
- Re-grab deployment lock with timeout of for 6 hours, so deployment happens at most every 6 hours. 
- Write latest deployed build file (~/deploy/deploy.latest)

Has options for:
- specifying a specific revision number to deploy (--revision)
- deploying even if there is an unexpired lock (--force)
"""


import sys
import os
import time
import getopt

mydir = sys.path[0]
buildSystemDir = os.path.expanduser("~/build_system")
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
    builds = getReleasesFromRevision(revision)
    found = True
    for  build in builds:
      if not os.path.exists(os.path.join(releasesdir, dir, build)):
        found = False
        break
    if found:
      break
  if not found:
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

def getReleasesFromRevision(revision):
  darwin86build = os.path.join(releasesdir,
                               "r%s" % revision, 
                               "nupic-vitamind-r%s-darwin86.tgz" % revision)
  win32build = os.path.join(releasesdir,
                               "r%s" % revision, 
                               "nupic-vitamind-r%s-win32.zip" % revision)
  darwin86nppbuild =   os.path.join(releasesdir,
                               "r%s" % revision, 
                               "nupic-npp-r%s-darwin86.tgz" % revision)

  win32nppbuild =   os.path.join(releasesdir,
                               "r%s" % revision, 
                               "nupic-npp-r%s-win32_installer.exe" % revision)

  return([darwin86nppbuild, win32nppbuild, darwin86build, win32build])

def deploy(files, host):
  print "Deploying %s to host %s" % (files, host)
  if testOnly:
    return
  utils.copyFilesToDirOnRemoteHost(files, host, "/extrabig/vitamind/releases", "buildaccount")

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
  print "usage: %s [--force] [[--revision <revision>]" % sys.argv[0]
  sys.exit(1)

options = ["force", "revision="]

if __name__ == "__main__":

  try:
    opts, args = getopt.getopt(sys.argv[1:], "", options)
  except getopt.GetoptError:
    usage()

  if len(args) > 0:
    usage()

  force = False
  revision = None

  for o, a in opts:
    if o == "--force":
      force = True
    elif o == "--revision":
      revision = int(a)
        
  rootdir = os.path.expanduser("~/deploy")
  releasesdir = "/Volumes/big/www/autobuild"
  latestDeployFile = os.path.join(rootdir, "deploy.latest")
  syslogFile = os.path.join(rootdir, "deploylog")
  syslog(syslogFile, "Deploying")

  deploylockfile = os.path.join(rootdir, "deploy.lock")
  try:
    lock = utils.getLock(deploylockfile, initialLockTime, processFree=True, force=force)
    if not lock:
      raise Exception("Unable to get deployment lock %s. Use --force to override" % deploylockfile)

    if revision is None:
      revision = getLatestPassedRevision(releasesdir)
      if revision is None:
        raise Exception("Unable to get latest passed revision")
      deployedRevision = getLatestDeployedRevision(latestDeployFile)
      if revision <= deployedRevision:
        raise Exception("Latest passed revision %d is not greater than latest deployed revision %d" % (revision, deployedRevision))
      builds  = getReleasesFromRevision(revision)
    lock = utils.getLock(deploylockfile, deployLockTime, processFree=True, force=True)
  
    if revision is not None:
      setLatestDeployedRevision(latestDeployFile, revision)

    deploy(builds,  "neo.numenta.com")

    syslog(syslogFile, "Deployed %s to neo" % builds)
  except Exception, e:
    tb = sys.exc_info()[2]
    import traceback
    lineNumber = traceback.extract_tb(tb)[-1][1]
    syslog(syslogFile, "Exception (line %d): %s" % (lineNumber, e))



