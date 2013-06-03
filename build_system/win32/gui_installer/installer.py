log_file = 'loggggg.txt'
def out(s):
  open(log_file, 'a').write(str(s) + '\n')
  print str(s)

import os
import sys
import glob
import platform
import shutil
import time
import subprocess
import traceback
import zipfile
#import firewall
#import win32api
#import win32gui
#import win32con
#import win32com.client
import config
import stat
#import license_validator

from _winreg import *
from win32con import * # Win32 constants
from config import * # test of message boxes

install_dir = ''

# Dictionary to keep original environment variables to restore on cancel
env = {}

def getRegistryValue(hive, path, name):
  reg = None
  key = None
  try:
    try:
      reg = ConnectRegistry(None, hive)
      key = OpenKey(reg, path, 0, KEY_READ)

      value = QueryValueEx(key, name)[0]
      return value

    except Exception, e:
      return None
  finally:
    if key:
      CloseKey(key)
    if reg:
      CloseKey(reg)

def getDocumentsDir():
  """Get the user's documents directory

  """
  path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
  return getRegistryValue(HKEY_CURRENT_USER, path, 'Personal')
  #return r'C:\Users\Gigi\Documents'
  

log_file = os.path.join(getDocumentsDir(), 'nupic.installer.log.txt')
if os.path.exists(log_file):
  os.remove(log_file)


def formatExceptionInfo(maxTBlevel=10):
  cla, exc, trbk = sys.exc_info()
  excName = cla.__name__
  try:
    excArgs = exc.__dict__["args"]
  except KeyError:
    excArgs = "<no args>"
  excTb = traceback.format_tb(trbk, maxTBlevel)
  return (excName, excArgs, excTb)

def setEnvironmentVariable(hive, path, name, value):
  reg = None
  key = None
  try:
    reg = ConnectRegistry(None, hive)
    key = OpenKey(reg, path, 0, KEY_ALL_ACCESS)

    SetValueEx(key, name, 0, REG_EXPAND_SZ, value)
    try:
      win32gui.SendMessageTimeout(HWND_BROADCAST,
                                  WM_SETTINGCHANGE,
                                  0,
                                  'Environment',
                                  0,
                                  1000)
    except:
      pass
  finally:
    if key:
      CloseKey(key)
    if reg:
      CloseKey(reg)

def setCurrentUserEnvironmentVariable(name, value):
  setEnvironmentVariable(HKEY_CURRENT_USER, 'Environment', name, value)

def setLocalMachineEnvironmentVariable(name, value):
  path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
  setEnvironmentVariable(HKEY_LOCAL_MACHINE, path, name, value)

def getPythonDir(version):
  """Get the installed directory of Python

  Take into account the version
  """
  path = r'Software\Python\PythonCore\%s\InstallPath' % version
  python_dir = getRegistryValue(HKEY_CURRENT_USER, path, '')
  if not python_dir:
    python_dir = getRegistryValue(HKEY_LOCAL_MACHINE, path, '')
  return python_dir

def getWxDir(python_dir, version):
  """Get the installed directory of wx relative to PYTHONHOME
  Muliple version of wx may be installed. Assume that """

  dir = "wx-%s-msw-unicode" % version
  path = os.path.join(python_dir, "Lib", "site-packages", dir)
  if not os.path.exists(path):
    return None
  # it is possible that the right version of wx is installed, but
  # it is not the default
  pth_path = os.path.join(python_dir, "Lib", "site-packages", "wx.pth")
  if not os.path.exists(pth_path) or \
     open(pth_path).read().strip() != dir:
    out("wx %s is installed, but does not appear to be the default version")
    return None
  return path

def getProgramFilesDir():
  """Get the program files directory from the registry

  This is not necessarilly 'c:\Program Files'
  """

  path = r'SOFTWARE\Microsoft\Windows\CurrentVersion'
  return getRegistryValue(HKEY_LOCAL_MACHINE, path, 'ProgramFilesDir')

#def getLicenseDir():
#  """Get the Numenta sub-dir of the user's common files directory
#
#  """
#  path = r'SOFTWARE\Microsoft\Windows\CurrentVersion'
#  common_dir = getRegistryValue(HKEY_LOCAL_MACHINE, path, 'CommonFilesDir')
#  return os.path.join(common_dir, 'Numenta')
#
def installPython(version, binary_dir, force=False):
  """Install Python from the official installer

  Check that Python is not installed already (unless 'force' is True)

  Launch the .msi file using msiexec in interactive mode

  """
  python_dir = getPythonDir(version)

  # If this version of Python is already installed
  # just return (unless forced to install)
  out('Checking Python installation...')
  if python_dir and not force:
    out('Python %s is already installed at: %s' % (version, python_dir))
    return

  save_dir = os.getcwd()
  if binary_dir:
    os.chdir(binary_dir)
  # Get the proper .msi file

  out('Installing Python %s...' % version)
  python_installer = glob.glob('python-%s.*.msi' % version)[0]

  cmd = ['msiexec', '/i', python_installer]
  retcode = subprocess.call(cmd)

  os.chdir(save_dir)

  if retcode == 0:
    return

  if retcode == 1602: # Installation cancelled
    if not python_dir : # Installation cancelled
      raise Exception('Python installation cancelled')
    else:
      return

  raise Exception('Python installation failed. error code: %d' % retcode)

def installWx(pythonVersion, wxVersion, binary_dir, force=False):
  """Install Wx from the official installer

  Fails if python is not installed or if the same version of wx
  is already installed (unless 'force' is True)

  """
  # If this version of Python is already installed
  # just return (unless forced to install)
  out('Checking Python installation...')
  python_dir = getPythonDir(pythonVersion)

  if not python_dir:
    raise Exception('WX installation cancelled -- Python %s is not installed' % pythonVersion)

  wx_dir = getWxDir(python_dir, wxVersion)
  if wx_dir and not force:
    out('WX %s is already installed at: %s' % (wxVersion, wx_dir))
    return

  save_dir = os.getcwd()
  if binary_dir:
    os.chdir(binary_dir)

  out('Installing wx %s...' % wxVersion)
  v = sys.version[:3:2]
  files = glob.glob('wxPython%s*-win32-unicode-*-py%s*.exe' % (wxVersion, v))
  if not files:
    raise Exception("Unable to find installer package for wxPython %s " % (wxVersion))
  wx_installer = files[0]

  cmd = [wx_installer]
  retcode = subprocess.call(cmd)

  os.chdir(save_dir)

  if retcode == 0:
    return

  if retcode == 2:
    raise Exception("WX installation cancelled")

  raise Exception('Wx installation failed. error code: %d' % retcode)

#def installPywin32(version):
#  # Note: this method is currently broken.
#  # It is left in in case we want to add pywin32 to the installation
#  # in the future.
#  python_dir = getPythonDir(version)
#  Pywin32_dir = os.path.join(python_dir, 'Lib/site-packages/win32')
#  if os.path.exists(Pywin32_dir):
#    out('Pywin32 extensions are already installed')
#    return
#
#  pywin32_installer = 'pywin32-210.win32-py%s.exe' % version
#  cmd = [pywin32_installer]
#  retcode = subprocess.call(cmd)
#  if retcode != 0:
#    raise Exception('Pywin32 extensions installation failed. error code: %d' % retcode)
#
def extractZipFile(filename, target_dir, shouldAbort, onUpdate):
  """Extract zip file contents to a target directory

  * Unzip files, creating subdirs as needed into the target dir
  * Check the shouldAbort() function in every iteration and returns if True
  * Invoke the onUpdate callback function for each file
  """

  out('Calculating total compressed size of ' +  filename)
  if not os.path.isfile(filename):
    raise Exception("Unable to find zip file '%s'" % filename)
  z = zipfile.ZipFile(filename, 'r', zipfile.ZIP_DEFLATED)
  total_bytes = 0
  for info in z.infolist():
    if shouldAbort():
      return
    total_bytes += info.compress_size

  onUpdate('', 0, total_bytes)
  print 'Extracting ', filename
  for info in z.infolist():
    if shouldAbort():
      return
    name = info.filename
    n = name .replace('/', '\\')
    # skip first directory
    correct_name = n[n.find('\\')+1:]
    path = os.path.join(target_dir, correct_name)
    if path[-1] == ('\\'):
      continue

    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
      os.makedirs(parent_dir)
    assert os.path.isdir(parent_dir)

    if config.debug:
      out(path)
    text = z.read(name)
    # fix end of lines of text files
    if os.path.splitext(name)[1].lower() == '.txt':
      if not ('\r\n') in text:
        text = text.replace('\n', '\r\n')
    open(path, 'wb').write(text)
    #time.sleep(0.2)
    onUpdate(path, info.compress_size, total_bytes)


#def selectInstallDir(nupic_version):
#  """Display a browse for folder dialog and return the result
#
#  If the selected folder exists and is not empty let the user
#  go ahead or select another folder or cancel the installation
#  """
#
#  while (True):
#    shell = win32com.client.Dispatch('Shell.Application')
#    title = """\
#The installer will create the folder
#'nupic-%s' inside the folder you select.
#The installation folder is highlighted. """ % nupic_version
#    folder = shell.BrowseForFolder(0, title, 0, '')
#    if not folder:
#      sys.exit()
#    base_dir = folder.Items().Item().Path
#
#    global install_dir
#    install_dir = os.path.join(base_dir, 'nupic-%s' % nupic_version)
#
#    # install dir is not empty ask user for further action
#    if os.path.exists(install_dir) and os.listdir(install_dir):
#      result = displayMessage(nupic_version,
#                              remove_dir_message % (install_dir, install_dir),
#                              MB_YESNOCANCEL | MB_ICONQUESTION)
#      if result == IDYES:  # proceed with installation
#        return install_dir
#      elif result == IDNO: # Select a different install dir
#        continue
#      elif result == IDCANCEL: # cancel installation altogether
#        return sys.exit()
#    else:
#      return install_dir
#
#def restoreEnvironment():
#  for k, v in env.items():
#    setCurrentUserEnvironmentVariable(k, v)
#
def installNupic(nupic_version,
                 pythonVersion,
                 binary_dir,
                 install_dir,
                 shouldAbort,
                 sink):
  """Install NuPIC into a user selected folder

  * Extract NuPIC zip file to target dir
  * Add Python to the PATH
  * Add <target dir>\lib to PYTHONPATH as first entry (remove previous NuPIC)
  * Add NTA environment variable that points to NuPIC's installation dir
  * Add the runtime engine to the firewall exceptions list (if supported)

  This function is designed to work with an interactive GUI. The 'shouldAbort'
  function is called to verify if it the calling thread cancelled the operation
  the 'sink' object supports onUpdate, onFailure, onCancel and onComplete
  callback functions.

  If the installation is cancelled the environment variables are restored to
  their pre-installation value.
  """
  #out('NOT Installing NuPIC version %s. FOR DEBUGGING ONLY!!!!!' % (nupic_version))
  #sink.onComplete()
  #return

  out('Installing NuPIC version %s' % nupic_version)
  # Install NuPIC into target dir
  filename = 'nupic-%s-win32.zip' % nupic_version
  if binary_dir:
    filename = os.path.join(binary_dir, filename)

  # Save current values of environment variables
  global env

  # Remove target directory if exist
  if os.path.exists(install_dir):
    try:
      shutil.rmtree(install_dir)
    except OSError, e:
      message = remove_dir_failure_message % install_dir
      raise RuntimeError(message)

  out(install_dir)
  assert not os.path.exists(install_dir)
  if not os.path.isdir(install_dir):
    os.makedirs(install_dir)
  assert os.path.isdir(install_dir)

  cu_env_path = 'Environment'
  lm_env_path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
  for hive, env_path in [(HKEY_CURRENT_USER,  cu_env_path),
                         (HKEY_LOCAL_MACHINE, lm_env_path)]:
    
    print env_path
    path = getRegistryValue(hive, env_path, 'PATH')
    if path:
      break
    
  if not path:
    raise Exception('Unable to find PATH environment variable')
    
  out("Installing into directory '%s'" % install_dir)
  extractZipFile(filename, install_dir, shouldAbort, sink.onUpdate)
  if shouldAbort():
    sink.onCancel()
    return

  # Add Python to the PATH
  s = 'Adding Python to PATH...'
  out(s)
  sink.logMessage(s)
  python_dir = getPythonDir(pythonVersion)

  assert path
  tokens = path.split(';')
  # Remove exisitng Python entries from the PATH (danger! can remove too much)
  tokens = [t for t in tokens if not 'python' in t.lower()]
  tokens = [python_dir, os.path.join(python_dir, 'Scripts')] + tokens
  new_path = ';'.join(tokens)

  if hive == HKEY_CURRENT_USER:
    os.environ['PATH'] = new_path
    setCurrentUserEnvironmentVariable('PATH', new_path)
  #else:
  #  setLocalMachineEnvironmentVariable('PATH', new_path)

  if shouldAbort():
    sink.onCancel()
    restoreEnvironment(env)
    return

  # Set PYTHONPATH
  s = 'Setting PYTHONPATH...'
  out(s)
  sink.logMessage(s)
  try:
    #get exisitng PYTHONPATH
    python_path = os.environ['PYTHONPATH']
    env['PYTHONPATH'] = python_path

    # clean up previous NuPIC entries
    tokens = python_path.split(';')
    tokens = [t for t in tokens if not 'nupic' in t.lower()]
    python_path = ';'.join(tokens)
  except KeyError:
    python_path = ''

  site_packages_dir = r'lib\python%s\site-packages' % pythonVersion
  new_python_path = os.path.join(install_dir, site_packages_dir)

  if python_path:
    new_python_path += ';' + python_path

  os.environ['PYTHONPATH'] = new_python_path
  setCurrentUserEnvironmentVariable('PYTHONPATH', new_python_path)

  if shouldAbort():
    sink.onCancel()
    restoreEnvironment(env)
    return

  # set NTA
  sink.logMessage('Setting NTA environment variable...')
  try:
    env['NTA'] = os.environ['NTA']
  except KeyError:
    pass
  os.environ['NTA'] = install_dir
  setCurrentUserEnvironmentVariable('NTA', install_dir)

  if shouldAbort():
    sink.onCancel()
    restoreEnvironment(env)
    return

  # Add numenta_runtime to firewall exceptions if OS is XP or up
  s = 'Adding the runtime engine to the firewall exceptions list...'
  out(s)
  sink.logMessage(s)
  p = platform.platform().split('-')
  out('platform.platform(): ' + str(p))

  major, minor = p[2].split('.')[:2]
  if len(p) > 3:
    sp = p[3][-1]
    sp = int(sp)
  else:
    sp = 0
  #win32api.GetVersionEx()[:2]
  #sp = win32api.GetVersionEx()[4]
  #sp = int(sp[-1]) if sp else 0
  v = 10 * int(major) + int(minor)

  # Firewall API is available on Windows XP SP2 and newer
  # and Windows server 2003 SP1 and newer
  # See: http://en.wikipedia.org/wiki/Windows_Firewall
  if (v == 51 and sp >= 2) or \
     (v == 52 and sp >= 1) or \
     v >= 60:

    numenta_runtime_path = os.path.join(install_dir, r'bin\numenta_runtime.exe')
    try:
      firewall.allow(numenta_runtime_path)
    except Exception, e:
      # Just log the firewall failure and continue normally
      out('Firewall authorization failed for: ' + numenta_runtime_path)
      out(str(e))

  sink.onComplete()

def openVisionDir(install_dir):
  save_dir = os.getcwd()
  try:
    vision_dir = os.path.join(install_dir, r'share\vision')
    os.chdir(vision_dir)
    os.system('start cmd.exe /k')
  finally:
    os.chdir(save_dir)

#def findLicenseFile():
#  # See if the NTA_LICENSECONFIG points to a license file
#  try:
#    license_file = os.environ['NTA_LICENSECONFIG']
#    if not os.path.isfile(license_file):
#      raise Exception("""\
#The NTA_LICENSECONFIG environment variable doesn't point to
#a valid license file: %s""" % license_file)
#    return license_file
#  except KeyError:
#    pass
#
#  # Check the documents dir for existing license
#  license_dir = getLicenseDir()
#  license_files = glob.glob(os.path.join(license_dir, '*license.cfg'))
#
#  license_file_count = len(license_files)
#  if license_file_count == 0: # No license. That's cool. User will install one.
#    return ''
#  elif license_file_count == 1: # License already exists. Nice.
#    return license_files[0]
#  else: # Multiple licenses. Oooh, that's bad. User will need to do something.
#    raise Exception('Multiple license files found in %s' % license_dir)
#
#def validateLicenseFile(validate_license, license_file, binary_dir, pythonVersion):
#  """Validate the license file by invoking license_validator
#
#  license_validator writes 'valid' or error message to the output file
#  """
#  license_validator = os.path.join(binary_dir, 'license_validator.py')
#  output_file = os.path.abspath(os.path.join(getDocumentsDir(),
#                                             'temp.license.validation.txt'))
#  if os.path.exists(output_file):
#    os.remove(output_file)
#  save_dir = os.getcwd()
#  os.chdir(getDocumentsDir())
#  python = os.path.join(getPythonDir(pythonVersion), 'python.exe')
#  cmd = [python, license_validator, validate_license, license_file, output_file]
#  cmd = [t.replace('\\', '/') for t in cmd]
#  startupinfo = subprocess.STARTUPINFO()
#  startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#  print ' '.join(cmd)
#  rc = subprocess.Popen(cmd, startupinfo=startupinfo).wait()
#  print 'rc=', rc
#  assert rc == 0
#  os.chdir(save_dir)
#  result = open(output_file).read()
#  os.remove(output_file)
#  print 'result = "%s"' % result
#  return (result == 'valid', result)
#
#if __name__=='__main__':
#  import NupicInstaller
#  NupicInstaller.main()
