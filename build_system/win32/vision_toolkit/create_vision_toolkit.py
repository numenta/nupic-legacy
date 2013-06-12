from __future__ import with_statement
import os
import sys
import glob
import shutil
import time
import subprocess
import getopt
import tarfile
import win32api
import win32con

pythonVersion = sys.version[:3]

def create_toolkit_release(trunk, install_dir, work_dir, version="DEV"):
  """Create the vision toolkit release in the release_dir"""

  release_dir = os.path.join(work_dir, 'install')
  print "Creating vision toolkit release in %s from installation at %s" % (release_dir, install_dir)

  # Clean the target dir to make sure starting from scratch
  if os.path.isfile(work_dir):
    os.remove(work_dir)
  if os.path.isdir(work_dir):
    print "Removing %s" % work_dir
    shutil.rmtree(work_dir)
  assert not os.path.exists(work_dir)

  # Use build system utilities to create the release.
  pybuild_dir = os.path.normpath(os.path.join(trunk, 'build_system/pybuild'))
  assert os.path.isdir(pybuild_dir)
  sys.path.insert(0, pybuild_dir)
  import manifest
  import utils
  utils.initlog(False)
  manifestFile = os.path.join(trunk,
    'release/toolkit_release/manifests/toolkit_release.manifest')

  manifest.installFromManifest(manifestFile, install_dir, release_dir, level=0, overwrite=False, destdirExists=False, allArchitectures=False)

  # Create version file which will show up in the about box
  versionFile = os.path.join(work_dir, ".version")
  open(versionFile, "w").write(version)

  print "Done creating release"

def copy_python(python_dir, work_dir):
  """Copy essential Python files and dirs to the work_dir"""
  important_files = 'python.exe pythonw.exe LICENSE.txt'.split()
  important_dirs = 'DLLs Lib libs include Scripts'.split()

  for d in important_dirs:
    print 'Copying %s...' % d
    shutil.copytree(os.path.join(python_dir, d), os.path.join(work_dir, d))

  for f in important_files:
    print 'Copying %s...' % f
    shutil.copy(os.path.join(python_dir, f), os.path.join(work_dir, f))

  shutil.copy('c:/windows/system32/python%s.dll' % sys.version[:3:2], work_dir)

def copy_launch_script(script_dir, trunk_dir, work_dir):
  # Copy launch script, icon and license file and other files
  vision_dir = os.path.join(work_dir, 'install/share/vision')
  files = [os.path.join(script_dir, 'VisionToolkitLauncher.pyw'),
           os.path.join(vision_dir, 'demo.ico'),
           os.path.join(vision_dir, 'demo_header.bmp'),
           os.path.join(vision_dir, 'demo_left.bmp'),
           os.path.join(vision_dir, 'LICENSE')]

  for f in files:
    print 'Copying %s...' % f
    shutil.copy(f, work_dir)

  # NuPIC requires a "bin" directory to be able to find the root
  bindir = os.path.join(work_dir, "install", "bin")
  if not os.path.exists(bindir):
    os.mkdir(bindir)


def move_nupic_bits(script_dir, trunk_dir, work_dir):
  # Move the RunVisionToolkit.py and rename it to VisionToolkit.pyw
  vision_dir = os.path.join(work_dir, 'install/share/vision')
  print 'Moving RunVisionToolkit.py --> VisionToolkit.pyw'
  shutil.move(os.path.join(vision_dir, 'RunVisionToolkit.py'),
              os.path.join(work_dir, 'VisionToolkit.pyw'))

  # Move the toolkit networks up
  print "Moving networks from share/vision to ./"
  shutil.move(os.path.join(vision_dir, 'networks'),
              os.path.join(work_dir, 'networks'))

  # Move the toolkit projects up
  print "Moving projects from share/vision to ./"
  shutil.move(os.path.join(vision_dir, 'projects'),
              os.path.join(work_dir, 'projects'))

  # # Move the toolkit help up
  # print "Moving help from share/vision to ./"
  # shutil.move(os.path.join(vision_dir, 'VisionToolkitHelp'),
  #             os.path.join(work_dir, 'VisionToolkitHelp'))

  ## Move the data and networks sub dirs
  #for d in ('data', 'networks'):
  #  print 'Moving', d
  #  shutil.move(os.path.join(vision_dir, d),
  #              os.path.join(work_dir, d))
  #
  ## Extract the the tarred dataset
  #data_dir = os.path.join(work_dir, 'data')
  #data_file = os.path.join(data_dir, 'nta4_test.tar.gz')
  #
  #assert os.path.isfile(data_file)
  #t = tarfile.open(name=data_file, mode="r:gz")
  #for member in t.getmembers():
  #  t.extract(member, os.path.dirname(data_file))
  #t.close()
  #
  ## Remove the original tar file
  #os.remove(data_file)
  #print 'Extracted ', data_file

  # Replace the default icon of traits with the demo icon
  traits_icon = os.path.join(
    work_dir,
    'install/lib/python%s/site-packages/enthought/traits/ui/wx/images/frame.ico'
    % pythonVersion)
  assert os.path.isfile(traits_icon)

  # Create a .licenseAccepted
  license_accepted_file = os.path.join(work_dir, '.licenseAccepted')
  open(license_accepted_file, 'w').write('Boring.....')
  win32api.SetFileAttributes(license_accepted_file, win32con.FILE_ATTRIBUTE_HIDDEN)

  shutil.copyfile(os.path.join(work_dir, 'demo.ico'), traits_icon)

def trim(work_dir):
  for d, s, files in os.walk(work_dir):
    for f in files:
      if os.path.splitext(f)[1] in ('.pyc', '.pyo'):
        os.remove(os.path.join(d, f))

def create_executable(trunk_dir, script_dir, work_dir, target):
  # Go to target dir and verify there is no executable yet
  os.chdir(work_dir)
  if os.path.exists('VisionToolkit.exe'):
    os.remove('VisionToolkit.exe')

  nsis = os.path.join(trunk_dir,
                      'external/win32/lib/buildtools/NSIS/makensis.exe')

  # Copy the NSIS script to work_dir because that's where it will execute
  shutil.copy(os.path.join(script_dir, 'vision_toolkit.nsi'), 'vision_toolkit.nsi')
  assert os.path.isfile(nsis)

  # Build the NSIS command line
  cmd = [nsis, 'vision_toolkit.nsi']
  #print ' '.join(cmd)

  # Launch NSIS and verify that the final executable has been created
  #subprocess.call(cmd)
  import utils
  import logging
  # log level was earlier set to info. We want all output from this command
  logging.getLogger('').setLevel(logging.DEBUG)
  utils.runCommand(cmd)
  assert os.path.isfile('VisionToolkit.exe')

  # Rename to target name
  try:
    shutil.move('VisionToolkit.exe', target)
  except Exception, e:
    print e
    raise

  assert os.path.isfile(target)
  print 'Final executable is:', target

def usage():
  print \
"""Usage: python2 create_vision_toolkit.py --install_dir=<install dir> --target=<target filename>
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
  tmpdir = os.environ["TEMP"]
  version = "DEV"
  for o, a in opts:
    if o == "--install_dir":
      install_dir = a
    elif o == '--target':
      target = a
    elif o == '--version':
      version = a
    elif o == '--tmpdir':
      tmpdir = a
    elif o == '--debug':
      debug = True

  if not os.path.isdir(install_dir) or target is None:
    if install_dir is not None:
      print "ERROR: install_dir %s does not exist" % install_dir
    if target is None:
      print "ERROR: target not specified"
    usage()

  # Locate directories
  script_dir = os.path.dirname(os.path.abspath(argv[0]))
  trunk_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
  python_dir = os.environ['NTAX_PYTHON_DIR']
  work_dir = os.path.join(tmpdir, 'VisionToolkit')

  target = os.path.abspath(target)

  # Verify that all of the diretories are valid
  for d in (trunk_dir, install_dir, python_dir):
    assert os.path.isdir(d)

  try:
    # Create the vision toolkit release
    create_toolkit_release(trunk_dir, install_dir, work_dir, version)

    # Copy all necessary Python files
    copy_python(python_dir, work_dir)

    # Copy launch script and license file
    copy_launch_script(script_dir, trunk_dir, work_dir)

    # Move NuPIC packages and the RunVisionToolkit.py
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
            '--target=%s/VisionToolkit.setup.exe' % os.environ['USERPROFILE'],
            '--debug']
  else:
    #"--install_dir=c:/nta/install" "--target=~/VisionToolkit.setup.exe" --debug
    argv = sys.argv

  main(argv)

  print 'Done.'
