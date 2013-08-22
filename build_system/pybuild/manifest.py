#!/usr/bin/env python
# Create a release based on a manifest file
#
# usage: python install_from_manifest.py manifest_file srcdir destdir
# --overwrite allows overwriting already existing files. E.g. for installing into an existing binary release
# --destdir_exists means a) don't create destdir and b) it is not an error that it already exists. Mostly used
# for submanifests (@tbd -- needed as a command line argument?)
# --submanifest used with recursive manifest files

import os
import sys
import getopt
import logging
import shutil

# sibling package
import utils
from arch import getArch


# Module globals
log = logging.getLogger('install')

def doSubstitutions(line, arch):
  # note: lib/pymod do not have the "." and exe does have it, for historical reasons
  if arch == "darwin86":
    libsuffix = "dylib"
    pymodsuffix = "so"
    exesuffix = ""
    libprefix = "lib"
  elif arch == "win32":
    libsuffix = "dll"
    pymodsuffix = "pyd"
    exesuffix = ".exe"
    libprefix = ""
  else:
    libsuffix = "so"
    pymodsuffix = "so"
    exesuffix = ""
    libprefix = "lib"
      
  pythonversion = "%d.%d" % (sys.version_info[0], sys.version_info[1])

  if line.find("@") != -1:
    line = line.replace("@libsuffix@", libsuffix)
    line = line.replace("@pymodsuffix@", pymodsuffix)
    line = line.replace("@exesuffix@", exesuffix)
    line = line.replace("@libprefix@", libprefix)
    line = line.replace("@pythonversion@", pythonversion)
    
  return line


def installFromManifest(manifestFileName, srcdir, destdir, level, overwrite, destdirExists, allArchitectures=False, arch=None, allowSymbolicLinks=False):
  # use an additional two spaces of indentation for each submanifest level
  indent = ""
  for i in xrange(0, level):
    indent = indent + "    "

  nfailures = 0
  if arch is None:
    myarch = getArch()
  else:
    myarch = arch

  log.info(indent + "Installing from %s" % os.path.basename(manifestFileName))

  try:

    try:
      manifest = open(manifestFileName)
    except:
      log.error(indent + "Unable to open manifest file '%s'" % manifestFileName)
      raise

    if not os.path.isdir(srcdir):
      nfailures = nfailures + 1
      raise Exception(indent + 'Source directory "%s" does not exist or is not a directory' % srcdir)

    if os.path.exists(destdir) and not destdirExists:
      raise Exception(indent + 'Destination directory "%s" already exists. Delete before installing manifest.' % destdir)
  
    #
    # by default, files in the manifest file are specified by a pathname
    # relative to the source root. There are two exceptions
    # 1. pathnames to a manifest file (beginning with '@include') are relative to the path
    # of the directory containing the current manifest file
    # 2. pathnames specified with @local are relative to the directory containing the current 
    #    manifest file (typically "../files/<filename>").

    fullManifestPath = os.path.abspath(manifestFileName)
    manifestDirPath = os.path.dirname(fullManifestPath)

    if not destdirExists:
      os.makedirs(destdir, mode=0755)

    nfiles = 0
    nsubmanifests = 0

    # Go through the manifest file line by line. Primitive parsing is ok our
    # simple format, though it is a bit clunky. 
    lines = manifest.readlines()
    for line in lines:
      # ignore comments and blank lines
      line = line.strip()
      if line == "":
        continue
      if line[0] == "#":
        continue

      # @all@ expands to one file per architecture
      if line.find("@all@") != -1:
        if allArchitectures:
          arches = ["linux64", "linux32", "linux32arm", "darwin86", "win32"]
        else:
          arches = [myarch]
        for a in arches:
          newline = line.replace("@all@", a)
          # Do the substitutions right here, rather than on the second
          # pass, because this is where we know the architecture type
          newline = doSubstitutions(newline, a)
          log.debug("Adding rule '%s' based on '%s'", newline, line)
          lines.append(newline)
        continue
      # @allunix@ expands to one file per unix architecture
      elif line.find("@allunix@") != -1:
        if allArchitectures:
          arches = ["linux64", "linux32", "linux32arm", "darwin86"]
        elif myarch != "win32":
          arches = [myarch]
        else:
          arches = list()
        for a in arches:
          newline = line.replace("@allunix@", a)
          # Do the substitutions right here, rather than on the second
          # pass, because this is where we know the architecture type
          newline = doSubstitutions(newline, a)
          lines.append(newline)
          log.debug("Adding rule '%s' based on '%s'",newline, line)
        continue
      else:
        line = doSubstitutions(line, myarch)

      fields = line.split()

      if len(fields) == 3:
        # @arch <archname> <filename>
        # This is an architecture-specific filename. If allArchitectures is false, 
        # it is only copied if myarch matches. If allArchitectures is true, 
        # then the file is copied for that specific architecture. 
        # archname may be a specific architecture or may be "win32"
        # @include arch <manifestfile>
        # @local <srcpath> <destpath>
        if fields[0] == "@arch":
          if allArchitectures or \
             myarch == fields[1] or \
             (fields[1] == "unix" and myarch != "win32"):
            srcpath = fields[2]
            fullsrcpath = os.path.join(srcdir, srcpath)
            destpath = srcpath
          else:
            log.debug(indent + "Skipping line for different architecture: %s" % line)
            continue
        elif fields[0] == "@include":
          arch = fields[1]
          submanifest = fields[2]
          if allArchitectures or (arch  == "unix" and myarch != "win32") or arch == myarch:
            # @todo consolidate submanifest code with @include below?
            if not os.path.isabs(submanifest):
              submanifest = os.path.abspath(os.path.join(manifestDirPath, submanifest))
            log.info(indent + "Installing files from sub-manifest %s" % submanifest)
            nsubmanifests = nsubmanifests + 1
            try:
              installFromManifest(submanifest, srcdir, destdir, 
                                  level=level+1, overwrite=overwrite, 
                                  destdirExists=True, allArchitectures=allArchitectures, 
                                  arch=myarch, allowSymbolicLinks=allowSymbolicLinks)
            except KeyboardInterrupt:
              nfailures = nfailures + 1
              raise Exception("Keyboard interrupt")
            except:
              nfailures = nfailures + 1
              log.error(indent + "Installation from sub-manifest %s failed", submanifest)
              continue
          else:
            log.debug("Skipping line for different achitecture: %s" % line)
          continue
        elif fields[0] == "@local":
          srcpath = fields[1]
          fullsrcpath = os.path.abspath(os.path.join(manifestDirPath, fields[1]))
          destpath = fields[2]
        else:
          log.error(indent + 'Format error in manifest file. Lines with three fields must begin with @local or @arch')
          nfailures = nfailures+1
          continue

      elif len(fields) == 2:
        # @include <manifestfile>
        # Include another manifest file. Path is relative to current manifest file
        #
        # <srcpath> <destpath>
        # Copy from srcpath in source tree to destpath in dest tree
        if fields[0] == "@include":
          submanifest = fields[1]
          if not os.path.isabs(submanifest):
            submanifest = os.path.abspath(os.path.join(manifestDirPath, submanifest))
          log.info(indent + "Installing files from sub-manifest %s" % submanifest)
          nsubmanifests = nsubmanifests + 1
          try:
            installFromManifest(submanifest, srcdir, destdir, 
                                level=level+1, overwrite=overwrite, 
                                destdirExists=True, allArchitectures=allArchitectures,
                                arch=myarch,allowSymbolicLinks=allowSymbolicLinks)
          except KeyboardInterrupt:
            nfailures = nfailures + 1
            raise Exception("Keyboard interrupt")
          except:
            nfailures = nfailures + 1
            log.error(indent + "Installation from sub-manifest %s failed", submanifest)
          continue
        else:
          srcpath = fields[0]
          fullsrcpath = os.path.join(srcdir, srcpath)
          destpath = fields[1]
      elif len(fields) == 1:
        # <path>
        # Copy from source to dest, using same relative path
        srcpath = fields[0]
        destpath = srcpath
        fullsrcpath = os.path.join(srcdir, srcpath)
      else:
        log.error(indent + "Format error in manifest file. ")
        log.error(indent + "Bad line: '%s'" % line)
        nfailures = nfailures + 1
        continue

      if not os.path.exists(fullsrcpath):
        log.error(indent + "Source path %s does not exist" % fullsrcpath)
        nfailures = nfailures + 1
        continue

      fulldestpath = os.path.join(destdir, destpath)
      fulldestdir = os.path.dirname(fulldestpath)
      if not os.path.exists(fulldestdir):
        log.debug(indent + "Creating directory %s" % fulldestdir)
        os.makedirs(fulldestdir, 0755)

      if os.path.exists(fulldestpath):
        if not overwrite:
          log.error(indent + "File %s already exists and overwrite flag is not set" % (fulldestpath))
          nfailures = nfailures + 1
        else:
          log.debug(indent + "File %s already exists -- overwriting" % (fulldestpath))

      if overwrite and not os.path.exists(fulldestpath):
        log.warning(indent + "File %s does not exist and overwrite flag is set (not fatal)" % (fulldestpath))

      # Complain if the file is a symbolic link but ok if allowSymbolicLinks is specified
      if os.path.islink(fullsrcpath):
        if allowSymbolicLinks:
          target = os.readlink(fullsrcpath)
          if os.path.isabs(target):
            fullsrcpath = target
          else:
            fullsrcpath = os.path.normpath(os.path.join(os.path.dirname(fullsrcpath), target))
          log.warn(indent + "Copying target of symbolic link %s" % fullsrcpath)
        else:
          log.error(indent + "Skipping symbolic link %s" % fullsrcpath)
          nfailures = nfailures + 1
          continue

      # copy the file
      log.debug(indent + "Copying %s -> %s" % (srcpath, destpath))
      nfiles = nfiles + 1
      try:
        shutil.copy2(fullsrcpath, fulldestpath)
      except Exception, e:
        nfailures = nfailures + 1
        log.error(indent + "Unable to copy %s to %s. Error: %s", srcpath, destpath, e)
      
      ### while(newline != "")

    if nfailures == 0:
      if nsubmanifests == 0:
        log.info(indent + "Done. %d files copied" % (nfiles))
      else:
        log.info(indent + "Done. %d files copied %s submanifests processed" % (nfiles, nsubmanifests))
    else:
      log.info(indent + "Done. %d copy attempts; %d failures; %d submanifests" % (nfiles, nfailures, nsubmanifests))
      raise Exception("install from manifest failed")

  except Exception, e:
    log.error("Exception: %s", e)
    raise

def usage():
  print "usage: %s [--debug] [--overwrite] [--destdir_exists] [--all] manifest_file srcdir destdir" % sys.argv[0]
  print " --debug prints extra information"
  print " --overwrite allows overwriting of existing files. Implies --overwrite"
  print " --destdir_exists allows destdir to already exist"
  print " --all builds for all architectures"
  print " --arch <arch> builds for a specific (non-default) architecture"
  sys.exit(1)

if __name__ == "__main__":

  logging.basicConfig(format="%(levelname)-7s %(message)s", level=logging.INFO, stream=sys.stdout)
  # logging.getLogger('').setLevel(logging.INFO)
  manifestFileName = "manifest file not specified"

  try:
    longOptionSpec = ["destdir_exists", "overwrite", "debug", "all", "arch="]

    destdirExists = False
    overwrite = False
    allArchitectures = False
    try:
      (opts, args) = getopt.getopt(sys.argv[1:], "", longOptionSpec)
    except:
      usage()

    if len(args) != 3:
      usage()

    arch = None
    for (option, val) in opts:
      if option == "--destdir_exists":
        destdirExists = True
      elif option == "--debug":
        logging.getLogger('').setLevel(logging.DEBUG)
      elif option == "--overwrite":
        overwrite = True
        destdirExists = True
      elif option == "--all":
        allArchitectures = True
      elif option == "--arch":
        arch = val

    manifestFileName = os.path.abspath(os.path.normpath(os.path.expanduser(args[0])))
    srcdir = os.path.abspath(os.path.normpath(os.path.expanduser(args[1])))
    destdir = os.path.abspath(os.path.normpath(os.path.expanduser(args[2])))

    installFromManifest(manifestFileName, srcdir, destdir, 
                        level=0, overwrite=overwrite, destdirExists=destdirExists,
                        allArchitectures=allArchitectures, arch=arch)

  except SystemExit, s:
    # usage message
    pass
  except:
    log.error("Install from '%s' failed", manifestFileName)

