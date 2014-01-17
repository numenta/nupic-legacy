#!/usr/bin/env python
#
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
#
# Utility functions and classes used by the automated build/test system

import sys
import os
import time
import subprocess
import shutil
import logging
import tempfile
import hashlib # instead of deprecated md5 (since Python 2.6)

# Make sure we can import siblings, later on
mydir = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
if mydir not in sys.path:
  sys.path.insert(0, mydir)

log = logging.getLogger("utils")
OUTPUT=15
logging.addLevelName(OUTPUT, "output")

if sys.platform == "win32":
  try:
    import win32pdh
  except:
    log.warn("Unable to import win32 modules on windows -- will not be able to use locks")

if sys.platform != "win32":
  if sys.platform == "darwin":
    TAR = "/usr/bin/tar"
  else:
    TAR = "/bin/tar"

import tarfile

def initlog(verbose = False) :
  """Perform basic log initialization. Used by
  calling modules that don't use the logging module themselves"""
  if verbose:
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="%(levelname)-7s %(message)s")
    logging.getLogger('').setLevel(logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)-7s %(message)s")
    logging.getLogger('').setLevel(logging.INFO)


class RunCommandException(Exception):
  pass



def runCommand(cmd, throwOnError=True, outputLogLevel=OUTPUT, logOutputOnlyOnFailure=True):
    """
    Run a command. Sends output from the command to the log

    @param cmd            string containing shell command to run
    @param throwOnError   If true, nonzero exit throws an exception
    @retval output        output from the command

    Historical note -- this method used to return the command status if throwOnError = True
    and now returns the captured output. It is similar to runCommandCaptureOutput except that
    output logging happens.
    """

    if throwOnError==False:
      raise Exception("throwOnError flag for runCommand no longer supported -- see Bill")

    if type(cmd) == type(list()):
      commandLine = subprocess.list2cmdline(cmd)
    else:
      commandLine = cmd

    try:
      curDir = os.getcwd()
    except:
      log.debug("CWD has been deleted while running command '%s'" % commandLine)
      curDir = "(Deleted)"

    log.debug('Running command "%s"', commandLine)
    log.debug('CWD: %s', curDir)
    # log.debug("Environment:")
    # for key in os.environ:
    #   log.debug("   %40s: %s", key, os.environ[key])
    # log.debug("Files:")
    # for f in os.listdir("."):
    #   log.debug("   %s", f)

    try:
      p = subprocess.Popen(commandLine, bufsize=1,
                           env=os.environ,
                           shell=True,
                           stdin=None,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    except:
      log.error('runCommand: unable to start command %s' % (commandLine))
      if throwOnError:
        raise
      else:
        return


    if logOutputOnlyOnFailure:
        allOutput = p.stdout.read()
    else:
        allOutput = ""
        # NOTE: "for line in p.stdout" is prone to deadlock when child blocks
        #       on write to stdout (look for "deadlock" in subprocess documentation)
        for line in iter(p.stdout.readline, ''):
            allOutput += line.rstrip() + "\n"
            log.log(outputLogLevel, line)
    s = p.wait()
    if s == 0 :
        log.debug('Command "%s" successful' % commandLine)
    else:
        log.debug('Command "%s" failed -- status = %s' % (commandLine, s))
        if logOutputOnlyOnFailure:
          log.log(outputLogLevel, "---- output -----")
          outputString = "".join(allOutput)
          log.log(outputLogLevel, outputString)
          log.log(outputLogLevel, "---- end of output -----")


    if throwOnError and s != 0:
        log.error("\n %s Command: '%s'" % (allOutput, commandLine))
        raise RunCommandException("\n %s Command: '%s'" % (allOutput, commandLine))
    else:
        return allOutput


def runCommandCaptureOutput(cmd, quiet=False):
  """
  Execute a shell command and capture its output.
  Returns a list of output lines. If the command fails
  with normal exit but nonzero exit status, return
  regular output (don't even print warning).

  If the command fails with abnormal exit (e.g. signalled),
  throw an exception.
  Setting quiet = True prevents log messages about running
  the command
  """
  if not quiet:
    log.debug('Running capturing output "%s"' % cmd)
  else:
    log.debug('Running capturing output "%s"' % cmd)

  try:
    curDir = os.getcwd()
  except:
    log.debug("CWD has been deleted while running command '%s'" % cmd)
    curDir = "(Deleted)"

  log.debug('CWD: %s', curDir)
  # log.debug("Environment:")
  # for key in os.environ:
  #   log.debug("   %40s: %s", key, os.environ[key])
  # log.debug("Files:")
  # for f in os.listdir("."):
  #   log.debug("   %s", f)

  if type(cmd) == type(list()):
    commandLine = subprocess.list2cmdline(cmd)
  else:
    commandLine = cmd

  try:
    p = subprocess.Popen(commandLine, bufsize=1,
                         env=os.environ,
                         shell=True,
                         stdin=None,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
  except:
    log.error("runCommandCaptureOutput: unable to start command %s" % cmd)
    raise

  output = p.stdout.readlines()
  if not quiet:
    for line in output :
      line = line.rstrip()
      log.log(OUTPUT, line)
  status = p.wait()
  if status == 0 :
    if not quiet:
      log.debug('Command "%s" successful' % cmd)
    return output
  elif status > 0:
    # log.warn('Command "%s" failed -- status = %s' % (cmd, status))
    return output
  else:
    log.error('Command "%s" terminated abnormally -- status = %s' % (cmd, status))
    raise Exception()

def runCommandReturnStatusAndOutput(cmd, quiet=False):
  """
  Execute a shell command and capture its output.
  Returns output status and list of output lines.
  Does not throw an exception when the command fails.
  """

  if not quiet:
    log.debug('Running capturing status and output "%s"' % cmd)
  else:
    log.debug('Running capturing status and output "%s"' % cmd)

  if type(cmd) == type(list()):
    commandLine = subprocess.list2cmdline(cmd)
  else:
    commandLine = cmd


  try:
    curDir = os.getcwd()
  except:
    log.debug("CWD has been deleted while running command '%s'" % commandLine)
    curDir = "(Deleted)"

  log.debug('CWD: %s', curDir)
  # log.debug("Environment:")
  # for key in os.environ:
  #   log.debug("   %40s: %s", key, os.environ[key])
  # log.debug("Files:")
  # for f in os.listdir("."):
  #   log.debug("   %s", f)


  try:
    p = subprocess.Popen(commandLine, bufsize=1,
                         env=os.environ,
                         shell=True,
                         stdin=None,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
  except:
    log.error("runCommandCaptureOutput: unable to start command %s" % cmd)
    raise

  output = p.stdout.readlines()
  status = p.wait()
  if not quiet:
    if status == 0 :
      log.debug('Command "%s" successful' % cmd)
    else:
      log.debug('Command "%s" failed status = %s' % (cmd, status))

  return (status, output)


def backquote(cmd, quiet = False):
  """
  Run a shell command and capture one line of output.
  Exactly one line of output is expected -- ERROR if not
  Setting quiet = True prevents log messages about running the command
  unless there is an error
  """
  output = runCommandCaptureOutput(cmd, quiet)
  if output is None:
    log.error('Command %s failed' %(cmd));
    raise Exception()
  if len(output) != 1:
    log.error('Exactly one line of output expected from command "%s" (output = %s)' % (cmd, output))
    raise Exception()
  return output[0].strip()




def createDir(dirname, quiet = False) :
  """
  Create a directory if it does not exist.
  ERROR if we're unable to create it.
  Similar to os.makedirs except that it logs
  """
  if not os.path.exists(dirname) :
    if not quiet:
      log.debug('Creating directory %s' % dirname)
    try:
      os.makedirs(dirname)
    except:
      log.exception("Unable to create directory %s" % (dirname))
      raise

  if not os.path.isdir(dirname) :
    log.error('Pathname %s is not a directory' % (dirname))
    raise Exception()


def changeDir(dirname) :
  """
  Change process working directory.
  Similar to os.chdir except that it logs
  """
  log.debug("Changing directory to %s" % (dirname))
  try:
    os.chdir(dirname)
  except:
    log.exception("Unable to change directory to %s" % (dirname))
    raise

def rename(oldName, newName):
  if not os.path.isabs(oldName) or not os.path.isabs(newName):
    log.debug("Renaming '%s' to '%s' in directory '%s'", oldName, newName, os.getcwd())
  else:
    log.debug("Renaming '%s' to '%s'", oldName, newName)
  os.rename(oldName, newName)

def remove(name, throwOnError=True) :
  """
  Delete a directory or file.
  Similar to shutil.rmtree except that it logs
  """
  # log.debug("Removing item %s", name)
  if not os.path.exists(name):
    log.debug("Item %s does not exist", name)
    return
  if os.path.isdir(name):
    try:
      shutil.rmtree(name)
    except:
      if throwOnError:
        log.error("Unable to remove directory %s", name)
        raise
      else:
        log.warn("Unable to remove directory %s", name)
        return
  else:
    try:
      os.unlink(name)
    except Exception, e:
      if throwOnError:
        log.error("Unable to remove file %s (%s)", name, e)
        raise
      else:
        log.warning("Unable to remove file %s (%s)", name, e)
        return


def setupCleanEnvironment(installdir=None) :
  """
  Make sure environment is correct for build system
  1. numenta_runtime/testeverything/launcher do not appear in PATH,
  2. PYTHONPATH/PYTHONROOT are empty
  """
  if installdir is not None:
    bindir = installdir + os.sep + "bin"
    majorMinorVersionString = "%d.%d" % sys.version_info[0:2]
    pythondir = os.path.join(installdir, "lib",
      "python" + majorMinorVersionString, "site-packages")
  else:
    bindir = ""
    pythondir = ""

  pythonpath = os.getenv('PYTHONPATH')
  if pythonpath is not None:
    if pythonpath != pythondir:
      # no error, since this is a normal occurence
      log.debug("PYTHONPATH set in the environment. Unsetting it.")
    del os.environ['PYTHONPATH']
  if os.getenv('PYTHONHOME') is not None:
    log.warn("PYTHONHOME set in the environment. Unsetting it.")
    del os.environ['PYTHONHOME']

  if os.getenv('PATH') is None:
    log.warn("PATH is not set in the environment. ")

  # check PATH
  newpath = ""

  path = os.environ['PATH']
  pathdirs = path.split(os.pathsep)
  for dir in pathdirs:
    if dir == ".":
      log.debug("Excluding directory '.' from PATH")
    else:
      found = []
      if os.path.exists(dir) and os.path.isdir(dir):
        files = os.listdir(dir)
      else:
        files = []
      for executable in ["numenta_runtime", "testeverything", "launcher"]:
        if executable in files:
          found.append(executable)
      if len(found) != 0:
        # exclude this directory because it contains NTA executables
        # exclude it even if it is the directory we're testing.
        # tests may assume that nothing is in the path.
        log.debug("Excluding directory %s from PATH because these executables found: %s" %
                (dir, str(found)))
      else:
        if newpath == "":
          newpath = dir
        else:
          newpath = newpath + os.pathsep + dir

  if newpath != path:
    log.debug("New path is: " + newpath)
    os.environ['PATH'] = newpath


def copyFilesToDirOnRemoteHost(fileList, remoteHost, remoteDir, user):
  """
  Copies a file from a local system to a remote system. Create directory if it
  doesn't exist. Throws an exception on failure.
  @param fileList    Full pathname to file, or list of full pathnames
  @param remoteHost  Name of remote host
  @param remoteDir   Name of directory on remote host
  """

  log.debug("Copying files %s to host %s in directory %s as user %s", fileList, remoteHost, remoteDir, user)
  if isinstance(fileList, str):
    fileList = [fileList]

  for file in fileList:
    log.debug("checking file '%s'", file)
    if not os.path.exists(file):
      raise Exception("copyFileToRemoteHost: local file %s does not exist" % file)

  if sys.platform != "win32":
    command1 = ["ssh", "%s@%s" % (user, remoteHost), "mkdir", "-p", remoteDir]
    command2 = ["scp"]
    command2.extend(fileList)
    command2.append("%s@%s:%s" % (user, remoteHost, remoteDir))
  else:
    # plink will interpret "-p" as its own option unless we put it inside an argument
    # Note that we can't make a remote dir with spaces in it.
    command1 = ["plink", "-load", "%s@%s" % (user, remoteHost),  "mkdir -p %s"% remoteDir]
    command2 = ["pscp", "-load", "%s@%s" % (user, remoteHost)]
    command2.extend(fileList)
    command2.append("%s@%s:%s" % (user, remoteHost, remoteDir))

  runCommand(command1)
  runCommand(command2)

def copyFileToDirOnRemoteHost(localName, remoteHost, remoteDir, remoteName, user):
  """
  Copies a file from a local system to a remote system. Create directory if it
  doesn't exist. Throws an exception on failure.  @param fileList    Full pathname to file, or list of full pathnames
  @param remoteHost  Name of remote host
  @param remoteDir   Name of directory on remote host  """
  log.debug("Copying file %s to host %s to file %s as user %s", localName, remoteHost, remoteName, user)

  if sys.platform != "win32":
    command1 = ["ssh", "%s@%s" % (user, remoteHost), "mkdir", "-p", remoteDir]
    command2 = ["scp"]
    command2.append(localName)
    command2.append("%s@%s:%s/%s" % (user, remoteHost, remoteDir, remoteName))
  else:    # plink will interpret "-p" as its own option unless we put it inside an argument
    # Note that we can't make a remote dir with spaces in it.
    command1 = ["plink", "-load", "%s@%s" % (user, remoteHost),  "mkdir -p %s"%
remoteDir]
    command2 = ["pscp", "-load", "%s@%s" % (user, remoteHost)]
    command2.append(localName)
    command2.append("%s@%s:%s/%s" % (user, remoteHost, remoteDir, remoteName))

  runCommand(command1)
  runCommand(command2)

def copyFileToRemoteHost(localName, remoteHost, remoteName, user):
  """
  Copies a file from a local system to a remote system.
  Like copyFilesToDirOnRemoteHost but copies a single file, and allows
  the file to be renamed.

  @param localName   Pathname to local file
  @param remoteHost  Name of remote host
  @param remoteDir   Pathname to file on remote host
  """
  log.debug("Copying file %s to host %s to file %s as user %s", localName, remoteHost, remoteName, user)

  if sys.platform != "win32":
    command = ["scp"]
  else:
    command = ["pscp", "-load", "%s@%s" % (user, remoteHost)]
  command.extend([localName, "%s@%s:%s" % (user, remoteHost, remoteName)])
  runCommand(command)

def copyFileFromRemoteHost(remoteHost, remoteName, localName, user):
  """Copy a single file.
  localName may be either a filename or a directory name
  """
  log.debug("Copying file %s from host %s to file %s as user %s", remoteName, remoteHost, localName, user)

  if sys.platform != "win32":
    command = ["scp"]
  else:
    command = ["pscp", "-load", "%s@%s" % (user, remoteHost)]
  command.extend(["%s@%s:%s" % (user, remoteHost, remoteName), localName])
  runCommand(command)

import time
def getLock(lockfile, duration, processFree=False, force=False):
  """
  Locks are implemented with a file. The file contains two lines:
  line 1: pid of process that acquired the lock
  line 2: time at which lock was acquired (as seconds since the epoch)
  line 3: the duration of the lock (in seconds). If the process still exists
          after the lock has expired, that is an error condition --
          the process holding the lock may be killed, and/or an alert may be
          sent (e.g. by a process that subsequently tries to acquire
          the lock)
  Locks are used for making sure that two build processes don't run concurrently.
  Returns True if lock was acquired
  Returns False is lock was not acquired because another process has it
  Throws an exception if another process has had it for longer than the
  timeout period (or on other bad errors)

  If processFree==True, then the lock is not associated with a process and
  is valid until it expires. This is implemented using proces id = 0

  @todo What id process id is reused? Unlikely, on the time scale of the build
  system, but possible. For this reason, just warn -- don't kill


  """
  mypid = os.getpid()
  now = time.time()

  if force and os.path.exists(lockfile):
    os.unlink(lockfile)

  if os.path.exists(lockfile):
    lines = open(lockfile).readlines()
    if len(lines) != 3:
      raise Exception("getLock: Lock file %s is corrupted." % lockfile)
    pid = int(lines[0].strip())
    locktime = int(float(lines[1].strip()))
    oldduration = int(lines[2].strip())
    expiretime = locktime + oldduration
    if not processFree:
      if pid == 0:
        raise Exception("Attempt to acquire a process-owned lock %s that is already process-free" % lockfile)
      if pid != mypid and isProcessRunning(pid):
        # Process is still there; Has lock expired?
        if (expiretime > now):
          return False
        # Process is running, but expired
        raise Exception("Another process (pid %s) holds an expired lock (duration: %s actual: %s)." % (pid, oldduration, int(now - locktime)))
      os.unlink(lockfile)
      # If I already hold the lock, renew it (but this should not happen)
      if pid == mypid:
        if expiretime > now:
          log.warn("getLock: renewing lock %s" % lockfile)
        else:
          log.warn("getLock: renewing expired lock %s" % lockfile)
    else:
      # processFree
      if pid != 0:
        raise Exception("Attempt to acquire a process-free lock %s, but owned by pid %s" % (lockfile, pid))
      if (expiretime > now):
        return False

  lock = open(lockfile, "w")
  if processFree:
    lock.write("0\n")
  else:
    lock.write("%s\n" % str(mypid))
  lock.write("%s\n" % str(now))
  lock.write("%s\n" % str(duration))
  lock.close()
  return True


def isProcessRunning(pid):
  if sys.platform == "win32":
    # First get a list of all processes. All we get is the process name
    ignoreme, processNames = win32pdh.EnumObjectItems(None,None,'process', win32pdh.PERF_DETAIL_WIZARD)
    processCounts = {}
    for name in processNames:
      if name in processCounts:
        processCounts[name] = processCounts[name] + 1
      else:
        processCounts[name]=0

    # For each process, get the pid. Stop if we find our PID
    found = False
    for name, nprocs in processCounts.items():
      if found:
        break
      for procNum in xrange(0, nprocs+1):
        hq = win32pdh.OpenQuery()
        path = win32pdh.MakeCounterPath( (None,'process',name, None, procNum,'ID Process') )
        counter_handle=win32pdh.AddCounter(hq, path)
        win32pdh.CollectQueryData(hq)
        type, val = win32pdh.GetFormattedCounterValue(counter_handle, win32pdh.PDH_FMT_LONG)
        win32pdh.CloseQuery(hq)
        if val == pid:
          found = True
          break
    return found
  else:
    # unix
    psoutput = runCommandCaptureOutput("ps -p %s" % pid, True)
    return len(psoutput) >= 2

def createTemporaryDirectory(basename, sharedFS=False, parentDir=None):
  """Create a temporary directory with the name basename.XXXXXX.
  Similar to tempfile.mkdtemp but action is logged"""
  if sharedFS and parentDir is not None:
    if "HOME" not in os.environ:
      raise Exception("createTemporaryDirectory -- shared filesystem requested but HOME not defined")
    home = os.environ["HOME"]
    parentDir = os.path.join(home, "nta_tmp")
    log.info("createTemporaryDirectory -- shared filesystem requested. Creating in %s" % parentDir)

  if parentDir is not None:
    createDir(parentDir)

  if parentDir:
    tmpdir = tempfile.mkdtemp(suffix="", prefix=basename + ".", dir=parentDir)
  else:
    tmpdir = tempfile.mkdtemp(suffix="", prefix=basename + ".")

  log.debug("Created temporary directory %s", tmpdir)
  return tmpdir

def createTemporaryFile(basename):
  """Create a temporary directory with the name basename.XXXXXX.
  Similar to tempfile.mkdtemp but action is logged"""
  file = tempfile.mkstemp(suffix="", prefix=basename + ".")
  log.debug("Created temporary file %s", file[1])
  os.close(file[0])
  return file[1]

def extractArchive(archive, targetDir):
  """Extract an archive file. Accepts both .tgz and .zip endings.
  Zip file is extracted into targetDir.
  """
  log.debug("Extracting archive '%s' into target '%s'", archive, targetDir)
  if not os.path.exists(targetDir):
    log.error("extractArchive: target directory '%s' does not exist", targetDir)
    raise Exception()
  if not os.path.isdir(targetDir):
    log.error("extractArchive: target '%s' exists but is not a directory", targetDir)
    raise Exception()
  archiveAbsolutePath = os.path.abspath(archive)
  log.debug("Archive absolute path = %s", archive)
  if not os.path.exists(archiveAbsolutePath):
    log.error("extractArchive: archive '%s' does not exist", archiveAbsolutePath)
    raise Exception()
  basename = os.path.basename(archiveAbsolutePath)
  dirname,ext = os.path.splitext(basename)
  extractedDir = os.path.join(targetDir, dirname)
  if os.path.exists(extractedDir):
    log.error("extractArchive: extraction directory '%s' already exists", extractedDir)
    raise Exception()

  if ext == ".tgz" or ext == ".tjz":
    if sys.platform == "win32":
      if ext == ".tgz":
        t = tarfile.open(name=archiveAbsolutePath, mode="r:gz")
      else:
        t = tarfile.open(name=archiveAbsolutePath, mode="r:bz2")
      # Arg. No recursive extraction or directories
      for member in t.getmembers():
        # log.debug("extracting item '%s' from archive" % member)
        t.extract(member, targetDir)
    else:
      if ext == ".tgz":
        flags = "xzf"
      else:
        flags = "xjf"
      saveDir = os.getcwd()
      os.chdir(targetDir)
      runCommand([TAR, flags, archiveAbsolutePath])
      os.chdir(saveDir)
    log.debug("extractArchive -- extracted directory %s into directory %s", dirname, targetDir)
  elif ext == ".zip":
    import zipfile
    # is_zipfile doesn't work
    # if not zipfile.is_zipfile(archive):
    z = zipfile.ZipFile(archiveAbsolutePath, mode="r")
    origDir = os.getcwd()
    try:
      changeDir(targetDir)
      for item in z.namelist():
        if not item.startswith(dirname + "/"):
          log.error("extractArchive: unexpected item '%s' found in archive '%s'",
                    item, archiveAbsolutePath)
          raise Exception()
        if item.endswith("/"):
          if not os.path.exists(item):
            # use makedirs to avoid logging
            os.makedirs(item)
        else:
          if not os.path.exists(os.path.dirname(item)):
            # use makedirs instead of createDir to avoid logging
            os.makedirs(os.path.dirname(item))
          # the "b" is important or this will corrupt binary files!
          ofile = open(item, "wb")
          ofile.write(z.read(item))
          ofile.close()
    finally:
      changeDir(origDir)
  else:
    log.error("extractArchive: Unknown archive extension '%s'", ext)
    raise Exception()

  if not os.path.exists(extractedDir) or not os.path.isdir(extractedDir):
    log.error("extractArchive: unknown error. Directory %s not found!", extractedDir)
  log.debug("extractArchive -- extracted '%s' into '%s'", archiveAbsolutePath, extractedDir)
  return extractedDir

def createArchive(dirToArchive, targetDir, rootRename=None, type="", tmpDir=None):
  """Create an archive of the given directory. On Unix, creates
  a tar file. On windows, creates zip file. The archive is placed
  into targetDir. Returns a full pathname to the archive file.
  If rootRename is not None, renames the root directory.
  The archive name is the name of the directory plug the suffix
  "tgz" or "zip".
  I.e. createArchive("bar", "/tmp", rootRename="foo")
  creates /tmp/foo.tgz on unix, that untars into the directory "foo".
  "Type" can be "zip" or "tgz" to override platform default.
  """
  # ensure that a directory change doesn't mess up a relative directory
  targetDir = os.path.abspath(targetDir)
  dirToArchive = os.path.abspath(dirToArchive)
  dirName = os.path.basename(dirToArchive)
  if type == "":
    if sys.platform == "win32":
      type = "zip"
    else:
      type = "tgz"
  log.debug("createArchive: creating archive of type '%s' in '%s' from directory '%s'",
            type, targetDir, dirToArchive)
  # If rename is unnecessary, don't do it
  if dirName == rootRename:
    rootRename = None
  if rootRename is not None:
    # renaming is fairly painful.
    # Copy the directory to a temp directory using
    # the archive methods; rename the top level directory,
    # and re-archive.
    log.debug("createArchive: renaming root to '%s'", rootRename)
    tempdir=createTemporaryDirectory("archive-rename", parentDir=tmpDir)
    try:
      tmparchive = createArchive(dirToArchive, tempdir, rootRename=None, type=type)
      tmpextract = extractArchive(tmparchive, tempdir)
      newDirToArchive = os.path.join(tempdir, rootRename)
      log.debug("renaming %s to %s", os.path.join(tempdir, dirName), newDirToArchive)
      os.rename(os.path.join(tempdir, dirName),
                newDirToArchive)
      # call ourselves recursively
      archiveName = createArchive(newDirToArchive, targetDir, rootRename=None, type=type)
    finally:
      remove(tempdir, throwOnError=False)
  else:
    # change directory to the parent of the directory we're archiving
    origDir = os.getcwd()
    newDir = os.path.abspath(os.path.join(dirToArchive, os.pardir))
    if newDir != origDir:
      changeDir(newDir)
    try:
      import zipfile
      if type == "zip":
        archiveName = os.path.join(targetDir, dirName + ".zip")
        z = zipfile.ZipFile(archiveName, mode="w", compression=zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(dirName, topdown=False):
          # zipfile module doesn't directly support empty directories
          # The hack below is explained at:
          # http://mail.python.org/pipermail/python-list/2003-June/211918.html
          for d in dirs:
            # log.debug("adding directory to zipfile: %s" % os.path.join(root, d))
            dirpath = os.path.join(root, d)
            t = time.localtime(os.stat(dirpath).st_mtime)
            zinfo = zipfile.ZipInfo(dirpath + os.sep, t[0:6])
            zinfo.external_attr = 48
            z.writestr(zinfo, "")
          for f in files:
            fileToArchive = os.path.join(root, f)
            if os.path.islink(fileToArchive):
              z.writestr(fileToArchive, "Symbolic link to '%s' (not available in zip archive)" % os.readlink(fileToArchive))
            else:
              z.write(os.path.join(root, f))
        z.close()
      else:
        archiveName = os.path.join(targetDir, dirName + ".tgz")
        if sys.platform == "win32":
          # Super slow!
          t = tarfile.open(archiveName, "w:gz")
          t.add(dirName)
          t.close()
        else:
          runCommand([TAR, "czf", archiveName, dirName])
    finally:
      if newDir != origDir:
        changeDir(origDir)
  log.debug("createArchive: created archive '%s'", archiveName)
  return archiveName

def touchFile(path):
  if os.path.isabs(path):
    log.debug("Touching file '%s'", path)
  else:
    log.debug("Touching file '%s' from dir '%s'", path, os.getcwd())
  try:
    f = open(path, "w")
    f.close()
  except:
    # XXX should re-raise. Leave out raise for now while
    # debugging a windows issue
    log.exception("Unable to touch file '%s'", path)


def computeFileMD5(filename):
  if not os.path.exists(filename):
    raise Exception("computeFileMD5: file '%s' does not exist" % filename)
  if os.path.isdir(filename):
    raise Exception("computeFileMD5: file '%s' is a directory" % filename)

  digester = hashlib.md5()
  file = open(filename, "rb")

  # read the file in chunks to avoid having to read very large files into
  # a large python string
  chunkSize = 1024*1024
  chunk = file.read(chunkSize)
  while len(chunk) > 0:
    digester.update(chunk)
    chunk = file.read(chunkSize)
  return digester.hexdigest()

class Environment(object):
  __slots__ = ["entered", "kvs", "values"]
  def __init__(self, **keywords):
    self.entered = False
    self.kvs = dict(keywords)
    self.values = None
  def __enter__(self):
    assert not self.entered
    self.entered = True
    import os
    assert self.values is None
    self.values = dict()
    for k, v in self.kvs.iteritems():
      old = os.getenv(k)
      self.values[k] = old
      if v is None:
        if old is not None:
          del os.environ[k]
      else:
        os.environ[k] = v
  def __exit__(self, type, value, traceback):
    assert self.entered
    assert self.values is not None
    import os
    for k, v in self.values.iteritems():
      if v is None:
        if self.kvs[k] is not None:
          del os.environ[k]
      else:
        os.environ[k] = v
    self.entered = False
    self.values = None

