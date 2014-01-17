#! /usr/bin/env python
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

# the file does not build in the current state, would be nice if we can make it run again 

import os
import sys
import shutil

pythonVersion = sys.version[:3]

def buildApp(trunkDir, releaseDir, version="DEV", appName="Numenta People Tracker"):
  
  print "Building application..."
  print "trunkDir: %s" % trunkDir
  print "releaseDir: %s" % releaseDir

  # Special incantation to import py2app checked in to svn
  py2appdir = "external/darwin86/lib/python%s/site-packages-py2app" % \
                  pythonVersion
  py2appdir = os.path.join(trunkDir, py2appdir)
  import site
  site.addsitedir(py2appdir)

  # Make sure we get nupic and external packages from the right place. 
  sitePackagesDir = os.path.join(releaseDir, 'lib/python%s/site-packages' %
                                 pythonVersion)
  sys.path.insert(0, sitePackagesDir)

  videoDir = os.path.join(releaseDir, "share", "projects", "video")
  origDir = os.getcwd()


  os.chdir(videoDir)
  if os.path.exists("dist"):
    print "Removing previous installation"
    shutil.rmtree("dist")

  # PIL moved from external sources to pip package, maybe the following paths need to be changed, 
  src = os.path.join(sitePackagesDir, "PIL")
  dest = os.path.join(sitePackagesDir, "Image")
  if not os.path.exists(dest):
    print "Linking %s to %s" % (dest, src)
    os.symlink(src, dest)

  from setuptools import setup
  import py2app.recipes

  assert(len(sys.argv) == 1)
  sys.argv.append("py2app")

  from plistlib import Plist
  licenseText = """
Copyright (C) 2009 Numenta Inc. All rights reserved.

This copy of the software is a development version
and is not authorized for any release or use outside of
the Numenta engineering team.
"""

  licenseFile = os.path.join(visionDir, "LICENSE")
  if os.path.exists(licenseFile):
    licenseText = open(licenseFile).read()

  # To appear properly in quicklook, 
  # license paragraph should be unwrapped. 
  # \n-><space>, but \n\n should remain unchanged
  licenseText = licenseText.replace("\n\n", "XXX")
  licenseText = licenseText.replace("\n", " ")
  licenseText = licenseText.replace("XXX", "\n\n")

  plistFile = os.path.join(visionDir, "Info.plist")
  if os.path.exists(plistFile):
    plist = Plist.fromFile(plistFile)
  else:
    print "File '%s' not found" % plistFile
    plist = dict()
  plist.update(dict(CFBundleVersion=version,
                    CFBundleShortVersionString=version,
                    CFBundleName=appName, 
                    NSHumanReadableCopyright=licenseText))



  print "Running setup..."
  setup(
    app=["RunVisionToolkit.py"], 
    setup_requires=["py2app"],
    options=dict(
      py2app=dict(
        includes=[],
        packages=['nupic',  # problem finding image files in site-packages.zip
                  #'matplotlib', # problem finding data files in site-packages.zip
                  'curses',  # seg fault in site-packages.zip
                  'opencv',  # import error
                  'enthought',
                  'wx',      # bus error when dragging files
                  ],  
        plist=plist,
        iconfile="demo.icns"
      )
    )
  )
  print "Done with base app creation"

  app = os.path.join(visionDir, "dist", "%s.app" % appName)

  appResources=os.path.join(app, "Contents/Resources")

  # Copy the base networks
  networkDir = os.path.join(appResources, "networks", "toolkit")
  if not os.path.exists(networkDir):
    os.makedirs(networkDir)
  networkNames = [f for f in os.listdir("networks/toolkit")
                  if f.endswith('.xml.gz')]
  for name in networkNames:
    shutil.copy("networks/toolkit/%s" % name, os.path.join(networkDir, name))

  # Copy the tutorial projects
  projectDir = os.path.join(appResources, "projects")
  if not os.path.exists(projectDir):
    os.makedirs(projectDir)
  projectNames = [f for f in os.listdir("projects") if f.endswith('.tgz')]
  for name in projectNames:
    shutil.copy("projects/%s" % name, os.path.join(projectDir, name))
  
  # # Copy the help files
  # helpDir = os.path.join(appResources, "VisionToolkitHelp")
  # if not os.path.exists(helpDir):
  #   os.makedirs(helpDir)
  # helpNames = [f for f in os.listdir("VisionToolkitHelp")
  #              if not f.startswith('.')]
  # for name in helpNames:
  #   shutil.copy("VisionToolkitHelp/%s" % name, os.path.join(helpDir, name))

  # py2app doesn't copy the plugins, currently
  libDir = os.path.join(appResources, "lib")
  assert(os.path.exists(libDir))
  srcLibDir = os.path.abspath("../../lib")
  shutil.copy(os.path.join(srcLibDir, "libBasicPlugin.dylib"), libDir)
  shutil.copy(os.path.join(srcLibDir, "libLearningPlugin.dylib"), libDir)
  
  # Used by the about box
  # XXX need a new icon
  if os.path.exists("demo.ico"):
    shutil.copy("demo.ico", os.path.join(appResources, "demo.ico"))
  else:
    print "Warning: file 'demo.ico' not found"

  # Used by the license checker and the about box
  if os.path.exists("LICENSE"):
    shutil.copy("LICENSE", os.path.join(appResources, "LICENSE"))
  else:
    print "Warning: file 'LICENSE' not found"

  # Also used by the about box
  versionFile = os.path.join(appResources, ".version")
  assert not os.path.exists(versionFile)
  open(versionFile, "w").write(version)

  # buildinfo not currently used by the about box but we put it
  # in for identification
  buildinfoFile = os.path.join(releaseDir, ".buildinfo")
  if os.path.exists(buildinfoFile):
    shutil.copy(buildinfoFile, os.path.join(appResources, ".buildinfo"))
  else:
    print "Warning: file '.buildinfo' not found"

  # We create a bin dir so that nupic can find its root directory, 
  # which it needs to find the libraries. 
  binDir = os.path.join(appResources, "bin")
  if not os.path.exists(binDir):
    os.mkdir(binDir)

  # extract test data if not already extracted
#   if not os.path.exists("data/nta4_test"):
#     os.chdir("data")
#     rc = os.system("tar xzf nta4_test.tar.gz")
#     if rc != 0:
#       raise Exception("tar xzf nta4_test.tar.gz failed")
#     os.chdir("..")

  # extract distractor data if not already extracted
#   if not os.path.exists("data/distractors"):
#     os.chdir("data")
#     rc = os.system("tar xzf distractors.tar.gz")
#     if rc != 0:
#       raise Exception("tar xzf distractors.tar.gz failed")
#     os.chdir("..")

  # Copy the license if it exists. This is not part of data_files in the setup
  # above because it may not exist if we're not installing from an official
  # demo release
#   licenseFile = os.path.join(visionDir, "demo_license.cfg")
#   if not os.path.exists(licenseFile):
#     print "WARNING: demo license file %s does not exist -- skipping" % licenseFile
#   else:
#     shutil.copy(licenseFile, appResources)

#   dataDir = os.path.join(appResources, "data")
#   try:
#     os.makedirs(dataDir)
#   except:
#     pass
#   shutil.copytree("data/nta4_test", os.path.join(dataDir, "nta4_test"))
#   shutil.copytree("data/distractors", os.path.join(dataDir, "distractors"))
  print "Done creating image"

  # Manual clean up of a bunch of stuff we don't need
  os.chdir(app)
  os.system("du -skh .")
  rc = os.system("find . -name \*.pyc -o -name \*.pyo| xargs rm")
  assert(rc == 0)
  rc = os.system("rm -rf Contents/Resources/lib/python%s/wx/tools" %
                  pythonVersion)
  assert(rc == 0)
  os.system("du -skh .")

  os.chdir(origDir)
  
  


  print "Created application in %s" % app
  return app

def createImage(distPath,imagePath):
  """Create disk image at imagePath from 
  directory at distPath"""

  if os.path.exists(imagePath):
    os.remove(imagePath)

  print "Creating disk image from directory %s" % distPath
  rc = os.system('hdiutil create "%s" -format UDBZ -srcdir "%s"' % (imagePath, distPath))
  if rc != 0:
    raise Exception("hdiutil failed")

  print "Done creating disk image at %s" % imagePath


def createRelease(trunkDir, installDir, tmpDir="/tmp"):

  # Get a release directory
  baseName = os.path.join(tmpDir, "toolkit_release.")
  for i in xrange(0, 10):
    releaseDir = baseName + str(i)
    if not os.path.exists(releaseDir):
      break
  if os.path.exists(releaseDir):
    raise Exception("unable to find release directory in tmpDir %s" % tmpDir)

  print "Creating release in %s" % releaseDir
  # install from the manifest
  pybuildDir = os.path.join(trunkDir, "build_system", "pybuild")
  sys.path.insert(0, pybuildDir)
  import manifest
  import utils
  utils.initlog(False)

  manifestFile = os.path.join(trunkDir, "release", "toolkit_release", "manifests", "toolkit_release.manifest")
  manifest.installFromManifest(manifestFile, installDir, releaseDir, level=0, overwrite=False, destdirExists=False, allArchitectures=False)
  print "Finished creating release"
  return releaseDir


if __name__ == "__main__":

  # usage in autobuild: 
  # build_standalone_demo.py --installDir=<path> | --releaseDir=<path> [--image=<path>] [--tmpDir=<path>]
  # --installDir is the location of the original installation dir.  Defaults to ~/nta/eng. "None" means don't install
  # --releaseDir is the location of the release dir
  # --image is the path of the created disk image. Defaults to "Demo.dmg" in the current directory
  # --tmpDir (optional) is the name of a temporary directory to use for the release
  # --version (optional) is be a build number, e.g. r19286. If not specified, is "DEV"

  if "PYTHONPATH" in os.environ:
    # if PYTHONPATH is set, modules may be included from outside the release
    print "You must unset PYTHONPATH before running this program."
    sys.exit(1)

  defaultInstallDir = "~/nta/eng"
  defaultVersion = "DEV"
  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("--installDir", dest="installDir", default=defaultInstallDir)
  parser.add_option("--releaseDir", dest="releaseDir", default=None)
  parser.add_option("--image", dest="image", default="NumentaVisionToolkit.dmg")
  parser.add_option("--tmpDir", dest="tmpDir", default="/tmp")
  parser.add_option("--version", dest="version", default=defaultVersion)

  (options, args) = parser.parse_args(sys.argv[1:])

  if len(args) > 0:
    parser.error("no extra arguments are allowed")

  if options.installDir == "None" and options.releaseDir is None:
    parser.error("If installDir==None then releaseDir must be specified")

  if options.installDir != "None" and options.releaseDir is not None:
    parser.error("Cannot specify both installdir and releasedir. Use --installDir=None")
    

  # Get rid of args after parsing because sys.argv is used later by setup
  sys.argv = sys.argv[0:1]

  myDir = os.path.dirname(os.path.abspath(__file__))

  # Assumes we are in trunk/build_system/unix/vision_toolkit
  trunkDir = os.path.normpath(os.path.join(myDir, "../../.."))
  
  if options.installDir != "None":
    installDir = os.path.normpath(os.path.abspath(os.path.expanduser(options.installDir)))
    releaseDir = createRelease(trunkDir, installDir, options.tmpDir)
  else:
    releaseDir = os.path.normpath(os.path.abspath(os.path.expanduser(options.releaseDir)))

  app = buildApp(trunkDir, releaseDir, version=options.version)

  if options.image != "None":
    image = os.path.normpath(os.path.abspath(os.path.expanduser(options.image)))
    createImage(app, image)
  else:
    print "Skipping disk image creation"

  # Cleanup
  if options.releaseDir is None:
    print "Removing temporary directory %s" % releaseDir
    shutil.rmtree(releaseDir)

  print "Done"
