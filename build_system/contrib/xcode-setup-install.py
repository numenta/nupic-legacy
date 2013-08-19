#!/usr/bin/env python

import os
import sys


doClean = ('clean' in sys.argv) or ('uninstall' in sys.argv)

rootDir = os.getcwd()
buildSystemDir = os.path.join(rootDir, 'build_system')

# Generate the configure input files.
setupCmd = 'python ' + os.path.join(buildSystemDir, 'setup.py')  + ' --autogen' \
                     + " --win32BuildDir '$(NTAX_BUILD_DIR)'"
print 'Running command:', setupCmd
sys.stdout.flush()

retCode = os.system(setupCmd)
if retCode != 0:
  print >>sys.stderr, 'setup.py failed: Error', retCode
  sys.exit(1)

buildDir = os.environ['BUILT_PRODUCTS_DIR']
buildStyle = os.environ['BUILD_STYLE']

# Build the configure command.
configureCmd = os.path.join(buildSystemDir, 'contrib', 'configure.py')
configureCmd += ' --mode=%s' % buildStyle
configureCmd += ' --builddir=%s' % buildDir

print 'Running command:', configureCmd
sys.stdout.flush()

retCode = os.system(configureCmd)
if retCode != 0:
  print >>sys.stderr, 'configure failed: Error', retCode
  sys.exit(1)

# Build
success = True
pushd = os.getcwd()
os.chdir(buildDir)

buildCmd = os.path.join(buildSystemDir, 'contrib', 'make.py')
if doClean: buildCmd += ' clean'

print 'Running command:', buildCmd
retCode = os.system(buildCmd)
if retCode != 0:
  print >>sys.stderr, 'Build failed: Error', retCode
  success = False

os.chdir(pushd)

if not success:
  sys.exit(1)


