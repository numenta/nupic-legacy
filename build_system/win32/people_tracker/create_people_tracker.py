from __future__ import with_statement
import os
import sys
import glob
import random
import shutil
import time
import subprocess
import getopt
import tarfile
import win32api
import win32con

exe_name = 'NumentaPeopleTrackingDemo.exe'
# Locate directories
tmpdir = os.environ["TEMP"]
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
trunk_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
python_dir = os.environ['NTAX_PYTHON_DIR']
work_dir = os.path.join(tmpdir, 'PeopleTrackingDemo', str(random.getrandbits(32)))
release_dir = os.path.join(work_dir, 'install')

pybuild_dir = os.path.normpath(os.path.join(trunk_dir, 'build_system/pybuild'))
assert os.path.isdir(pybuild_dir)
sys.path.insert(0, pybuild_dir)
import manifest
import utils

def install_vitamind(target_dir):
  """Run the install_vitamind.py script

  Installs ffmpeg, scipy and vitamind obfuscated pipeline
  to the target dir
  """
  print 'install_vitamind() into', target_dir
  save_dir = os.getcwd()
  os.chdir(os.path.join(trunk_dir, 'external/src/python_modules/vitamind'))
  utils.runCommand(['python', 'install_vitamind.py', target_dir])
  os.chdir(save_dir)

def create_people_tracker_release(trunk_dir, install_dir, work_dir, version="DEV"):
  """Create the people tracker release in the release_dir"""
  # TODO: release_dir is a global

  print "Creating people tracker release in %s from installation at %s" % (release_dir, install_dir)

  # Clean the target dir to make sure starting from scratch
  if os.path.isfile(work_dir):
    os.remove(work_dir)
  if os.path.isdir(work_dir):
    print "Removing %s" % work_dir
    shutil.rmtree(work_dir)
  assert not os.path.exists(work_dir)

  # Use build system utilities to create the release.
  manifestFile = os.path.join(trunk_dir,
    'release/tracker_release/manifests/tracker_release.manifest')

  manifest.installFromManifest(manifestFile, install_dir, release_dir, level=0, overwrite=False, destdirExists=False, allArchitectures=False)

  # Create version file which will show up in the about box
  versionFile = os.path.join(work_dir, ".version")
  open(versionFile, "w").write(version)

  print "Done creating release"

def copy_python(python_dir, work_dir):
  """Copy essential Python files and dirs to the work_dir"""
  important_files = 'msvcr71.dll python.exe pythonw.exe LICENSE.txt'.split()
  important_dirs = 'DLLs Lib libs include Scripts'.split()

  for d in important_dirs:
    print 'Copying %s...' % d
    shutil.copytree(os.path.join(python_dir, d), os.path.join(work_dir, d))

  for f in important_files:
    print 'Copying %s...' % f
    shutil.copy(os.path.join(python_dir, f), os.path.join(work_dir, f))

  shutil.copy('c:/windows/system32/python%s.dll' % sys.version[:3:2], work_dir)

def copy_support_files(script_dir, trunk_dir, work_dir):
  """Copy icons, bitmaps and license files

  Also creates an install/bin dir if needed (required by NuPIC)
  """
  # Copy launch script, icon and license file and other files
  video_dir = os.path.join(work_dir, 'install/share/projects/video')
  files = [os.path.join(video_dir, 'demo.ico'),
           os.path.join(video_dir, 'demo_header.bmp'),
           os.path.join(video_dir, 'demo_left.bmp'),
           os.path.join(video_dir, 'demo_license.cfg'),
           os.path.join(video_dir, 'LICENSE')]

  for f in files:
    print 'Copying %s...' % f
    shutil.copy(f, work_dir)

  # NuPIC requires a "bin" directory to be able to find the root
  bindir = os.path.join(work_dir, 'install/bin')
  if not os.path.exists(bindir):
    os.mkdir(bindir)

def move_nupic_bits(script_dir, trunk_dir, work_dir):
  # Move the RunPeopleTracker.py and rename it to PeopleTracker.pyw
  video_dir = os.path.join(work_dir, 'install/share/projects/video')
  print 'Copying RunPeopleTrackingDemo.pyw to', work_dir
  shutil.copy(os.path.join(video_dir, 'RunPeopleTrackingDemo.pyw'),
              os.path.join(work_dir, 'RunPeopleTrackingDemo.pyw'))

  # Create a .licenseAccepted
  license_accepted_file = os.path.join(work_dir, '.licenseAccepted')
  open(license_accepted_file, 'w').write('THIS FILE DESIGNATES THAT THE PROVIDED LICENSE WAS ACCEPTED. DO NOT DELETE')
  win32api.SetFileAttributes(license_accepted_file, win32con.FILE_ATTRIBUTE_HIDDEN)

def trim(work_dir):
  for d, s, files in os.walk(work_dir):
    for f in files:
      if os.path.splitext(f)[1] in ('.pyc', '.pyo'):
        os.remove(os.path.join(d, f))

def create_executable(trunk_dir, script_dir, work_dir, target):
  # Go to target dir and verify there is no executable yet
  os.chdir(work_dir)
  if os.path.exists(exe_name):
    os.remove(exe_name)

  nsis = os.path.join(trunk_dir,
                      'external/win32/lib/buildtools/NSIS/makensis.exe')

  # Copy the NSIS script to work_dir because that's where it will execute
  shutil.copy(os.path.join(script_dir, 'people_tracker.nsi'), 'people_tracker.nsi')
  assert os.path.isfile(nsis)

  # Build the NSIS command line
  cmd = [nsis, 'people_tracker.nsi']
  #print ' '.join(cmd)

  # Launch NSIS and verify that the final executable has been created
  import utils
  import logging
  # log level was earlier set to info. We want all output from this command
  logging.getLogger('').setLevel(logging.DEBUG)
  utils.runCommand(cmd)
  assert os.path.isfile(exe_name)

  # Rename to target name
  try:
    shutil.move(exe_name, target)
  except Exception, e:
    print e
    raise

  assert os.path.isfile(target)
  print 'Final executable is:', target

def usage():
  print \
"""Usage: python2 create_people_tracker.py --install_dir=<install dir> --target=<target filename>
                                --tmpdir=<tmpdir> --version=<version> [--debug]

install_dir (required): The installation directory of NuPIC
target (required): full filename of the final executable (the installer)
version: a build number, e.g. r20014 -- used only by the autobuild
"""
  sys.exit(2)

def main(argv):

  try:
    opts, args = getopt.gnu_getopt(argv, '', ['install_dir=', 'target=', 'tmpdir=', 'version=', 'debug'])
  except Exception, e:
    print e
    usage()

  debug = False
  install_dir = None
  target = None
  version = "DEV"
  for o, a in opts:
    if o == "--install_dir":
      install_dir = a
    elif o == '--target':
      target = a
    elif o == '--version':
      version = a
    elif o == '--tmpdir':
      global tmpdir
      tmpdir = a
    elif o == '--debug':
      debug = True

  if install_dir is None or not os.path.isdir(install_dir) or target is None:
    if install_dir is not None:
      print "ERROR: install_dir %s does not exist" % install_dir
    if target is None:
      print "ERROR: target not specified"
    usage()

  # Initialize the logger
  utils.initlog(False)
  target = os.path.abspath(target)

  # Verify that all of the diretories are valid
  for d in (trunk_dir, install_dir, python_dir):
    assert os.path.isdir(d)

  try:
    # Run the vitamind install script (installs scipy and ffmpeg too)
    install_vitamind(install_dir)

    # Create the people tracker release
    create_people_tracker_release(trunk_dir, install_dir, work_dir, version)

    # Copy all necessary Python files
    copy_python(python_dir, work_dir)

    # Copy icons, license files, etc
    copy_support_files(script_dir, trunk_dir, work_dir)

    # Move NuPIC packages and the RunPeopleTracker.py
    move_nupic_bits(script_dir, trunk_dir, work_dir)

    # Cleanup .pyc and .pyo files
    trim(work_dir)

    # Create executable in work dir, rename to target
    create_executable(trunk_dir, script_dir, work_dir, target)
  finally:
    if not debug:
      # remove work dir
      os.chdir(script_dir)
      if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

if __name__=='__main__':
  if '-t' in sys.argv:
    argv = [sys.argv[0],
            '--install_dir=%s' % os.environ['NTAX_INSTALL_DIR'],
            '--target=%s/PeopleTracker.setup.exe' % os.environ['USERPROFILE'],
           ]
    #'--debug']
  else:
    #"--install_dir=c:/nta/install" "--target=~/PeopleTracker.setup.exe" --debug
    argv = sys.argv

  main(argv)

  print 'Done.'
