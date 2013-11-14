import sys
import os

buildSystemDir = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
if buildSystemDir not in sys.path:
  sys.path.insert(0, buildSystemDir)

import pybuild.utils as utils

def usage():
  print "%s [source directory] [dest directory]" % sys.argv[0]
  print "   source directory basename is, e.g., 'r12345' and has archive files for svn r12345"
  print "   dest directory basename is the name of the release, e.g. '1.3'"
  print "   This tool can be used to rename autobuilds to release builds and can"
  print "   also be used to rename release candidates to final releases, e.g. 1.3rc1 to 1.3"
  sys.exit(1)


if __name__ == "__main__":
  if len(sys.argv) != 3:
    usage()

  utils.initlog(False)
  sourceDir = sys.argv[1]
  sourceDir = os.path.abspath(os.path.normpath(os.path.expanduser(sourceDir)))
  destDir = sys.argv[2]
  destDir = os.path.abspath(os.path.normpath(os.path.expanduser(destDir)))

  if not os.path.exists(sourceDir):
    raise Exception("source directory '%s' does not exist" % sourceDir)

  if os.path.exists(destDir):
    raise Exception("destination directory '%s' already exists" % destDir)
  utils.createDir(destDir)

  oldStamp = os.path.basename(sourceDir)
  newStamp = os.path.basename(destDir)

  utils.log.info("Renaming release '%s' to release '%s'", oldStamp, newStamp)

  renameList = []
  for arch,archiveType in [("linux64", "tgz"), 
                           ("linux32", "tgz"), 
                           ("linux32arm", "tgz"), 
                           ("linux32armv7", "tgz"),
                           ("darwin86", "tgz"),
                           ("win32", "zip")]:
    oldname = "nupic-%s-%s" % (oldStamp, arch)
    newname = "nupic-%s-%s" % (newStamp, arch)
    renameList.append((oldname, newname, archiveType))

    #oldname = "nupic-npp-%s-%s" % (oldStamp, arch)
    #newname = "nupic-npp-%s-%s" % (newStamp, arch)
    #renameList.append((oldname, newname, archiveType))

#  for sourcetype in ["basicplugin", "learningplugin", "tools"]:
  for sourcetype in ["basicplugin"]:
    oldname = "nupic-%s-%s-source" % (oldStamp, sourcetype)
    newname = "nupic-%s-%s-source" % (newStamp, sourcetype)
    renameList.append((oldname, newname, "tgz"))
    renameList.append((oldname, newname, "zip"))

  print "Will perform the following renames:"
  for i in renameList:
    print "    %s" % str(i)

  tempDir = utils.createTemporaryDirectory("release_rename")
  print "renaming: %s" % str(renameList)
  try:
    for (oldname, newname, archiveType) in renameList:
      sourceArchive = os.path.join(sourceDir, oldname + "." + archiveType)
      if not os.path.exists(sourceArchive):
        utils.log.warn("Warning: archive '%s' does not exist", sourceArchive)
        continue
      
      utils.log.info("Extracting %s" % sourceArchive)
      extractedDir = utils.extractArchive(sourceArchive, tempDir)
      newArchive = utils.createArchive(extractedDir, destDir, rootRename=newname, type=archiveType)
      utils.log.info("Created '%s'", newArchive)
      utils.remove(extractedDir)

  finally:
    utils.remove(tempDir)

  utils.log.info("Done")
