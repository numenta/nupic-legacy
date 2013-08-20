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

import utils
import os
import sys
import logging

log = logging.getLogger("build")

if sys.platform == "win32":
  import win32com.client
  import codecs

def prepareSourceTree(srcdir, customerRelease=False):
  if not customerRelease:
    # import setup.py from src/build_system
    buildsystemdir = os.path.join(srcdir, "build_system")
    if sys.path[0] != buildsystemdir:
      if buildsystemdir in sys.path:
        sys.path.remove(buildsystemdir)
      sys.path.insert(0, buildsystemdir)
    import setup
    setup.setup(srcdir)
    
  # Run autogen.sh
  if sys.platform != "win32":
    origDir = os.getcwd()
    # autogen.sh in the source dir
    try:
      utils.changeDir(srcdir)
      utils.runCommand('sh build_system/unix/autogen.sh')
    finally:
      utils.changeDir(origDir)

def build(srcdir, builddir, installdir, assertions, customerRelease=False, nprocs=1):

  # For testing convenience
  srcdir = os.path.expanduser(os.path.normpath(srcdir))
  installdir = os.path.expanduser(os.path.normpath(installdir))
  builddir = os.path.expanduser(os.path.normpath(builddir))
  
  log.debug("Building with srcdir: %s" % srcdir)
  log.debug("Building with installdir: %s" % installdir)
  log.debug("Building with builddir: %s" % builddir)


  if sys.platform == "win32":
    build_win32(srcdir, builddir, installdir, assertions, customerRelease)
  else:
    build_unix(srcdir, builddir, installdir, assertions, customerRelease, nprocs=nprocs)


def build_unix(srcdir, builddir, installdir, assertions, customerRelease=False, nprocs=1):
    
    # VPATH configure
    utils.changeDir(builddir)
    if assertions:
      assertstr="yes"
    else:
      assertstr="no"
    utils.runCommand('%s/configure --disable-debugsymbols --enable-assertions=%s --prefix=%s' % (srcdir, assertstr, installdir))

    #
    # Build the software. Use make -k rather than make so that we see all errors, not just the first
    # Any error will result in an exception from runCommand
    #
    if nprocs != 1:
      utils.runCommand('make -j %s -k' % nprocs)
    else:
      utils.runCommand('make -k')
      
    # Install
    if customerRelease:
      utils.runCommand('make install')
    else:
      utils.runCommand('make install')



def build_win32(srcdir, builddir, installdir, assertions, customerRelease):


  log.info("build_win32: srcdir = '%s'", srcdir)
  log.info("build_win32: builddir = '%s'", builddir)
  log.info("build_win32: installdir = '%s'", installdir)
  # deprecated
  os.environ["NTA"] = installdir
  # These are what I would like to use. Currently only used by the test project
  os.environ["NTAX_INSTALL_DIR"] = installdir
  os.environ["NTAX_BUILD_DIR"] = builddir

  log.debug("build_win32: srcdir: '%s'", srcdir)
  log.debug("build_win32: installdir: '%s'", installdir)
  log.debug("build_win32: builddir: '%s'", builddir)

  # how to quote "Release|Win32" so that it doesn't cause an error?
  # command = ["vcbuild", "/logcommands", "/showenv", "/time", os.path.join(srcdir, "trunk.sln")]
  utils.changeDir(srcdir)
  if customerRelease:
    import glob
    solutionFiles = glob.glob("*.sln")
    if len(solutionFiles) == 0:
      raise Exception("Unable to find any solution files in customer source release")
    elif len(solutionFiles) > 1:
      raise Exception("More than one solution file found in customer source release: %s" % solutionFiles)
    command = 'vcbuild /logcommands /showenv /time %s "Release|Win32"' % solutionFiles[0]
  else:
    command = 'vcbuild /logcommands /showenv /time trunk.sln "Release|Win32"'
  utils.runCommand(command)

  postbuild_win32(srcdir, installdir)

def postbuild_win32(srcdir, installdir):
  srcdir = os.path.abspath(os.path.normpath(os.path.expanduser(srcdir)))
  installdir = os.path.abspath(os.path.normpath(os.path.expanduser(installdir)))
  # Delete .exp, .pdb and .lib files 
  extensionsToDelete = [".exp", ".pdb", ".lib"]
  log.info("Performing postbuild processing for win32. Deleting: %s", extensionsToDelete)
  for (root, dirs, files) in os.walk(installdir):
    # don't delete the precompiled runtime and node libraries
    for exclude in ['release', 'debug']:
      if exclude in dirs:
        dirs.remove(exclude)
    # this file is needed for linking!
    # todo: remove the special case
    excludedBases = ['nta_vision']
    for f in files:
      (base, ext) = os.path.splitext(f)
      if ext in extensionsToDelete and base not in excludedBases:
        path = os.path.join(root, f)
        utils.remove(path)
  log.info("Postbuild complete")

                      
                      
