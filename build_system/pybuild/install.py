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
## @file
Installation tool for the Numenta build system.
If NTAX_DEVELOPER_BUILD is set, copy is optimized (directories are linked to on Unix,
and files are not copied if the modification time of the target is more recent).
"""
import sys
import os
import logging
import getopt
import shutil
import string
import ctypes

log_level = logging.INFO
#log_level = logging.DEBUG
mydir = os.path.abspath(os.path.dirname(__file__))
buildSystemDir = os.path.normpath(os.path.join(mydir, os.pardir))
sys.path.append(buildSystemDir)

from arch import getArch
log = logging.getLogger("install")

FILE_ATTRIBUTE_REPARSE_POINT = 1024 # sym link
def isWin32SymLink(path):
  if not hasSymlinks:
    return False

  res = kernel_dll.GetFileAttributesA(path)
  return (res & 1024) == 1024


if sys.platform == 'win32':
  hasSymLinks = False 
#  kernel_dll = ctypes.windll.LoadLibrary('kernel32.dll')
#  # Vista/Windows server 2008 has version 6.0
#  # Windows 7 has version 6.1
#  hasSymLinks = int(platform.win32_ver()[1][0]) > 5
#  isSymLink = isWin32SymLink
else:
  hasSymLinks = True
  isSymLink = os.path.islink
  

def createLink(src, dest):
  """Cross-platform function to create a symbolic link
  
  Works all *nix and Windows Vista and up operating systems
  """
  assert hasSymLinks
  if sys.platform == 'win32':
    global kernel_dll
    if kernel_dll is None:
      kernel_dll = ctypes.windll.LoadLibrary('kernel32.dll')
    
    dir_flag = 0 if os.path.isfile(src) else 1
    parent_dir = os.path.dirname(dest)
    if not os.path.isdir(parent_dir):
      os.makedirs(parent_dir)
    res = kernel_dll.CreateSymbolicLinkA(dest, src, dir_flag)
    if res == 0:
      raise ctypes.WinError()
    
  else:
    os.symlink(src, dest)

def smartCopy(src, dest, overwrite=True, link=False, optimizeCopy=False,developerOnly=False, copyStatInfo=True):
  """Copy a file or directory from src to dest.
  Does not copy .svn dirs, .pyc, .pyo, .la
  @param src Path to file or directory to be copied
  @param dest Path to final location of file or directory.
  @param overwrite Use overwrite mode if True
  @param link Create a link instead of copying (unix only)
  In overwrite mode:
    If dest exists and is a link, the link is replaced
    If dest exists and is a file, the file is replaced
    If dest exists and is a directory, the original contents
      of the directory are untouched unless they are overwritten
    If the dest exists and is a directory, but we would normally
    be creating a link/file, remove the directory and replace with a link/file.
  If the source is itself a link, we copy the target of the link, not the link itself
  If the source is a directory tree that contains links, we will throw an exception
  when we encounter the link.

  """

  log.info("Copying from '%s' to '%s'", src, dest)

  src = os.path.abspath(src)
  dest = os.path.abspath(dest)

  # Check args
  if not os.path.exists(src):
    # Catches broken symbolic links as well
    raise Exception("copy: source '%s' does not exist" % src)

  destExists = os.path.exists(dest)
  if not overwrite and destExists:
    raise Exception("copy: dest '%s' exists but overwrite is not set" % dest)

  if sys.platform == "win32":
    link = link and hasSymLinks

  if os.path.islink(src):
    realpath = os.readlink(src)
    log.debug("Source %s is a link to %s. Copying target of link", src, realpath)
    smartCopy(realpath, dest, overwrite, link)
    return

  if destExists:
    if os.path.islink(dest):
      # Shortcut if link is already correct
      if link:
        if os.readlink(dest) == src and link:
          log.debug("Link %s to %s already exists" % (dest, src))
          return
      remove(dest)
    elif os.path.isfile(dest):
      if os.path.isdir(src):
        # file is incompatible with new content. Delete it.
        remove(dest)
    elif os.path.isdir(dest):
      if os.path.isfile(src):
        # directory is incompatible with new content. Delete it.
        remove(dest)
      elif link and os.path.isdir(src):
        # If we're linking to directories instead of copying, delete it.
        remove(dest)

  else:
    destDir = os.path.dirname(dest)
    if not os.path.isdir(destDir):
      os.makedirs(destDir)


  # At this point we have:
  # src is a file or dir (not a link)
  # if src is a file dest does not exist
  # parent directory of dest exists
  # no problems with overwrite setting
  if os.path.isfile(src):
    _copyOneFile(src, dest, optimizeCopy, copyStatInfo)
    return

  # Directory copy
  # Try link first
  if link:
    log.debug("Creating link from '%s' to '%s'", dest, src)
    if os.path.exists(dest):
      remove(dest)
    createLink(src, dest)
    return

  # At this point we're doing a full directory copy
  if not os.path.isdir(dest):
    os.makedirs(dest)

  origDir = os.getcwd()
  os.chdir(src)
  try:
    # walk using topdown=true so that we can prune .svn directories
    for root, dirs, files in os.walk(".", topdown=True):
      destroot = os.path.join(dest, root)
      if os.path.exists(destroot) and not os.path.isdir(destroot):
        remove(destroot)
      if not os.path.exists(destroot):
        os.makedirs(destroot)
      for dir in dirs:
        if dir == ".svn":
          # Disabling because of too verbose autotest
          # log.debug("Skipping directory %s" % dir)
          dirs.remove(dir)
        elif os.path.islink(dir):
          target = os.readlink(dir)
          newdir = os.path.join(dest, root, dir)
          # Disabling because of too verbose autotest
          # log.debug("copying symbolic link %s to %s" % (target, newdir))
          if os.path.exists(newdir):
            remove(newdir)
          os.symlink(target, newdir)
        else:
          newdir = os.path.join(dest, root, dir)
          if os.path.exists(newdir) and not os.path.isdir(newdir):
            remove(newdir)
          if not os.path.exists(newdir):
            os.makedirs(newdir)
      for file in files:
        _copyOneFile(os.path.join(root, file),
                     os.path.join(dest, root, file),
                     optimizeCopy)
  finally:
    os.chdir(origDir)





_ignoreList = [".pyc", ".pyo", ".la"]

def _copyOneFile(source, dest, optimizeCopy=False, copyStatInfo=True):
  """Copy a single file. Dest is a path to the target, not a directory.
  Does not copy .pyc and .pyo files
  Pre-conditions:
  - source exists
  - source is a file

  If dest exists, it is deleted, even if it is a directory
  """

  (base, ext) = os.path.splitext(os.path.basename(source))
  if ext in _ignoreList:
    # Disabling because of too verbose autotest
    # log.debug("Skipping '%s'", source)
    return



  if (os.path.exists(dest)):
    if optimizeCopy:
      try:
        if os.stat(dest).st_mtime >= os.stat(source).st_mtime:
          log.debug("Not copying '%s' to '%s' - dest is newer", source, dest)
          return
        # Disabling because of too verbose autotest
        # log.debug("Dest is not newer: %s (%s) -> %s (%s)", source, os.stat(source).st_mtime, dest, os.stat(dest).st_mtime)
      except:
        # most likely cause of exception is that source or dest is a symbolic
        # link whose target doesn't exist. Ok to fall through to normal copy
        log.warn("Unable to get stat data for %s or %s", dest, source)
        pass

    remove(dest)


  if os.path.islink(source):
    # Disabled because of too-verbose autotest
    # log.debug("Copying symbolic link '%s' to %s", source, dest)
    target = os.readlink(source)
    os.symlink(target, dest)
  else:
    # Disabled because of too-verbose autotest
    # log.debug("Copying '%s' to %s", source, dest)
    if copyStatInfo:
      shutil.copy2(source, dest)
    else:
      shutil.copyfile(source, dest)


def remove(path):
  log.debug("Removing '%s'", path)
  if os.path.isfile(path) or os.path.islink(path):
    os.unlink(path)
    return

  shutil.rmtree(path)

def installFromList(filename, srcdir, destdir, overwrite=True, link=False, optimizeCopy=False,developerOnly=False):
  """Takes a list of src/dest files and directories. Each line has a source,
  and a destination. Lines starting with "#" are comments.
  This method is use for the post-build step on both unix
  and windows.
  A line may be preceded by "@unix" or "@win32" to indicate that
  it should only be copied for that architecture
  """
  substitutions = dict(
    PythonVersion="%d.%d" % (sys.version_info[0], sys.version_info[1]),
    arch=getArch())

  text = open(filename).read()
  t = string.Template(text)
  text = t.substitute(substitutions)
  lines = text.split("\n")

  # strip out comments and newlines
  lines = [l.strip() for l in lines]
  lines = [l for l in lines if l != ""]
  lines = [l for l in lines if l[0] != "#"]

  for line in lines:
    elements = line.split()

    arch = elements[0]
    if len(elements) == 3:
      if arch == "@win32":
        if getArch() != "win32": continue
      elif arch == "@unix":
        if getArch() == "win32": continue
      elif arch == "@darwin86":
        if getArch() != "darwin86": continue
      elif arch == "@darwin64":
        if getArch() != "darwin64": continue
      elif arch == "@darwin":
        # both darwin86 and darwin64
        if getArch() not in ["darwin86", "darwin64"]: continue
      elif arch == "@linux64":
        if getArch() != "linux64": continue
      elif arch == "@linux32":
        if getArch() != "linux32": continue
      elif arch == "@linux32arm":
        if getArch() != "linux32arm": continue
      elif arch == "@linux32armv7":
        if getArch() != "linux32armv7": continue
      else:
        raise Exception("Unknown architecture type %s in file %s" % (arch, filename))
      src = elements[1]
      dest = elements[2]
    elif len(elements) == 2:
      src = elements[0]
      dest = elements[1]
    else:
      raise Exception("Line in unknown format: '%s'" % line)
    src = os.path.join(srcdir, src)
    dest = os.path.join(destdir, dest)
    smartCopy(src, dest, overwrite=overwrite, link=link, optimizeCopy=optimizeCopy, developerOnly=developerOnly)


def usage():
  print "usage: %s [--optimizeCopy] [--debug] [--overwrite] [--link] file srcdir destdir" % sys.argv[0]
  print " --debug prints extra information"
  print " --overwrite allows overwriting of existing files and writing into existing directories. "
  print " --link causes directories to be linked to, rather than copied"
  print " --optimizeCopy causes copy operation to check modification time. No copy is"
  print "   performed if modification time of dest is newer than mod time of source"
  print "\nActual arguments:"
  for i in xrange(1, len(sys.argv)):
    print "%d: %s" % (i, sys.argv[i])
  sys.exit(1)

def main(copyList, srcdir, destdir, debug, overwrite, link, optimizeCopy, developerOnly):
  logging.basicConfig(format="%(levelname)-7s %(message)s", level=log_level, stream=sys.stdout)

  if debug:
    logging.getLogger('').setLevel(logging.DEBUG)
  
  installFromList(copyList, srcdir, destdir, overwrite=overwrite, link=link, optimizeCopy=optimizeCopy, developerOnly=developerOnly)

if __name__ == "__main__":
  debug = False
  overwrite = False
  link = False
  optimizeCopy = False
  developerOnly = False

  longOptionSpec = ["overwrite", "debug", "link", "optimizeCopy"]

  if os.environ.has_key("NTAX_DEVELOPER_BUILD"):
    overwrite = True
    link = True
    optimizeCopy = True
    developerOnly = True
    log.info("NTAX_DEVELOPER_BUILD set -- performing optimized copies")

  try:
    (opts, args) = getopt.getopt(sys.argv[1:], "", longOptionSpec)
  except Exception, e:
    log.error("Error parsing arguments: %s" % e)
    usage()

  if len(args) != 3:
    usage()

  for (option, val) in opts:
    if option == "--debug":
      debug = True
      
    elif option == "--overwrite":
      overwrite = True
    elif option == "--link":
      link = True
    elif option == "--optimizeCopy":
      optimizeCopy = True

  copyList = args[0]
  srcdir = os.path.abspath(os.path.normpath(os.path.expanduser(args[1])))
  destdir = os.path.abspath(os.path.normpath(os.path.expanduser(args[2])))
  
  main(copyList, srcdir, destdir, debug, overwrite, link,
       optimizeCopy, developerOnly)
