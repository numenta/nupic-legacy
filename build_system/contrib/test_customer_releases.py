#!/usr/bin/env python2

import os
import sys
import logging
import getopt
log = logging.getLogger("tcr")

def testCustomerReleases(trunk, installdir, destdir, binaryReleases, sourceReleases, doTests, doBuild):

  # global module imports
  global release
  global test

  if "binary" in binaryReleases:
    doBinary = True
  else:
    doBinary = False

  releaseNames = ""
  for r in binaryReleases + sourceReleases:
    releaseNames += r + " "
  print "Creating the following releases: %s" % releaseNames

  if len(sourceReleases) > 0:
    if doTests and not doBinary:
      raise Exception("Unable to test source releases %s because binary release not being built. Either specify --noTest or add --release=binary" % sourceReleases)
    if doTests and not doBuild:
      raise Exception("Unable to test source releases %s because they are not being built. Remove --noBuild from the command line" % sourceReleases)


  print "Trunk = %s" % trunk
  print "Installdir = %s" % installdir
  print "Tarballs will be placed in %s" % destdir


  if os.environ.has_key("NTAX_DEVELOPER_BUILD"):
    del os.environ["NTAX_DEVELOPER_BUILD"]

  releaseDir = os.path.join(trunk, "release")

  #####################
  # Create the tarballs
  #####################
  binaryTarballs = dict()
  for releaseType in binaryReleases:
    releaseName = release.getReleaseName(name, releaseType)
    binaryTarballs[releaseType] = release.createCustomerRelease(releaseType, releaseDir, destdir, installdir, releaseName, allArchitectures=False, allowSymbolicLinks=True)
    print "Created %s tarball" % releaseType

  sourceTarballs = dict()
  for releaseType in sourceReleases:
    releaseName = release.getReleaseName(name, releaseType)
    sourceTarballs[releaseType] = release.createCustomerRelease(releaseType, releaseDir, destdir, trunk, releaseName, allArchitectures=False, allowSymbolicLinks=True)
    print "Created %s tarball" % releaseType



  passed = dict()    
  failed = dict()
  disabled = dict()

  
  if doTests:
    for releaseType in binaryReleases:
      (passed[releaseType], failed[releaseType], disabled[releaseType]) = release.testCustomerRelease(releaseType, binaryTarballs[releaseType], trunk, None, testlist=releaseType)
      test.logTestResults((passed[releaseType], failed[releaseType], disabled[releaseType]), (True, True, True), "%s release test" % releaseType, log)
  else:
    log.warn("Skipping tests for %s" % binaryReleases)

  
  if doBuild:
    for releaseType in sourceReleases:
      if doTests:
        if (not doBinary) and (releaseType in release.releasesRequiringSPNupic):
          raise Exception("Release '%s' requires SP-NuPIC, but binary release not built. Add --release=binary to the command line")
        buildOnly = False
      else:
        buildOnly = True

      (passed[releaseType], failed[releaseType], disabled[releaseType]) = \
          release.testCustomerRelease(releaseType, sourceTarballs[releaseType], trunk, binaryTarballs["binary"], testlist=releaseType, buildOnly=buildOnly)

      test.logTestResults((passed[releaseType], failed[releaseType], disabled[releaseType]), 
                          (True, True, True), "%s release" % releaseType, log)

        
  for releaseType in passed:
    test.logTestResults((passed[releaseType], failed[releaseType], disabled[releaseType]), 
                        (False, True, False), "%s release (summary)" % releaseType, log)

  print "Done testing customer releases"


def usage(sourceReleaseTypes=None):
  print "usage: %s [--release=name] [--noTest] [--noBuild] <trunkdir> <installdir> <destdir>"
  print "   trunkdir == location of source" 
  print "   installdir == installation directory, e.g. ~/nta/eng"
  print "   destdir == directory into which tarballs will be placed."
  print "  --release=name Specifies which release to build. May be used multiple times."
  print "    If this option is not specified, all releases are used. "
  if sourceReleaseTypes is not None:
    print "    Release types: binary, %s" % sourceReleaseTypes
  print "  --noTest Omits testing"
  print "  --noBuild Omits building (and testing) of source releases"
  print "  --verbose inrease the logging level"
  sys.exit(1)

if __name__ == "__main__":

  optionSpec = ["release=", "noTest", "noBuild", "verbose"]

  try:
    (opts, args) = getopt.gnu_getopt(sys.argv[1:], "", optionSpec)
  except Exception, e:
    print "Error parsing command line: %s" % e
    usage()


  if len(args) != 3:
    usage()
  trunk = os.path.normpath(os.path.abspath(os.path.expanduser(args[0])))
  installdir = os.path.normpath(os.path.abspath(os.path.expanduser(args[1])))
  destdir = os.path.normpath(os.path.abspath(os.path.expanduser(args[2])))
  name = os.path.basename(destdir)

  builddir = os.path.join(trunk, "build_system")
  sys.path.insert(0, builddir)


  # Unusual way of importing because we can't import until
  # we've parsed our arguments. We need to make these available
  # as global variables. 
  try:
    release = __import__("pybuild.make_release").make_release
    utils = __import__("pybuild.utils").utils
    test = __import__("pybuild.test_release").test_release
  except Exception, e:
    print "Exception while importing"
    print "Exception message: %s" % e
    print "sys.path = " 
    for p in sys.path:
      print "   %s" % p
    sys.exit(1)
  

  sourceReleasesToBuild = release.sourceReleaseTypes
  binaryReleases = ["binary"]
  releasesHaveBeenReset = False
  doTests = True
  doBuild = True
  verbose = False
  for (option, val) in opts:
    if option == "--release":
      if not (val in release.binaryReleaseTypes or val in release.sourceReleaseTypes):
        print "Unknown release type %s" % val
        usage(release.sourceReleaseTypes)
      if not releasesHaveBeenReset:
        releasesHaveBeenReset = True
        sourceReleasesToBuild = []
        binaryReleases = []
      if val in release.binaryReleaseTypes:
        binaryReleases.append(val)
      elif val not in sourceReleasesToBuild:
        sourceReleasesToBuild.append(val)

    elif option == "--noTest":
      doTests = False
    elif option == "--noBuild":
      doBuild = False
    elif option == "--verbose":
      verbose = True
    else:
      usage()


  utils.initlog(verbose)


  testCustomerReleases(trunk, installdir, destdir, binaryReleases,  sourceReleasesToBuild, doTests=doTests, doBuild=doBuild)

