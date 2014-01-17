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

# Script for building standalone demo for mac
# usage: python <thisscript> py2app

import os
import sys
import shutil

pythonVersion = sys.version[:3]

# We rely on some pybuild utilities. TODO: better mechanism for putting this in sys.path
# Assumes we're in build_system/unix/standalone_apps
pybuildDir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pybuild"))

sys.path.insert(0, pybuildDir)

# import after adding pybuildDir to path
from standalone_utils import createRelease


# initialize logging for pybuild utilities
# need debug=True to be able to output from vitamind install
import utils
utils.initlog(True)

# Copied from windows script
def installVitamind(trunkDir, installDir):
  """Run the installVitamind.py script

  Installs ffmpeg, scipy and vitamind obfuscated pipeline
  to the install dir
  """
  print 'installVitamind()'
  saveDir = os.getcwd()
  os.chdir(os.path.join(trunkDir, 'external/src/python_modules/vitamind'))
  utils.runCommand(['python', 'install_vitamind.py', "--force", installDir])
  os.chdir(saveDir)

def patchLibs(libdir):
  """Make sure that libraries can by dynamically loaded. This is a brute force approach"""

  saveDir = os.getcwd()

  # fix libVitaCFilters.dylib
  dir = os.path.join(
    libdir,
    "python%s/site-packages/vitamind/analyticsLib/pipelineElements" %
    pythonVersion)
  os.chdir(dir)
  # Fix up library references in libVitaCFilters.dylib
  lib = "libVitaCFilters.dylib"
  utils.runCommand(["install_name_tool", "-change", "/tmp/external.buildaccount/lib/libcv.1.dylib", "./libcv.1.dylib", lib])
  utils.runCommand(["install_name_tool", "-change", "/tmp/external.buildaccount/lib/libcxcore.1.dylib", "./libcxcore.1.dylib", lib])

  for lib in ["libcv.1.dylib", "libcxcore.1.dylib"]:
    try:
      os.remove(lib)
    except:
      pass

    os.symlink("../../../opencv/%s" % lib, lib)
  
  os.chdir(saveDir)
  
def buildApp(trunkDir, releaseDir, version="DEV", appName="Numenta People Tracking Demo"):
  
  print "Building application..."
  print "trunkDir: %s" % trunkDir
  print "releaseDir: %s" % releaseDir

  # Special incantation to import py2app checked in to svn
  py2appdir = "external/darwin86/lib/python%s/site-packages-py2app" % pythonVersion
  py2appdir = os.path.join(trunkDir, py2appdir)
  import site
  site.addsitedir(py2appdir)

  # Make sure we get nupic and external packages from the right place. 
  sitePackagesDir = os.path.join(releaseDir, "lib/python%s/site-packages" %
                                 pythonVersion)
  sys.path.insert(0, sitePackagesDir)

  videoDir = os.path.join(releaseDir, "share", "projects", "video")
  origDir = os.getcwd()


  os.chdir(videoDir)
  if os.path.exists("dist"):
    print "Removing previous installation"
    shutil.rmtree("dist")

  src = os.path.join(sitePackagesDir, "PIL")
  dest = os.path.join(sitePackagesDir, "Image")
  if not os.path.exists(dest):
    print "Linking %s to %s" % (dest, src)
    os.symlink(src, dest)

  from setuptools import setup
  import py2app.recipes
  # the matplotlib recipe adds a bad dependency on pytz.zoneinfo
  del py2app.recipes.matplotlib

  assert(len(sys.argv) == 1)
  sys.argv.append("py2app")

  from plistlib import Plist
  licenseText = """
Copyright (C) 2009 Numenta Inc. All rights reserved.

This copy of the software is a development version
and is not authorized for any release or use outside of
the Numenta engineering team.
"""

  licenseFile = os.path.join(videoDir, "LICENSE")
  if os.path.exists(licenseFile):
    licenseText = open(licenseFile).read()

  # To appear properly in quicklook, 
  # license paragraph should be unwrapped. 
  # \n-><space>, but \n\n should remain unchanged
  licenseText = licenseText.replace("\n\n", "XXX")
  licenseText = licenseText.replace("\n", " ")
  licenseText = licenseText.replace("XXX", "\n\n")

  plistFile = os.path.join(videoDir, "Info.plist")
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
    app=["RunPeopleTrackingDemo.pyw"], 
    setup_requires=["py2app"],
    options=dict(
      py2app=dict(
        includes=['csv', # needed by vitamind; not picked up by py2app
],
        # py2app will try to include these packages in site-packages.zip
        # but they don't work there. By listing them explicitly, they 
        # are installed as regular python packages
        packages=['nupic',  # problem finding image files in site-packages.zip
                  # TODO: other demo apps require matplotlib. 
                  # 'matplotlib', # problem finding data files in site-packages.zip
                  'curses',  # seg fault in site-packages.zip
                  'opencv',  # import error
                  # TODO: other demo apps require enthought
                  # 'enthought',
                  'wx',      # bus error when dragging files
                  'vitamind', # not found when in site-packages
                  ],  
        excludes=['matplotlib'], # not needed by PTD but found by py2app
        plist=plist,
        iconfile="demo.icns"
      )
    )
  )
  print "Done with base app creation"

  app = os.path.join(videoDir, "dist", "%s.app" % appName)

  appResources=os.path.join(app, "Contents/Resources")

  # A bunch of files are not copied by py2app because they aren't in 
  # python modules

  topLevelDirFilesToCopy = [".buildinfo"]
  for file in topLevelDirFilesToCopy:
    src = os.path.join(releaseDir, file)
    try:
      shutil.copy(src, appResources)
    except:
      print "%s not found" % src

  videoDirFilesToCopy = ["demo.ico", "LICENSE", "demo_license.cfg", "samples", "images", 
                          "PeopleTrackingCore.py", "PeopleTrackingDemo.py", 
                          "PeopleTrackingGui.py", "SamplesScrolledPanel.py"]
  for file in videoDirFilesToCopy:
    src = os.path.join(videoDir, file)
    try:
      if os.path.isdir(src):
        shutil.copytree(src, os.path.join(appResources, file))
      else:
        shutil.copy(src, appResources)
    except:
      print "%s not found" % src



  libDirFilesToCopy = ["libBasicPlugin.dylib", "libLearningPlugin.dylib", "ffmpeg"]
  # we are in share/examples/video
  srcLibDir = os.path.abspath("../../../lib")
  libDir = os.path.join(appResources, "lib")
  assert(os.path.exists(libDir))
  for f in libDirFilesToCopy:
    src = os.path.join(srcLibDir, f)
    if os.path.isdir(src):
      shutil.copytree(src, os.path.join(libDir, f))
    else:
      shutil.copy(src, libDir)
  
  # The About dialog gets its version string from a file called ".version"
  versionFile = os.path.join(appResources, ".version")
  assert not os.path.exists(versionFile)
  open(versionFile, "w").write(version)

  # We create a bin dir so that nupic can find its root directory, 
  # which it needs to find the libraries. 
  binDir = os.path.join(appResources, "bin")
  if not os.path.exists(binDir):
    os.mkdir(binDir)


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



if __name__ == "__main__":

  # usage in autobuild: 
  # build_standalone_demo.py --installDir=<path> | --releaseDir=<path> [--image=<path>] [--tmpDir=<path>]
  # --installDir is the location of the original installation dir.  Defaults to ~/nta/eng. "None" means don't install
  # --releaseDir is the location of the release dir
  # --image is the path of the created disk image. Defaults to "NumentaPeopleTrackingDemo.dmg" in the current directory
  # --tmpDir (optional) is the name of a temporary directory to use for the release
  # --version (optional) is be a build number, e.g. r19286. If not specified, is "DEV"

  defaultInstallDir = "~/nta/eng"
  defaultVersion = "DEV"
  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("--installDir", dest="installDir", default=defaultInstallDir)
  parser.add_option("--releaseDir", dest="releaseDir", default=None)
  parser.add_option("--image", dest="image", default="NumentaPeopleTrackingDemo.dmg")
  parser.add_option("--tmpDir", dest="tmpDir", default="/tmp")
  parser.add_option("--version", dest="version", default=defaultVersion)
  parser.add_option("--debug", dest="debug", action="store_true", default=False)

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

  # Assumes we are in trunk\/build_system/unix/standalone_apps
  trunkDir = os.path.normpath(os.path.join(myDir, "../../.."))
  
  if options.installDir != "None":
    installDir = os.path.normpath(os.path.abspath(os.path.expanduser(options.installDir)))
    # put the vitamind extras into our install dir and then copy using the manifest
    installVitamind(trunkDir, installDir)
    releaseDir = createRelease("tracker", trunkDir, installDir, options.tmpDir)
    # patchLibs(os.path.join(installDir, "lib"))
  else:
    releaseDir = os.path.normpath(os.path.abspath(os.path.expanduser(options.releaseDir)))

  app = buildApp(trunkDir, releaseDir, version=options.version)

  if options.image != "None":
    image = os.path.normpath(os.path.abspath(os.path.expanduser(options.image)))
    createImage(app, image)
  else:
    print "Skipping disk image creation"

  # Cleanup
  if options.releaseDir is None and not options.debug:
    print "Removing temporary directory %s" % releaseDir
    shutil.rmtree(releaseDir)

  if options.debug:
    print "Release dir %s not deleted" % releaseDir

  print "Done"
