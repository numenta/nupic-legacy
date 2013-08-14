#!/usr/bin/env python

# Identical to make, but assumes that the default rule is install,
# rather than all (which just builds).
# Does not attempt install if clean is present.

import sys
import os
import string
import time

buildDir = os.environ['BUILDDIR']
makeJobs = os.environ['MK_JOBS']
pushd = os.getcwd()

if not os.path.exists(buildDir):
  os.makedirs(buildDir)
os.chdir(buildDir)

if 'clean' in sys.argv[1:]:
  retCode = os.system('make uninstall clean')
  if retCode != 0:
    print >>sys.stderr, 'Clean failed: Error', retCode
    sys.exit(1)
  else:
    print 'Clean completed.'
    sys.exit(0)
elif sys.argv[1:]:
  args = sys.argv[1:]
else:
  args = ['install']

useMake = True
if useMake:
  os.system('make -j %s ' % makeJobs)
  retCode = os.system(string.join(["make"] + args, " "))
  if retCode != 0:
    print >>sys.stderr, "Build failed. Error", retCode
    sys.exit(1)
  else:
    sys.exit(0)
