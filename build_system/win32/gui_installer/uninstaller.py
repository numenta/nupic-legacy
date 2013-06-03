import os
import shutil
import installer
import firewall

def uninstallNupic():
                 
  """Uninstalls NuPIC

  * Remove the NuPIC installation directory
  * remove <install dir>\lib from PYTHONPATH
  * Remove NTA environment variable
  * Remove the runtime engine to the firewall exceptions list
  """
  install_dir = os.environ['NTA']
  
  # Remove the NuPIC directory
  try:
    shutil.rmtree(install_dir)
  except:
    pass
  
  lib_dir = os.path.join(install_dir, 'lib')
  python_path = os.environ['PYTHONPATH']
  items = python_path.split(';')
  items = [item.strip() for item in items if not item.startswith(lib_dir)]
  python_path = ';'.join(items)
  
  # Remove lib dir from PYTHONPATH
  installer.setCurrentUserEnvironmentVariable('PYTHONPATH', python_path)
  installer.setLocalMachineEnvironmentVariable('PYTHONPATH', python_path)

  # Clear NTA environment variable
  os.environ['NTA'] = ''
  installer.setCurrentUserEnvironmentVariable('NTA', '')
    
  # Remove numenta_runtime to firewall exceptions if OS is XP or up
  numenta_runtime_path = os.path.join(install_dir, r'bin\numenta_runtime.exe')
  firewall.remove(numenta_runtime_path)
  
if __name__=='__main__':
  uninstallNupic()

