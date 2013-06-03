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
import getopt
import logging
import platform

import utils
import test_release as test
import svn
import build
from manifest import installFromManifest
from arch import getArch
from install import smartCopy

pythonVersion = sys.version[:3]

# sourceReleaseTypes = ["basicplugin-source", "learningplugin-source", "tools-source"]
sourceReleaseTypes = ["basicplugin-source"]
binaryReleaseTypes = ["binary", "vitamind"]

releasesRequiringSPNupic = ["tools-source"]

#
# do a full checkout (virtual) and build
#
def buildit(rootdir, srcdir, builddir, installdir, svnpath, stamp, revision, datestamp, assertions, update, nprocs=1):
  """
  Do a full checkout and build
  """

  arch = getArch()
  log.info("Building for architecture " + arch)

  #
  # If source dir already exists, we're doing an incremental checkout. If not, we're
  # doing a full checkout. 
  #
  incremental = True
  if not os.path.exists(srcdir):
    if not update:
      log.error("No svn update requested, but source dir '%s' does not exist.", srcdir)
      raise Exception()
    else:
      incremental = False
      log.info("Source directory %s does not exist. Will do a full checkout", srcdir)
  else:
    if not os.path.isdir(srcdir):
      log.error("Source directory %s is not a directory.", srcdir)
      raise Exception()


  log.debug("Creating release directory %s", installdir)
  utils.createDir(installdir, True)
  utils.changeDir(os.path.join(installdir, os.pardir))
  buildfilename = os.path.join(installdir, ".buildinfo")

  #
  # Bring source tree up to date if requested
  #
  if update:
    log.info("Bringing source tree up to date at svnpath %s revision %s", svnpath, revision)
    svn.checkout(srcdir, repo=svnpath, revision=revision, incremental=incremental, keepLocalMods=False)
  else:
    log.warn("Skipping bringing up to date. Build will be tainted")
    utils.touchFile(os.path.join(installdir, "TAINTED_BUILD"))

  #
  # Revision may not be a number. May be "HEAD" or "PREV" or something else, so
  # retrieve it from svn
  #
  revisionnum = svn.getRevision(srcdir)

  #
  # place a temporary file in the install dir to indicate a build in progress
  # the file is removed at the end of the build process
  #
  build_in_progress_filename = os.path.join(installdir,"UNFINISHED_BUILD." + arch)
  utils.touchFile(build_in_progress_filename)


  log.debug("Updating build description file " + buildfilename)
  try:
    f = open(buildfilename, mode = "a")
    print >> f, "============================="
    print >> f, "Timestamp: " + datestamp
    print >> f, "Arch:      " + arch
    print >> f, "Buildhost: " + platform.node()
    print >> f, "Svnpath:   " + svnpath
    print >> f, "Revision:  " + str(revisionnum)
    print >> f, "Rootdir:   " + rootdir
    print >> f, "Srcdir:    " + srcdir
    print >> f, "Stamp:     " + stamp
    print >> f, "Assertions:" + str(assertions)
    print >> f, "Update:    " + str(update)
    print >> f, ""
    f.close()
  except Exception, e:
    raise Exception("Error writing to build description file '%s'", buildfilename)

  log.info('Configuring and building %s at revision %s into %s', svnpath, revisionnum, installdir)

  build.prepareSourceTree(srcdir)
  build.build(srcdir, builddir, installdir, assertions, nprocs=nprocs)

  log.info("Build is finished")
  utils.remove(build_in_progress_filename)

######### End of buildit ###########


def getReleaseName(stamp, releaseType, debug=False):
  arch = getArch()
  if debug:
    prefix = "nupic-debug"
  else:
    prefix = "nupic"

  if releaseType == "binary":
    releaseName = "%s-%s-%s" % (prefix, stamp, arch)
  elif releaseType == "vitamind":
    releaseName = "%s-vitamind-%s-%s" % (prefix, stamp, arch)
  elif releaseType == "npp":
    releaseName = "%s-npp-%s-%s" % (prefix, stamp, arch)
  elif releaseType in sourceReleaseTypes:
    releaseName = "%s-%s-%s" % (prefix, stamp, releaseType)
  else:
    raise Exception("getReleaseName: unknown release type '%s'" % releaseType)

  return releaseName

def createEngineeringRelease(destDir, engReleaseDir, releaseName, tmpDir=None):
  """Create and engineering release tarball in destDir from the
  directory engReleaseDir.  Returns a path to the tarball
  Throws an exception on error. """

  log.info("Creating engineering release tarball")
  if not os.path.exists(destDir):
    utils.createDir(destDir)

  engReleaseTarball = utils.createArchive(engReleaseDir, 
                                          destDir, 
                                          rootRename=releaseName, 
                                          tmpDir=tmpDir)
  return engReleaseTarball




def createCustomerRelease(releaseType, releaseSpecDir, destDir, fromDir, releaseName, allArchitectures=True, allArchiveTypes=False, allowSymbolicLinks=False, parentTmpDir=None):
  """Create a customer release tarball in destdir from the
  directories engReleaseDir and releaseSpecDir
  releaseType is one of biaryReleaseTypes or sourceReleaseTypes
  fromDir is engineering build for the binary release, 
             source dir for a source release
  releaseSpecDir is directory containing manifests
  Returns a path to the tarball
  Throws an exception on error"""

  if not os.path.exists(destDir):
    utils.createDir(destDir)

  if releaseType in binaryReleaseTypes:
    isSourceRelease = False
  elif releaseType in sourceReleaseTypes:
    isSourceRelease = True
  else:
    raise Exception("Unknown release type '%s'" % releaseType)
    
  if not isSourceRelease:
    allArchitectures=False

  manifestFile = os.path.join(releaseSpecDir, releaseType + "_release", 
                              "manifests", releaseType + "_release.manifest")

  log.info("Creating customer release of type %s", releaseType)
  log.info("specDir: %s", releaseSpecDir)
  log.info("fromDir: %s", fromDir)
  tempdir = utils.createTemporaryDirectory("assemble_release", parentDir=parentTmpDir)
  try:
    releaseImageDir = os.path.join(tempdir, releaseName)
    installFromManifest(manifestFile, fromDir, releaseImageDir, 
                        level=0, overwrite=False, destdirExists=False, 
                        allArchitectures=allArchitectures, allowSymbolicLinks=allowSymbolicLinks)
    if isSourceRelease:
      # run autogen equivalent on source trees
      build.prepareSourceTree(releaseImageDir, customerRelease=True)

    # Need to create both zip and tgz source releases on the master build system
    if allArchiveTypes == True:
      # sanity checks
      if not isSourceRelease:
        raise Exception("Attempt to create both zip and tar file for a binary release. Probably an error")
      if getArch() == "win32":
        raise Exception("Attempt to create .tgz source release on a windows system. Would not include autogen.sh")
      zipFile = utils.createArchive(releaseImageDir, destDir, type="zip")
      tarFile = utils.createArchive(releaseImageDir, destDir, type="tar")
      return (tarFile, zipFile)
    else:
      release = utils.createArchive(releaseImageDir, destDir)
      return release
  finally:
    utils.remove(tempdir)


def buildTestSourceReleaseQA(releaseType, releaseTarball, srcDir, binaryTarball=None, short=False, testlist=None, nprocs=1):

  srcTestDir = utils.createTemporaryDirectory("release_testing")
  if releaseType == "binary":
    tarball = releaseTarball
    if testlist is None:
        testlist = "binary"
  elif (releaseType in sourceReleaseTypes):
    tarball = binaryTarball
    if testlist is None:
        testlist = releaseType
  else:
    raise Exception("buildTestSourceReleaseQA: unknown release type %s" % releaseType)
  if tarball == None:
    raise Exception("buildTestSourceReleaseQA: no binary tarball specified for release type %s" % releaseType)

  testdir = utils.extractArchive(tarball, srcTestDir)
  log.info("Testing customer release %s in directory %s" % (releaseType, testdir))
  if releaseType != "binary":
    try:
      print releaseType
      print srcDir
      print releaseTarball
      print binaryTarball
      print testdir
      buildCustomerRelease(releaseType,  srcDir, releaseTarball, binaryTarball, testdir)
    except Exception, e:
      log.error("Source release failed: %s", e)
      # note: leaves temp directory intact
      return(list(), ["build source release"], list())

  utils.setupCleanEnvironment(testdir)
  (passed, failed, disabled) = test.runTests(testdir, srcDir,  short=short, testlist=testlist, nprocs=nprocs)

  return (passed, failed, disabled, testdir)


def buildCustomerRelease(releaseType, releaseSpecDir, releaseTarball, binaryTarball, prefix=None, nprocs=1,parentTmpDir=None):
    """From the given source release tarball, compile and verify that the 
    build product is correct.
    @param releaseType -- one of the source release types
    @param releaseSpecDir -- trunk/release directory containing manifest files for this release
    @param releaseTarball -- tarball containing the release to be built. 
    @param binaryTarball -- tarball containing the binary release. This must be provided
        when building the tools source release, which requires prebuilt libraries that 
        only exist in the binary release. These libraries are copied in to the source 
        release tree prior to building the source release. 
    Throws an exception if the build fails or the build product does not 
    exactly match the manifest file.
    If prefix is not None, install the build product into the prefix directory
    No return value"""


    log.info("Building customer %s release", releaseType)
    

    origDir = os.getcwd()

    if not releaseType in sourceReleaseTypes:
        raise Exception("buildCustomerRelease: unknown release type %s" % releaseType)

    tarballBasename = os.path.basename(releaseTarball)
    (dirName, ext) = os.path.splitext(tarballBasename)

    manifest = os.path.abspath(os.path.join(releaseSpecDir, 
                                            "release",
                                            releaseType+"_release", 
                                            "manifests", 
                                            "build_output.manifest"))
    
    tempdir = utils.createTemporaryDirectory("build_"+releaseType, parentDir=parentTmpDir)

    installdir = os.path.join(tempdir, "install")
    utils.createDir(installdir)

    builddir = os.path.join(tempdir, "build")
    utils.createDir(builddir)

    srcdir = utils.extractArchive(releaseTarball, tempdir)

    # Use the precompiled runtime library for the full source build. 
    if releaseType in releasesRequiringSPNupic:
      if binaryTarball is None:
        raise Exception("No binary tarball provided when building tools release, which requires prebuilt libraries")
      binarydir = utils.extractArchive(binaryTarball, tempdir)
      log.info("Copying libruntime.a from binary release into source release")
      if getArch() != "win32":
        smartCopy(os.path.join(binarydir, "lib", "libruntime.a"), 
                  os.path.join(srcdir, "external", getArch(), "lib", "libruntime.a"))
        smartCopy(os.path.join(binarydir, "lib", "libnode.a"), 
                  os.path.join(srcdir, "external", getArch(), "lib", "libnode.a"))
        smartCopy(os.path.join(binarydir, "lib", "libipcserial.a"), 
                  os.path.join(srcdir, "external", getArch(), "lib", "libipcserial.a"))
      else:
        smartCopy(os.path.join(binarydir, "lib", "release", "runtime.lib"), 
                  os.path.join(srcdir, "external", getArch(), "lib", "runtime.lib"))
        smartCopy(os.path.join(binarydir, "lib", "release", "node.lib"), 
                  os.path.join(srcdir, "external", getArch(), "lib", "node.lib"))
        smartCopy(os.path.join(binarydir, "lib", "release", "ipcserial.lib"), 
                  os.path.join(srcdir, "external", getArch(), "lib", "ipcserial.lib"))


    build.build(srcdir, builddir, installdir, assertions=False, customerRelease=True, nprocs=nprocs)

    # To verify the build product, we install from manifest and then 
    # confirm that the installed tree has the same number of files as the original tree. 
    # An exception in the installFromManifest phase usually means there is a file in 
    # the manifest that was not built. Then if the number of files is the same, it usually
    # means that a file was built that was not in the manifest. 
    tempInstallDir = os.path.join(tempdir, "temp_install")
    installFromManifest(manifest, installdir, tempInstallDir, 
                        level=0, overwrite=False, destdirExists=False)
    
    installedFiles = []

    for root,dirs,files in os.walk(tempInstallDir):
      installedFiles += [os.path.join(root, f) for f in files]
    # normalize the list of files
    prefixLen = len(tempInstallDir)
    installedFiles = [f[prefixLen:] for f in installedFiles]
    installedFiles = sorted(installedFiles)
      
    builtFiles = []
    for root,dirs,files in os.walk(installdir):
      builtFiles += [os.path.join(root, f) for f in files]
    # normalize the list of files
    prefixLen = len(installdir)
    builtFiles = [f[prefixLen:] for f in builtFiles]
    builtFiles = sorted(builtFiles)

    if len(installedFiles) != len(builtFiles):
      log.error("Manifest error when building %s release", releaseType)
      log.error("Built files: %d  Files in manifest: %d", len(builtFiles), len(installedFiles))
      # we know that every file in installedFiles is also in builtFiles
      # because installed dir was created from built dir
      for f in installedFiles:
        builtFiles.remove(f)
      
      for f in builtFiles:
        log.error("File '%s' installed but not in build_output.manifest" % f)
      
      raise Exception("Error building %s release -- file(s) missing from build_output.manifest" % releaseType)
    else:
      log.info("Release %s built successfully. Build produces %d files", releaseType, len(builtFiles))

    # copy all built files from directory where built into the the prefix dir, if specified
    if prefix is not None:
      log.info("Installing build products from '%s' release into binary release at '%s'", 
               releaseType, prefix)
      installFromManifest(manifest, installdir, prefix, 
                          level=0, overwrite=True, destdirExists=True)
    

    # clean up
    os.chdir(origDir)
    utils.remove(tempdir)

def testCustomerRelease(releaseType, releaseTarball, srcDir, binaryTarball=None, short=True, testlist=None, buildOnly=False, nprocs=1,parentTmpDir=None):
  """
  Test a customer release by
  binary release and vitamind release:
    extract it
    run tests

  source release
    extract binary release
    extract source release
    build source release and install into binary releaes
    run tests
  @param releaseType    One of binaryReleaseTypes or sourceReleaseTypes
  @param releaseTarball Absolute pathname to the tarball being tested
  @param srcDir         Absolute path to source tree (where tests may reside)
  @param binaryTarball  Absolute pathname to the binary tarball (used/required only 
                        for the tools source release if buildOnly is False)
  @param short          If true, run short versions of hte tests
  @param testlist       Name of testlist. If None, then defaults to release type
  @param buildOnly      For source releases, just build -- don't run the tests.
  @retval               tuple of (pass, fail, disabled) tests
  """

  # Require binary tarball if we're building a source release and 
  # either 1) we will test the release or 2) the release requires spnupic libraries to build
  if releaseType in sourceReleaseTypes and binaryTarball is None:
    if buildOnly == False or releaseType in releasesRequiringSPNupic:
      raise Exception("testCustomerRelease: no binary tarball specified for release type %s" % releaseType)

  if testlist is None:
    testlist = releaseType

  tmpDir = utils.createTemporaryDirectory("release_testing", parentDir=parentTmpDir)
  if releaseType in binaryReleaseTypes:
    tarballToExtract = releaseTarball
  elif releaseType in sourceReleaseTypes:
    tarballToExtract = binaryTarball
  else:
    raise Exception("testCustomerRelease: unknown release type '%s'" % releaseType)

  if tarballToExtract is not None:
    testdir = utils.extractArchive(tarballToExtract, tmpDir)
  else:
    testdir = os.path.join(tmpDir, "binary")
    utils.createDir(testdir)

  passed = list()
  failed = list()
  disabled = list()


  log.info("Testing customer release %s in directory %s" % (releaseType, testdir))
  if releaseType in sourceReleaseTypes:
    try:
      buildCustomerRelease(releaseType,  srcDir, releaseTarball, binaryTarball, testdir, nprocs=nprocs)
    except Exception, e:
      log.error("Source release failed: %s", e)
      failed = ["build source release"]

  if len(failed) == 0:
    if buildOnly:
      passed = ["build source release"]
      failed = list()
      disabled = list()
    else:
      utils.setupCleanEnvironment(testdir)
      (passed, failed, disabled) = test.runTests(testdir, srcDir,  short=short, testlist=testlist, nprocs=nprocs)

  # make sure we're not in the directory we're about to remove
  utils.changeDir("/")
  if len(failed) == 0:
    utils.remove(tmpDir, throwOnError=False)
  else:
    newname = tmpDir + "_failed";
    try:
      os.rename(tmpDir, newname)
    except:
      log.warn("Unable to rename directory %s to %s after failure", tmpDir, newname)
        
  return (passed, failed, disabled)

def buildPlugins(binaryTarball, pluginTarball, srcDir, integrateScript=None, pluginList=None):
  """
  Test a plugin source release by
  1. extract binary tarball
  2. extract algorithm source tarball
  3. integrate test code into algorithm source tarball
     if integrate script is not None, run:  integrateScript algorithmSrcDir srcDir
  4. build from algorithm source and install into binary release
  4a. move all plugins from lib to testlib directory in binary release

  @param binaryTarball   Absolute pathname to the binary tarball
  @param pluginTarball   Absolute path to plugin source release tarball
  @param srcDir          Absolute path to source tree (where tests may reside)
  @param integrateScript Script for integrating test code into algorithm source directory
  @param testlist        Name of testlist. If None, no tests are performed. 
  @param short           If True, short version of tests is run
  @param pluginList      File containing a list of directories that will be integrated into the source
                         Must be set if integrateScript is set
  @retval                tuple of (binaryDir, tmpDir)
                         binaryDir is in tmpDir; tmpDir must be deleted by called
  """
  # XXX PORT FOR WINDOWS
  # METHOD IS CURRENTLY UNUSED?
  if integrateScript is not None:
    assert os.path.exists(integrateScript), "integrateScript '%s' does not exist" % integrateScript
    assert pluginList is not None
    assert os.path.exists(pluginList), "pluginList '%s' does not exist" % pluginList

  tmpDir = utils.backquote("mktemp -d -q /tmp/plugin_test.XXXXXX")
  binaryDir = utils.extractArchive(binaryTarball, tmpDir)
  pluginSrcDir = utils.extractArchive(pluginTarball, tmpDir)



  try:
    # Move the original plugins out of the way. Save them in case we want to use t hem. 
    libDir = os.path.join(binaryDir, "lib")
    origPluginDir = os.path.join(binaryDir, "origLib")
    os.mkdir(origPluginDir)
    for file in os.listdir(libDir):
      (base, ext) = os.path.splitext(file)
      if ext == ".so" or ext == ".dylib":
        os.rename(os.path.join(libDir, file),
                  os.path.join(origPluginDir, file))

    if integrateScript is not None:
      command = ["python", integrateScript, pluginSrcDir, srcDir, pluginList]
      utils.runCommand(command)
      
    buildDir = os.path.join(tmpDir, "build")
    os.mkdir(buildDir)
    if integrateScript is not None:
      utils.changeDir(pluginSrcDir)
      command = "/bin/sh autogen.sh"
      utils.runCommand(command)
    
    # configure
    utils.changeDir(buildDir)
    command = "%s/configure --prefix=%s" % (pluginSrcDir, binaryDir)
    utils.runCommand(command)

    # build
    command = "make -k install"
    utils.runCommand(command)

    # With an integrate script, put all the plugins in a "testLib" directory
    # and let the tests copy in the plugins they need
    if integrateScript is not None:
      testPluginDir = os.path.join(binaryDir, "testLib")
      os.mkdir(testPluginDir)
      for file in os.listdir(libDir):
        (base, ext) = os.path.splitext(file)
        if ext == ".so" or ext == ".dylib":
          os.rename(os.path.join(libDir, file),
                    os.path.join(testPluginDir, file))

  except Exception, e:
    # import traceback
    # traceback.print_exc()
    raise Exception("Caught exception in integrate/build: %s" % e)

  # binaryDir is in tmpDir. tmpDir must be removed afterwards
  return (binaryDir, tmpDir)
                    

def createReleases(destDir, engReleaseDir, srcDir, stamp, locallogger=logging.getLogger('release')):
    """
    Create and test all customer releases.
    Return tuple of pathnames to the releases.
    """
    engTarball = None
    binaryTarball = None
    sourceTarball = None
    failedReleases = list()

    # Create engineering tarball. No additional tests
    releaseName = getReleasename(stamp, "npp")
    engTarball = createEngineeringRelease(destDir, engReleaseDir, releaseName)

    # Create and test binary tarball.
    releaseName = getReleasename(stamp, "binary")
    binaryTarball = createCustomerRelease("binary", os.path.join(srcDir, "release"), 
                                          destDir, engReleaseDir, releaseName)
    (passed, failed, disabled) = testCustomerRelease("binary", binaryTarball, srcDir)
    test.logTestResults((passed, failed, disabled), (False, True, True), "Binary Release Tests", locallogger)
    if len(failed) > 0:
        failedReleases.append("Binary release")
        locallogger.warning("Binary release FAILED")

    for releaseType in sourceReleaseTypes:
      # Create and test full source release
      try:
        releaseName = getReleasename(stamp, releaseType)
        sourceTarball = createCustomerRelease(releaseType, os.path.join(srcDir, "release"),
                                                 destDir, srcDir, releaseName)
        (passed, failed, disabled) = \
            testCustomerRelease(releaseType, sourceTarball, srcDir, binaryTarball=binaryTarball)
        test.logTestResults((passed, failed, disabled), (False, True, True), 
                            "Source release: %s" % releaseType, locallogger)
        if len(failed) > 0:
          failedReleases.append("'%s' release" % releaseType)
      except Exception, e:
        locallogger.exception("%s release FAILED; %s", (releaseType, e))
        failedReleases.append("%s release" % releaseType)


    if len(failedReleases) > 0:
        raise Exception("Failure while building customer releases: %s" % str(failedReleases))

    return((engTarball, binaryTarball, sourceTarball))


def simpleLogSetup():
    """Simple log setup for testing only."""
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
    console.setFormatter(formatter)
    console.setLevel(logging.NOTSET)
    rootlogger = logging.getLogger('')
    rootlogger.setLevel(logging.NOTSET)
    rootlogger.addHandler(console)


# ----------------------------------------------------------------------------
# Main Program
# ----------------------------------------------------------------------------

#
# usage message for make_release.py
#

def usage() :
    print "usage: %s [--rootdir=<dir>] [--srcdir=<dir>] [--svnpath=<path>] [--revision=<rev>] [--stamp=<stamp>] [--enable-assertions] [--disable-update] [--disable-release] [--help]" % os.path.basename(sys.argv[0])
    print "  default values:"
    print "    rootdir  = ~/releases"
    print "    srcdir   = rootdir/src"
    print "    svnpath  = trunk"
    print "    revision = HEAD"
    print "    stamp    = YYYY-MM-DD-HHMM.<arch>"
    print "    assertions = False"
    print "    update   = True"
    print "    release  = False"
    sys.exit(1)


log = logging.getLogger("release")

if __name__ == '__main__':

    # make sure we don't use random tools to build/install
    os.environ['PATH'] = os.pathsep.join(
      "/opt/subversion/bin",
      "/opt/gcc/bin",
      "/opt/tools/bin",
      "/Library/Frameworks/Python.framework/Versions/Current/bin/python",
      "/opt/buildtools/bin",
      "/opt/python%s/bin" % pythonVersion,
      "/usr/local/bin",
      "/usr/bin",
      "/bin")
    rootdir = os.path.expanduser("~/releases")
    builddir = ""
    srcdir = ""
    svnpath = "trunk"
    revision = "HEAD"
    assertions = False;
    update = True;
    dotests = True;
    dobuild = True;
    dorelease = True;
    arch = getArch()

    datestamp = time.strftime("%Y-%m-%d-%H%M")
    stamp = datestamp + "." + os.path.basename(svnpath)

    options = [
        "rootdir=",
        "srcdir=",
        "builddir=",
        "svnpath=",
        "stamp=",
        "revision=",
        "disable-test",
        "enable-assertions",
        "disable-update",
        "disable-build",
        "disable-release"]

    try:
        opts, arags = getopt.getopt(sys.argv[1:], "", options)
    except getopt.GetoptError:
        usage()

    if len(opts) == 0:
        usage()

    for o, a in opts:
        if o == "--help":
            usage()
        if o == "--rootdir":
            rootdir = os.path.expanduser(a)
        if o == "--srcdir":
            srcdir = a
        if o == "--builddir":
            builddir = a
        if o == "--svnpath":
            svnpath = a
        if o == "--stamp":
            stamp = a
        if o == "--revision":
            revision = a
        if o == "--enable-assertions":
            assertions = True;
        if o == "--disable-update":
            update = False;
        if o == "--disable-test":
            dotests = False;
        if o == "--disable-build":
            # undocumented option since this is dangerous. To speed up testing only.
            dobuild = False;
        if o == "--disable-release":
            dorelease = False;

    # Configure logging for when we are called as a standalone program
    # Does not affect logging configuration when we're imported into another
    # module.

    utils.createDir(rootdir)

    logdir = rootdir + os.sep + "status"
    utils.createDir(logdir)

    logfilename = logdir + os.sep + "log." + stamp + "." + arch
    rootlogger = logging.getLogger('')
    rootlogger.setLevel(logging.NOTSET)

    fulllog = logging.FileHandler(logfilename, "w")
    formatter = logging.Formatter("%(asctime)s %(name)-8s %(levelname)-7s %(message)s", "%y-%m-%d %H:%M:%S")
    fulllog.setFormatter(formatter)
    fulllog.setLevel(logging.NOTSET)

    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)

    rootlogger.addHandler(console)
    rootlogger.addHandler(fulllog)

    # reinitialize the logger to use the correct log files.
    # utils.log.__init__("stdout", logfilename + ".old")
    if srcdir == "":
        srcdir = rootdir + os.sep + "src"
    else:
        srcdir = os.path.expanduser(srcdir)

    # release name is stamp-<arch>
    releaseName = "%s-%s" % (stamp, getArch())

    if builddir == "":
        builddir = rootdir + os.sep + "builds" + os.sep + "build." + releaseName
    else:
      builddir = os.path.expanduser(builddir)

    installdir = rootdir + os.sep + "installs" + os.sep + "install." + releaseName
    utils.createDir(installdir)

    # Set PATH and PYTHONPATH variables to good values.
    utils.setupCleanEnvironment()

    if dobuild:
        if (os.path.exists(builddir)) :
          log.error("Build directory %s already exists. Can't build twice into the same location", builddir)
          raise Exception()
        utils.createDir(builddir)
        try:
            buildit(rootdir, srcdir, builddir, installdir, svnpath, stamp, revision, datestamp, assertions, update)
        except Exception, e:
            log.error("Build FAILED: %s", e)
            sys.exit(1)
    else:
      log.warn("Build skipped.")

    tests_ok = True
    if dotests:
        try:
          (passed, failed, disabled) = \
              test.runTestsInSeparateDirectory(installdir, srcdir, testlist="standard")

          test.logTestResults((passed, failed, disabled), (True, True, True), "Primary Tests", log)

          if len(failed) != 0:
            tests_ok = False
        except Exception, e:
            log.exception("Caught exception from testit routine: %s", e)
            tests_ok = False
    else:
        log.info("Tests skipped")
        utils.touchFile(os.path.join(installdir, "UNTESTED_BUILD." + arch))

    if not tests_ok:
        log.error("Tests FAILED. Exiting")
        sys.exit(1)

    release_ok = True
    if dorelease:
        log.info("Building customer releases")
        try:
            destDir = os.path.join(rootdir, "releases", stamp)
            createReleases(destDir, installdir, srcdir, stamp)
        except Exception, e:
            log.exception("Caught exception in createReleases: %s" % e)
            release_ok = False

        if not release_ok:
            log.error("Release creation FAILED")
            sys.exit(1)
        else:
            log.info("Release creation succeeded")
    else:
        log.info("Releases skipped")

    log.info("Done")
    log.info("Finished build is in " + installdir)
    sys.exit(0)

