#!/usr/bin/env python2
import os
import sys
import getopt

def usage() :
    print "usage: " + sys.argv[0] + ": --mode=[debug,release] --builddir=[builddir] [--prefix=prefixdir]"
    sys.exit(1)

options = [
    "mode=", 
    "builddir=",
    "action=",
    "prefix="]
    
try:
    opts, args = getopt.getopt(sys.argv[1:], "m:b:a:", options)
except getopt.GetoptError:
    usage()

if len(args) > 0 :
    usage()

builddir="."
mode="debug"
action=""
prefix=None
for o,a in opts:
    if o in ("--mode", "-m"):
        mode=a
    if o in ("--builddir", "-b"):
        builddir=a
    if o in ("--action", "-a"):
        action=a
    if o in ("--prefix", ):
        prefix=a

# Ignore the clean action, which most-likely came from Xcode.
if (action == "clean"):
    print "Ignoring configure.py clean"
    sys.exit(0)

if (mode == "Debug"):
    mode = "debug"
elif (mode == "Release"):
    mode = "release"

if mode == "release":
#    if prefix is None:
#        prefix = "'${HOME}/nta/eng-release/${nta_platform}'"
    pass
elif mode == "debug":
    pass
else:
    usage();

builddir=os.path.abspath(builddir)

print "Configuring with mode " + mode + " in directory " + builddir

if not os.path.exists(builddir) :
    print "Creating directory " + builddir
    try:
        os.makedirs(builddir)
    except OSError, err:
        print "Unable to create directory. Error: " + err.strerror
        sys.exit(1)
    
if not os.path.isdir(builddir) :
    print "Specified directory name is not a directory - aborting"
    sys.exit(1)

srcdir = os.path.join(os.path.dirname(__file__), "..", "..")
pushd = os.getcwd()
os.chdir(srcdir)
srcdir = os.getcwd()
os.chdir(pushd)
#srcdir = os.getcwd()

pushd = os.getcwd()
os.chdir(builddir)

cmd = "configure "
if mode == "release":
    cmd = cmd + " --enable-optimization=yes --enable-debugsymbols=yes --enable-assertions=no"
else:
    cmd = cmd + " --enable-optimization=no  --enable-debugsymbols=yes --enable-assertions=yes"

if prefix is not None:
    cmd += " --prefix=" + prefix

print "Configuring with command " + cmd
retCode = os.system(srcdir + "/" + cmd)

#if (sys.platform == 'darwin'):
#print "Fixing external library TOC dates."
#os.system("make fixlibs")

os.chdir(pushd)

if retCode != 0:
  print "Configure failed: Error %d" % retCode
  sys.exit(1)

  



            

