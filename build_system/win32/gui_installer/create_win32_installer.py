import os
import sys
import glob
import shutil
import time
import subprocess
import tempfile
import string
import getopt

pythonVersion = sys.version[:3]
if pythonVersion == '2.6':
  full_pythonVersion = '2.6.6'
else:
  raise Exception('Bad Python version: ' + pythonVersion)
pyinstaller_version = '1.4'
# the version of wx that we install on user's system,
# not the version used by the installer
wx_version = '2.8'
full_wx_version = '2.8.11.0'

python_int_version = pythonVersion.replace(".", "")

def createInstaller(nta_install_dir, nupic_archive_path, installer_path, nupic_version, src_dir, debug=False, force=False):
  temp_dir = None
  try:
    # auxilliary files are in a direcory relaive to directory with this script
    installer_dir = os.path.dirname(os.path.abspath(__file__))

    # 3rd party (external) software via relative path
    external_dir = os.path.join(src_dir, r'external\src\Win32InstallerFiles')

    external_dir = os.path.abspath(external_dir)
    pyinstaller_dir = os.path.join(external_dir,
                                   'pyinstaller-%s' % pyinstaller_version)

    #print "Copying validate_license.exe to the installer dir"
    #license_validator = os.path.join(nta_install_dir, 'bin/validate_license.exe')
    #shutil.copy2(license_validator, installer_dir)

    temp_dir = tempfile.mkdtemp(prefix="win32installer.")
    print "Looking for external files in '%s'" % external_dir
    print "Using temporary directory '%s'" % temp_dir

    # Debug version should be distinguishable
    installer_name = os.path.basename(installer_path)

    #external_site_packages = os.path.join(external_dir, 'site-packages')
    #wxfile = os.path.join(external_site_packages, 'wx.pth')
    #wxversion = open(wxfile).read().strip()
    #wx_dir = os.path.join(external_site_packages, wxversion)
    #additional_site_packages = "'%s'" % wx_dir
    additional_site_packages=""

    if os.path.exists(installer_path) and not force:
      print "ERROR: %s already exists" % installer_path
      sys.exit(1)

    nupic_archive_name = os.path.basename(nupic_archive_path)
    if not os.path.exists(nupic_archive_path):
      print "ERROR: archive %s does not exist" % nupic_archive_path
      sys.exit(1)

    print 'Creating installer %s' % (installer_path)
    # Create NupicInstaller.spec
    try:
      template_file = os.path.join(installer_dir, 'NupicInstaller_template.spec')
      template = string.Template(open(template_file).read())
      # Prepare substitution dict
      d = dict(NupicArchivePath=nupic_archive_path,
               NupicArchiveName=nupic_archive_name,
               WorkDir=temp_dir,
               SourceDir=installer_dir,
               ExternalDir=external_dir,
               FullPythonVersion=full_pythonVersion,
               PythonVersion=pythonVersion,
               PythonIntVersion=python_int_version,
               WxVersion=wx_version,
               FullWxVersion=full_wx_version,
               InstallerName=installer_name,
               AdditionalSitePackages=additional_site_packages)
      installer_spec = template.substitute(d)
      spec_path = os.path.join(temp_dir, "NupicInstaller.spec")
      open(spec_path, 'w').write(installer_spec)

    except Exception, e:
      raise Exception('Error generating NupicInstaller.spec.py: %s' % str(e))

    # Create config.py
    try:
      template_file = os.path.join(installer_dir, 'config_template.py')
      template = string.Template(open(template_file).read())

      # Prepare substitution dict
      d = dict(NupicVersion=nupic_version,
               Debug=debug,
               PythonVersion=pythonVersion,
               FullPythonVersion=full_pythonVersion,
               WxVersion=wx_version)

      config = template.substitute(d)
      config_path = os.path.join(temp_dir, 'config.py')
      open(config_path, 'w').write(config)
      # Copy config.py into the gui_installer directory so that
      # NupicInstaller.pyw can be run easily (from the command line)
      # Do not copy to "config.py"  -- BIC-233
      try:
        shutil.copy2(config_path, "generated_config.py")
      except:
        print "Warning: unable to copy %s" % config_path
    except Exception, e:
      raise Exception('Error generating config.py: %s' % str(e))

    # Configure PyInstaller
    configurePath = os.path.join(pyinstaller_dir, "Configure.py")
    print "Configuring pyinstaller"
    retcode = subprocess.call(['python', configurePath])
    if retcode != 0:
      raise Exception("ERROR configuring pyinstaller.")

    # Launch PyInstaller
    build_py_path = os.path.join(pyinstaller_dir, 'Build.py')
    # os.environ["PYTHONPATH"] = wx_dir

    print "Running pyinstaller with spec file '%s'" % spec_path
    retcode = subprocess.call(['python', build_py_path, spec_path])
    if retcode != 0:
      raise Exception('ERROR running pyinstaller. return code: %d' % retcode)

    # Copy from temp directory to nupic archive directory
    if force:
      if os.path.exists(installer_path):
        os.remove(installer_path)
    os.rename(os.path.join(temp_dir, installer_name), installer_path)

  finally:
    if not debug and temp_dir is not None and os.path.isdir(temp_dir):
      shutil.rmtree(temp_dir)


def usage():
  print """\
python2 create_win32_installer.py <install_dir> <nupic_archive> <trunk> [--debug] [--force]

install_dir (mandatory):
  Path to the NuPIc installation dir (NuPIC must be installed)
  
nupic_archive (mandatory):
  Path to the location of the basic release (.zip file)
  The installer will be placed into the same directory
  (note: the underlying createInstaller method can place the installer in a different
  directory, but there is no current use case)

The archive name is expected to be of the form "nupic-<version>-win32.zip"
<version> can be of any form, including "r12345" and "npp-r12345".

trunk (mandatory):
  Location of the trunk. Used to find external files.

--debug (optional):
  A string that determines if a debug version will be produced. Specify '--debug'
  to create a debug version of the installer that displays exception traceback
  on failure and also the installed files.

--force (optional):
  Specify --force to force the generated installer to replace existing
  file with the same filename.

"""
  sys.exit(1)


def main():
  optionSpec = ["force", "debug"]
  try:
    (opts, args) = getopt.gnu_getopt(sys.argv[1:], "", optionSpec)
  except Exception, e:
    print "Error parsing command line: %s" % e
    usage()

  if len(args) != 3:
    usage()
    

  install_dir = args[0]
  install_dir = os.path.abspath(os.path.expanduser(os.path.normpath(args[0])))

  nupic_archive_path = args[1]
  nupic_archive_path = os.path.abspath(os.path.expanduser(os.path.normpath(nupic_archive_path)))
  nupic_archive_dir = os.path.dirname(nupic_archive_path)

  src_dir = args[2]
  src_dir = os.path.abspath(os.path.expanduser(os.path.normpath(src_dir)))

  nupic_archive = os.path.basename(nupic_archive_path)
  if not nupic_archive.startswith("nupic-"):
    raise Exception("archive name '%s' does not start with 'nupic-'" % nupic_archive)
  if not nupic_archive.endswith("-win32.zip"):
    raise Exception("archive name '%s' does not end with '-win32.zip'" % nupic_archive)

  # Chop off "nupic-" and "-win32.zip"
  nupic_version = nupic_archive[6:len(nupic_archive) - 10]

  debug = False
  force = False
  for (option, val) in opts:
    if option == "--debug":
      debug = True
    if option == "--force":
      force = True

  if debug:
    installer_path = os.path.join(nupic_archive_dir, "nupic-%s-win32_installer_debug.exe" % nupic_version)
  else:
    installer_path = os.path.join(nupic_archive_dir, "nupic-%s-win32_installer.exe" % nupic_version)

  createInstaller(install_dir, nupic_archive_path, installer_path, nupic_version, src_dir, debug, force)

if __name__=='__main__':
  main()

 # py .\create_win32_installer.py c:\nta\install .\nupic-npp-r27858-win32.zip z:\trunk --force
